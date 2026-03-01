"""Sentinel aggregator — collects assessments and runs consensus.

Ported from packages/agents/src/coordinator/aggregator.ts
"""

from aegis.coordinator.consensus import reach_consensus
from aegis.models import ConsensusResult, SentinelVote, ThreatAssessment


class SentinelAggregator:
    """Aggregates assessments from multiple sentinels and produces a consensus result."""

    def __init__(self) -> None:
        self._assessments: dict[str, ThreatAssessment] = {}

    def submit_assessment(self, assessment: ThreatAssessment) -> None:
        """Submit an assessment from a sentinel."""
        self._assessments[assessment.sentinel_id] = assessment

    def aggregate(self) -> ConsensusResult:
        """Convert current assessments to votes and run consensus."""
        votes: list[SentinelVote] = []

        for sentinel_id, assessment in self._assessments.items():
            votes.append(
                SentinelVote(
                    sentinel_id=sentinel_id,
                    threat_level=assessment.threat_level,
                    confidence=assessment.confidence,
                    timestamp=assessment.timestamp,
                    signature="",  # Would be signed in production
                )
            )

        return reach_consensus(votes)

    def clear(self) -> None:
        """Clear all assessments (e.g., after a consensus round)."""
        self._assessments.clear()

    @property
    def count(self) -> int:
        """Get count of current assessments."""
        return len(self._assessments)

    @property
    def assessments(self) -> list[ThreatAssessment]:
        """Get all current assessments as a list."""
        return list(self._assessments.values())
