"""Curve Finance Protocol Adapter.

Reads TVL, token balances, and events from Curve pools.
Supports StableSwap and CryptoSwap pools on various EVM chains.
"""

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

# ============ Curve Contract Addresses ============

CURVE_ADDRESSES = {
    # Ethereum Mainnet
    1: {
        "address_provider": "0x0000000022D53366457F9d5E68Ec105046FC4383",
        "registry": "0x90E00ACe148ca3b23Ac1bC8C240C2a7Dd9c2d7f5",
        "factory": "0xB9fC157394Af804a3578134A6585C0dc9cc990d4",
        # Popular pools
        "pools": {
            "3pool": "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7",  # DAI/USDC/USDT
            "steth": "0xDC24316b9AE028F1497c275EB9192a3Ea0f67022",  # ETH/stETH
            "fraxusdc": "0xDcEF968d416a41Cdac0ED8702fAC8128A64241A2",  # FRAX/USDC
            "tricrypto2": "0xD51a44d3FaE010294C616388b506AcdA1bfAAE46",  # USDT/WBTC/WETH
            "crvusd_usdc": "0x4DEcE678ceceb27446b35C672dC7d61F30bAD69E",  # crvUSD/USDC
            "crvusd_usdt": "0x390f3595bCa2Df7d23783dFd126427CCeb997BF4",  # crvUSD/USDT
        },
    },
    # Base Mainnet
    8453: {
        "address_provider": "0x0000000022D53366457F9d5E68Ec105046FC4383",
        "factory": "0xd2002373543Ce3527023C75e7518C274A51ce712",
        "pools": {
            "4pool": "0xf6C5F01C7F3148891ad0e19DF78743D31E390D1f",  # USDC/USDbC/axlUSDC/crvUSD
            "tricrypto": "0x6e53131F68a034873b6bFA15502aF094Ef0c5854",  # WETH/cbETH/wstETH
        },
    },
    # Arbitrum
    42161: {
        "address_provider": "0x0000000022D53366457F9d5E68Ec105046FC4383",
        "factory": "0xb17b674D9c5CB2e441F8e196a2f048A81355d031",
        "pools": {
            "2pool": "0x7f90122BF0700F9E7e1F688fe926940E8839F353",  # USDC/USDT
            "tricrypto": "0x960ea3e3C7FB317332d990873d354E18d7645590",  # USDT/WBTC/WETH
        },
    },
    # Optimism
    10: {
        "address_provider": "0x0000000022D53366457F9d5E68Ec105046FC4383",
        "factory": "0x2db0E83599a91b508Ac268a6197b8B14F5e72840",
        "pools": {
            "3pool": "0x1337BedC9D22ecbe766dF105c9623922A27963EC",  # DAI/USDC/USDT
        },
    },
    # Polygon
    137: {
        "address_provider": "0x0000000022D53366457F9d5E68Ec105046FC4383",
        "factory": "0x722272D36ef0Da72FF51c5A65Db7b870E2e8D4ee",
        "pools": {
            "aave": "0x445FE580eF8d70FF569aB36e80c647af338db351",  # aDAI/aUSDC/aUSDT
            "atricrypto3": "0x92215849c439E1f8612b6646060B4E3E5ef822cC",  # aDAI/aUSDC/aUSDT/aWBTC/aWETH
        },
    },
}

# ============ Curve ABIs (Minimal) ============

