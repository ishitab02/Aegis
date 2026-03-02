"""Historical TVL Tracking.

This module provides persistent TVL tracking capabilities:
- Store TVL snapshots with timestamps
- Calculate rolling averages (1h, 24h, 7d)
- Detect anomalous drops vs historical baseline
- In-memory storage with optional SQLite persistence
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from aegis.adapters.base import BaseProtocolAdapter

logger = logging.getLogger(__name__)

# ============ Time Constants ============

SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400
SECONDS_PER_WEEK = 604800


# ============ Data Models ============


class TVLSnapshot(BaseModel):
    """A single TVL snapshot at a point in time."""

    protocol_address: str
    tvl_wei: int
    timestamp: int
    block_number: int = 0
    protocol_type: str = ""

    @property
    def tvl_eth(self) -> float:
        """TVL in ETH (assuming 18 decimals)."""
        return self.tvl_wei / 10**18


class RollingAverage(BaseModel):
    """Rolling average TVL over a time period."""

    period_seconds: int
    period_name: str  # "1h", "24h", "7d"
    average_tvl: int
    sample_count: int
    start_timestamp: int
    end_timestamp: int


class AnomalyType(str, Enum):
    """Types of TVL anomalies."""

    SUDDEN_DROP = "SUDDEN_DROP"
    GRADUAL_DECLINE = "GRADUAL_DECLINE"
    BELOW_BASELINE = "BELOW_BASELINE"
    FLASH_DRAIN = "FLASH_DRAIN"
    RECOVERY = "RECOVERY"


class TVLAnomaly(BaseModel):
    """Detected TVL anomaly."""

    protocol_address: str
    anomaly_type: AnomalyType
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    current_tvl: int
    baseline_tvl: int
    deviation_percent: float
    detected_at: int
    message: str


class HistoricalStats(BaseModel):
    """Historical statistics for a protocol's TVL."""

    protocol_address: str
    current_tvl: int
    avg_1h: int
    avg_24h: int
    avg_7d: int
    change_1h_percent: float
    change_24h_percent: float
    change_7d_percent: float
    min_tvl_24h: int
    max_tvl_24h: int
    snapshot_count: int
    first_snapshot: int
    last_snapshot: int


# ============ Anomaly Detection Thresholds ============


@dataclass
class AnomalyThresholds:
    """Thresholds for anomaly detection."""

    # Sudden drop thresholds (single snapshot vs previous)
    sudden_drop_critical: float = -20.0  # >= 20% drop = CRITICAL
    sudden_drop_high: float = -10.0  # >= 10% drop = HIGH
    sudden_drop_medium: float = -5.0  # >= 5% drop = MEDIUM

    # Below baseline thresholds (current vs rolling average)
    baseline_deviation_critical: float = -30.0
    baseline_deviation_high: float = -20.0
    baseline_deviation_medium: float = -10.0

    # Flash drain (very rapid drop within minutes)
    flash_drain_threshold: float = -15.0  # 15% drop in < 5 minutes
    flash_drain_window_seconds: int = 300  # 5 minutes


DEFAULT_THRESHOLDS = AnomalyThresholds()


# ============ In-Memory History Store ============


