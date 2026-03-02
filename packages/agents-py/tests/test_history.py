"""Tests for the historical TVL tracking module.

These tests verify TVL snapshot storage, rolling averages, and anomaly detection.
"""

import time
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from aegis.adapters.history import (
    SECONDS_PER_HOUR,
    AnomalyThresholds,
    AnomalyType,
    HistoricalTVLTracker,
    RollingAverage,
    SQLiteTVLStore,
    TVLAnomaly,
    TVLHistoryStore,
    TVLSnapshot,
    get_tvl_tracker,
    reset_tvl_tracker,
)

# ============ TVLSnapshot Tests ============


class TestTVLSnapshot:
    """Tests for TVLSnapshot model."""

    def test_create_snapshot(self):
        """Test creating a TVL snapshot."""
        snapshot = TVLSnapshot(
            protocol_address="0x1234567890123456789012345678901234567890",
            tvl_wei=1000 * 10**18,
            timestamp=int(time.time()),
            block_number=12345678,
            protocol_type="aave_v3",
        )
        assert snapshot.tvl_wei == 1000 * 10**18
        assert snapshot.protocol_type == "aave_v3"

    def test_tvl_eth_property(self):
        """Test tvl_eth property conversion."""
        snapshot = TVLSnapshot(
            protocol_address="0x1234",
            tvl_wei=2 * 10**18,  # 2 ETH
            timestamp=int(time.time()),
        )
        assert snapshot.tvl_eth == 2.0


# ============ RollingAverage Tests ============


class TestRollingAverage:
    """Tests for RollingAverage model."""

    def test_create_rolling_average(self):
        """Test creating a rolling average."""
        avg = RollingAverage(
            period_seconds=3600,
            period_name="1h",
            average_tvl=1000 * 10**18,
            sample_count=60,
            start_timestamp=1000,
            end_timestamp=4600,
        )
        assert avg.period_name == "1h"
        assert avg.sample_count == 60


# ============ TVLAnomaly Tests ============


class TestTVLAnomaly:
    """Tests for TVLAnomaly model."""

    def test_create_anomaly(self):
        """Test creating an anomaly."""
        anomaly = TVLAnomaly(
            protocol_address="0x1234",
            anomaly_type=AnomalyType.SUDDEN_DROP,
            severity="CRITICAL",
            current_tvl=500 * 10**18,
            baseline_tvl=1000 * 10**18,
            deviation_percent=-50.0,
            detected_at=int(time.time()),
            message="TVL dropped 50%",
        )
        assert anomaly.anomaly_type == AnomalyType.SUDDEN_DROP
        assert anomaly.severity == "CRITICAL"


# ============ TVLHistoryStore Tests ============


class TestTVLHistoryStore:
    """Tests for in-memory TVL history store."""

    def test_add_and_get_snapshot(self):
        """Test adding and retrieving snapshots."""
        store = TVLHistoryStore()
        snapshot = TVLSnapshot(
            protocol_address="0x1234",
            tvl_wei=1000,
            timestamp=int(time.time()),
        )

        store.add_snapshot_sync(snapshot)
        snapshots = store.get_snapshots("0x1234")

        assert len(snapshots) == 1
        assert snapshots[0].tvl_wei == 1000

    def test_get_latest_snapshot(self):
        """Test getting the most recent snapshot."""
        store = TVLHistoryStore()
        now = int(time.time())

        store.add_snapshot_sync(TVLSnapshot(
            protocol_address="0x1234",
            tvl_wei=1000,
            timestamp=now - 100,
        ))
        store.add_snapshot_sync(TVLSnapshot(
            protocol_address="0x1234",
            tvl_wei=2000,
            timestamp=now,
        ))

        latest = store.get_latest_snapshot("0x1234")
        assert latest is not None
        assert latest.tvl_wei == 2000

    def test_get_previous_snapshot(self):
        """Test getting the second most recent snapshot."""
        store = TVLHistoryStore()
        now = int(time.time())

        store.add_snapshot_sync(TVLSnapshot(
            protocol_address="0x1234",
            tvl_wei=1000,
            timestamp=now - 100,
        ))
        store.add_snapshot_sync(TVLSnapshot(
            protocol_address="0x1234",
            tvl_wei=2000,
            timestamp=now,
        ))

        previous = store.get_previous_snapshot("0x1234")
        assert previous is not None
        assert previous.tvl_wei == 1000

    def test_filter_by_timestamp(self):
        """Test filtering snapshots by timestamp."""
        store = TVLHistoryStore()
        now = int(time.time())

        store.add_snapshot_sync(TVLSnapshot(
            protocol_address="0x1234",
            tvl_wei=1000,
            timestamp=now - 200,
        ))
        store.add_snapshot_sync(TVLSnapshot(
            protocol_address="0x1234",
            tvl_wei=2000,
            timestamp=now - 50,
        ))

        # Only get snapshots from last 100 seconds
        snapshots = store.get_snapshots("0x1234", since_timestamp=now - 100)
        assert len(snapshots) == 1
        assert snapshots[0].tvl_wei == 2000

    def test_clear_snapshots(self):
        """Test clearing snapshots."""
        store = TVLHistoryStore()
        store.add_snapshot_sync(TVLSnapshot(
            protocol_address="0x1234",
            tvl_wei=1000,
            timestamp=int(time.time()),
        ))

        store.clear("0x1234")
        assert store.get_snapshot_count("0x1234") == 0

    def test_max_snapshots_limit(self):
        """Test that snapshots are limited by max_snapshots."""
        store = TVLHistoryStore(max_snapshots_per_protocol=5)
        now = int(time.time())

        # Add 10 snapshots
        for i in range(10):
            store.add_snapshot_sync(TVLSnapshot(
                protocol_address="0x1234",
                tvl_wei=i * 1000,
                timestamp=now + i,
            ))

        # Should only keep last 5
        assert store.get_snapshot_count("0x1234") == 5
        snapshots = store.get_snapshots("0x1234")
        assert snapshots[0].tvl_wei == 5000  # First kept is index 5


