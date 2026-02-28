"""Consensus algorithms for AEGIS sentinel voting.

Ported from packages/agents/src/coordinator/consensus.ts
"""

from collections import Counter

from aegis.config import SENTINEL_CONFIG
from aegis.models import (
    ActionRecommendation,
    ConsensusResult,
    SentinelVote,
    ThreatLevel,
)

THREAT_ORDER = [
    ThreatLevel.NONE,
    ThreatLevel.LOW,
    ThreatLevel.MEDIUM,
    ThreatLevel.HIGH,
    ThreatLevel.CRITICAL,
]


def reach_consensus(votes: list[SentinelVote]) -> ConsensusResult:
    """Reach consensus among sentinel votes using 2/3 majority rule.

    Exact port of the TypeScript implementation.
    """
    if len(votes) < SENTINEL_CONFIG["min_votes_for_consensus"]:
        return ConsensusResult(
            consensus_reached=False,
            final_threat_level=ThreatLevel.NONE,
            agreement_ratio=0.0,
            votes=votes,
            action_recommended=ActionRecommendation.NONE,
        )

    # Count votes by threat level
    threat_counts: Counter[ThreatLevel] = Counter()
    for vote in votes:
        threat_counts[vote.threat_level] += 1

    # Find majority
    majority_threat, max_count = threat_counts.most_common(1)[0]

    agreement_ratio = max_count / len(votes)
    consensus_reached = agreement_ratio >= SENTINEL_CONFIG["consensus_threshold"]

    # Determine recommended action
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
    )


def weighted_consensus(votes: list[SentinelVote]) -> ConsensusResult:
    """Calculate a weighted threat level considering confidence scores.

    Higher confidence votes carry more weight. Exact port of the TypeScript
    implementation.
    """
    if len(votes) < SENTINEL_CONFIG["min_votes_for_consensus"]:
        return ConsensusResult(
            consensus_reached=False,
            final_threat_level=ThreatLevel.NONE,
            agreement_ratio=0.0,
            votes=votes,
            action_recommended=ActionRecommendation.NONE,
        )

    # Weight each vote by confidence
    weighted_scores: dict[ThreatLevel, float] = {}
    total_weight = 0.0

    for vote in votes:
        weight = vote.confidence
        total_weight += weight
        weighted_scores[vote.threat_level] = (
            weighted_scores.get(vote.threat_level, 0.0) + weight
        )

    # Find the threat level with highest weighted score
    majority_threat = max(weighted_scores, key=weighted_scores.get)  # type: ignore[arg-type]
    max_weight = weighted_scores[majority_threat]

    agreement_ratio = max_weight / total_weight if total_weight > 0 else 0.0
    consensus_reached = agreement_ratio >= SENTINEL_CONFIG["consensus_threshold"]

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
    )