class TVLHistoryStore:
    """In-memory store for TVL history with rolling window.

    Maintains a configurable window of historical snapshots for each protocol.
    """

    def __init__(
        self,
        max_snapshots_per_protocol: int = 10080,  # 1 week at 1 snapshot/min
        snapshot_interval_seconds: int = 60,
    ):
        self._snapshots: dict[str, deque[TVLSnapshot]] = {}
        self._max_snapshots = max_snapshots_per_protocol
        self._interval = snapshot_interval_seconds
        self._lock = asyncio.Lock()

    async def add_snapshot(self, snapshot: TVLSnapshot) -> None:
        """Add a TVL snapshot for a protocol."""
        async with self._lock:
            addr = snapshot.protocol_address.lower()
            if addr not in self._snapshots:
                self._snapshots[addr] = deque(maxlen=self._max_snapshots)
            self._snapshots[addr].append(snapshot)

    def add_snapshot_sync(self, snapshot: TVLSnapshot) -> None:
        """Synchronous version of add_snapshot."""
        addr = snapshot.protocol_address.lower()
        if addr not in self._snapshots:
            self._snapshots[addr] = deque(maxlen=self._max_snapshots)
        self._snapshots[addr].append(snapshot)

    def get_snapshots(
        self,
        protocol_address: str,
        since_timestamp: int | None = None,
        limit: int | None = None,
    ) -> list[TVLSnapshot]:
        """Get snapshots for a protocol, optionally filtered by time."""
        addr = protocol_address.lower()
        if addr not in self._snapshots:
            return []

        snapshots = list(self._snapshots[addr])

        if since_timestamp is not None:
            snapshots = [s for s in snapshots if s.timestamp >= since_timestamp]

        if limit is not None:
            snapshots = snapshots[-limit:]

        return snapshots

    def get_latest_snapshot(self, protocol_address: str) -> TVLSnapshot | None:
        """Get the most recent snapshot for a protocol."""
        addr = protocol_address.lower()
        if addr not in self._snapshots or not self._snapshots[addr]:
            return None
        return self._snapshots[addr][-1]

    def get_previous_snapshot(self, protocol_address: str) -> TVLSnapshot | None:
        """Get the second most recent snapshot for a protocol."""
        addr = protocol_address.lower()
        if addr not in self._snapshots or len(self._snapshots[addr]) < 2:
            return None
        return self._snapshots[addr][-2]

    def get_snapshot_count(self, protocol_address: str) -> int:
        """Get the number of snapshots for a protocol."""
        addr = protocol_address.lower()
        return len(self._snapshots.get(addr, []))

    def clear(self, protocol_address: str | None = None) -> None:
        """Clear snapshots for a protocol or all protocols."""
        if protocol_address:
            addr = protocol_address.lower()
            if addr in self._snapshots:
                self._snapshots[addr].clear()
        else:
            self._snapshots.clear()


# ============ SQLite Persistence ============


class SQLiteTVLStore:
    """SQLite-based persistent TVL history store."""

    def __init__(self, db_path: str | Path = ":memory:"):
        self._db_path = str(db_path)
        self._conn: sqlite3.Connection | None = None
        self._initialized = False

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def initialize(self) -> None:
        """Initialize database schema."""
        if self._initialized:
            return

        conn = self._get_conn()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tvl_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                protocol_address TEXT NOT NULL,
                tvl_wei TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                block_number INTEGER DEFAULT 0,
                protocol_type TEXT DEFAULT '',
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            );

            CREATE INDEX IF NOT EXISTS idx_snapshots_protocol
                ON tvl_snapshots(protocol_address);

            CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp
                ON tvl_snapshots(timestamp);

            CREATE INDEX IF NOT EXISTS idx_snapshots_protocol_timestamp
                ON tvl_snapshots(protocol_address, timestamp);
            """
        )
        conn.commit()
        self._initialized = True

    def add_snapshot(self, snapshot: TVLSnapshot) -> int:
        """Add a snapshot and return the row ID."""
        self.initialize()
        conn = self._get_conn()
        cursor = conn.execute(
            """
            INSERT INTO tvl_snapshots (protocol_address, tvl_wei, timestamp, block_number, protocol_type)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                snapshot.protocol_address.lower(),
                str(snapshot.tvl_wei),
                snapshot.timestamp,
                snapshot.block_number,
                snapshot.protocol_type,
            ),
        )
        conn.commit()
        return cursor.lastrowid or 0

    def get_snapshots(
        self,
        protocol_address: str,
        since_timestamp: int | None = None,
        until_timestamp: int | None = None,
        limit: int = 1000,
    ) -> list[TVLSnapshot]:
        """Get snapshots for a protocol with optional time filtering."""
        self.initialize()
        conn = self._get_conn()

        query = "SELECT * FROM tvl_snapshots WHERE protocol_address = ?"
        params: list[Any] = [protocol_address.lower()]

        if since_timestamp is not None:
            query += " AND timestamp >= ?"
            params.append(since_timestamp)

        if until_timestamp is not None:
            query += " AND timestamp <= ?"
            params.append(until_timestamp)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()

        return [
            TVLSnapshot(
                protocol_address=row["protocol_address"],
                tvl_wei=int(row["tvl_wei"]),
                timestamp=row["timestamp"],
                block_number=row["block_number"],
                protocol_type=row["protocol_type"],
            )
            for row in reversed(rows)  # Return chronologically
        ]

    def get_latest_snapshot(self, protocol_address: str) -> TVLSnapshot | None:
        """Get the most recent snapshot."""
        snapshots = self.get_snapshots(protocol_address, limit=1)
        return snapshots[0] if snapshots else None

    def cleanup_old_snapshots(self, max_age_seconds: int = SECONDS_PER_WEEK * 4) -> int:
        """Delete snapshots older than max_age_seconds. Returns count deleted."""
        self.initialize()
        conn = self._get_conn()
        cutoff = int(time.time()) - max_age_seconds
        cursor = conn.execute(
            "DELETE FROM tvl_snapshots WHERE timestamp < ?", (cutoff,)
        )
        conn.commit()
        return cursor.rowcount

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None


