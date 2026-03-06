"""Tests for VRF tie-breaker functionality."""

from unittest.mock import patch

from aegis.coordinator.consensus import (
    SENTINEL_ID_TO_TYPE,
    SENTINEL_TYPE_TO_ID,
    get_sentinel_ids_from_votes,
    is_tie,
    reach_consensus,
)
from aegis.models import SentinelVote, ThreatLevel


class TestTieDetection:
    """Test tie detection logic."""

    def test_no_tie_with_majority(self):
        """2/3 majority should not be a tie."""
        votes = [
            SentinelVote(sentinel_id="liquidity-sentinel-0", threat_level=ThreatLevel.CRITICAL, confidence=0.9, timestamp=1000),
            SentinelVote(sentinel_id="oracle-sentinel-0", threat_level=ThreatLevel.CRITICAL, confidence=0.9, timestamp=1000),
            SentinelVote(sentinel_id="governance-sentinel-0", threat_level=ThreatLevel.NONE, confidence=0.9, timestamp=1000),
        ]
        assert not is_tie(votes)

    def test_tie_with_three_way_split(self):
        """Three different votes should be a tie."""
        votes = [
            SentinelVote(sentinel_id="liquidity-sentinel-0", threat_level=ThreatLevel.CRITICAL, confidence=0.9, timestamp=1000),
            SentinelVote(sentinel_id="oracle-sentinel-0", threat_level=ThreatLevel.HIGH, confidence=0.9, timestamp=1000),
            SentinelVote(sentinel_id="governance-sentinel-0", threat_level=ThreatLevel.NONE, confidence=0.9, timestamp=1000),
        ]
        assert is_tie(votes)

    def test_not_tie_with_insufficient_votes(self):
        """Not enough votes should return False (not a tie, just invalid)."""
        votes = [
            SentinelVote(sentinel_id="liquidity-sentinel-0", threat_level=ThreatLevel.CRITICAL, confidence=0.9, timestamp=1000),
        ]
        assert not is_tie(votes)


class TestSentinelIdExtraction:
    """Test sentinel ID extraction from votes."""

    def test_extract_liquidity_sentinel(self):
        """Should extract LIQUIDITY sentinel ID."""
        votes = [
            SentinelVote(sentinel_id="liquidity-sentinel-0", threat_level=ThreatLevel.CRITICAL, confidence=0.9, timestamp=1000),
        ]
        ids = get_sentinel_ids_from_votes(votes)
        assert ids == [SENTINEL_TYPE_TO_ID["LIQUIDITY"]]

    def test_extract_multiple_sentinels(self):
        """Should extract all sentinel IDs."""
        votes = [
            SentinelVote(sentinel_id="liquidity-sentinel-0", threat_level=ThreatLevel.CRITICAL, confidence=0.9, timestamp=1000),
            SentinelVote(sentinel_id="oracle-sentinel-0", threat_level=ThreatLevel.HIGH, confidence=0.9, timestamp=1000),
            SentinelVote(sentinel_id="governance-sentinel-0", threat_level=ThreatLevel.NONE, confidence=0.9, timestamp=1000),
        ]
        ids = get_sentinel_ids_from_votes(votes)
        assert ids == [1, 2, 3]  # LIQUIDITY=1, ORACLE=2, GOVERNANCE=3


class TestSentinelIdMapping:
    """Test sentinel ID <-> type mappings."""

    def test_sentinel_type_to_id(self):
        """Should map types to correct IDs."""
        assert SENTINEL_TYPE_TO_ID["LIQUIDITY"] == 1
        assert SENTINEL_TYPE_TO_ID["ORACLE"] == 2
        assert SENTINEL_TYPE_TO_ID["GOVERNANCE"] == 3

    def test_sentinel_id_to_type(self):
        """Should reverse map IDs to types."""
        assert SENTINEL_ID_TO_TYPE[1] == "LIQUIDITY"
        assert SENTINEL_ID_TO_TYPE[2] == "ORACLE"
        assert SENTINEL_ID_TO_TYPE[3] == "GOVERNANCE"


class TestConsensusWithVRF:
    """Test consensus with VRF tie-breaker option."""

    def test_consensus_with_vrf_flag_no_tie(self):
        """VRF should not be triggered when there's consensus."""
        votes = [
            SentinelVote(sentinel_id="liquidity-sentinel-0", threat_level=ThreatLevel.CRITICAL, confidence=0.9, timestamp=1000),
            SentinelVote(sentinel_id="oracle-sentinel-0", threat_level=ThreatLevel.CRITICAL, confidence=0.9, timestamp=1000),
            SentinelVote(sentinel_id="governance-sentinel-0", threat_level=ThreatLevel.NONE, confidence=0.9, timestamp=1000),
        ]

        result = reach_consensus(votes, use_vrf_on_tie=True)

        assert result.consensus_reached
        assert result.final_threat_level == ThreatLevel.CRITICAL
        assert not result.tie_breaker_used
        assert result.vrf_request_id is None

    def test_consensus_without_vrf_on_tie(self):
        """Without VRF, tie should result in no consensus."""
        votes = [
            SentinelVote(sentinel_id="liquidity-sentinel-0", threat_level=ThreatLevel.CRITICAL, confidence=0.9, timestamp=1000),
            SentinelVote(sentinel_id="oracle-sentinel-0", threat_level=ThreatLevel.HIGH, confidence=0.9, timestamp=1000),
            SentinelVote(sentinel_id="governance-sentinel-0", threat_level=ThreatLevel.NONE, confidence=0.9, timestamp=1000),
        ]

        result = reach_consensus(votes, use_vrf_on_tie=False)

        assert not result.consensus_reached
        assert not result.tie_breaker_used

    @patch('aegis.blockchain.vrf_consumer.request_vrf_tie_breaker')
    def test_consensus_with_vrf_on_tie_triggers_vrf(self, mock_vrf):
        """With VRF enabled, tie should trigger VRF request."""
        mock_vrf.return_value = (12345, 1, "0xabc123")

        votes = [
            SentinelVote(sentinel_id="liquidity-sentinel-0", threat_level=ThreatLevel.CRITICAL, confidence=0.9, timestamp=1000),
            SentinelVote(sentinel_id="oracle-sentinel-0", threat_level=ThreatLevel.HIGH, confidence=0.9, timestamp=1000),
            SentinelVote(sentinel_id="governance-sentinel-0", threat_level=ThreatLevel.NONE, confidence=0.9, timestamp=1000),
        ]

        result = reach_consensus(votes, use_vrf_on_tie=True)

        # VRF was triggered
        mock_vrf.assert_called_once()
        assert result.tie_breaker_used
        assert result.vrf_request_id == 12345

        # But consensus is still not reached (pending VRF fulfillment)
        assert not result.consensus_reached


class TestConsensusResultFields:
    """Test ConsensusResult has VRF fields."""

    def test_consensus_result_has_vrf_fields(self):
        """ConsensusResult should have VRF tie-breaker fields."""
        votes = [
            SentinelVote(sentinel_id="liquidity-sentinel-0", threat_level=ThreatLevel.NONE, confidence=0.9, timestamp=1000),
            SentinelVote(sentinel_id="oracle-sentinel-0", threat_level=ThreatLevel.NONE, confidence=0.9, timestamp=1000),
        ]

        result = reach_consensus(votes)

        assert hasattr(result, 'tie_breaker_used')
        assert hasattr(result, 'vrf_request_id')
        assert hasattr(result, 'vrf_selected_sentinel')
        assert not result.tie_breaker_used
        assert result.vrf_request_id is None
        assert result.vrf_selected_sentinel is None
