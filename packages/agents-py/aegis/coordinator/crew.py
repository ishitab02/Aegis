"""Detection crew -- orchestrates sentinels for threat detection."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aegis.blockchain.chainlink_feeds import get_eth_usd_price
from aegis.blockchain.contracts import get_protocol_tvl
from aegis.blockchain.web3_client import get_web3
from aegis.coordinator.aggregator import SentinelAggregator
from aegis.models import (
    DetectionResponse,
    GovernanceProposal,
    ThreatAssessment,
)
from aegis.sentinels.governance_sentinel import analyze_proposal
from aegis.sentinels.liquidity_sentinel import monitor_tvl
from aegis.sentinels.oracle_sentinel import monitor_price_feeds
from aegis.utils import now_seconds

if TYPE_CHECKING:
    from aegis.adapters.base import BaseProtocolAdapter

logger = logging.getLogger(__name__)


def run_detection_cycle(
    protocol_address: str,
    protocol_name: str = "MockProtocol",
    previous_tvl: int = 0,
    protocol_price: float | None = None,
    governance_proposal: GovernanceProposal | None = None,
    # Simulation parameters
    simulate_tvl_drop_percent: float | None = None,
    simulate_price_deviation_percent: float | None = None,
    simulate_short_voting_period: bool = False,
    # Adapter parameter
    adapter: "BaseProtocolAdapter | None" = None,
) -> DetectionResponse:
    w3 = get_web3()
    aggregator = SentinelAggregator()
    assessments: list[ThreatAssessment] = []

    is_simulation = any([
        simulate_tvl_drop_percent is not None,
        simulate_price_deviation_percent is not None,
        simulate_short_voting_period,
    ])

    if adapter is None and not is_simulation:
        try:
            from aegis.adapters import get_adapter
            adapter = get_adapter(w3, protocol_address)
            logger.info("Auto-detected adapter: %s", adapter.protocol_type)
        except Exception as e:
            logger.debug("Could not auto-detect adapter: %s", e)
            adapter = None

    # liquidity sentinel
    try:
        if simulate_tvl_drop_percent is not None:
            base_tvl = 1_000_000 * 10**18
            current_tvl = int(base_tvl * (1 - simulate_tvl_drop_percent / 100))
            prev_tvl = base_tvl
            logger.info("SIMULATION: TVL drop %.1f%% (from %d to %d)", simulate_tvl_drop_percent, prev_tvl, current_tvl)
        elif adapter is not None:
            try:
                current_tvl = adapter.get_tvl_sync()
                prev_tvl = previous_tvl if previous_tvl > 0 else None
                logger.info("ADAPTER: Fetched TVL %d from %s", current_tvl, adapter.protocol_type)
            except Exception as e:
                logger.warning("Adapter TVL fetch failed: %s, falling back", e)
                current_tvl = 1_000_000 * 10**18
                prev_tvl = None
        else:
            try:
                current_tvl = get_protocol_tvl(w3, protocol_address)
                prev_tvl = previous_tvl if previous_tvl > 0 else None
            except Exception:
                # fallback to mock data if chain read fails
                current_tvl = 1_000_000 * 10**18
                prev_tvl = None
                logger.warning("Could not read TVL from chain, using mock data")

        liquidity_assessment = monitor_tvl(
            protocol_address=protocol_address,
            current_tvl=current_tvl,
            previous_tvl=prev_tvl,
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

    # oracle sentinel
    try:
        chainlink_data = get_eth_usd_price(w3)

        if simulate_price_deviation_percent is not None:
            p_price = chainlink_data.price * (1 + simulate_price_deviation_percent / 100)
            logger.info("SIMULATION: Price deviation %.1f%% (Chainlink: $%.2f, Protocol: $%.2f)",
                       simulate_price_deviation_percent, chainlink_data.price, p_price)
        elif protocol_price is not None:
            p_price = protocol_price
        else:
            p_price = chainlink_data.price

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

    # governance sentinel
    try:
        if simulate_short_voting_period:
            simulated_proposal = GovernanceProposal(
                proposal_id="sim-001",
                proposer="0xAttacker",
                targets=["0xProtocol"],
                calldatas=["0x" + "a9059cbb" + "0" * 56],  # transfer signature
                voting_period_blocks=50,
                description="Emergency fund transfer",
            )
            logger.info("SIMULATION: Short voting period proposal (50 blocks)")
            gov_assessment = analyze_proposal(simulated_proposal)
        elif governance_proposal is not None:
            gov_assessment = analyze_proposal(governance_proposal)
        else:
            # no active proposal, default to none
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

    # consensus
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
