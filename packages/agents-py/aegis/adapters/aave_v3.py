"""Aave V3 adapter."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from web3 import Web3

from aegis.adapters.base import (
    BaseProtocolAdapter,
    ProtocolEvent,
    TokenBalance,
)

if TYPE_CHECKING:
    from web3.contract import Contract

logger = logging.getLogger(__name__)


AAVE_V3_ADDRESSES = {
    # Base Mainnet
    8453: {
        "pool": "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
        "pool_data_provider": "0x2d8A3C5677189723C4cB8873CfC9C8976FDF38Ac",
    },
    # Base Sepolia (testnet)
    84532: {
        "pool": "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
        "pool_data_provider": "0x2d8A3C5677189723C4cB8873CfC9C8976FDF38Ac",
    },
    # Ethereum Mainnet
    1: {
        "pool": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        "pool_data_provider": "0x7B4EB56E7CD4b454BA8ff71E4518426369a138a3",
    },
}


AAVE_POOL_ABI = [
    {
        "inputs": [],
        "name": "getReservesList",
        "outputs": [{"internalType": "address[]", "name": "", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
        "name": "getReserveData",
        "outputs": [
            {
                "components": [
                    {
                        "components": [{"internalType": "uint256", "name": "data", "type": "uint256"}],
                        "internalType": "struct DataTypes.ReserveConfigurationMap",
                        "name": "configuration",
                        "type": "tuple",
                    },
                    {"internalType": "uint128", "name": "liquidityIndex", "type": "uint128"},
                    {"internalType": "uint128", "name": "currentLiquidityRate", "type": "uint128"},
                    {"internalType": "uint128", "name": "variableBorrowIndex", "type": "uint128"},
                    {"internalType": "uint128", "name": "currentVariableBorrowRate", "type": "uint128"},
                    {"internalType": "uint128", "name": "currentStableBorrowRate", "type": "uint128"},
                    {"internalType": "uint40", "name": "lastUpdateTimestamp", "type": "uint40"},
                    {"internalType": "uint16", "name": "id", "type": "uint16"},
                    {"internalType": "address", "name": "aTokenAddress", "type": "address"},
                    {"internalType": "address", "name": "stableDebtTokenAddress", "type": "address"},
                    {"internalType": "address", "name": "variableDebtTokenAddress", "type": "address"},
                    {"internalType": "address", "name": "interestRateStrategyAddress", "type": "address"},
                    {"internalType": "uint128", "name": "accruedToTreasury", "type": "uint128"},
                    {"internalType": "uint128", "name": "unbacked", "type": "uint128"},
                    {"internalType": "uint128", "name": "isolationModeTotalDebt", "type": "uint128"},
                ],
                "internalType": "struct DataTypes.ReserveData",
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
]

AAVE_DATA_PROVIDER_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
        "name": "getReserveTokensAddresses",
        "outputs": [
            {"internalType": "address", "name": "aTokenAddress", "type": "address"},
            {"internalType": "address", "name": "stableDebtTokenAddress", "type": "address"},
            {"internalType": "address", "name": "variableDebtTokenAddress", "type": "address"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
        "name": "getTotalDebt",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
        "name": "getATokenTotalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

ERC20_ABI = [
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

ATOKEN_EVENTS_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "reserve", "type": "address"},
            {"indexed": False, "name": "user", "type": "address"},
            {"indexed": True, "name": "onBehalfOf", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"},
            {"indexed": True, "name": "referralCode", "type": "uint16"},
        ],
        "name": "Supply",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "reserve", "type": "address"},
            {"indexed": True, "name": "user", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"},
        ],
        "name": "Withdraw",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "reserve", "type": "address"},
            {"indexed": False, "name": "user", "type": "address"},
            {"indexed": True, "name": "onBehalfOf", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"},
            {"indexed": False, "name": "interestRateMode", "type": "uint8"},
            {"indexed": False, "name": "borrowRate", "type": "uint256"},
            {"indexed": True, "name": "referralCode", "type": "uint16"},
        ],
        "name": "Borrow",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "reserve", "type": "address"},
            {"indexed": True, "name": "user", "type": "address"},
            {"indexed": True, "name": "repayer", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"},
            {"indexed": False, "name": "useATokens", "type": "bool"},
        ],
        "name": "Repay",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "reserve", "type": "address"},
            {"indexed": False, "name": "liquidityRate", "type": "uint256"},
            {"indexed": False, "name": "stableBorrowRate", "type": "uint256"},
            {"indexed": False, "name": "variableBorrowRate", "type": "uint256"},
            {"indexed": False, "name": "liquidityIndex", "type": "uint256"},
            {"indexed": False, "name": "variableBorrowIndex", "type": "uint256"},
        ],
        "name": "ReserveDataUpdated",
        "type": "event",
    },
]


class AaveV3Adapter(BaseProtocolAdapter):

    PROTOCOL_TYPE = "aave_v3"

    def __init__(
        self,
        web3: Web3,
        protocol_address: str | None = None,
        cache_ttl: int | None = None,
    ):
        chain_id = web3.eth.chain_id
        addresses = AAVE_V3_ADDRESSES.get(chain_id, AAVE_V3_ADDRESSES[84532])

        pool_address = protocol_address or addresses["pool"]
        super().__init__(web3, pool_address, cache_ttl)

        self._data_provider_address = addresses["pool_data_provider"]
        self._pool_contract: Contract | None = None
        self._data_provider_contract: Contract | None = None
        self._reserves: list[str] = []

    @property
    def pool_contract(self) -> Contract:
        if self._pool_contract is None:
            self._pool_contract = self._web3.eth.contract(
                address=self._protocol_address,
                abi=AAVE_POOL_ABI + ATOKEN_EVENTS_ABI,
            )
        return self._pool_contract

    @property
    def data_provider(self) -> Contract:
        if self._data_provider_contract is None:
            self._data_provider_contract = self._web3.eth.contract(
                address=self._web3.to_checksum_address(self._data_provider_address),
                abi=AAVE_DATA_PROVIDER_ABI,
            )
        return self._data_provider_contract

    async def _get_reserves_list(self) -> list[str]:
        cache_key = f"reserves:{self._protocol_address}"

        async def fetch():
            loop = asyncio.get_event_loop()
            reserves = await loop.run_in_executor(
                None, self.pool_contract.functions.getReservesList().call
            )
            return [self._web3.to_checksum_address(r) for r in reserves]

        return await self._cache.get_or_fetch(cache_key, fetch)

    async def _get_token_info(self, token_address: str) -> dict[str, Any]:
        cache_key = f"token_info:{token_address}"

        async def fetch():
            loop = asyncio.get_event_loop()
            token = self._web3.eth.contract(
                address=self._web3.to_checksum_address(token_address),
                abi=ERC20_ABI,
            )
            try:
                symbol = await loop.run_in_executor(
                    None, token.functions.symbol().call
                )
                decimals = await loop.run_in_executor(
                    None, token.functions.decimals().call
                )
            except Exception:
                symbol = "UNKNOWN"
                decimals = 18

            return {"symbol": symbol, "decimals": decimals}

        return await self._cache.get_or_fetch(cache_key, fetch)

    async def _fetch_tvl(self) -> int:
        reserves = await self._get_reserves_list()
        loop = asyncio.get_event_loop()

        total_tvl = 0
        for reserve in reserves:
            try:
                supply = await loop.run_in_executor(
                    None,
                    self.data_provider.functions.getATokenTotalSupply(reserve).call,
                )
                total_tvl += supply
                logger.debug("Reserve %s supply: %d", reserve, supply)
            except Exception as e:
                logger.warning("Failed to get supply for reserve %s: %s", reserve, e)

        logger.info("Aave V3 Total TVL: %d wei", total_tvl)
        return total_tvl

    async def get_total_borrows(self) -> int:
        reserves = await self._get_reserves_list()
        loop = asyncio.get_event_loop()

        total_debt = 0
        for reserve in reserves:
            try:
                debt = await loop.run_in_executor(
                    None,
                    self.data_provider.functions.getTotalDebt(reserve).call,
                )
                total_debt += debt
            except Exception as e:
                logger.warning("Failed to get debt for reserve %s: %s", reserve, e)

        return total_debt

    async def get_utilization_rate(self) -> float:
        tvl, borrows = await asyncio.gather(
            self.get_tvl(),
            self.get_total_borrows(),
        )

        if tvl == 0:
            return 0.0

        return borrows / tvl

    async def _fetch_token_balances(self) -> list[TokenBalance]:
        reserves = await self._get_reserves_list()
        balances: list[TokenBalance] = []

        for reserve in reserves:
            try:
                token_info = await self._get_token_info(reserve)
                loop = asyncio.get_event_loop()

                supply = await loop.run_in_executor(
                    None,
                    self.data_provider.functions.getATokenTotalSupply(reserve).call,
                )

                decimals = token_info["decimals"]
                balances.append(
                    TokenBalance(
                        token_address=reserve,
                        symbol=token_info["symbol"],
                        decimals=decimals,
                        balance_raw=supply,
                        balance_formatted=supply / (10**decimals),
                    )
                )
            except Exception as e:
                logger.warning("Failed to get balance for %s: %s", reserve, e)

        return balances

    async def _fetch_events(
        self,
        event_name: str | None = None,
        from_block: int | None = None,
        limit: int = 100,
    ) -> list[ProtocolEvent]:
        loop = asyncio.get_event_loop()

        current_block = await loop.run_in_executor(
            None, lambda: self._web3.eth.block_number
        )

        if from_block is None:
            from_block = max(0, current_block - 1000)

        events: list[ProtocolEvent] = []
        event_names = (
            [event_name]
            if event_name
            else ["Supply", "Withdraw", "Borrow", "Repay", "ReserveDataUpdated"]
        )

        for name in event_names:
            try:
                event_filter = getattr(self.pool_contract.events, name)
                raw_events = await loop.run_in_executor(
                    None,
                    lambda ef=event_filter: ef.create_filter(
                        fromBlock=from_block,
                        toBlock=current_block,
                    ).get_all_entries(),
                )

                for e in raw_events[:limit]:
                    events.append(
                        ProtocolEvent(
                            event_name=name,
                            block_number=e["blockNumber"],
                            transaction_hash=e["transactionHash"].hex(),
                            log_index=e["logIndex"],
                            args=dict(e["args"]),
                        )
                    )

            except Exception as ex:
                logger.warning("Failed to fetch %s events: %s", name, ex)

        events.sort(key=lambda x: x.block_number, reverse=True)
        return events[:limit]

    async def get_large_withdrawals(
        self,
        threshold_usd: float = 100_000,
        from_block: int | None = None,
    ) -> list[ProtocolEvent]:
        events = await self._fetch_events(
            event_name="Withdraw",
            from_block=from_block,
            limit=500,
        )

        # rough estimate assuming ~$2000/ETH, needs chainlink feeds for accuracy
        threshold_raw = int(threshold_usd * 10**18 / 2000)

        return [e for e in events if e.args.get("amount", 0) > threshold_raw]


def get_aave_v3_adapter(
    web3: Web3,
    pool_address: str | None = None,
) -> AaveV3Adapter:
    return AaveV3Adapter(web3, pool_address)
