"""Protocol adapters."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aegis.adapters.aave_v3 import (
    AAVE_V3_ADDRESSES,
    AaveV3Adapter,
    get_aave_v3_adapter,
)
from aegis.adapters.base import (
    BaseProtocolAdapter,
    ProtocolEvent,
    ProtocolMetricsSnapshot,
    TokenBalance,
    TTLCache,
)
from aegis.adapters.compound_v3 import (
    COMPOUND_V3_ADDRESSES,
    CompoundV3Adapter,
    get_compound_v3_adapter,
)
from aegis.adapters.curve import (
    CURVE_ADDRESSES,
    CurveAdapter,
    get_curve_adapter,
    get_known_curve_pools,
)
from aegis.adapters.history import (
    AnomalyThresholds,
    AnomalyType,
    HistoricalStats,
    HistoricalTVLTracker,
    RollingAverage,
    SQLiteTVLStore,
    TVLAnomaly,
    TVLHistoryStore,
    TVLSnapshot,
    get_tvl_tracker,
    reset_tvl_tracker,
)
from aegis.adapters.uniswap_v3 import (
    UNISWAP_V3_ADDRESSES,
    UniswapV3Adapter,
    get_uniswap_v3_adapter,
)

if TYPE_CHECKING:
    from web3 import Web3

logger = logging.getLogger(__name__)

class ProtocolType:
    AAVE_V3 = "aave_v3"
    UNISWAP_V3 = "uniswap_v3"
    COMPOUND_V3 = "compound_v3"
    CURVE = "curve"
    UNKNOWN = "unknown"


KNOWN_PROTOCOLS: dict[int, dict[str, str]] = {
    # Base Mainnet (8453)
    8453: {
        # Aave V3
        "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5": ProtocolType.AAVE_V3,  # Pool
        "0x2d8A3C5677189723C4cB8873CfC9C8976FDF38Ac": ProtocolType.AAVE_V3,  # DataProvider
        # Uniswap V3
        "0x33128a8fC17869897dcE68Ed026d694621f6FDfD": ProtocolType.UNISWAP_V3,  # Factory
        "0x03a520b32C04BF3bEEf7BEb72E919cf822ED34f1": ProtocolType.UNISWAP_V3,  # NFTManager
        # Compound V3
        "0x46e6b214b524310239732D51387075E0e70970bf": ProtocolType.COMPOUND_V3,  # USDC Comet
        "0x784efeB622244d2348d4F2522f8860B96fbEcE89": ProtocolType.COMPOUND_V3,  # WETH Comet
        # Curve
        "0xf6C5F01C7F3148891ad0e19DF78743D31E390D1f": ProtocolType.CURVE,  # 4pool
        "0x6e53131F68a034873b6bFA15502aF094Ef0c5854": ProtocolType.CURVE,  # tricrypto
    },
    # Base Sepolia (84532)
    84532: {
        "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5": ProtocolType.AAVE_V3,
        "0x2d8A3C5677189723C4cB8873CfC9C8976FDF38Ac": ProtocolType.AAVE_V3,
        "0x33128a8fC17869897dcE68Ed026d694621f6FDfD": ProtocolType.UNISWAP_V3,
        "0x46e6b214b524310239732D51387075E0e70970bf": ProtocolType.COMPOUND_V3,  # USDC Comet
    },
    # Ethereum Mainnet (1)
    1: {
        "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2": ProtocolType.AAVE_V3,  # Pool
        "0x7B4EB56E7CD4b454BA8ff71E4518426369a138a3": ProtocolType.AAVE_V3,  # DataProvider
        "0x1F98431c8aD98523631AE4a59f267346ea31F984": ProtocolType.UNISWAP_V3,  # Factory
        "0xc3d688B66703497DAA19211EEdff47f25384cdc3": ProtocolType.COMPOUND_V3,  # USDC Comet
        "0xA17581A9E3356d9A858b789D68B4d866e593aE94": ProtocolType.COMPOUND_V3,  # WETH Comet
        # Curve
        "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7": ProtocolType.CURVE,  # 3pool
        "0xDC24316b9AE028F1497c275EB9192a3Ea0f67022": ProtocolType.CURVE,  # stETH
        "0xDcEF968d416a41Cdac0ED8702fAC8128A64241A2": ProtocolType.CURVE,  # FRAX/USDC
        "0xD51a44d3FaE010294C616388b506AcdA1bfAAE46": ProtocolType.CURVE,  # tricrypto2
        "0x4DEcE678ceceb27446b35C672dC7d61F30bAD69E": ProtocolType.CURVE,  # crvUSD/USDC
        "0x390f3595bCa2Df7d23783dFd126427CCeb997BF4": ProtocolType.CURVE,  # crvUSD/USDT
    },
    # Arbitrum Mainnet (42161)
    42161: {
        "0x9c4ec768c28520B50860ea7a15bd7213a9fF58bf": ProtocolType.COMPOUND_V3,  # USDC Comet
        "0xA5EDBDD9646f8dFF606d7448e414884C7d905dCA": ProtocolType.COMPOUND_V3,  # USDC.e Comet
        # Curve
        "0x7f90122BF0700F9E7e1F688fe926940E8839F353": ProtocolType.CURVE,  # 2pool
        "0x960ea3e3C7FB317332d990873d354E18d7645590": ProtocolType.CURVE,  # tricrypto
    },
    # Polygon Mainnet (137)
    137: {
        "0xF25212E676D1F7F89Cd72fFEe66158f541246445": ProtocolType.COMPOUND_V3,  # USDC Comet
        # Curve
        "0x445FE580eF8d70FF569aB36e80c647af338db351": ProtocolType.CURVE,  # aave
        "0x92215849c439E1f8612b6646060B4E3E5ef822cC": ProtocolType.CURVE,  # atricrypto3
    },
    # Optimism Mainnet (10)
    10: {
        # Curve
        "0x1337BedC9D22ecbe766dF105c9623922A27963EC": ProtocolType.CURVE,  # 3pool
    },
}


def detect_protocol_type(web3: "Web3", address: str) -> str:
    address = web3.to_checksum_address(address)
    chain_id = web3.eth.chain_id

    chain_protocols = KNOWN_PROTOCOLS.get(chain_id, {})
    if address in chain_protocols:
        return chain_protocols[address]

    try:
        # Aave V3 Pool
        from aegis.adapters.aave_v3 import AAVE_POOL_ABI

        contract = web3.eth.contract(address=address, abi=AAVE_POOL_ABI)
        contract.functions.getReservesList().call()
        logger.info("Detected Aave V3 Pool at %s", address)
        return ProtocolType.AAVE_V3
    except Exception:
        pass

    try:
        # Uniswap V3 Factory
        from aegis.adapters.uniswap_v3 import FACTORY_ABI

        contract = web3.eth.contract(address=address, abi=FACTORY_ABI)
        contract.functions.getPool(
            "0x0000000000000000000000000000000000000001",
            "0x0000000000000000000000000000000000000002",
            3000,
        ).call()
        logger.info("Detected Uniswap V3 Factory at %s", address)
        return ProtocolType.UNISWAP_V3
    except Exception:
        pass

    try:
        # Uniswap V3 Pool
        from aegis.adapters.uniswap_v3 import POOL_ABI

        contract = web3.eth.contract(address=address, abi=POOL_ABI)
        contract.functions.token0().call()
        contract.functions.token1().call()
        contract.functions.fee().call()
        logger.info("Detected Uniswap V3 Pool at %s", address)
        return ProtocolType.UNISWAP_V3
    except Exception:
        pass

    try:
        # Compound V3 Comet
        from aegis.adapters.compound_v3 import COMET_ABI

        contract = web3.eth.contract(address=address, abi=COMET_ABI)
        contract.functions.baseToken().call()
        contract.functions.totalSupply().call()
        contract.functions.totalBorrow().call()
        logger.info("Detected Compound V3 Comet at %s", address)
        return ProtocolType.COMPOUND_V3
    except Exception:
        pass

    try:
        # Curve Pool
        from aegis.adapters.curve import CURVE_POOL_ABI

        contract = web3.eth.contract(address=address, abi=CURVE_POOL_ABI)
        contract.functions.coins(0).call()
        contract.functions.balances(0).call()
        contract.functions.get_virtual_price().call()
        logger.info("Detected Curve Pool at %s", address)
        return ProtocolType.CURVE
    except Exception:
        pass

    logger.warning("Could not detect protocol type for %s", address)
    return ProtocolType.UNKNOWN




class AdapterRegistry:
    def __init__(self, web3: "Web3"):
        self._web3 = web3
        self._adapters: dict[str, BaseProtocolAdapter] = {}
        self._custom_mappings: dict[str, str] = {}

    @property
    def web3(self) -> "Web3":
        return self._web3

    @property
    def chain_id(self) -> int:
        return self._web3.eth.chain_id

    def register_custom(self, address: str, protocol_type: str) -> None:
        address = self._web3.to_checksum_address(address)
        self._custom_mappings[address] = protocol_type
        logger.info("Registered custom mapping: %s -> %s", address, protocol_type)

    def get_protocol_type(self, address: str) -> str:
        address = self._web3.to_checksum_address(address)

        if address in self._custom_mappings:
            return self._custom_mappings[address]

        return detect_protocol_type(self._web3, address)

    def get_adapter(
        self,
        address: str,
        force_type: str | None = None,
        cache_ttl: int | None = None,
    ) -> BaseProtocolAdapter:
        address = self._web3.to_checksum_address(address)

        cache_key = f"{address}:{force_type or 'auto'}"
        if cache_key in self._adapters:
            return self._adapters[cache_key]

        protocol_type = force_type or self.get_protocol_type(address)

        adapter: BaseProtocolAdapter

        if protocol_type == ProtocolType.AAVE_V3:
            adapter = AaveV3Adapter(
                self._web3,
                protocol_address=address,
                cache_ttl=cache_ttl,
            )
        elif protocol_type == ProtocolType.UNISWAP_V3:
            adapter = UniswapV3Adapter(
                self._web3,
                protocol_address=address,
                cache_ttl=cache_ttl,
            )
        elif protocol_type == ProtocolType.COMPOUND_V3:
            adapter = CompoundV3Adapter(
                self._web3,
                protocol_address=address,
                cache_ttl=cache_ttl,
            )
        elif protocol_type == ProtocolType.CURVE:
            adapter = CurveAdapter(
                self._web3,
                pool_address=address,
                cache_ttl=cache_ttl,
            )
        else:
            raise ValueError(
                f"Unknown protocol type '{protocol_type}' for address {address}. "
                f"Use force_type to specify the adapter type."
            )

        self._adapters[cache_key] = adapter
        logger.info(
            "Created %s adapter for %s",
            adapter.protocol_type,
            address[:10] + "...",
        )
        return adapter

    def get_all_adapters(self) -> list[BaseProtocolAdapter]:
        return list(self._adapters.values())

    def clear(self) -> None:
        self._adapters.clear()




_default_registry: AdapterRegistry | None = None


def get_registry(web3: "Web3 | None" = None) -> AdapterRegistry:
    global _default_registry

    if _default_registry is None:
        if web3 is None:
            from aegis.blockchain.web3_client import get_web3

            web3 = get_web3()
        _default_registry = AdapterRegistry(web3)

    return _default_registry


def get_adapter(
    web3: "Web3",
    address: str,
    force_type: str | None = None,
    cache_ttl: int | None = None,
) -> BaseProtocolAdapter:
    registry = get_registry(web3)
    return registry.get_adapter(address, force_type=force_type, cache_ttl=cache_ttl)


def reset_registry() -> None:
    global _default_registry
    _default_registry = None



__all__ = [
    # Base classes
    "BaseProtocolAdapter",
    "ProtocolEvent",
    "ProtocolMetricsSnapshot",
    "TokenBalance",
    "TTLCache",
    # Adapters
    "AaveV3Adapter",
    "UniswapV3Adapter",
    "CompoundV3Adapter",
    "CurveAdapter",
    # Factory functions
    "get_aave_v3_adapter",
    "get_uniswap_v3_adapter",
    "get_compound_v3_adapter",
    "get_curve_adapter",
    "get_known_curve_pools",
    "get_adapter",
    # Registry
    "AdapterRegistry",
    "get_registry",
    "reset_registry",
    # Detection
    "ProtocolType",
    "detect_protocol_type",
    # Constants
    "AAVE_V3_ADDRESSES",
    "UNISWAP_V3_ADDRESSES",
    "COMPOUND_V3_ADDRESSES",
    "CURVE_ADDRESSES",
    "KNOWN_PROTOCOLS",
    # History tracking
    "AnomalyThresholds",
    "AnomalyType",
    "HistoricalStats",
    "HistoricalTVLTracker",
    "RollingAverage",
    "SQLiteTVLStore",
    "TVLAnomaly",
    "TVLHistoryStore",
    "TVLSnapshot",
    "get_tvl_tracker",
    "reset_tvl_tracker",
]
