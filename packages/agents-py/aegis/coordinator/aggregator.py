"""Sentinel aggregator -- collects assessments and runs consensus."""

from aegis.coordinator.consensus import reach_consensus
from aegis.models import ConsensusResult, SentinelVote, ThreatAssessment


class SentinelAggregator:

    def __init__(self) -> None:
        self._assessments: dict[str, ThreatAssessment] = {}

    def submit_assessment(self, assessment: ThreatAssessment) -> None:
        self._assessments[assessment.sentinel_id] = assessment

    def aggregate(self) -> ConsensusResult:
        votes: list[SentinelVote] = []

        for sentinel_id, assessment in self._assessments.items():
            votes.append(
                SentinelVote(
                    sentinel_id=sentinel_id,
                    threat_level=assessment.threat_level,
                    confidence=assessment.confidence,
                    timestamp=assessment.timestamp,
                    signature="",  # would be signed in production
                )
            )

        return reach_consensus(votes)

    def clear(self) -> None:
        self._assessments.clear()

    @property
    def count(self) -> int:
        return len(self._assessments)

    @property
    def assessments(self) -> list[ThreatAssessment]:
        return list(self._assessments.values())
