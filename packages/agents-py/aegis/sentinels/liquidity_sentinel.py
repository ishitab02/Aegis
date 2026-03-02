"""Liquidity sentinel."""

import logging

from crewai import Agent

from aegis.config import LIQUIDITY_THRESHOLDS
from aegis.models import (
    ActionRecommendation,
    SentinelType,
    ThreatAssessment,
    ThreatLevel,
)
from aegis.utils import calculate_change_percent, now_seconds, wei_to_ether

logger = logging.getLogger(__name__)

# previous tvl, reset per cycle
_previous_tvl: int = 0


def set_previous_tvl(tvl: int) -> None:
    global _previous_tvl
    _previous_tvl = tvl


def get_previous_tvl() -> int:
    return _previous_tvl


def monitor_tvl(
    protocol_address: str,
    current_tvl: int,
    previous_tvl: int | None = None,
) -> ThreatAssessment:
    # >=20% drop -> CRITICAL, >=10% -> HIGH, >=5% -> MEDIUM
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

    set_previous_tvl(current_tvl)

    return ThreatAssessment(
        threat_level=threat_level,
        confidence=confidence,
        details=(
            f"TVL changed by {change_percent:.2f}% - "
            f"from {wei_to_ether(prev):.4f} to {wei_to_ether(current_tvl):.4f} ETH"
        ),
        indicators=indicators,
        recommendation=recommendation,
        timestamp=now_seconds(),
        sentinel_id="liquidity-sentinel-0",
        sentinel_type=SentinelType.LIQUIDITY,
    )



_liquidity_sentinel: Agent | None = None


def get_liquidity_sentinel() -> Agent:
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
                "cautious - only flag HIGH or CRITICAL threats when clear indicators exist. "
                "False positives are costly, but missed exploits are catastrophic."
            ),
            verbose=False,
            allow_delegation=False,
        )
    return _liquidity_sentinel
