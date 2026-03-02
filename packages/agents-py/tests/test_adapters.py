"""Tests for protocol adapters."""

import time
from unittest.mock import MagicMock, patch

import pytest

from aegis.adapters.base import (
    ProtocolEvent,
    ProtocolMetricsSnapshot,
    TokenBalance,
    TTLCache,
)


class TestTTLCache:
    def test_set_and_get(self):
        cache = TTLCache(ttl_seconds=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_nonexistent_key(self):
        cache = TTLCache(ttl_seconds=60)
        assert cache.get("nonexistent") is None

    def test_expiration(self):
        cache = TTLCache(ttl_seconds=1)
        cache.set("key", "value")
        assert cache.get("key") == "value"

        # wait for expiration
        time.sleep(1.1)
        assert cache.get("key") is None

    def test_clear(self):
        cache = TTLCache(ttl_seconds=60)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_invalidate(self):
        cache = TTLCache(ttl_seconds=60)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.invalidate("key1")
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    @pytest.mark.asyncio
    async def test_get_or_fetch_cache_hit(self):
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
        cache = TTLCache(ttl_seconds=60)

        async def fetch():
            return "fetched_value"

        result = await cache.get_or_fetch("key", fetch)
        assert result == "fetched_value"
        assert cache.get("key") == "fetched_value"




class TestTokenBalance:
    def test_create_token_balance(self):
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
        balance = TokenBalance(
            token_address="0x1234567890123456789012345678901234567890",
            symbol="ETH",
            decimals=18,
            balance_raw=10**18,
            balance_formatted=1.0,
        )
        assert balance.balance_wei == balance.balance_raw




class TestProtocolEvent:
    def test_create_protocol_event(self):
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




class TestProtocolMetricsSnapshot:
    def test_create_snapshot(self):
        snapshot = ProtocolMetricsSnapshot(
            protocol_address="0x1234567890123456789012345678901234567890",
            protocol_type="aave_v3",
            tvl_wei=1000 * 10**18,
            timestamp=int(time.time()),
            block_number=12345678,
        )
        assert snapshot.protocol_type == "aave_v3"
        assert snapshot.tvl_wei == 1000 * 10**18




class TestAdapterRegistry:
    def test_protocol_type_detection_known_address(self):
        from aegis.adapters import KNOWN_PROTOCOLS, ProtocolType

        # aave v3 pool on base
        base_protocols = KNOWN_PROTOCOLS.get(8453, {})
        aave_pool = "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"
        assert base_protocols.get(aave_pool) == ProtocolType.AAVE_V3

        # uniswap v3 factory on base
        uni_factory = "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"
        assert base_protocols.get(uni_factory) == ProtocolType.UNISWAP_V3




class TestAaveV3Adapter:
    def test_adapter_creation(self):
        mock_web3 = MagicMock()
        mock_web3.eth.chain_id = 8453
        mock_web3.to_checksum_address = lambda x: x

        from aegis.adapters.aave_v3 import AaveV3Adapter

        adapter = AaveV3Adapter(mock_web3)
        assert adapter.protocol_type == "aave_v3"
        assert adapter.protocol_address == "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"

    def test_adapter_with_custom_address(self):
        mock_web3 = MagicMock()
        mock_web3.eth.chain_id = 8453
        mock_web3.to_checksum_address = lambda x: x

        from aegis.adapters.aave_v3 import AaveV3Adapter

        custom_addr = "0x1234567890123456789012345678901234567890"
        adapter = AaveV3Adapter(mock_web3, protocol_address=custom_addr)
        assert adapter.protocol_address == custom_addr




class TestUniswapV3Adapter:
    def test_adapter_creation_factory_mode(self):
        mock_web3 = MagicMock()
        mock_web3.eth.chain_id = 8453
        mock_web3.to_checksum_address = lambda x: x

        from aegis.adapters.uniswap_v3 import UniswapV3Adapter

        adapter = UniswapV3Adapter(mock_web3)
        assert adapter.protocol_type == "uniswap_v3"
        assert adapter.protocol_address == "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"

    def test_adapter_creation_pool_mode(self):
        mock_web3 = MagicMock()
        mock_web3.eth.chain_id = 8453
        mock_web3.to_checksum_address = lambda x: x

        from aegis.adapters.uniswap_v3 import UniswapV3Adapter

        pool_addr = "0x1234567890123456789012345678901234567890"
        adapter = UniswapV3Adapter(mock_web3, pool_address=pool_addr)
        assert adapter.protocol_address == pool_addr
        assert adapter._is_pool_mode is True




class TestGetAdapterFactory:
    def test_get_adapter_aave(self):
        mock_web3 = MagicMock()
        mock_web3.eth.chain_id = 8453
        mock_web3.to_checksum_address = lambda x: x

        from aegis.adapters import get_adapter, reset_registry

        reset_registry()

        aave_pool = "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"
        adapter = get_adapter(mock_web3, aave_pool)
        assert adapter.protocol_type == "aave_v3"

    def test_get_adapter_uniswap(self):
        mock_web3 = MagicMock()
        mock_web3.eth.chain_id = 8453
        mock_web3.to_checksum_address = lambda x: x

        from aegis.adapters import get_adapter, reset_registry

        reset_registry()

        uni_factory = "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"
        adapter = get_adapter(mock_web3, uni_factory)
        assert adapter.protocol_type == "uniswap_v3"

    def test_get_adapter_force_type(self):
        mock_web3 = MagicMock()
        mock_web3.eth.chain_id = 8453
        mock_web3.to_checksum_address = lambda x: x

        from aegis.adapters import ProtocolType, get_adapter, reset_registry

        reset_registry()

        # use unknown address but force aave type
        unknown_addr = "0x9999999999999999999999999999999999999999"
        adapter = get_adapter(mock_web3, unknown_addr, force_type=ProtocolType.AAVE_V3)
        assert adapter.protocol_type == "aave_v3"




class TestCrewIntegration:
    def test_detection_cycle_with_adapter(self):
        from unittest.mock import MagicMock

        from aegis.coordinator.crew import run_detection_cycle

        mock_adapter = MagicMock()
        mock_adapter.protocol_type = "aave_v3"
        mock_adapter.get_tvl_sync.return_value = 1_000_000 * 10**18

        # need to mock chainlink price feed
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
            assert len(result.assessments) == 3

    def test_detection_cycle_simulation_takes_precedence(self):
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

            # simulate a critical tvl drop
            result = run_detection_cycle(
                protocol_address="0x1234567890123456789012345678901234567890",
                adapter=mock_adapter,
                simulate_tvl_drop_percent=25.0,  # this should take precedence
            )

            # adapter should NOT have been called since simulating
            mock_adapter.get_tvl_sync.assert_not_called()

            # should detect a critical threat
            liquidity_assessment = next(
                a for a in result.assessments if a.sentinel_type.value == "LIQUIDITY"
            )
            assert liquidity_assessment.threat_level.value == "CRITICAL"
