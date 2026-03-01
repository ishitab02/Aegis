"""Tests for protocol adapters.

These tests verify the adapter base class and protocol-specific implementations.
Most tests use mocked Web3 responses to avoid requiring network access.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aegis.adapters.base import (
    BaseProtocolAdapter,
    ProtocolEvent,
    ProtocolMetricsSnapshot,
    TokenBalance,
    TTLCache,
)


# ============ TTLCache Tests ============


class TestTTLCache:
    """Tests for the TTL cache implementation."""

    def test_set_and_get(self):
        """Test basic set and get operations."""
        cache = TTLCache(ttl_seconds=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist."""
        cache = TTLCache(ttl_seconds=60)
        assert cache.get("nonexistent") is None

    def test_expiration(self):
        """Test that values expire after TTL."""
        cache = TTLCache(ttl_seconds=1)
        cache.set("key", "value")
        assert cache.get("key") == "value"

        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key") is None

    def test_clear(self):
        """Test clearing the cache."""
        cache = TTLCache(ttl_seconds=60)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_invalidate(self):
        """Test invalidating a specific key."""
        cache = TTLCache(ttl_seconds=60)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.invalidate("key1")
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    @pytest.mark.asyncio
    async def test_get_or_fetch_cache_hit(self):
        """Test get_or_fetch returns cached value without calling fetch."""
        cache = TTLCache(ttl_seconds=60)
        cache.set("key", "cached_value")

        fetch_called = False

        async def fetch():
            nonlocal fetch_called
            fetch_called = True
            return "fetched_value"

        result = await cache.get_or_fetch("key", fetch)
        assert result == "cached_value"
        assert not fetch_called

    @pytest.mark.asyncio
    async def test_get_or_fetch_cache_miss(self):
        """Test get_or_fetch calls fetch and caches result."""
        cache = TTLCache(ttl_seconds=60)

        async def fetch():
            return "fetched_value"

        result = await cache.get_or_fetch("key", fetch)
        assert result == "fetched_value"
        assert cache.get("key") == "fetched_value"


# ============ TokenBalance Tests ============


class TestTokenBalance:
    """Tests for TokenBalance model."""

    def test_create_token_balance(self):
        """Test creating a TokenBalance."""
        balance = TokenBalance(
            token_address="0x1234567890123456789012345678901234567890",
            symbol="USDC",
            decimals=6,
            balance_raw=1_000_000,
            balance_formatted=1.0,
        )
        assert balance.symbol == "USDC"
        assert balance.decimals == 6
        assert balance.balance_raw == 1_000_000
        assert balance.balance_wei == 1_000_000  # alias

    def test_balance_wei_property(self):
        """Test balance_wei property is alias for balance_raw."""
        balance = TokenBalance(
            token_address="0x1234567890123456789012345678901234567890",
            symbol="ETH",
            decimals=18,
            balance_raw=10**18,
            balance_formatted=1.0,
        )
        assert balance.balance_wei == balance.balance_raw


# ============ ProtocolEvent Tests ============


class TestProtocolEvent:
    """Tests for ProtocolEvent model."""

    def test_create_protocol_event(self):
        """Test creating a ProtocolEvent."""
        event = ProtocolEvent(
            event_name="Transfer",
            block_number=12345678,
            transaction_hash="0xabc123",
            log_index=5,
            args={"from": "0x111", "to": "0x222", "amount": 1000},
        )
        assert event.event_name == "Transfer"
        assert event.block_number == 12345678
        assert event.args["amount"] == 1000


# ============ ProtocolMetricsSnapshot Tests ============


class TestProtocolMetricsSnapshot:
    """Tests for ProtocolMetricsSnapshot model."""

    def test_create_snapshot(self):
        """Test creating a metrics snapshot."""
        snapshot = ProtocolMetricsSnapshot(
            protocol_address="0x1234567890123456789012345678901234567890",
            protocol_type="aave_v3",
            tvl_wei=1000 * 10**18,
            timestamp=int(time.time()),
            block_number=12345678,
        )
        assert snapshot.protocol_type == "aave_v3"
        assert snapshot.tvl_wei == 1000 * 10**18


# ============ Adapter Registry Tests ============


class TestAdapterRegistry:
    """Tests for the adapter registry."""

    def test_protocol_type_detection_known_address(self):
        """Test that known addresses are detected correctly."""
        from aegis.adapters import KNOWN_PROTOCOLS, ProtocolType

        # Aave V3 Pool on Base
        base_protocols = KNOWN_PROTOCOLS.get(8453, {})
        aave_pool = "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"
        assert base_protocols.get(aave_pool) == ProtocolType.AAVE_V3

        # Uniswap V3 Factory on Base
        uni_factory = "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"
        assert base_protocols.get(uni_factory) == ProtocolType.UNISWAP_V3


# ============ Aave V3 Adapter Tests ============


class TestAaveV3Adapter:
    """Tests for Aave V3 adapter."""

    def test_adapter_creation(self):
        """Test creating an Aave V3 adapter with mocked Web3."""
        mock_web3 = MagicMock()
        mock_web3.eth.chain_id = 8453
        mock_web3.to_checksum_address = lambda x: x

        from aegis.adapters.aave_v3 import AaveV3Adapter

        adapter = AaveV3Adapter(mock_web3)
        assert adapter.protocol_type == "aave_v3"
        assert adapter.protocol_address == "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"

    def test_adapter_with_custom_address(self):
        """Test creating adapter with custom pool address."""
        mock_web3 = MagicMock()
        mock_web3.eth.chain_id = 8453
        mock_web3.to_checksum_address = lambda x: x

        from aegis.adapters.aave_v3 import AaveV3Adapter

        custom_addr = "0x1234567890123456789012345678901234567890"
        adapter = AaveV3Adapter(mock_web3, protocol_address=custom_addr)
        assert adapter.protocol_address == custom_addr