# ============ SQLiteTVLStore Tests ============


class TestSQLiteTVLStore:
    """Tests for SQLite TVL store."""

    def test_in_memory_store(self):
        """Test in-memory SQLite store."""
        store = SQLiteTVLStore(":memory:")
        store.initialize()

        snapshot = TVLSnapshot(
            protocol_address="0x1234",
            tvl_wei=1000,
            timestamp=int(time.time()),
        )

        row_id = store.add_snapshot(snapshot)
        assert row_id > 0

        snapshots = store.get_snapshots("0x1234")
        assert len(snapshots) == 1
        assert snapshots[0].tvl_wei == 1000

        store.close()

    def test_file_persistence(self):
        """Test file-based SQLite persistence."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Write
            store1 = SQLiteTVLStore(db_path)
            store1.add_snapshot(TVLSnapshot(
                protocol_address="0x1234",
                tvl_wei=1000,
                timestamp=int(time.time()),
            ))
            store1.close()

            # Read back
            store2 = SQLiteTVLStore(db_path)
            snapshots = store2.get_snapshots("0x1234")
            assert len(snapshots) == 1
            assert snapshots[0].tvl_wei == 1000
            store2.close()

    def test_time_filtering(self):
        """Test filtering by time range."""
        store = SQLiteTVLStore(":memory:")
        now = int(time.time())

        store.add_snapshot(TVLSnapshot(
            protocol_address="0x1234",
            tvl_wei=1000,
            timestamp=now - 200,
        ))
        store.add_snapshot(TVLSnapshot(
            protocol_address="0x1234",
            tvl_wei=2000,
            timestamp=now - 50,
        ))

        # Only get recent
        snapshots = store.get_snapshots("0x1234", since_timestamp=now - 100)
        assert len(snapshots) == 1
        assert snapshots[0].tvl_wei == 2000

        store.close()


# ============ HistoricalTVLTracker Tests ============


class TestHistoricalTVLTracker:
    """Tests for the main TVL tracker."""

    def test_record_snapshot(self):
        """Test recording snapshots."""
        tracker = HistoricalTVLTracker()
        snapshot = tracker.record_snapshot_sync(
            protocol_address="0x1234",
            tvl_wei=1000 * 10**18,
            protocol_type="aave_v3",
        )

        assert snapshot.tvl_wei == 1000 * 10**18
        assert snapshot.protocol_type == "aave_v3"

    def test_rolling_average(self):
        """Test calculating rolling averages."""
        tracker = HistoricalTVLTracker()
        now = int(time.time())

        # Record several snapshots
        for i in range(5):
            tracker._memory_store.add_snapshot_sync(TVLSnapshot(
                protocol_address="0x1234",
                tvl_wei=(1000 + i * 100) * 10**18,
                timestamp=now - (4 - i) * 60,  # 1 per minute
            ))

        avg = tracker.get_rolling_average("0x1234", SECONDS_PER_HOUR, "1h")
        assert avg is not None
        assert avg.sample_count == 5
        # Average of 1000, 1100, 1200, 1300, 1400 = 1200
        assert avg.average_tvl == 1200 * 10**18

    def test_historical_stats(self):
        """Test getting historical statistics."""
        tracker = HistoricalTVLTracker()
        now = int(time.time())

        # Add some snapshots
        for i in range(10):
            tracker._memory_store.add_snapshot_sync(TVLSnapshot(
                protocol_address="0x1234",
                tvl_wei=(1000 + i * 50) * 10**18,
                timestamp=now - (9 - i) * 60,
            ))

        stats = tracker.get_historical_stats("0x1234")
        assert stats is not None
        assert stats.snapshot_count == 10
        assert stats.current_tvl == 1450 * 10**18

    def test_detect_sudden_drop_critical(self):
        """Test detecting critical sudden drop."""
        tracker = HistoricalTVLTracker()
        now = int(time.time())

        # Previous snapshot: 1000 ETH
        tracker._memory_store.add_snapshot_sync(TVLSnapshot(
            protocol_address="0x1234",
            tvl_wei=1000 * 10**18,
            timestamp=now - 60,
        ))

        # Current snapshot: 700 ETH (30% drop = CRITICAL)
        tracker._memory_store.add_snapshot_sync(TVLSnapshot(
            protocol_address="0x1234",
            tvl_wei=700 * 10**18,
            timestamp=now,
        ))

        anomalies = tracker.detect_anomalies("0x1234")
        assert len(anomalies) > 0

        critical_drops = [a for a in anomalies if a.severity == "CRITICAL"]
        assert len(critical_drops) > 0
        assert critical_drops[0].anomaly_type == AnomalyType.SUDDEN_DROP

    def test_detect_sudden_drop_high(self):
        """Test detecting high severity sudden drop."""
        tracker = HistoricalTVLTracker()
        now = int(time.time())

        # Previous: 1000, Current: 850 (15% drop = HIGH)
        tracker._memory_store.add_snapshot_sync(TVLSnapshot(
            protocol_address="0x1234",
            tvl_wei=1000 * 10**18,
            timestamp=now - 60,
        ))
        tracker._memory_store.add_snapshot_sync(TVLSnapshot(
            protocol_address="0x1234",
            tvl_wei=850 * 10**18,
            timestamp=now,
        ))

        anomalies = tracker.detect_anomalies("0x1234")
        high_drops = [a for a in anomalies if a.severity == "HIGH"]
        assert len(high_drops) > 0

    def test_detect_flash_drain(self):
        """Test detecting flash drain (rapid drop within window)."""
        thresholds = AnomalyThresholds(
            flash_drain_threshold=-15.0,
            flash_drain_window_seconds=300,
        )
        tracker = HistoricalTVLTracker(thresholds=thresholds)
        now = int(time.time())

        # Start of window: 1000 ETH
        tracker._memory_store.add_snapshot_sync(TVLSnapshot(
            protocol_address="0x1234",
            tvl_wei=1000 * 10**18,
            timestamp=now - 200,  # Within 5 min window
        ))

        # Current: 800 ETH (20% drop within window)
        tracker._memory_store.add_snapshot_sync(TVLSnapshot(
            protocol_address="0x1234",
            tvl_wei=800 * 10**18,
            timestamp=now,
        ))

        anomalies = tracker.detect_anomalies("0x1234")
        flash_drains = [a for a in anomalies if a.anomaly_type == AnomalyType.FLASH_DRAIN]
        assert len(flash_drains) > 0

    def test_no_anomalies_for_stable_tvl(self):
        """Test that stable TVL doesn't trigger anomalies."""
        tracker = HistoricalTVLTracker()
        now = int(time.time())

        # Stable TVL (< 5% change)
        tracker._memory_store.add_snapshot_sync(TVLSnapshot(
            protocol_address="0x1234",
            tvl_wei=1000 * 10**18,
            timestamp=now - 60,
        ))
        tracker._memory_store.add_snapshot_sync(TVLSnapshot(
            protocol_address="0x1234",
            tvl_wei=980 * 10**18,  # Only 2% drop
            timestamp=now,
        ))

        anomalies = tracker.detect_anomalies("0x1234")
        # Should not detect sudden drop (only 2%)
        sudden_drops = [a for a in anomalies if a.anomaly_type == AnomalyType.SUDDEN_DROP]
        assert len(sudden_drops) == 0


