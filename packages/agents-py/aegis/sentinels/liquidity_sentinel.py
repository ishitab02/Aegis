"""Liquidity Sentinel - monitors protocol TVL for anomalies.

Ported from packages/agents/src/sentinels/LiquiditySentinel/actions/monitorTVL.ts
"""

import logging

from crewai import Agent
from crewai.tools import tool

from aegis.config import LIQUIDITY_THRESHOLDS, MOCK_PROTOCOL_ABI
from aegis.models import (
    ActionRecommendation,
    SentinelType,
    ThreatAssessment,
    ThreatLevel,
)
from aegis.utils import calculate_change_percent, now_seconds, wei_to_ether

logger = logging.getLogger(__name__)

# Module-level state for previous TVL (reset per detection cycle)
_previous_tvl: int = 0


def set_previous_tvl(tvl: int) -> None:
    """Set the previous TVL for the next detection cycle."""
    global _previous_tvl
    _previous_tvl = tvl


def get_previous_tvl() -> int:
    return _previous_tvl


def monitor_tvl(
    protocol_address: str,
    current_tvl: int,
    previous_tvl: int | None = None,
) -> ThreatAssessment:
    """Monitor Total Value Locked for anomalies indicating potential exploits.

    Uses the same thresholds as the TypeScript implementation:
    - >= 20% drop in 5 min -> CRITICAL
    - >= 10% drop -> HIGH
    - >= 5% drop -> MEDIUM
    """
    prev = previous_tvl if previous_tvl is not None else _previous_tvl

    if prev == 0:
        set_previous_tvl(current_tvl)
        return ThreatAssessment(
            threat_level=ThreatLevel.NONE,
            confidence=0.9,
            details=f"Initial TVL snapshot: {wei_to_ether(current_tvl):.4f} ETH",
            indicators=[],
            recommendation=ActionRecommendation.NONE,
            timestamp=now_seconds(),
            sentinel_id="liquidity-sentinel-0",
            sentinel_type=SentinelType.LIQUIDITY,
        )

    change_percent = calculate_change_percent(prev, current_tvl)

    threat_level = ThreatLevel.NONE
    confidence = 0.9
    indicators: list[str] = []
    recommendation = ActionRecommendation.NONE

    if change_percent <= LIQUIDITY_THRESHOLDS["critical_tvl_drop"]:
        threat_level = ThreatLevel.CRITICAL
        confidence = 0.95
        indicators.append(
            f"TVL dropped {change_percent:.2f}% "
            f"(threshold: {LIQUIDITY_THRESHOLDS['critical_tvl_drop']}%)"
        )
        recommendation = ActionRecommendation.CIRCUIT_BREAKER
    elif change_percent <= LIQUIDITY_THRESHOLDS["high_tvl_drop"]:
        threat_level = ThreatLevel.HIGH
        confidence = 0.9
        indicators.append(
            f"TVL dropped {change_percent:.2f}% "
            f"(threshold: {LIQUIDITY_THRESHOLDS['high_tvl_drop']}%)"
        )
        recommendation = ActionRecommendation.ALERT
    elif change_percent <= LIQUIDITY_THRESHOLDS["medium_tvl_drop"]:
        threat_level = ThreatLevel.MEDIUM
        confidence = 0.8
        indicators.append(
            f"TVL dropped {change_percent:.2f}% "
            f"(threshold: {LIQUIDITY_THRESHOLDS['medium_tvl_drop']}%)"
        )
        recommendation = ActionRecommendation.ALERT

    # Update stored TVL for next cycle
    set_previous_tvl(current_tvl)

    return ThreatAssessment(
        threat_level=threat_level,
        confidence=confidence,
        details=(
            f"TVL changed by {change_percent:.2f}% — "
            f"from {wei_to_ether(prev):.4f} to {wei_to_ether(current_tvl):.4f} ETH"
        ),
        indicators=indicators,
        recommendation=recommendation,
        timestamp=now_seconds(),
        sentinel_id="liquidity-sentinel-0",
        sentinel_type=SentinelType.LIQUIDITY,
    )


# ============ CrewAI Agent ============

_liquidity_sentinel: Agent | None = None


def get_liquidity_sentinel() -> Agent:
    """Lazy-load the CrewAI agent (requires LLM API key at runtime)."""
    global _liquidity_sentinel
    if _liquidity_sentinel is None:
        _liquidity_sentinel = Agent(
            role="Liquidity Sentinel",
            goal=(
                "Monitor DeFi protocol liquidity pools for anomalies that indicate "
                "potential exploits such as flash loan attacks, rug pulls, or abnormal withdrawals."
            ),
            backstory=(
                "You are the AEGIS Liquidity Sentinel, a vigilant AI security agent. "
                "You specialize in DeFi liquidity analysis, flash loan detection, "
                "TVL monitoring, and withdrawal pattern analysis. You are precise and "
                "cautious — only flag HIGH or CRITICAL threats when clear indicators exist. "
                "False positives are costly, but missed exploits are catastrophic."
            ),
            verbose=False,
            allow_delegation=False,
        )
    return _liquidity_sentinel
