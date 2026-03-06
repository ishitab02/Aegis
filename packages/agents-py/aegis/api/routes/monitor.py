"""Live monitoring routes — real DeFi protocol monitoring on Base Mainnet."""

from __future__ import annotations

import asyncio
import logging
import os
from collections import deque
from typing import Any

from fastapi import APIRouter, HTTPException

from aegis.adapters.aave_v3 import AaveV3Adapter
from aegis.adapters.base import TokenBalance
from aegis.blockchain.chainlink_feeds import get_chainlink_price
from aegis.config import CHAINLINK_FEEDS_BASE
from aegis.coordinator.crew import run_detection_cycle
from aegis.utils import now_seconds, wei_to_ether

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Base Mainnet (chain ID 8453)
# Use env var if available, otherwise fallback to public RPC
BASE_MAINNET_RPC = os.getenv("BASE_MAINNET_RPC", "https://mainnet.base.org")

# Aave V3 Pool on Base Mainnet
AAVE_V3_POOL_BASE = "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"

# Chainlink ETH/USD feed on Base Mainnet
ETH_USD_FEED_BASE = CHAINLINK_FEEDS_BASE["ETH/USD"]

# Background monitoring interval (seconds)
MONITOR_INTERVAL = 30

# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------

# Recent readings (last 100)
_aave_history: deque[dict[str, Any]] = deque(maxlen=100)

# Previous TVL for change detection
_previous_tvl: int = 0

# Background task handle
_monitor_task: asyncio.Task | None = None


# ---------------------------------------------------------------------------
# Helpers (cached Web3 for Base Mainnet)
# ---------------------------------------------------------------------------

_base_mainnet_w3 = None


def _get_base_mainnet_w3():
    """Return a Web3 instance connected to Base Mainnet (cached)."""
    global _base_mainnet_w3
    if _base_mainnet_w3 is None:
        from web3 import Web3

        _base_mainnet_w3 = Web3(Web3.HTTPProvider(BASE_MAINNET_RPC))
    return _base_mainnet_w3


# Cached adapter instance (to preserve TTL cache between requests)
_aave_adapter: AaveV3Adapter | None = None


def _get_aave_adapter(w3=None) -> AaveV3Adapter:
    """Get or create an Aave V3 adapter for Base Mainnet (cached).

    Uses a longer cache TTL (120s) to avoid rate limiting on public RPCs.
    """
    global _aave_adapter
    if _aave_adapter is None:
        if w3 is None:
            w3 = _get_base_mainnet_w3()
        # Use 120s cache TTL to avoid rate limiting on public RPC
        _aave_adapter = AaveV3Adapter(
            web3=w3,
            protocol_address=AAVE_V3_POOL_BASE,
            cache_ttl=120,  # 2 minutes cache for public RPC
        )
    return _aave_adapter


