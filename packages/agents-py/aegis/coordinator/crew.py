"""AEGIS Detection Crew — orchestrates sentinel agents for threat detection.

This module runs the full detection cycle:
1. Each sentinel analyzes its domain (liquidity, oracle, governance)
2. Assessments are aggregated
3. Consensus is reached via 2/3 majority rule
"""

import logging

from aegis.blockchain.chainlink_feeds import get_eth_usd_price
from aegis.blockchain.contracts import get_protocol_tvl, is_protocol_paused
from aegis.blockchain.web3_client import get_web3
from aegis.coordinator.aggregator import SentinelAggregator
from aegis.models import (
    ConsensusResult,
    DetectionResponse,
    GovernanceProposal,
    ThreatAssessment,
)
from aegis.sentinels.governance_sentinel import analyze_proposal
from aegis.sentinels.liquidity_sentinel import monitor_tvl
from aegis.sentinels.oracle_sentinel import monitor_price_feeds
from aegis.utils import now_seconds

logger = logging.getLogger(__name__)


def run_detection_cycle(
    protocol_address: str,
    protocol_name: str = "MockProtocol",
    previous_tvl: int = 0,
    protocol_price: float | None = None,
    governance_proposal: GovernanceProposal | None = None,
) -> DetectionResponse:
    """Run a full threat detection cycle across all 3 sentinels.

    This is the primary entry point called by the CRE workflow via
    POST /api/v1/detect.

    Returns a DetectionResponse with all individual assessments and
    the consensus result.
    """
    w3 = get_web3()
    aggregator = SentinelAggregator()
    assessments: list[ThreatAssessment] = []

    # --- 1. Liquidity Sentinel ---
    try:
        current_tvl = get_protocol_tvl(w3, protocol_address)
        liquidity_assessment = monitor_tvl(
            protocol_address=protocol_address,
            current_tvl=current_tvl,
            previous_tvl=previous_tvl if previous_tvl > 0 else None,
        )
        aggregator.submit_assessment(liquidity_assessment)
        assessments.append(liquidity_assessment)
        logger.info(
            "Liquidity Sentinel: %s (confidence: %.2f)",
            liquidity_assessment.threat_level.value,
            liquidity_assessment.confidence,
        )
    except Exception as e:
        logger.error("Liquidity Sentinel failed: %s", e)

    # --- 2. Oracle Sentinel ---
    try:
        chainlink_data = get_eth_usd_price(w3)
        # Use provided protocol price or default to Chainlink price (no deviation)
        p_price = protocol_price if protocol_price is not None else chainlink_data.price
        oracle_assessment = monitor_price_feeds(
            protocol_price=p_price,
            chainlink_data=chainlink_data,
        )
        aggregator.submit_assessment(oracle_assessment)
        assessments.append(oracle_assessment)
        logger.info(
            "Oracle Sentinel: %s (confidence: %.2f)",
            oracle_assessment.threat_level.value,
            oracle_assessment.confidence,
        )
    except Exception as e:
        logger.error("Oracle Sentinel failed: %s", e)

    # --- 3. Governance Sentinel ---
    try:
        if governance_proposal is not None:
            gov_assessment = analyze_proposal(governance_proposal)
        else:
            # No active proposal — default to NONE
            gov_assessment = ThreatAssessment(
                threat_level="NONE",
                confidence=0.9,
                details="No active governance proposals to analyze",
                indicators=[],
                recommendation="NONE",
                timestamp=now_seconds(),
                sentinel_id="governance-sentinel-0",
                sentinel_type="GOVERNANCE",
            )
        aggregator.submit_assessment(gov_assessment)
        assessments.append(gov_assessment)
        logger.info(
            "Governance Sentinel: %s (confidence: %.2f)",
            gov_assessment.threat_level.value,
            gov_assessment.confidence,
        )
    except Exception as e:
        logger.error("Governance Sentinel failed: %s", e)

    # --- 4. Consensus ---
    consensus = aggregator.aggregate()
    logger.info(
        "Consensus: reached=%s, level=%s, ratio=%.2f, action=%s",
        consensus.consensus_reached,
        consensus.final_threat_level.value,
        consensus.agreement_ratio,
        consensus.action_recommended.value,
    )

    return DetectionResponse(
        consensus=consensus,
        assessments=assessments,
        timestamp=now_seconds(),
    )
