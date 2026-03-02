"""Uniswap V3 adapter."""

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


UNISWAP_V3_ADDRESSES = {
    # Base Mainnet
    8453: {
        "factory": "0x33128a8fC17869897dcE68Ed026d694621f6FDfD",
        "quoter_v2": "0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a",
        "nft_position_manager": "0x03a520b32C04BF3bEEf7BEb72E919cf822ED34f1",
    },
    # Base Sepolia (testnet)
    84532: {
        "factory": "0x33128a8fC17869897dcE68Ed026d694621f6FDfD",
        "quoter_v2": "0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a",
        "nft_position_manager": "0x03a520b32C04BF3bEEf7BEb72E919cf822ED34f1",
    },
    # Ethereum Mainnet
    1: {
        "factory": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
        "quoter_v2": "0x61fFE014bA17989E743c5F6cB21bF9697530B21e",
        "nft_position_manager": "0xC36442b4a4522E871399CD717aBDD847Ab11FE88",
    },
    # Arbitrum
    42161: {
        "factory": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
        "quoter_v2": "0x61fFE014bA17989E743c5F6cB21bF9697530B21e",
        "nft_position_manager": "0xC36442b4a4522E871399CD717aBDD847Ab11FE88",
    },
}

FEE_TIERS = [100, 500, 3000, 10000]  # 0.01%, 0.05%, 0.3%, 1%

