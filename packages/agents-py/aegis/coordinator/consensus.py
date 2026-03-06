"""Consensus algorithms for sentinel voting with VRF tie-breaker support."""

from __future__ import annotations

import logging
from collections import Counter
from typing import TYPE_CHECKING

from aegis.config import SENTINEL_CONFIG
from aegis.models import (
    ActionRecommendation,
    ConsensusResult,
    SentinelVote,
    ThreatLevel,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

THREAT_ORDER = [
    ThreatLevel.NONE,
    ThreatLevel.LOW,
    ThreatLevel.MEDIUM,
    ThreatLevel.HIGH,
    ThreatLevel.CRITICAL,
]

# Sentinel ID to index mapping (for VRF selection)
SENTINEL_TYPE_TO_ID = {
    "LIQUIDITY": 1,
    "ORACLE": 2,
    "GOVERNANCE": 3,
}

SENTINEL_ID_TO_TYPE = {v: k for k, v in SENTINEL_TYPE_TO_ID.items()}


def is_tie(votes: list[SentinelVote]) -> bool:
    """Check if there's a tie in the votes (no 2/3 majority)."""
    if len(votes) < SENTINEL_CONFIG["min_votes_for_consensus"]:
        return False

    threat_counts: Counter[ThreatLevel] = Counter()
    for vote in votes:
        threat_counts[vote.threat_level] += 1

    _, max_count = threat_counts.most_common(1)[0]
    agreement_ratio = max_count / len(votes)

    # Tie if we don't reach consensus threshold
    return agreement_ratio < SENTINEL_CONFIG["consensus_threshold"]


def get_sentinel_ids_from_votes(votes: list[SentinelVote]) -> list[int]:
    """Extract sentinel IDs from votes for VRF tie-breaker."""
    sentinel_ids = []
    for vote in votes:
        # Parse sentinel type from sentinel_id (e.g., "liquidity-sentinel-0" -> LIQUIDITY -> 1)
        sentinel_id_str = vote.sentinel_id.lower()
        if "liquidity" in sentinel_id_str:
            sentinel_ids.append(SENTINEL_TYPE_TO_ID["LIQUIDITY"])
        elif "oracle" in sentinel_id_str:
            sentinel_ids.append(SENTINEL_TYPE_TO_ID["ORACLE"])
        elif "governance" in sentinel_id_str:
            sentinel_ids.append(SENTINEL_TYPE_TO_ID["GOVERNANCE"])
    return sentinel_ids


def reach_consensus(votes: list[SentinelVote], use_vrf_on_tie: bool = False) -> ConsensusResult:
    """
    Reach consensus among sentinel votes using 2/3 majority rule.

    If use_vrf_on_tie=True and there's a tie, will trigger VRF tie-breaker.
    """
    # 2/3 majority rule
    if len(votes) < SENTINEL_CONFIG["min_votes_for_consensus"]:
        return ConsensusResult(
            consensus_reached=False,
            final_threat_level=ThreatLevel.NONE,
            agreement_ratio=0.0,
            votes=votes,
            action_recommended=ActionRecommendation.NONE,
            tie_breaker_used=False,
        )

    threat_counts: Counter[ThreatLevel] = Counter()
    for vote in votes:
        threat_counts[vote.threat_level] += 1

    majority_threat, max_count = threat_counts.most_common(1)[0]

    agreement_ratio = max_count / len(votes)
    consensus_reached = agreement_ratio >= SENTINEL_CONFIG["consensus_threshold"]

    # Check for tie and use VRF if enabled
    tie_breaker_used = False
    vrf_request_id = None
    vrf_selected_sentinel = None

    if not consensus_reached and use_vrf_on_tie and len(votes) >= 2:
        logger.info("Tie detected (agreement_ratio=%.2f), triggering VRF tie-breaker", agreement_ratio)

        try:
            from aegis.blockchain.vrf_consumer import (
                request_vrf_tie_breaker,
            )

            # Get sentinel IDs for VRF
            sentinel_ids = get_sentinel_ids_from_votes(votes)

            if len(sentinel_ids) >= 2:
                # Request VRF tie-breaker
                request_id, tie_breaker_id, tx_hash = request_vrf_tie_breaker(sentinel_ids)
                vrf_request_id = request_id
                tie_breaker_used = True

                logger.info(
                    "VRF tie-breaker requested: request_id=%d, tx=%s",
                    request_id,
                    tx_hash,
                )

                # Note: VRF fulfillment is async, so we return pending state
                # The caller can poll for fulfillment later

        except Exception as e:
            logger.error("VRF tie-breaker request failed: %s", e)
            # Fall back to non-VRF behavior

    action_recommended = ActionRecommendation.NONE
    if consensus_reached:
        if majority_threat == ThreatLevel.CRITICAL:
            action_recommended = ActionRecommendation.CIRCUIT_BREAKER
        elif majority_threat in (ThreatLevel.HIGH, ThreatLevel.MEDIUM):
            action_recommended = ActionRecommendation.ALERT

    return ConsensusResult(
        consensus_reached=consensus_reached,
        final_threat_level=majority_threat,
        agreement_ratio=agreement_ratio,
        votes=votes,
        action_recommended=action_recommended,
        tie_breaker_used=tie_breaker_used,
        vrf_request_id=vrf_request_id,
        vrf_selected_sentinel=vrf_selected_sentinel,
    )


def resolve_tie_with_vrf(
    votes: list[SentinelVote],
    vrf_request_id: int,
) -> ConsensusResult:
    """
    Resolve a tie using the VRF result.

    This function checks if VRF is fulfilled and uses the selected sentinel's
    vote as the deciding vote.
    """
    from aegis.blockchain.vrf_consumer import check_vrf_fulfillment

    vrf_result = check_vrf_fulfillment(vrf_request_id)

    if vrf_result is None or not vrf_result.get("fulfilled"):
        # VRF not yet fulfilled, return pending state
        return ConsensusResult(
            consensus_reached=False,
            final_threat_level=ThreatLevel.NONE,
            agreement_ratio=0.0,
            votes=votes,
            action_recommended=ActionRecommendation.NONE,
            tie_breaker_used=True,
            vrf_request_id=vrf_request_id,
            vrf_selected_sentinel=None,
        )

    selected_sentinel_id = vrf_result["selected_sentinel_id"]
    selected_sentinel_type = SENTINEL_ID_TO_TYPE.get(selected_sentinel_id, "UNKNOWN")

    logger.info(
        "VRF tie-breaker resolved: selected sentinel %d (%s)",
        selected_sentinel_id,
        selected_sentinel_type,
    )

    # Find the vote from the selected sentinel
    selected_vote = None
    for vote in votes:
        sentinel_id_str = vote.sentinel_id.lower()
        if selected_sentinel_type.lower() in sentinel_id_str:
            selected_vote = vote
            break

    if selected_vote is None:
        # Fallback: use first vote if selected sentinel not found
        logger.warning("Selected sentinel vote not found, using first vote")
        selected_vote = votes[0]

    # The selected sentinel's vote becomes the final decision
    final_threat_level = selected_vote.threat_level

    action_recommended = ActionRecommendation.NONE
    if final_threat_level == ThreatLevel.CRITICAL:
        action_recommended = ActionRecommendation.CIRCUIT_BREAKER
    elif final_threat_level in (ThreatLevel.HIGH, ThreatLevel.MEDIUM):
        action_recommended = ActionRecommendation.ALERT

    return ConsensusResult(
        consensus_reached=True,  # VRF resolves the tie
        final_threat_level=final_threat_level,
        agreement_ratio=1.0 / len(votes),  # Single decider
        votes=votes,
        action_recommended=action_recommended,
        tie_breaker_used=True,
        vrf_request_id=vrf_request_id,
        vrf_selected_sentinel=selected_sentinel_type,
    )


def weighted_consensus(votes: list[SentinelVote], use_vrf_on_tie: bool = False) -> ConsensusResult:
    """
    Weighted consensus considering confidence scores.

    Higher confidence votes carry more weight.
    If use_vrf_on_tie=True and there's a tie, will trigger VRF tie-breaker.
    """
    if len(votes) < SENTINEL_CONFIG["min_votes_for_consensus"]:
        return ConsensusResult(
            consensus_reached=False,
            final_threat_level=ThreatLevel.NONE,
            agreement_ratio=0.0,
            votes=votes,
            action_recommended=ActionRecommendation.NONE,
            tie_breaker_used=False,
        )

    weighted_scores: dict[ThreatLevel, float] = {}
    total_weight = 0.0

    for vote in votes:
        weight = vote.confidence
        total_weight += weight
        weighted_scores[vote.threat_level] = (
            weighted_scores.get(vote.threat_level, 0.0) + weight
        )

    majority_threat = max(weighted_scores, key=weighted_scores.get)  # type: ignore[arg-type]
    max_weight = weighted_scores[majority_threat]

    agreement_ratio = max_weight / total_weight if total_weight > 0 else 0.0
    consensus_reached = agreement_ratio >= SENTINEL_CONFIG["consensus_threshold"]

    # Check for tie and use VRF if enabled
    tie_breaker_used = False
    vrf_request_id = None
    vrf_selected_sentinel = None

    if not consensus_reached and use_vrf_on_tie and len(votes) >= 2:
        logger.info("Weighted tie detected (agreement_ratio=%.2f), triggering VRF tie-breaker", agreement_ratio)

        try:
            from aegis.blockchain.vrf_consumer import request_vrf_tie_breaker

            sentinel_ids = get_sentinel_ids_from_votes(votes)

            if len(sentinel_ids) >= 2:
                request_id, tie_breaker_id, tx_hash = request_vrf_tie_breaker(sentinel_ids)
                vrf_request_id = request_id
                tie_breaker_used = True

                logger.info(
                    "VRF tie-breaker requested: request_id=%d, tx=%s",
                    request_id,
                    tx_hash,
                )

        except Exception as e:
            logger.error("VRF tie-breaker request failed: %s", e)

    action_recommended = ActionRecommendation.NONE
    if consensus_reached:
        idx = THREAT_ORDER.index(majority_threat)
        if idx >= 4:  # CRITICAL
            action_recommended = ActionRecommendation.CIRCUIT_BREAKER
        elif idx >= 2:  # MEDIUM or HIGH
            action_recommended = ActionRecommendation.ALERT

    return ConsensusResult(
        consensus_reached=consensus_reached,
        final_threat_level=majority_threat,
        agreement_ratio=agreement_ratio,
        votes=votes,
        action_recommended=action_recommended,
        tie_breaker_used=tie_breaker_used,
        vrf_request_id=vrf_request_id,
        vrf_selected_sentinel=vrf_selected_sentinel,
    )
