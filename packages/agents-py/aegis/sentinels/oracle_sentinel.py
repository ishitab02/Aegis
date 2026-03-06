"""Oracle sentinel.

Monitors DeFi protocol price feeds for manipulation or staleness.
When thresholds trigger HIGH or CRITICAL, uses AI to analyze the context and
either CONFIRM or DOWNGRADE the threat assessment.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from crewai import Agent

from aegis.config import ORACLE_THRESHOLDS
from aegis.models import (
    ActionRecommendation,
    PriceFeedData,
    SentinelType,
    ThreatAssessment,
    ThreatLevel,
)
from aegis.utils import now_seconds

if TYPE_CHECKING:
    from aegis.adapters.base import BaseProtocolAdapter, ProtocolEvent

logger = logging.getLogger(__name__)


def monitor_price_feeds(
    protocol_price: float,
    chainlink_data: PriceFeedData,
    adapter: "BaseProtocolAdapter | None" = None,
    recent_events: list["ProtocolEvent"] | None = None,
    use_ai: bool = True,
) -> ThreatAssessment:
    """Monitor price feeds for manipulation or staleness.

    Compares protocol's internal price against Chainlink Data Feeds.

    Thresholds:
    - deviation: >5% -> CRITICAL, >2% -> HIGH
    - staleness: >1hr -> HIGH, >30min -> MEDIUM

    When threat >= HIGH and use_ai=True, invokes AI analysis to either
    CONFIRM or DOWNGRADE the threat based on contextual analysis.

    Args:
        protocol_price: Price reported by the protocol
        chainlink_data: Price data from Chainlink feed
        adapter: Optional protocol adapter for fetching additional context
        recent_events: Optional list of recent protocol events (e.g., swaps)
        use_ai: Whether to use AI analysis for HIGH/CRITICAL threats

    Returns:
        ThreatAssessment with threat level, confidence, and details
    """
    # deviation: >5% -> CRITICAL, >2% -> HIGH
    # staleness: >1hr -> HIGH, >30min -> MEDIUM
    chainlink_price = chainlink_data.price
    feed_age = now_seconds() - chainlink_data.updated_at

    if chainlink_price == 0:
        deviation_percent = 0.0
    else:
        deviation_percent = abs(
            ((protocol_price - chainlink_price) / chainlink_price) * 100
        )

    threat_level = ThreatLevel.NONE
    confidence = 0.9
    indicators: list[str] = []
    recommendation = ActionRecommendation.NONE
    details = (
        f"Chainlink: ${chainlink_price:.2f}, "
        f"Protocol: ${protocol_price:.2f}, "
        f"Deviation: {deviation_percent:.2f}%, "
        f"Feed age: {feed_age}s"
    )

    if deviation_percent > ORACLE_THRESHOLDS["critical_deviation"]:
        threat_level = ThreatLevel.CRITICAL
        confidence = 0.95
        indicators.append(
            f"Price deviation {deviation_percent:.2f}% exceeds critical "
            f"threshold {ORACLE_THRESHOLDS['critical_deviation']}%"
        )
        recommendation = ActionRecommendation.CIRCUIT_BREAKER
    elif deviation_percent > ORACLE_THRESHOLDS["high_deviation"]:
        threat_level = ThreatLevel.HIGH
        indicators.append(
            f"Price deviation {deviation_percent:.2f}% exceeds high "
            f"threshold {ORACLE_THRESHOLDS['high_deviation']}%"
        )
        recommendation = ActionRecommendation.ALERT

    # staleness, only escalate if not already higher
    if (
        feed_age > ORACLE_THRESHOLDS["high_staleness"]
        and ThreatLevel.severity(threat_level) < ThreatLevel.severity(ThreatLevel.HIGH)
    ):
        threat_level = ThreatLevel.HIGH
        indicators.append(
            f"Feed is {feed_age}s old - exceeds staleness "
            f"threshold {ORACLE_THRESHOLDS['high_staleness']}s"
        )
        recommendation = ActionRecommendation.ALERT
    elif (
        feed_age > ORACLE_THRESHOLDS["medium_staleness"]
        and ThreatLevel.severity(threat_level) < ThreatLevel.severity(ThreatLevel.MEDIUM)
    ):
        threat_level = ThreatLevel.MEDIUM
        indicators.append(
            f"Feed is {feed_age}s old - exceeds medium staleness "
            f"threshold {ORACLE_THRESHOLDS['medium_staleness']}s"
        )
        recommendation = ActionRecommendation.ALERT

    # AI Analysis for HIGH/CRITICAL threats
    if use_ai and threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
        threat_level, confidence, indicators = _apply_oracle_ai_analysis(
            protocol_price=protocol_price,
            chainlink_price=chainlink_price,
            deviation_percent=deviation_percent,
            feed_age=feed_age,
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

    return ThreatAssessment(
        threat_level=threat_level,
        confidence=confidence,
        details=details,
        indicators=indicators,
        recommendation=recommendation,
        timestamp=now_seconds(),
        sentinel_id="oracle-sentinel-0",
        sentinel_type=SentinelType.ORACLE,
    )


def _apply_oracle_ai_analysis(
    protocol_price: float,
    chainlink_price: float,
    deviation_percent: float,
    feed_age: int,
    threat_level: ThreatLevel,
    confidence: float,
    indicators: list[str],
    adapter: "BaseProtocolAdapter | None" = None,
    recent_events: list["ProtocolEvent"] | None = None,
) -> tuple[ThreatLevel, float, list[str]]:
    """Apply AI analysis to a HIGH/CRITICAL oracle threat assessment.

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
                # For oracle, Swap events are most relevant
                events_for_context = adapter.get_recent_events_sync(limit=20)
                logger.debug("Fetched %d events for AI context", len(events_for_context))
            except Exception as e:
                logger.warning("Could not fetch events for AI context: %s", e)

        # Build context for AI analysis
        context = {
            "sentinel_type": "oracle",
            "protocol_price": protocol_price,
            "chainlink_price": chainlink_price,
            "price_deviation": deviation_percent,
            "feed_age": feed_age,
            "threshold_threat_level": threat_level.value,
            "indicators": indicators,
            "recent_events": events_for_context,
        }

        # Run AI analysis
        logger.info("Invoking AI analysis for oracle anomaly...")
        ai_result = analyze_anomaly_with_ai(
            sentinel_type="oracle",
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
                "AI DOWNGRADED oracle threat: %s -> %s (confidence: %.2f, reason: %s)",
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
                "AI UPGRADED oracle threat: %s -> %s (confidence: %.2f, reason: %s)",
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
                "AI CONFIRMED oracle threat: %s (confidence: %.2f, reason: %s)",
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



_oracle_sentinel: Agent | None = None


def get_oracle_sentinel() -> Agent:
    global _oracle_sentinel
    if _oracle_sentinel is None:
        _oracle_sentinel = Agent(
            role="Oracle Sentinel",
            goal=(
                "Monitor DeFi protocol price feeds for manipulation, staleness, or "
                "deviations from Chainlink Data Feeds (the source of truth)."
            ),
            backstory=(
                "You are the AEGIS Oracle Sentinel, a specialized AI agent that monitors "
                "price oracle integrity. You compare protocol-internal prices against "
                "Chainlink Data Feeds and detect manipulation attempts, stale data, or "
                "anomalous price movements that could indicate an exploit in progress."
            ),
            verbose=False,
            allow_delegation=False,
        )
    return _oracle_sentinel