# ============ Factory Function Tests ============


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_get_tvl_tracker(self):
        """Test getting default tracker."""
        reset_tvl_tracker()

        tracker1 = get_tvl_tracker()
        tracker2 = get_tvl_tracker()

        assert tracker1 is tracker2  # Same instance

        reset_tvl_tracker()

    def test_reset_tvl_tracker(self):
        """Test resetting default tracker."""
        tracker1 = get_tvl_tracker()
        reset_tvl_tracker()
        tracker2 = get_tvl_tracker()

        assert tracker1 is not tracker2
        reset_tvl_tracker()


# ============ Integration Tests ============


class TestTrackerIntegration:
    """Integration tests for the tracker."""

    @pytest.mark.asyncio
    async def test_async_record_snapshot(self):
        """Test async snapshot recording."""
        tracker = HistoricalTVLTracker()

        snapshot = await tracker.record_snapshot(
            protocol_address="0x1234",
            tvl_wei=1000 * 10**18,
        )

        assert snapshot.tvl_wei == 1000 * 10**18

        latest = tracker._memory_store.get_latest_snapshot("0x1234")
        assert latest is not None
        assert latest.tvl_wei == snapshot.tvl_wei

    def test_with_sqlite_persistence(self):
        """Test tracker with SQLite persistence."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "tvl.db"
            tracker = HistoricalTVLTracker(db_path=db_path)

            tracker.record_snapshot_sync(
                protocol_address="0x1234",
                tvl_wei=1000 * 10**18,
            )

            # Check both stores have the data
            mem_snapshot = tracker._memory_store.get_latest_snapshot("0x1234")
            sql_snapshot = tracker._sqlite_store.get_latest_snapshot("0x1234")

            assert mem_snapshot is not None
            assert sql_snapshot is not None
            assert mem_snapshot.tvl_wei == sql_snapshot.tvl_wei

            tracker.close()
