"""Tests for consensus algorithms.

Ported from packages/agents/test/consensus.test.ts
"""

import time

from aegis.coordinator.consensus import reach_consensus, weighted_consensus
from aegis.models import ActionRecommendation, SentinelVote, ThreatLevel


def make_vote(
    sentinel_id: str, level: ThreatLevel, confidence: float = 0.9
) -> SentinelVote:
    return SentinelVote(
        sentinel_id=sentinel_id,
        threat_level=level,
        confidence=confidence,
        timestamp=int(time.time()),
        signature="",
    )


class TestReachConsensus:
    def test_insufficient_votes(self):
        result = reach_consensus([make_vote("s1", ThreatLevel.CRITICAL)])
        assert result.consensus_reached is False
        assert result.action_recommended == ActionRecommendation.NONE

    def test_two_thirds_critical(self):
        votes = [
            make_vote("s1", ThreatLevel.CRITICAL),
            make_vote("s2", ThreatLevel.CRITICAL),
            make_vote("s3", ThreatLevel.HIGH),
        ]
        result = reach_consensus(votes)
        assert result.consensus_reached is True
        assert result.final_threat_level == ThreatLevel.CRITICAL
        assert result.action_recommended == ActionRecommendation.CIRCUIT_BREAKER
        assert abs(result.agreement_ratio - 0.67) < 0.01

    def test_unanimous_none(self):
        votes = [
            make_vote("s1", ThreatLevel.NONE),
            make_vote("s2", ThreatLevel.NONE),
            make_vote("s3", ThreatLevel.NONE),
        ]
        result = reach_consensus(votes)
        assert result.consensus_reached is True
        assert result.final_threat_level == ThreatLevel.NONE
        assert result.action_recommended == ActionRecommendation.NONE

    def test_three_way_split(self):
        votes = [
            make_vote("s1", ThreatLevel.CRITICAL),
            make_vote("s2", ThreatLevel.HIGH),
            make_vote("s3", ThreatLevel.MEDIUM),
        ]
        result = reach_consensus(votes)
        assert result.consensus_reached is False

    def test_high_consensus_alert(self):
        votes = [
            make_vote("s1", ThreatLevel.HIGH),
            make_vote("s2", ThreatLevel.HIGH),
            make_vote("s3", ThreatLevel.MEDIUM),
        ]
        result = reach_consensus(votes)
        assert result.consensus_reached is True
        assert result.action_recommended == ActionRecommendation.ALERT

    def test_two_sentinel_consensus(self):
        votes = [
            make_vote("s1", ThreatLevel.CRITICAL),
            make_vote("s2", ThreatLevel.CRITICAL),
        ]
        result = reach_consensus(votes)
        assert result.consensus_reached is True
        assert result.final_threat_level == ThreatLevel.CRITICAL
        assert result.agreement_ratio == 1.0


class TestWeightedConsensus:
    def test_high_confidence_wins(self):
        votes = [
            make_vote("s1", ThreatLevel.CRITICAL, 0.95),
            make_vote("s2", ThreatLevel.CRITICAL, 0.90),
            make_vote("s3", ThreatLevel.NONE, 0.50),
        ]
        result = weighted_consensus(votes)
        assert result.consensus_reached is True
        assert result.final_threat_level == ThreatLevel.CRITICAL
