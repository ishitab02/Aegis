"""Tests for sentinel detection logic."""

from aegis.models import (
    ActionRecommendation,
    GovernanceProposal,
    PriceFeedData,
    ThreatLevel,
)
from aegis.sentinels.governance_sentinel import analyze_proposal
from aegis.sentinels.liquidity_sentinel import monitor_tvl
from aegis.sentinels.oracle_sentinel import monitor_price_feeds
from aegis.utils import now_seconds


class TestLiquiditySentinel:
    def test_initial_snapshot_returns_none(self):
        result = monitor_tvl(
            protocol_address="0x0000000000000000000000000000000000000001",
            current_tvl=100 * 10**18,
            previous_tvl=0,
        )
        assert result.threat_level == ThreatLevel.NONE
        assert "Initial TVL" in result.details

    def test_critical_tvl_drop(self):
        prev = 100 * 10**18
        current = 75 * 10**18  # 25% drop
        result = monitor_tvl(
            protocol_address="0x0000000000000000000000000000000000000001",
            current_tvl=current,
            previous_tvl=prev,
        )
        assert result.threat_level == ThreatLevel.CRITICAL
        assert result.confidence == 0.95
        assert result.recommendation == ActionRecommendation.CIRCUIT_BREAKER

    def test_high_tvl_drop(self):
        prev = 100 * 10**18
        current = 88 * 10**18  # 12% drop
        result = monitor_tvl(
            protocol_address="0x0000000000000000000000000000000000000001",
            current_tvl=current,
            previous_tvl=prev,
        )
        assert result.threat_level == ThreatLevel.HIGH
        assert result.recommendation == ActionRecommendation.ALERT

    def test_medium_tvl_drop(self):
        prev = 100 * 10**18
        current = 93 * 10**18  # 7% drop
        result = monitor_tvl(
            protocol_address="0x0000000000000000000000000000000000000001",
            current_tvl=current,
            previous_tvl=prev,
        )
        assert result.threat_level == ThreatLevel.MEDIUM

    def test_no_threat(self):
        prev = 100 * 10**18
        current = 98 * 10**18  # 2% drop
        result = monitor_tvl(
            protocol_address="0x0000000000000000000000000000000000000001",
            current_tvl=current,
            previous_tvl=prev,
        )
        assert result.threat_level == ThreatLevel.NONE


class TestOracleSentinel:
    def test_critical_deviation(self):
        chainlink = PriceFeedData(
            price=2000.0,
            updated_at=now_seconds(),
            decimals=8,
            feed_address="0x0000000000000000000000000000000000000001",
        )
        result = monitor_price_feeds(protocol_price=2120.0, chainlink_data=chainlink)
        assert result.threat_level == ThreatLevel.CRITICAL
        assert result.recommendation == ActionRecommendation.CIRCUIT_BREAKER

    def test_high_deviation(self):
        chainlink = PriceFeedData(
            price=2000.0,
            updated_at=now_seconds(),
            decimals=8,
            feed_address="0x0000000000000000000000000000000000000001",
        )
        result = monitor_price_feeds(protocol_price=2050.0, chainlink_data=chainlink)
        assert result.threat_level == ThreatLevel.HIGH

    def test_stale_feed(self):
        chainlink = PriceFeedData(
            price=2000.0,
            updated_at=now_seconds() - 4000,
            decimals=8,
            feed_address="0x0000000000000000000000000000000000000001",
        )
        result = monitor_price_feeds(protocol_price=2000.0, chainlink_data=chainlink)
        assert result.threat_level == ThreatLevel.HIGH

    def test_no_threat(self):
        chainlink = PriceFeedData(
            price=2000.0,
            updated_at=now_seconds(),
            decimals=8,
            feed_address="0x0000000000000000000000000000000000000001",
        )
        result = monitor_price_feeds(protocol_price=2005.0, chainlink_data=chainlink)
        assert result.threat_level == ThreatLevel.NONE


class TestGovernanceSentinel:
    def test_no_threats_in_clean_proposal(self):
        proposal = GovernanceProposal(
            id="1",
            proposer="0x1234",
            description="Increase rewards by 5%",
            targets=["0xabc"],
            calldatas=["0xdeadbeef"],
            values=["0"],
            start_block=1000,
            end_block=2000,
        )
        result = analyze_proposal(proposal)
        assert result.threat_level == ThreatLevel.NONE

    def test_short_voting_period(self):
        proposal = GovernanceProposal(
            id="2",
            proposer="0x1234",
            description="Emergency fix",
            targets=["0xabc"],
            calldatas=["0xdeadbeef"],
            values=["0"],
            start_block=1000,
            end_block=1050,
        )
        result = analyze_proposal(proposal)
        assert result.threat_level == ThreatLevel.HIGH
        assert any("short voting period" in i for i in result.indicators)