# ============ Historical TVL Tracker ============


class HistoricalTVLTracker:
    """Tracks TVL history and detects anomalies.

    Combines in-memory cache for fast access with optional SQLite persistence.
    """

    def __init__(
        self,
        db_path: str | Path | None = None,
        thresholds: AnomalyThresholds | None = None,
    ):
        self._memory_store = TVLHistoryStore()
        self._sqlite_store = SQLiteTVLStore(db_path) if db_path else None
        self._thresholds = thresholds or DEFAULT_THRESHOLDS
        self._adapters: dict[str, "BaseProtocolAdapter"] = {}

    def register_adapter(self, protocol_address: str, adapter: "BaseProtocolAdapter") -> None:
        """Register an adapter for automatic TVL polling."""
        self._adapters[protocol_address.lower()] = adapter

    async def record_snapshot(
        self,
        protocol_address: str,
        tvl_wei: int,
        block_number: int = 0,
        protocol_type: str = "",
    ) -> TVLSnapshot:
        """Record a new TVL snapshot."""
        snapshot = TVLSnapshot(
            protocol_address=protocol_address,
            tvl_wei=tvl_wei,
            timestamp=int(time.time()),
            block_number=block_number,
            protocol_type=protocol_type,
        )

        # Add to memory store
        await self._memory_store.add_snapshot(snapshot)

        # Persist to SQLite if configured
        if self._sqlite_store:
            self._sqlite_store.add_snapshot(snapshot)

        logger.debug(
            "Recorded TVL snapshot: %s = %d wei at %d",
            protocol_address[:10],
            tvl_wei,
            snapshot.timestamp,
        )

        return snapshot

    def record_snapshot_sync(
        self,
        protocol_address: str,
        tvl_wei: int,
        block_number: int = 0,
        protocol_type: str = "",
    ) -> TVLSnapshot:
        """Synchronous version of record_snapshot."""
        snapshot = TVLSnapshot(
            protocol_address=protocol_address,
            tvl_wei=tvl_wei,
            timestamp=int(time.time()),
            block_number=block_number,
            protocol_type=protocol_type,
        )

        self._memory_store.add_snapshot_sync(snapshot)

        if self._sqlite_store:
            self._sqlite_store.add_snapshot(snapshot)

        return snapshot

    def get_rolling_average(
        self,
        protocol_address: str,
        period_seconds: int,
        period_name: str = "",
    ) -> RollingAverage | None:
        """Calculate rolling average TVL for a time period."""
        now = int(time.time())
        since = now - period_seconds

        # Try memory store first
        snapshots = self._memory_store.get_snapshots(protocol_address, since_timestamp=since)

        # Fall back to SQLite if needed
        if not snapshots and self._sqlite_store:
            snapshots = self._sqlite_store.get_snapshots(
                protocol_address, since_timestamp=since
            )

        if not snapshots:
            return None

        total_tvl = sum(s.tvl_wei for s in snapshots)
        avg_tvl = total_tvl // len(snapshots)

        return RollingAverage(
            period_seconds=period_seconds,
            period_name=period_name or f"{period_seconds}s",
            average_tvl=avg_tvl,
            sample_count=len(snapshots),
            start_timestamp=snapshots[0].timestamp,
            end_timestamp=snapshots[-1].timestamp,
        )

    def get_historical_stats(self, protocol_address: str) -> HistoricalStats | None:
        """Get comprehensive historical statistics."""
        now = int(time.time())

        # Get snapshots for different periods
        snapshots_1h = self._memory_store.get_snapshots(
            protocol_address, since_timestamp=now - SECONDS_PER_HOUR
        )
        snapshots_24h = self._memory_store.get_snapshots(
            protocol_address, since_timestamp=now - SECONDS_PER_DAY
        )
        snapshots_7d = self._memory_store.get_snapshots(
            protocol_address, since_timestamp=now - SECONDS_PER_WEEK
        )

        # Get latest snapshot
        latest = self._memory_store.get_latest_snapshot(protocol_address)
        if not latest:
            return None

        # Calculate averages
        avg_1h = sum(s.tvl_wei for s in snapshots_1h) // len(snapshots_1h) if snapshots_1h else 0
        avg_24h = sum(s.tvl_wei for s in snapshots_24h) // len(snapshots_24h) if snapshots_24h else 0
        avg_7d = sum(s.tvl_wei for s in snapshots_7d) // len(snapshots_7d) if snapshots_7d else 0

        # Calculate changes
        def calc_change(current: int, baseline: int) -> float:
            if baseline == 0:
                return 0.0
            return ((current - baseline) / baseline) * 100

        change_1h = calc_change(latest.tvl_wei, avg_1h) if avg_1h else 0.0
        change_24h = calc_change(latest.tvl_wei, avg_24h) if avg_24h else 0.0
        change_7d = calc_change(latest.tvl_wei, avg_7d) if avg_7d else 0.0

        # Min/max for 24h
        min_24h = min(s.tvl_wei for s in snapshots_24h) if snapshots_24h else 0
        max_24h = max(s.tvl_wei for s in snapshots_24h) if snapshots_24h else 0

        # First/last timestamps
        all_snapshots = self._memory_store.get_snapshots(protocol_address)
        first_ts = all_snapshots[0].timestamp if all_snapshots else 0
        last_ts = all_snapshots[-1].timestamp if all_snapshots else 0

        return HistoricalStats(
            protocol_address=protocol_address,
            current_tvl=latest.tvl_wei,
            avg_1h=avg_1h,
            avg_24h=avg_24h,
            avg_7d=avg_7d,
            change_1h_percent=change_1h,
            change_24h_percent=change_24h,
            change_7d_percent=change_7d,
            min_tvl_24h=min_24h,
            max_tvl_24h=max_24h,
            snapshot_count=len(all_snapshots),
            first_snapshot=first_ts,
            last_snapshot=last_ts,
        )

    def detect_anomalies(self, protocol_address: str) -> list[TVLAnomaly]:
        """Detect TVL anomalies for a protocol."""
        anomalies: list[TVLAnomaly] = []
        now = int(time.time())

        # Get latest and previous snapshots
        latest = self._memory_store.get_latest_snapshot(protocol_address)
        previous = self._memory_store.get_previous_snapshot(protocol_address)

        if not latest:
            return anomalies

        # Get rolling averages for baseline
        avg_24h = self.get_rolling_average(protocol_address, SECONDS_PER_DAY, "24h")

        # 1. Check for sudden drop (current vs previous)
        if previous and previous.tvl_wei > 0:
            change_pct = ((latest.tvl_wei - previous.tvl_wei) / previous.tvl_wei) * 100

            if change_pct <= self._thresholds.sudden_drop_critical:
                anomalies.append(
                    TVLAnomaly(
                        protocol_address=protocol_address,
                        anomaly_type=AnomalyType.SUDDEN_DROP,
                        severity="CRITICAL",
                        current_tvl=latest.tvl_wei,
                        baseline_tvl=previous.tvl_wei,
                        deviation_percent=change_pct,
                        detected_at=now,
                        message=f"Critical TVL drop: {change_pct:.2f}% in single snapshot",
                    )
                )
            elif change_pct <= self._thresholds.sudden_drop_high:
                anomalies.append(
                    TVLAnomaly(
                        protocol_address=protocol_address,
                        anomaly_type=AnomalyType.SUDDEN_DROP,
                        severity="HIGH",
                        current_tvl=latest.tvl_wei,
                        baseline_tvl=previous.tvl_wei,
                        deviation_percent=change_pct,
                        detected_at=now,
                        message=f"High TVL drop: {change_pct:.2f}% in single snapshot",
                    )
                )
            elif change_pct <= self._thresholds.sudden_drop_medium:
                anomalies.append(
                    TVLAnomaly(
                        protocol_address=protocol_address,
                        anomaly_type=AnomalyType.SUDDEN_DROP,
                        severity="MEDIUM",
                        current_tvl=latest.tvl_wei,
                        baseline_tvl=previous.tvl_wei,
                        deviation_percent=change_pct,
                        detected_at=now,
                        message=f"Medium TVL drop: {change_pct:.2f}% in single snapshot",
                    )
                )

        # 2. Check deviation from 24h baseline
        if avg_24h and avg_24h.average_tvl > 0:
            baseline_change = ((latest.tvl_wei - avg_24h.average_tvl) / avg_24h.average_tvl) * 100

            if baseline_change <= self._thresholds.baseline_deviation_critical:
                anomalies.append(
                    TVLAnomaly(
                        protocol_address=protocol_address,
                        anomaly_type=AnomalyType.BELOW_BASELINE,
                        severity="CRITICAL",
                        current_tvl=latest.tvl_wei,
                        baseline_tvl=avg_24h.average_tvl,
                        deviation_percent=baseline_change,
                        detected_at=now,
                        message=f"TVL {baseline_change:.2f}% below 24h average",
                    )
                )
            elif baseline_change <= self._thresholds.baseline_deviation_high:
                anomalies.append(
                    TVLAnomaly(
                        protocol_address=protocol_address,
                        anomaly_type=AnomalyType.BELOW_BASELINE,
                        severity="HIGH",
                        current_tvl=latest.tvl_wei,
                        baseline_tvl=avg_24h.average_tvl,
                        deviation_percent=baseline_change,
                        detected_at=now,
                        message=f"TVL {baseline_change:.2f}% below 24h average",
                    )
                )

        # 3. Check for flash drain (rapid drop within window)
        window_start = now - self._thresholds.flash_drain_window_seconds
        window_snapshots = self._memory_store.get_snapshots(
            protocol_address, since_timestamp=window_start
        )

        if len(window_snapshots) >= 2:
            first_in_window = window_snapshots[0]
            if first_in_window.tvl_wei > 0:
                flash_change = ((latest.tvl_wei - first_in_window.tvl_wei) / first_in_window.tvl_wei) * 100

                if flash_change <= self._thresholds.flash_drain_threshold:
                    anomalies.append(
                        TVLAnomaly(
                            protocol_address=protocol_address,
                            anomaly_type=AnomalyType.FLASH_DRAIN,
                            severity="CRITICAL",
                            current_tvl=latest.tvl_wei,
                            baseline_tvl=first_in_window.tvl_wei,
                            deviation_percent=flash_change,
                            detected_at=now,
                            message=f"Flash drain detected: {flash_change:.2f}% drop in {self._thresholds.flash_drain_window_seconds}s",
                        )
                    )

        return anomalies

    def close(self) -> None:
        """Close any open resources."""
        if self._sqlite_store:
            self._sqlite_store.close()


# ============ Factory Functions ============


_default_tracker: HistoricalTVLTracker | None = None


def get_tvl_tracker(db_path: str | Path | None = None) -> HistoricalTVLTracker:
    """Get or create the default TVL tracker."""
    global _default_tracker
    if _default_tracker is None:
        _default_tracker = HistoricalTVLTracker(db_path)
    return _default_tracker


def reset_tvl_tracker() -> None:
    """Reset the default tracker (useful for testing)."""
    global _default_tracker
    if _default_tracker:
        _default_tracker.close()
    _default_tracker = None