# ============ Uniswap V3 Adapter Tests ============


class TestUniswapV3Adapter:
    """Tests for Uniswap V3 adapter."""

    def test_adapter_creation_factory_mode(self):
        """Test creating a Uniswap V3 adapter in factory mode."""
        mock_web3 = MagicMock()
        mock_web3.eth.chain_id = 8453
        mock_web3.to_checksum_address = lambda x: x

        from aegis.adapters.uniswap_v3 import UniswapV3Adapter

        adapter = UniswapV3Adapter(mock_web3)
        assert adapter.protocol_type == "uniswap_v3"
        assert adapter.protocol_address == "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"

    def test_adapter_creation_pool_mode(self):
        """Test creating a Uniswap V3 adapter in pool mode."""
        mock_web3 = MagicMock()
        mock_web3.eth.chain_id = 8453
        mock_web3.to_checksum_address = lambda x: x

        from aegis.adapters.uniswap_v3 import UniswapV3Adapter

        pool_addr = "0x1234567890123456789012345678901234567890"
        adapter = UniswapV3Adapter(mock_web3, pool_address=pool_addr)
        assert adapter.protocol_address == pool_addr
        assert adapter._is_pool_mode is True


# ============ get_adapter Factory Tests ============


class TestGetAdapterFactory:
    """Tests for the get_adapter factory function."""

    def test_get_adapter_aave(self):
        """Test getting an Aave adapter via factory."""
        mock_web3 = MagicMock()
        mock_web3.eth.chain_id = 8453
        mock_web3.to_checksum_address = lambda x: x

        from aegis.adapters import get_adapter, reset_registry

        reset_registry()  # Clear any cached state

        aave_pool = "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"
        adapter = get_adapter(mock_web3, aave_pool)
        assert adapter.protocol_type == "aave_v3"

    def test_get_adapter_uniswap(self):
        """Test getting a Uniswap adapter via factory."""
        mock_web3 = MagicMock()
        mock_web3.eth.chain_id = 8453
        mock_web3.to_checksum_address = lambda x: x

        from aegis.adapters import get_adapter, reset_registry

        reset_registry()

        uni_factory = "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"
        adapter = get_adapter(mock_web3, uni_factory)
        assert adapter.protocol_type == "uniswap_v3"

    def test_get_adapter_force_type(self):
        """Test forcing a specific adapter type."""
        mock_web3 = MagicMock()
        mock_web3.eth.chain_id = 8453
        mock_web3.to_checksum_address = lambda x: x

        from aegis.adapters import get_adapter, ProtocolType, reset_registry

        reset_registry()

        # Use unknown address but force Aave type
        unknown_addr = "0x9999999999999999999999999999999999999999"
        adapter = get_adapter(mock_web3, unknown_addr, force_type=ProtocolType.AAVE_V3)
        assert adapter.protocol_type == "aave_v3"


# ============ Integration with Crew Tests ============


class TestCrewIntegration:
    """Tests for adapter integration with detection crew."""

    def test_detection_cycle_with_adapter(self):
        """Test that detection cycle accepts adapter parameter."""
        from aegis.coordinator.crew import run_detection_cycle
        from unittest.mock import MagicMock

        # Create a mock adapter
        mock_adapter = MagicMock()
        mock_adapter.protocol_type = "aave_v3"
        mock_adapter.get_tvl_sync.return_value = 1_000_000 * 10**18

        # Run detection cycle with adapter
        # We also need to mock the Chainlink price feed
        with patch("aegis.coordinator.crew.get_eth_usd_price") as mock_price:
            from aegis.models import PriceFeedData

            mock_price.return_value = PriceFeedData(
                price=2000.0,
                updated_at=int(time.time()),
                decimals=8,
                feed_address="0x4aDC67696bA383F43DD60A9e78F2C97Fbbfc7cb1",
            )

            result = run_detection_cycle(
                protocol_address="0x1234567890123456789012345678901234567890",
                adapter=mock_adapter,
            )

            assert result.consensus is not None
            assert len(result.assessments) == 3  # liquidity, oracle, governance

    def test_detection_cycle_simulation_takes_precedence(self):
        """Test that simulation parameters override adapter."""
        from aegis.coordinator.crew import run_detection_cycle

        mock_adapter = MagicMock()
        mock_adapter.protocol_type = "aave_v3"
        mock_adapter.get_tvl_sync.return_value = 1_000_000 * 10**18

        with patch("aegis.coordinator.crew.get_eth_usd_price") as mock_price:
            from aegis.models import PriceFeedData

            mock_price.return_value = PriceFeedData(
                price=2000.0,
                updated_at=int(time.time()),
                decimals=8,
                feed_address="0x4aDC67696bA383F43DD60A9e78F2C97Fbbfc7cb1",
            )

            # Simulate a critical TVL drop
            result = run_detection_cycle(
                protocol_address="0x1234567890123456789012345678901234567890",
                adapter=mock_adapter,
                simulate_tvl_drop_percent=25.0,  # This should take precedence
            )

            # Adapter should NOT have been called since we're simulating
            mock_adapter.get_tvl_sync.assert_not_called()

            # Should detect a critical threat
            liquidity_assessment = next(
                a for a in result.assessments if a.sentinel_type.value == "LIQUIDITY"
            )
            assert liquidity_assessment.threat_level.value == "CRITICAL"