def _format_token_balance(b: TokenBalance) -> dict:
    return {
        "token_address": b.token_address,
        "symbol": b.symbol,
        "decimals": b.decimals,
        "balance_raw": str(b.balance_raw),
        "balance_formatted": b.balance_formatted,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/aave")
async def monitor_aave_live():
    """Monitor real Aave V3 on Base Mainnet.

    This endpoint proves AEGIS can monitor real DeFi protocols.  It reads
    live TVL, token balances, recent events and the Chainlink ETH/USD price
    from Base Mainnet — no simulation, no mock data.
    """
    global _previous_tvl

    try:
        w3 = _get_base_mainnet_w3()
        adapter = _get_aave_adapter(w3)

        # Fetch real data in parallel
        tvl, balances, events = await asyncio.gather(
            adapter.get_tvl(),
            adapter.get_token_balances(),
            adapter.get_recent_events(limit=10),
        )

        # Chainlink ETH/USD on Base Mainnet (synchronous call)
        loop = asyncio.get_event_loop()
        chainlink_data = await loop.run_in_executor(
            None, lambda: get_chainlink_price(ETH_USD_FEED_BASE, w3),
        )

        # TVL change from previous reading
        tvl_change_percent = 0.0
        if _previous_tvl > 0:
            tvl_change_percent = round(
                ((tvl - _previous_tvl) / _previous_tvl) * 100, 4,
            )

        # Run detection cycle with the live adapter
        detection = run_detection_cycle(
            protocol_address=AAVE_V3_POOL_BASE,
            protocol_name="Aave V3 (Base Mainnet)",
            previous_tvl=_previous_tvl,
            adapter=adapter,
        )

        # Remember TVL for next cycle
        _previous_tvl = tvl

        # Sort balances by value descending for top-5
        sorted_balances = sorted(balances, key=lambda b: b.balance_raw, reverse=True)

        result = {
            "status": "live",
            "protocol": "Aave V3",
            "chain": "Base Mainnet",
            "chain_id": 8453,
            "pool_address": AAVE_V3_POOL_BASE,
            "tvl_wei": str(tvl),
            "tvl_eth": wei_to_ether(tvl),
            "tvl_change_percent": tvl_change_percent,
            "chainlink_eth_usd": chainlink_data.price,
            "chainlink_updated_at": chainlink_data.updated_at,
            "tvl_usd_estimate": wei_to_ether(tvl) * chainlink_data.price,
            "token_balances": [
                _format_token_balance(b) for b in sorted_balances[:5]
            ],
            "recent_events": [
                {
                    "type": e.event_name,
                    "block": e.block_number,
                    "tx": e.transaction_hash[:10] + "...",
                }
                for e in events[:5]
            ],
            "threat_assessment": {
                "threat_level": detection.consensus.final_threat_level.value,
                "confidence": detection.consensus.agreement_ratio,
                "action": detection.consensus.action_recommended.value,
                "assessments": [
                    {
                        "sentinel": a.sentinel_id,
                        "threat_level": a.threat_level.value,
                        "confidence": a.confidence,
                    }
                    for a in detection.assessments
                ],
            },
            "timestamp": now_seconds(),
        }

        return result

    except Exception as e:
        logger.error("Aave live monitoring failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch live Aave data: {e}",
        )


@router.get("/aave/history")
async def get_aave_history():
    """Get recent Aave TVL readings collected by the background monitor.

    Returns the last ≤100 readings (one every ~30 s).
    """
    return {
        "protocol": "Aave V3",
        "chain": "Base Mainnet",
        "reading_count": len(_aave_history),
        "readings": list(_aave_history),
    }


@router.get("/status")
async def monitor_status():
    """Return status of the background monitoring loop."""
    task_running = _monitor_task is not None and not _monitor_task.done()
    return {
        "background_monitor": "running" if task_running else "stopped",
        "history_size": len(_aave_history),
        "previous_tvl": str(_previous_tvl),
        "interval_seconds": MONITOR_INTERVAL,
    }


# ---------------------------------------------------------------------------
# Background monitoring task
# ---------------------------------------------------------------------------


async def _monitor_aave_background():
    """Background task: monitor Aave V3 every MONITOR_INTERVAL seconds."""
    global _previous_tvl

    logger.info(
        "Starting background Aave V3 monitor (interval=%ds)", MONITOR_INTERVAL,
    )

    while True:
        try:
            w3 = _get_base_mainnet_w3()
            adapter = _get_aave_adapter(w3)

            tvl = await adapter.get_tvl()

            # Chainlink ETH/USD
            loop = asyncio.get_event_loop()
            chainlink_data = await loop.run_in_executor(
                None, lambda: get_chainlink_price(ETH_USD_FEED_BASE, w3),
            )

            tvl_change_percent = 0.0
            if _previous_tvl > 0:
                tvl_change_percent = round(
                    ((tvl - _previous_tvl) / _previous_tvl) * 100, 4,
                )

            reading = {
                "tvl_wei": str(tvl),
                "tvl_eth": wei_to_ether(tvl),
                "tvl_change_percent": tvl_change_percent,
                "chainlink_eth_usd": chainlink_data.price,
                "timestamp": now_seconds(),
            }

            _aave_history.append(reading)
            _previous_tvl = tvl

            logger.info(
                "Aave TVL: %s ETH ($%.2f) | change: %.4f%%",
                f"{wei_to_ether(tvl):,.2f}",
                wei_to_ether(tvl) * chainlink_data.price,
                tvl_change_percent,
            )

        except Exception as e:
            logger.error("Background Aave monitor error: %s", e)

        await asyncio.sleep(MONITOR_INTERVAL)


def start_background_monitor():
    """Schedule the background monitor coroutine (idempotent)."""
    global _monitor_task
    if _monitor_task is not None and not _monitor_task.done():
        return  # already running
    _monitor_task = asyncio.create_task(_monitor_aave_background())
    logger.info("Background Aave monitor task scheduled")


def stop_background_monitor():
    """Cancel the background monitor task."""
    global _monitor_task
    if _monitor_task is not None and not _monitor_task.done():
        _monitor_task.cancel()
        _monitor_task = None
        logger.info("Background Aave monitor task cancelled")