# StableSwap pool ABI (most common)
CURVE_POOL_ABI = [
    # Read functions
    {
        "name": "get_virtual_price",
        "outputs": [{"type": "uint256", "name": ""}],
        "inputs": [],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "name": "balances",
        "outputs": [{"type": "uint256", "name": ""}],
        "inputs": [{"type": "uint256", "name": "i"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "name": "coins",
        "outputs": [{"type": "address", "name": ""}],
        "inputs": [{"type": "uint256", "name": "i"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "name": "A",
        "outputs": [{"type": "uint256", "name": ""}],
        "inputs": [],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "name": "fee",
        "outputs": [{"type": "uint256", "name": ""}],
        "inputs": [],
        "stateMutability": "view",
        "type": "function",
    },
    # N_COINS getter (not always present)
    {
        "name": "N_COINS",
        "outputs": [{"type": "uint256", "name": ""}],
        "inputs": [],
        "stateMutability": "view",
        "type": "function",
    },
]

# Events ABI
CURVE_EVENTS_ABI = [
    {
        "name": "AddLiquidity",
        "inputs": [
            {"name": "provider", "type": "address", "indexed": True},
            {"name": "token_amounts", "type": "uint256[2]", "indexed": False},
            {"name": "fees", "type": "uint256[2]", "indexed": False},
            {"name": "invariant", "type": "uint256", "indexed": False},
            {"name": "token_supply", "type": "uint256", "indexed": False},
        ],
        "anonymous": False,
        "type": "event",
    },
    {
        "name": "RemoveLiquidity",
        "inputs": [
            {"name": "provider", "type": "address", "indexed": True},
            {"name": "token_amounts", "type": "uint256[2]", "indexed": False},
            {"name": "fees", "type": "uint256[2]", "indexed": False},
            {"name": "token_supply", "type": "uint256", "indexed": False},
        ],
        "anonymous": False,
        "type": "event",
    },
    {
        "name": "RemoveLiquidityOne",
        "inputs": [
            {"name": "provider", "type": "address", "indexed": True},
            {"name": "token_amount", "type": "uint256", "indexed": False},
            {"name": "coin_amount", "type": "uint256", "indexed": False},
        ],
        "anonymous": False,
        "type": "event",
    },
    {
        "name": "RemoveLiquidityImbalance",
        "inputs": [
            {"name": "provider", "type": "address", "indexed": True},
            {"name": "token_amounts", "type": "uint256[2]", "indexed": False},
            {"name": "fees", "type": "uint256[2]", "indexed": False},
            {"name": "invariant", "type": "uint256", "indexed": False},
            {"name": "token_supply", "type": "uint256", "indexed": False},
        ],
        "anonymous": False,
        "type": "event",
    },
    {
        "name": "TokenExchange",
        "inputs": [
            {"name": "buyer", "type": "address", "indexed": True},
            {"name": "sold_id", "type": "int128", "indexed": False},
            {"name": "tokens_sold", "type": "uint256", "indexed": False},
            {"name": "bought_id", "type": "int128", "indexed": False},
            {"name": "tokens_bought", "type": "uint256", "indexed": False},
        ],
        "anonymous": False,
        "type": "event",
    },
    {
        "name": "TokenExchangeUnderlying",
        "inputs": [
            {"name": "buyer", "type": "address", "indexed": True},
            {"name": "sold_id", "type": "int128", "indexed": False},
            {"name": "tokens_sold", "type": "uint256", "indexed": False},
            {"name": "bought_id", "type": "int128", "indexed": False},
            {"name": "tokens_bought", "type": "uint256", "indexed": False},
        ],
        "anonymous": False,
        "type": "event",
    },
]

# ERC20 ABI for token info
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
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


class CurveAdapter(BaseProtocolAdapter):
    """Adapter for Curve Finance pools.

    Monitors:
    - Total liquidity (sum of all coin balances)
    - Individual coin balances
    - Pool imbalance (deviation from ideal ratio)
    - AddLiquidity, RemoveLiquidity, TokenExchange events
    """

    PROTOCOL_TYPE = "curve"

    # Maximum coins to check (most pools have 2-4)
    MAX_COINS = 8

    def __init__(
        self,
        web3: Web3,
        pool_address: str,
        cache_ttl: int | None = None,
    ):
        """Initialize Curve adapter for a specific pool.

        Args:
            web3: Web3 instance
            pool_address: Address of the Curve pool
            cache_ttl: Cache TTL in seconds (default: 60)
        """
        super().__init__(web3, pool_address, cache_ttl)
        self._pool_contract: Contract | None = None
        self._coin_addresses: list[str] = []
        self._n_coins: int | None = None

    @property
    def pool_contract(self) -> Contract:
        """Get or create the pool contract instance."""
        if self._pool_contract is None:
            self._pool_contract = self._web3.eth.contract(
                address=self._protocol_address,
                abi=CURVE_POOL_ABI + CURVE_EVENTS_ABI,
            )
        return self._pool_contract

    async def _get_n_coins(self) -> int:
        """Determine the number of coins in the pool."""
        if self._n_coins is not None:
            return self._n_coins

        cache_key = f"n_coins:{self._protocol_address}"

        async def fetch():
            loop = asyncio.get_event_loop()

            # Try to read N_COINS directly
            try:
                n = await loop.run_in_executor(
                    None, self.pool_contract.functions.N_COINS().call
                )
                return n
            except Exception:
                pass

            # Otherwise, probe coins until we hit an error
            for i in range(self.MAX_COINS):
                try:
                    await loop.run_in_executor(
                        None, self.pool_contract.functions.coins(i).call
                    )
                except Exception:
                    return i

            return self.MAX_COINS

        self._n_coins = await self._cache.get_or_fetch(cache_key, fetch)
        return self._n_coins

    async def _get_coin_addresses(self) -> list[str]:
        """Get all coin addresses in the pool."""
        if self._coin_addresses:
            return self._coin_addresses

        cache_key = f"coins:{self._protocol_address}"

        async def fetch():
            n_coins = await self._get_n_coins()
            loop = asyncio.get_event_loop()
            coins = []

            for i in range(n_coins):
                try:
                    coin = await loop.run_in_executor(
                        None, self.pool_contract.functions.coins(i).call
                    )
                    coins.append(self._web3.to_checksum_address(coin))
                except Exception as e:
                    logger.warning("Failed to get coin %d: %s", i, e)
                    break

            return coins

        self._coin_addresses = await self._cache.get_or_fetch(cache_key, fetch)
        return self._coin_addresses

    async def _get_token_info(self, token_address: str) -> dict[str, Any]:
        """Get token symbol and decimals."""
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
                # Handle ETH placeholder (0xEeee...) or non-standard tokens
                if token_address.lower() == "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee":
                    symbol = "ETH"
                    decimals = 18
                else:
                    symbol = "UNKNOWN"
                    decimals = 18

            return {"symbol": symbol, "decimals": decimals}

        return await self._cache.get_or_fetch(cache_key, fetch)

    async def _get_balances(self) -> list[int]:
        """Get raw balances for all coins in the pool."""
        n_coins = await self._get_n_coins()
        loop = asyncio.get_event_loop()
        balances = []

        for i in range(n_coins):
            try:
                balance = await loop.run_in_executor(
                    None, self.pool_contract.functions.balances(i).call
                )
                balances.append(balance)
            except Exception as e:
                logger.warning("Failed to get balance %d: %s", i, e)
                balances.append(0)

        return balances

    async def _fetch_tvl(self) -> int:
        """Fetch total TVL as sum of all coin balances.

        Note: This is a simplified TVL that doesn't account for different
        token decimals or prices. For accurate USD TVL, multiply by prices.
        """
        balances = await self._get_balances()
        coins = await self._get_coin_addresses()

        total_tvl = 0
        for i, balance in enumerate(balances):
            if i < len(coins):
                token_info = await self._get_token_info(coins[i])
                # Normalize to 18 decimals for comparison
                decimals = token_info["decimals"]
                normalized = balance * (10 ** (18 - decimals))
                total_tvl += normalized

        logger.info("Curve pool %s TVL: %d (normalized wei)", self._protocol_address[:10], total_tvl)
        return total_tvl

    async def _fetch_token_balances(self) -> list[TokenBalance]:
        """Fetch token balances for all coins in the pool."""
        coins = await self._get_coin_addresses()
        balances = await self._get_balances()
        token_balances: list[TokenBalance] = []

        for i, coin in enumerate(coins):
            if i >= len(balances):
                break

            try:
                token_info = await self._get_token_info(coin)
                decimals = token_info["decimals"]
                raw_balance = balances[i]

                token_balances.append(
                    TokenBalance(
                        token_address=coin,
                        symbol=token_info["symbol"],
                        decimals=decimals,
                        balance_raw=raw_balance,
                        balance_formatted=raw_balance / (10**decimals),
                    )
                )
            except Exception as e:
                logger.warning("Failed to get token balance for %s: %s", coin, e)

        return token_balances

    async def _fetch_events(
        self,
        event_name: str | None = None,
        from_block: int | None = None,
        limit: int = 100,
    ) -> list[ProtocolEvent]:
        """Fetch recent Curve pool events.

        Supported events: AddLiquidity, RemoveLiquidity, RemoveLiquidityOne,
        RemoveLiquidityImbalance, TokenExchange, TokenExchangeUnderlying
        """
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
            else [
                "AddLiquidity",
                "RemoveLiquidity",
                "RemoveLiquidityOne",
                "RemoveLiquidityImbalance",
                "TokenExchange",
                "TokenExchangeUnderlying",
            ]
        )

        for name in event_names:
            try:
                # Check if event exists on contract
                if not hasattr(self.pool_contract.events, name):
                    continue

                event_filter = getattr(self.pool_contract.events, name)
                raw_events = await loop.run_in_executor(
                    None,
                    lambda ef=event_filter: ef.create_filter(
                        fromBlock=from_block,
                        toBlock=current_block,
                    ).get_all_entries(),
                )

                for e in raw_events[:limit]:
                    # Convert args to serializable dict
                    args = {}
                    for key, value in e["args"].items():
                        if isinstance(value, bytes):
                            args[key] = value.hex()
                        elif isinstance(value, (list, tuple)):
                            args[key] = [
                                v.hex() if isinstance(v, bytes) else v for v in value
                            ]
                        else:
                            args[key] = value

                    events.append(
                        ProtocolEvent(
                            event_name=name,
                            block_number=e["blockNumber"],
                            transaction_hash=e["transactionHash"].hex(),
                            log_index=e["logIndex"],
                            args=args,
                        )
                    )

            except Exception as ex:
                logger.debug("Failed to fetch %s events: %s", name, ex)

        # Sort by block number descending
        events.sort(key=lambda x: x.block_number, reverse=True)
        return events[:limit]

    async def get_virtual_price(self) -> int:
        """Get the pool's virtual price.

        Virtual price represents the value of LP tokens.
        A manipulation attack often causes sudden virtual price changes.
        """
        cache_key = f"virtual_price:{self._protocol_address}"

        async def fetch():
            loop = asyncio.get_event_loop()
            try:
                return await loop.run_in_executor(
                    None, self.pool_contract.functions.get_virtual_price().call
                )
            except Exception:
                return 10**18  # Default to 1.0

        return await self._cache.get_or_fetch(cache_key, fetch)

    async def get_amplification(self) -> int:
        """Get the pool's amplification coefficient (A).

        The A parameter affects slippage. Changes to A can affect pool behavior.
        """
        cache_key = f"A:{self._protocol_address}"

        async def fetch():
            loop = asyncio.get_event_loop()
            try:
                return await loop.run_in_executor(
                    None, self.pool_contract.functions.A().call
                )
            except Exception:
                return 0

        return await self._cache.get_or_fetch(cache_key, fetch)

    async def get_pool_imbalance(self) -> dict[str, Any]:
        """Calculate pool imbalance from ideal 1:1:... ratio.

        Returns:
            Dictionary with:
            - max_deviation: Maximum deviation from ideal (0.0 to 1.0)
            - deviations: List of deviation percentages per coin
            - is_imbalanced: True if any coin deviates > 10%
            - balances: Current balances per coin
        """
        balances = await self._get_balances()
        coins = await self._get_coin_addresses()

        if not balances or sum(balances) == 0:
            return {
                "max_deviation": 0.0,
                "deviations": [],
                "is_imbalanced": False,
                "balances": [],
            }

        # Normalize balances to same decimals
        normalized = []
        for i, balance in enumerate(balances):
            if i < len(coins):
                token_info = await self._get_token_info(coins[i])
                decimals = token_info["decimals"]
                normalized.append(balance * (10 ** (18 - decimals)))
            else:
                normalized.append(balance)

        total = sum(normalized)
        n_coins = len(normalized)
        ideal_share = 1.0 / n_coins

        deviations = []
        for norm_balance in normalized:
            actual_share = norm_balance / total if total > 0 else 0
            deviation = abs(actual_share - ideal_share) / ideal_share
            deviations.append(round(deviation * 100, 2))  # As percentage

        max_deviation = max(deviations) / 100 if deviations else 0.0

        return {
            "max_deviation": round(max_deviation, 4),
            "deviations": deviations,
            "is_imbalanced": max_deviation > 0.10,  # >10% from ideal
            "balances": balances,
            "normalized_balances": normalized,
        }

    async def get_large_swaps(
        self,
        threshold_usd: float = 100_000,
        from_block: int | None = None,
    ) -> list[ProtocolEvent]:
        """Get token swaps above a USD threshold.

        Note: For accurate USD values, we'd need price feeds.
        This is a simplified version.
        """
        events = await self._fetch_events(
            event_name="TokenExchange",
            from_block=from_block,
            limit=500,
        )

        # Also check underlying swaps
        underlying_events = await self._fetch_events(
            event_name="TokenExchangeUnderlying",
            from_block=from_block,
            limit=500,
        )
        events.extend(underlying_events)

        # Filter for large amounts (simplified: assume 18 decimals, ~$2000/ETH)
        threshold_raw = int(threshold_usd * 10**18 / 2000)

        large_swaps = []
        for e in events:
            sold = e.args.get("tokens_sold", 0)
            bought = e.args.get("tokens_bought", 0)
            if sold > threshold_raw or bought > threshold_raw:
                large_swaps.append(e)

        return large_swaps

    async def get_large_withdrawals(
        self,
        threshold_usd: float = 100_000,
        from_block: int | None = None,
    ) -> list[ProtocolEvent]:
        """Get liquidity removals above a USD threshold."""
        events = []

        for event_name in [
            "RemoveLiquidity",
            "RemoveLiquidityOne",
            "RemoveLiquidityImbalance",
        ]:
            batch = await self._fetch_events(
                event_name=event_name,
                from_block=from_block,
                limit=500,
            )
            events.extend(batch)

        # Filter for large amounts
        threshold_raw = int(threshold_usd * 10**18 / 2000)

        large_withdrawals = []
        for e in events:
            # Check different event formats
            amounts = e.args.get("token_amounts", [])
            if isinstance(amounts, (list, tuple)):
                if any(a > threshold_raw for a in amounts):
                    large_withdrawals.append(e)
            else:
                coin_amount = e.args.get("coin_amount", 0)
                if coin_amount > threshold_raw:
                    large_withdrawals.append(e)

        return large_withdrawals

    async def detect_manipulation(self) -> dict[str, Any]:
        """Detect potential pool manipulation.

        Checks for:
        1. High imbalance (>20% deviation)
        2. Virtual price anomalies
        3. Suspicious swap patterns

        Returns:
            Dictionary with manipulation indicators
        """
        imbalance = await self.get_pool_imbalance()
        virtual_price = await self.get_virtual_price()

        # Check for recent large swaps
        large_swaps = await self.get_large_swaps(
            threshold_usd=500_000,  # $500k+ swaps
            from_block=None,
        )

        # Indicators
        high_imbalance = imbalance["max_deviation"] > 0.20
        suspicious_swaps = len(large_swaps) > 5  # Many large swaps recently

        # Virtual price should be close to 1e18 for new pools
        # Large deviations may indicate manipulation or profits/losses
        virtual_price_deviation = abs(virtual_price - 10**18) / 10**18

        return {
            "high_imbalance": high_imbalance,
            "imbalance_details": imbalance,
            "suspicious_swaps": suspicious_swaps,
            "large_swap_count": len(large_swaps),
            "virtual_price": virtual_price,
            "virtual_price_deviation": round(virtual_price_deviation, 4),
            "potential_manipulation": high_imbalance or suspicious_swaps,
        }


def get_curve_adapter(
    web3: Web3,
    pool_address: str | None = None,
    pool_name: str | None = None,
) -> CurveAdapter:
    """Factory function to create a Curve adapter.

    Args:
        web3: Web3 instance
        pool_address: Direct pool address (optional)
        pool_name: Pool name like "3pool", "steth" (optional)

    Returns:
        CurveAdapter instance
    """
    chain_id = web3.eth.chain_id
    addresses = CURVE_ADDRESSES.get(chain_id, CURVE_ADDRESSES[1])

    if pool_address:
        return CurveAdapter(web3, pool_address)

    if pool_name and "pools" in addresses:
        pool_addr = addresses["pools"].get(pool_name)
        if pool_addr:
            return CurveAdapter(web3, pool_addr)

    # Default to first pool if available
    if "pools" in addresses:
        first_pool = next(iter(addresses["pools"].values()))
        return CurveAdapter(web3, first_pool)

    raise ValueError(
        f"No Curve pool found. Provide pool_address or pool_name. "
        f"Available pools: {list(addresses.get('pools', {}).keys())}"
    )


def get_known_curve_pools(chain_id: int = 1) -> dict[str, str]:
    """Get known Curve pool addresses for a chain."""
    addresses = CURVE_ADDRESSES.get(chain_id, {})
    return addresses.get("pools", {})
