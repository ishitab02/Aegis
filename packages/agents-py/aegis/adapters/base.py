"""Base adapter class for all DeFi protocol integrations.

Protocol adapters provide a unified interface to read TVL, token balances,
and events from various DeFi protocols (Aave, Uniswap, Compound, etc.).
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from web3 import Web3


# ============ Cache Implementation ============


@dataclass
class CacheEntry:
    """A cached value with expiration time."""

    value: Any
    expires_at: float


class TTLCache:
    """Simple time-based cache with configurable TTL."""

    def __init__(self, ttl_seconds: int = 60):
        self.ttl = ttl_seconds
        self._cache: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    def _is_expired(self, entry: CacheEntry) -> bool:
        return time.time() > entry.expires_at

    def get(self, key: str) -> Any | None:
        """Get a cached value if it exists and is not expired."""
        entry = self._cache.get(key)
        if entry is None:
            return None
        if self._is_expired(entry):
            del self._cache[key]
            return None
        return entry.value

    def set(self, key: str, value: Any) -> None:
        """Cache a value with the default TTL."""
        self._cache[key] = CacheEntry(
            value=value,
            expires_at=time.time() + self.ttl,
        )

    async def get_or_fetch(self, key: str, fetch_fn) -> Any:
        """Get from cache or fetch using the provided async function."""
        async with self._lock:
            cached = self.get(key)
            if cached is not None:
                return cached

        # Fetch outside the lock to allow concurrent fetches for different keys
        value = await fetch_fn()

        async with self._lock:
            self.set(key, value)

        return value

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    def invalidate(self, key: str) -> None:
        """Remove a specific entry from cache."""
        self._cache.pop(key, None)


# ============ Data Models ============


class TokenBalance(BaseModel):
    """Token balance for a specific address."""

    token_address: str
    symbol: str
    decimals: int
    balance_raw: int  # Raw balance in smallest unit
    balance_formatted: float  # Human-readable balance

    @property
    def balance_wei(self) -> int:
        """Alias for balance_raw."""
        return self.balance_raw


class ProtocolEvent(BaseModel):
    """Generic event from a DeFi protocol."""

    event_name: str
    block_number: int
    transaction_hash: str
    log_index: int
    args: dict[str, Any]
    timestamp: int | None = None


class ProtocolMetricsSnapshot(BaseModel):
    """Snapshot of protocol metrics at a point in time."""

    protocol_address: str
    protocol_type: str  # "aave_v3", "uniswap_v3", etc.
    tvl_wei: int
    tvl_usd: float | None = None
    token_balances: list[TokenBalance] = []
    timestamp: int
    block_number: int


# ============ Protocol Interface ============


class ProtocolAdapterProtocol(Protocol):
    """Protocol interface for type checking (structural subtyping)."""

    @property
    def protocol_address(self) -> str:
        ...

    @property
    def protocol_type(self) -> str:
        ...

    async def get_tvl(self) -> int:
        ...

    async def get_token_balances(self) -> list[TokenBalance]:
        ...

    async def get_recent_events(
        self, event_name: str | None = None, from_block: int | None = None
    ) -> list[ProtocolEvent]:
        ...


# ============ Abstract Base Class ============


T = TypeVar("T", bound="BaseProtocolAdapter")


class BaseProtocolAdapter(ABC):
    """Abstract base class for all DeFi protocol adapters.

    Subclasses must implement:
    - _fetch_tvl(): Fetch raw TVL from the protocol
    - _fetch_token_balances(): Fetch token balances
    - _fetch_events(): Fetch protocol events

    The base class handles caching and provides a consistent interface.
    """

    # Class-level defaults
    DEFAULT_CACHE_TTL = 60  # seconds
    PROTOCOL_TYPE: str = "unknown"

    def __init__(
        self,
        web3: Web3,
        protocol_address: str,
        cache_ttl: int | None = None,
    ):
        """Initialize the adapter.

        Args:
            web3: Web3 instance connected to the appropriate network
            protocol_address: The main protocol contract address
            cache_ttl: Optional cache TTL override (default: 60 seconds)
        """
        self._web3 = web3
        self._protocol_address = web3.to_checksum_address(protocol_address)
        self._cache = TTLCache(ttl_seconds=cache_ttl or self.DEFAULT_CACHE_TTL)
        self._initialized = False

    @property
    def protocol_address(self) -> str:
        """The main protocol contract address."""
        return self._protocol_address

    @property
    def protocol_type(self) -> str:
        """The type of protocol (e.g., 'aave_v3', 'uniswap_v3')."""
        return self.PROTOCOL_TYPE

    @property
    def web3(self) -> Web3:
        """The Web3 instance."""
        return self._web3

    @property
    def chain_id(self) -> int:
        """The chain ID."""
        return self._web3.eth.chain_id

    # ============ Public API ============

    async def get_tvl(self) -> int:
        """Get the Total Value Locked in wei.

        Returns cached value if available, otherwise fetches from chain.
        """
        cache_key = f"tvl:{self._protocol_address}"
        return await self._cache.get_or_fetch(cache_key, self._fetch_tvl)

    async def get_token_balances(self) -> list[TokenBalance]:
        """Get token balances for the protocol.

        Returns cached value if available, otherwise fetches from chain.
        """
        cache_key = f"balances:{self._protocol_address}"
        return await self._cache.get_or_fetch(cache_key, self._fetch_token_balances)

    async def get_recent_events(
        self,
        event_name: str | None = None,
        from_block: int | None = None,
        limit: int = 100,
    ) -> list[ProtocolEvent]:
        """Get recent events from the protocol.

        Args:
            event_name: Optional filter by event name
            from_block: Starting block (default: latest - 1000)
            limit: Maximum number of events to return

        Returns:
            List of ProtocolEvent objects
        """
        # Events are not cached by default since they're time-sensitive
        return await self._fetch_events(
            event_name=event_name,
            from_block=from_block,
            limit=limit,
        )

    async def get_metrics_snapshot(self) -> ProtocolMetricsSnapshot:
        """Get a complete snapshot of protocol metrics.

        Fetches TVL and token balances in parallel.
        """
        tvl, balances = await asyncio.gather(
            self.get_tvl(),
            self.get_token_balances(),
        )

        return ProtocolMetricsSnapshot(
            protocol_address=self._protocol_address,
            protocol_type=self.protocol_type,
            tvl_wei=tvl,
            token_balances=balances,
            timestamp=int(time.time()),
            block_number=self._web3.eth.block_number,
        )

    def invalidate_cache(self) -> None:
        """Clear all cached data for this adapter."""
        self._cache.clear()

    # ============ Abstract Methods (Must Be Implemented) ============

    @abstractmethod
    async def _fetch_tvl(self) -> int:
        """Fetch the Total Value Locked from the protocol.

        Must be implemented by subclasses.

        Returns:
            TVL in wei (or smallest token unit for stablecoin protocols)
        """
        ...

    @abstractmethod
    async def _fetch_token_balances(self) -> list[TokenBalance]:
        """Fetch token balances from the protocol.

        Must be implemented by subclasses.

        Returns:
            List of TokenBalance objects for tracked tokens
        """
        ...

    @abstractmethod
    async def _fetch_events(
        self,
        event_name: str | None = None,
        from_block: int | None = None,
        limit: int = 100,
    ) -> list[ProtocolEvent]:
        """Fetch recent events from the protocol.

        Must be implemented by subclasses.

        Args:
            event_name: Optional filter by event name
            from_block: Starting block
            limit: Maximum events to return

        Returns:
            List of ProtocolEvent objects
        """
        ...

    # ============ Helper Methods ============

    def _run_sync(self, coro) -> Any:
        """Run an async coroutine synchronously.

        Useful for integrating with sync code.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # We're already in an async context, create a new thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)

    def get_tvl_sync(self) -> int:
        """Synchronous version of get_tvl()."""
        return self._run_sync(self.get_tvl())

    def get_token_balances_sync(self) -> list[TokenBalance]:
        """Synchronous version of get_token_balances()."""
        return self._run_sync(self.get_token_balances())

    def get_recent_events_sync(
        self,
        event_name: str | None = None,
        from_block: int | None = None,
        limit: int = 100,
    ) -> list[ProtocolEvent]:
        """Synchronous version of get_recent_events()."""
        return self._run_sync(
            self.get_recent_events(
                event_name=event_name,
                from_block=from_block,
                limit=limit,
            )
        )

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"type={self.protocol_type} "
            f"address={self._protocol_address[:10]}...>"
        )
