"""Oracle Sentinel - monitors price feeds for manipulation or staleness.

Ported from packages/agents/src/sentinels/OracleSentinel/actions/monitorPriceFeeds.ts
"""

import logging

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

logger = logging.getLogger(__name__)


def monitor_price_feeds(
    protocol_price: float,
    chainlink_data: PriceFeedData,
) -> ThreatAssessment:
    """Monitor price feeds for manipulation or staleness.

    Compares protocol's internal price against Chainlink Data Feeds (source of truth).
    Same thresholds as TypeScript:
    - > 5% deviation -> CRITICAL
    - > 2% deviation -> HIGH
    - Feed age > 1 hour -> HIGH
    - Feed age > 30 min -> MEDIUM
    """
    chainlink_price = chainlink_data.price
    feed_age = now_seconds() - chainlink_data.updated_at

    # Calculate deviation
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

    # Check price deviation
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

    # Check staleness (only escalate if not already higher)
    if (
        feed_age > ORACLE_THRESHOLDS["high_staleness"]
        and ThreatLevel.severity(threat_level) < ThreatLevel.severity(ThreatLevel.HIGH)
    ):
        threat_level = ThreatLevel.HIGH
        indicators.append(
            f"Feed is {feed_age}s old — exceeds staleness "
            f"threshold {ORACLE_THRESHOLDS['high_staleness']}s"
        )
        recommendation = ActionRecommendation.ALERT
    elif (
        feed_age > ORACLE_THRESHOLDS["medium_staleness"]
        and ThreatLevel.severity(threat_level) < ThreatLevel.severity(ThreatLevel.MEDIUM)
    ):
        threat_level = ThreatLevel.MEDIUM
        indicators.append(
            f"Feed is {feed_age}s old — exceeds medium staleness "
            f"threshold {ORACLE_THRESHOLDS['medium_staleness']}s"
        )
        recommendation = ActionRecommendation.ALERT

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


# ============ CrewAI Agent ============

_oracle_sentinel: Agent | None = None


def get_oracle_sentinel() -> Agent:
    """Lazy-load the CrewAI agent (requires LLM API key at runtime)."""
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