BASE_POPULAR_PAIRS = [
    ("0x4200000000000000000000000000000000000006", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"),
    # bridged USDC
    ("0x4200000000000000000000000000000000000006", "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA"),
]


FACTORY_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenA", "type": "address"},
            {"internalType": "address", "name": "tokenB", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
        ],
        "name": "getPool",
        "outputs": [{"internalType": "address", "name": "pool", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

POOL_ABI = [
    {
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "fee",
        "outputs": [{"internalType": "uint24", "name": "", "type": "uint24"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "liquidity",
        "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"internalType": "int24", "name": "tick", "type": "int24"},
            {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
            {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
            {"internalType": "bool", "name": "unlocked", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]

POOL_EVENTS_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "sender", "type": "address"},
            {"indexed": True, "name": "recipient", "type": "address"},
            {"indexed": False, "name": "amount0", "type": "int256"},
            {"indexed": False, "name": "amount1", "type": "int256"},
            {"indexed": False, "name": "sqrtPriceX96", "type": "uint160"},
            {"indexed": False, "name": "liquidity", "type": "uint128"},
            {"indexed": False, "name": "tick", "type": "int24"},
        ],
        "name": "Swap",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "name": "sender", "type": "address"},
            {"indexed": True, "name": "owner", "type": "address"},
            {"indexed": True, "name": "tickLower", "type": "int24"},
            {"indexed": True, "name": "tickUpper", "type": "int24"},
            {"indexed": False, "name": "amount", "type": "uint128"},
            {"indexed": False, "name": "amount0", "type": "uint256"},
            {"indexed": False, "name": "amount1", "type": "uint256"},
        ],
        "name": "Mint",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "owner", "type": "address"},
            {"indexed": True, "name": "tickLower", "type": "int24"},
            {"indexed": True, "name": "tickUpper", "type": "int24"},
            {"indexed": False, "name": "amount", "type": "uint128"},
            {"indexed": False, "name": "amount0", "type": "uint256"},
            {"indexed": False, "name": "amount1", "type": "uint256"},
        ],
        "name": "Burn",
        "type": "event",
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
]


class UniswapV3Adapter(BaseProtocolAdapter):

    PROTOCOL_TYPE = "uniswap_v3"

    def __init__(
        self,
        web3: Web3,
        protocol_address: str | None = None,
        pool_address: str | None = None,
        tracked_pools: list[str] | None = None,
        cache_ttl: int | None = None,
    ):
        chain_id = web3.eth.chain_id
        addresses = UNISWAP_V3_ADDRESSES.get(chain_id, UNISWAP_V3_ADDRESSES[8453])

        if pool_address:
            main_address = pool_address
            self._is_pool_mode = True
        else:
            main_address = protocol_address or addresses["factory"]
            self._is_pool_mode = False

        super().__init__(web3, main_address, cache_ttl)

        self._factory_address = addresses["factory"]
        self._tracked_pools = tracked_pools or []
        self._factory_contract: Contract | None = None
        self._pool_contracts: dict[str, Contract] = {}

    @property
    def factory_contract(self) -> Contract:
        if self._factory_contract is None:
            self._factory_contract = self._web3.eth.contract(
                address=self._web3.to_checksum_address(self._factory_address),
                abi=FACTORY_ABI,
            )
        return self._factory_contract

    def _get_pool_contract(self, pool_address: str) -> Contract:
        if pool_address not in self._pool_contracts:
            self._pool_contracts[pool_address] = self._web3.eth.contract(
                address=self._web3.to_checksum_address(pool_address),
                abi=POOL_ABI + POOL_EVENTS_ABI,
            )
        return self._pool_contracts[pool_address]

    async def get_pool_address(
        self,
        token_a: str,
        token_b: str,
        fee: int = 3000,
    ) -> str | None:
        loop = asyncio.get_event_loop()

        try:
            pool_address = await loop.run_in_executor(
                None,
                self.factory_contract.functions.getPool(
                    self._web3.to_checksum_address(token_a),
                    self._web3.to_checksum_address(token_b),
                    fee,
                ).call,
            )

            if pool_address == "0x0000000000000000000000000000000000000000":
                return None

            return self._web3.to_checksum_address(pool_address)
        except Exception as e:
            logger.warning("Failed to get pool for %s/%s: %s", token_a, token_b, e)
            return None

    async def discover_pools(self) -> list[str]:
        if self._tracked_pools:
            return self._tracked_pools

        discovered: list[str] = []

        # Check popular pairs across all fee tiers
        for token_a, token_b in BASE_POPULAR_PAIRS:
            for fee in FEE_TIERS:
                pool = await self.get_pool_address(token_a, token_b, fee)
                if pool:
                    discovered.append(pool)
                    logger.debug("Discovered pool: %s (fee=%d)", pool, fee)

        self._tracked_pools = discovered
        return discovered

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

    async def _get_pool_tvl(self, pool_address: str) -> int:
        # sums raw token balances, not usd-converted
        loop = asyncio.get_event_loop()
        pool = self._get_pool_contract(pool_address)

        try:
            token0_addr = await loop.run_in_executor(
                None, pool.functions.token0().call
            )
            token1_addr = await loop.run_in_executor(
                None, pool.functions.token1().call
            )

            token0 = self._web3.eth.contract(
                address=token0_addr, abi=ERC20_ABI
            )
            token1 = self._web3.eth.contract(
                address=token1_addr, abi=ERC20_ABI
            )

            balance0, balance1 = await asyncio.gather(
                loop.run_in_executor(
                    None, token0.functions.balanceOf(pool_address).call
                ),
                loop.run_in_executor(
                    None, token1.functions.balanceOf(pool_address).call
                ),
            )

            return balance0 + balance1

        except Exception as e:
            logger.warning("Failed to get TVL for pool %s: %s", pool_address, e)
            return 0

    async def _fetch_tvl(self) -> int:
        if self._is_pool_mode:
            return await self._get_pool_tvl(self._protocol_address)

        pools = await self.discover_pools()

        if not pools:
            logger.warning("No pools to track for TVL")
            return 0

        tvls = await asyncio.gather(
            *[self._get_pool_tvl(pool) for pool in pools]
        )

        total_tvl = sum(tvls)
        logger.info("Uniswap V3 Total TVL across %d pools: %d", len(pools), total_tvl)
        return total_tvl

    async def get_pool_info(self, pool_address: str) -> dict[str, Any]:
        loop = asyncio.get_event_loop()
        pool = self._get_pool_contract(pool_address)

        try:
            token0 = await loop.run_in_executor(None, pool.functions.token0().call)
            token1 = await loop.run_in_executor(None, pool.functions.token1().call)
            fee = await loop.run_in_executor(None, pool.functions.fee().call)
            liquidity = await loop.run_in_executor(None, pool.functions.liquidity().call)
            slot0 = await loop.run_in_executor(None, pool.functions.slot0().call)

            token0_info = await self._get_token_info(token0)
            token1_info = await self._get_token_info(token1)

            return {
                "address": pool_address,
                "token0": {
                    "address": token0,
                    "symbol": token0_info["symbol"],
                    "decimals": token0_info["decimals"],
                },
                "token1": {
                    "address": token1,
                    "symbol": token1_info["symbol"],
                    "decimals": token1_info["decimals"],
                },
                "fee": fee,
                "fee_percent": fee / 10000,
                "liquidity": liquidity,
                "sqrt_price_x96": slot0[0],
                "tick": slot0[1],
            }
        except Exception as e:
            logger.error("Failed to get pool info for %s: %s", pool_address, e)
            return {}

    async def _fetch_token_balances(self) -> list[TokenBalance]:
        if self._is_pool_mode:
            pools = [self._protocol_address]
        else:
            pools = await self.discover_pools()

        balances: dict[str, TokenBalance] = {}
        loop = asyncio.get_event_loop()

        for pool_addr in pools:
            pool = self._get_pool_contract(pool_addr)

            try:
                token0_addr = await loop.run_in_executor(
                    None, pool.functions.token0().call
                )
                token1_addr = await loop.run_in_executor(
                    None, pool.functions.token1().call
                )

                for token_addr in [token0_addr, token1_addr]:
                    token = self._web3.eth.contract(address=token_addr, abi=ERC20_ABI)
                    token_info = await self._get_token_info(token_addr)

                    balance = await loop.run_in_executor(
                        None, token.functions.balanceOf(pool_addr).call
                    )

                    if token_addr in balances:
                        balances[token_addr].balance_raw += balance
                        balances[token_addr].balance_formatted = (
                            balances[token_addr].balance_raw
                            / (10 ** balances[token_addr].decimals)
                        )
                    else:
                        balances[token_addr] = TokenBalance(
                            token_address=token_addr,
                            symbol=token_info["symbol"],
                            decimals=token_info["decimals"],
                            balance_raw=balance,
                            balance_formatted=balance / (10 ** token_info["decimals"]),
                        )

            except Exception as e:
                logger.warning("Failed to get balances for pool %s: %s", pool_addr, e)

        return list(balances.values())

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

        if self._is_pool_mode:
            pools = [self._protocol_address]
        else:
            pools = await self.discover_pools()

        events: list[ProtocolEvent] = []
        event_names = [event_name] if event_name else ["Swap", "Mint", "Burn"]

        for pool_addr in pools:
            pool = self._get_pool_contract(pool_addr)

            for name in event_names:
                try:
                    event_filter = getattr(pool.events, name)
                    raw_events = await loop.run_in_executor(
                        None,
                        lambda ef=event_filter: ef.create_filter(
                            fromBlock=from_block,
                            toBlock=current_block,
                        ).get_all_entries(),
                    )

                    for e in raw_events:
                        events.append(
                            ProtocolEvent(
                                event_name=name,
                                block_number=e["blockNumber"],
                                transaction_hash=e["transactionHash"].hex(),
                                log_index=e["logIndex"],
                                args={**dict(e["args"]), "pool": pool_addr},
                            )
                        )

                except Exception as ex:
                    logger.debug("Failed to fetch %s events from %s: %s", name, pool_addr, ex)

        events.sort(key=lambda x: x.block_number, reverse=True)
        return events[:limit]

    async def get_large_swaps(
        self,
        threshold_usd: float = 100_000,
        from_block: int | None = None,
    ) -> list[ProtocolEvent]:
        # simplified, would need real price data in production
        events = await self._fetch_events(
            event_name="Swap",
            from_block=from_block,
            limit=500,
        )

        threshold_raw = int(threshold_usd * 10**18 / 2000)

        large_swaps = []
        for e in events:
            amount0 = abs(e.args.get("amount0", 0))
            amount1 = abs(e.args.get("amount1", 0))
            if amount0 > threshold_raw or amount1 > threshold_raw:
                large_swaps.append(e)

        return large_swaps


def get_uniswap_v3_adapter(
    web3: Web3,
    pool_address: str | None = None,
    factory_address: str | None = None,
) -> UniswapV3Adapter:
    return UniswapV3Adapter(
        web3,
        protocol_address=factory_address,
        pool_address=pool_address,
    )
