"""Liquidity sentinel.

Monitors DeFi protocol liquidity for anomalies indicating potential exploits.
When thresholds trigger HIGH or CRITICAL, uses AI to analyze the context and
either CONFIRM or DOWNGRADE the threat assessment.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from crewai import Agent

from aegis.config import LIQUIDITY_THRESHOLDS
from aegis.models import (
    ActionRecommendation,
    SentinelType,
    ThreatAssessment,
    ThreatLevel,
)
from aegis.utils import calculate_change_percent, now_seconds, wei_to_ether

if TYPE_CHECKING:
    from aegis.adapters.base import BaseProtocolAdapter, ProtocolEvent

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
    adapter: "BaseProtocolAdapter | None" = None,
    recent_events: list["ProtocolEvent"] | None = None,
    use_ai: bool = True,
) -> ThreatAssessment:
    """Monitor Total Value Locked for anomalies indicating potential exploits.

    Uses threshold-based detection:
    - >= 20% drop -> CRITICAL (confidence 0.95, CIRCUIT_BREAKER)
    - >= 10% drop -> HIGH (confidence 0.9, ALERT)
    - >= 5% drop  -> MEDIUM (confidence 0.8, ALERT)

    When threat >= HIGH and use_ai=True, invokes AI analysis to either
    CONFIRM or DOWNGRADE the threat based on contextual analysis.

    Args:
        protocol_address: Address of the protocol being monitored
        current_tvl: Current TVL in wei
        previous_tvl: Previous TVL in wei (uses global state if None)
        adapter: Optional protocol adapter for fetching additional context
        recent_events: Optional list of recent protocol events
        use_ai: Whether to use AI analysis for HIGH/CRITICAL threats

    Returns:
        ThreatAssessment with threat level, confidence, and details
    """
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

    # AI Analysis for HIGH/CRITICAL threats
    if use_ai and threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
        threat_level, confidence, indicators = _apply_ai_analysis(
            protocol_address=protocol_address,
            current_tvl=current_tvl,
            previous_tvl=prev,
            change_percent=change_percent,
            threat_level=threat_level,
            confidence=confidence,
            indicators=indicators,
            adapter=adapter,
            recent_events=recent_events,
        )

        # Update recommendation based on final threat level
        if threat_level == ThreatLevel.CRITICAL:
            recommendation = ActionRecommendation.CIRCUIT_BREAKER
        elif threat_level in (ThreatLevel.HIGH, ThreatLevel.MEDIUM):
            recommendation = ActionRecommendation.ALERT
        else:
            recommendation = ActionRecommendation.NONE

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


def _apply_ai_analysis(
    protocol_address: str,
    current_tvl: int,
    previous_tvl: int,
    change_percent: float,
    threat_level: ThreatLevel,
    confidence: float,
    indicators: list[str],
    adapter: "BaseProtocolAdapter | None" = None,
    recent_events: list["ProtocolEvent"] | None = None,
) -> tuple[ThreatLevel, float, list[str]]:
    """Apply AI analysis to a HIGH/CRITICAL threat assessment.

    Returns potentially modified (threat_level, confidence, indicators).
    """
    from aegis.sentinels.ai_analyzer import (
        analyze_anomaly_with_ai,
        map_threat_level_str_to_enum,
        should_use_ai_analysis,
    )

    if not should_use_ai_analysis():
        logger.debug("AI analysis disabled - ANTHROPIC_API_KEY not set")
        return threat_level, confidence, indicators

    try:
        # Gather recent events if adapter available and events not provided
        events_for_context = recent_events or []
        if adapter is not None and not events_for_context:
            try:
                events_for_context = adapter.get_recent_events_sync(limit=20)
                logger.debug("Fetched %d events for AI context", len(events_for_context))
            except Exception as e:
                logger.warning("Could not fetch events for AI context: %s", e)

        # Build context for AI analysis
        context = {
            "protocol_address": protocol_address,
            "sentinel_type": "liquidity",
            "current_tvl": current_tvl,
            "previous_tvl": previous_tvl,
            "change_percent": change_percent,
            "threshold_threat_level": threat_level.value,
            "indicators": indicators,
            "recent_events": events_for_context,
        }

        # Run AI analysis
        logger.info("Invoking AI analysis for liquidity anomaly...")
        ai_result = analyze_anomaly_with_ai(
            sentinel_type="liquidity",
            context=context,
        )

        ai_threat_level = map_threat_level_str_to_enum(ai_result["threat_level"])
        ai_confidence = ai_result["confidence"]
        ai_reasoning = ai_result["reasoning"]
        ai_attack_type = ai_result["attack_type"]

        # Add AI analysis to indicators
        new_indicators = list(indicators)
        new_indicators.append(f"AI Analysis: {ai_reasoning}")
        new_indicators.append(f"AI Attack Type: {ai_attack_type}")

        # Determine if AI downgraded the threat
        original_severity = ThreatLevel.severity(threat_level)
        ai_severity = ThreatLevel.severity(ai_threat_level)

        if ai_severity < original_severity and ai_confidence > 0.75:
            # AI downgraded with high confidence
            logger.info(
                "AI DOWNGRADED threat: %s -> %s (confidence: %.2f, reason: %s)",
                threat_level.value,
                ai_threat_level.value,
                ai_confidence,
                ai_reasoning[:100],
            )
            # Don't fully dismiss - keep at least MEDIUM for caution
            final_level = ai_threat_level if ai_severity >= 2 else ThreatLevel.MEDIUM
            new_indicators.append(
                f"AI downgraded from {threat_level.value} to {final_level.value}"
            )
            return final_level, ai_confidence, new_indicators

        elif ai_severity > original_severity:
            # AI upgraded the threat
            logger.info(
                "AI UPGRADED threat: %s -> %s (confidence: %.2f, reason: %s)",
                threat_level.value,
                ai_threat_level.value,
                ai_confidence,
                ai_reasoning[:100],
            )
            new_indicators.append(
                f"AI upgraded from {threat_level.value} to {ai_threat_level.value}"
            )
            return ai_threat_level, ai_confidence, new_indicators

        else:
            # AI confirmed the threshold assessment
            logger.info(
                "AI CONFIRMED threat: %s (confidence: %.2f, reason: %s)",
                threat_level.value,
                ai_confidence,
                ai_reasoning[:100],
            )
            new_indicators.append("AI confirmed threshold assessment")
            # Use the higher confidence between threshold and AI
            final_confidence = max(confidence, ai_confidence)
            return threat_level, final_confidence, new_indicators

    except Exception as e:
        logger.error("AI analysis failed, using threshold assessment: %s", e)
        indicators_with_error = list(indicators)
        indicators_with_error.append(f"AI analysis failed: {e}")
        return threat_level, confidence, indicators_with_error



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
