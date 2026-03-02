"""Base adapter for DeFi protocol integrations."""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from web3 import Web3




@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class TTLCache:
    def __init__(self, ttl_seconds: int = 60):
        self.ttl = ttl_seconds
        self._cache: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    def _is_expired(self, entry: CacheEntry) -> bool:
        return time.time() > entry.expires_at

    def get(self, key: str) -> Any | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        if self._is_expired(entry):
            del self._cache[key]
            return None
        return entry.value

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = CacheEntry(
            value=value,
            expires_at=time.time() + self.ttl,
        )

    async def get_or_fetch(self, key: str, fetch_fn) -> Any:
        async with self._lock:
            cached = self.get(key)
            if cached is not None:
                return cached

        # fetch outside lock so different keys can be fetched concurrently
        value = await fetch_fn()

        async with self._lock:
            self.set(key, value)

        return value

    def clear(self) -> None:
        self._cache.clear()

    def invalidate(self, key: str) -> None:
        self._cache.pop(key, None)




class TokenBalance(BaseModel):
    token_address: str
    symbol: str
    decimals: int
    balance_raw: int
    balance_formatted: float

    @property
    def balance_wei(self) -> int:
        return self.balance_raw


class ProtocolEvent(BaseModel):
    event_name: str
    block_number: int
    transaction_hash: str
    log_index: int
    args: dict[str, Any]
    timestamp: int | None = None


class ProtocolMetricsSnapshot(BaseModel):
    protocol_address: str
    protocol_type: str
    tvl_wei: int
    tvl_usd: float | None = None
    token_balances: list[TokenBalance] = []
    timestamp: int
    block_number: int




class ProtocolAdapterProtocol(Protocol):
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




T = TypeVar("T", bound="BaseProtocolAdapter")


class BaseProtocolAdapter(ABC):
    DEFAULT_CACHE_TTL = 60
    PROTOCOL_TYPE: str = "unknown"

    def __init__(
        self,
        web3: Web3,
        protocol_address: str,
        cache_ttl: int | None = None,
    ):
        self._web3 = web3
        self._protocol_address = web3.to_checksum_address(protocol_address)
        self._cache = TTLCache(ttl_seconds=cache_ttl or self.DEFAULT_CACHE_TTL)
        self._initialized = False

    @property
    def protocol_address(self) -> str:
        return self._protocol_address

    @property
    def protocol_type(self) -> str:
        return self.PROTOCOL_TYPE

    @property
    def web3(self) -> Web3:
        return self._web3

    @property
    def chain_id(self) -> int:
        return self._web3.eth.chain_id


    async def get_tvl(self) -> int:
        cache_key = f"tvl:{self._protocol_address}"
        return await self._cache.get_or_fetch(cache_key, self._fetch_tvl)

    async def get_token_balances(self) -> list[TokenBalance]:
        cache_key = f"balances:{self._protocol_address}"
        return await self._cache.get_or_fetch(cache_key, self._fetch_token_balances)

    async def get_recent_events(
        self,
        event_name: str | None = None,
        from_block: int | None = None,
        limit: int = 100,
    ) -> list[ProtocolEvent]:
        return await self._fetch_events(
            event_name=event_name,
            from_block=from_block,
            limit=limit,
        )

    async def get_metrics_snapshot(self) -> ProtocolMetricsSnapshot:
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
        self._cache.clear()


    @abstractmethod
    async def _fetch_tvl(self) -> int:
        ...

    @abstractmethod
    async def _fetch_token_balances(self) -> list[TokenBalance]:
        ...

    @abstractmethod
    async def _fetch_events(
        self,
        event_name: str | None = None,
        from_block: int | None = None,
        limit: int = 100,
    ) -> list[ProtocolEvent]:
        ...


    def _run_sync(self, coro) -> Any:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # already in async context, use a thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)

    def get_tvl_sync(self) -> int:
        return self._run_sync(self.get_tvl())

    def get_token_balances_sync(self) -> list[TokenBalance]:
        return self._run_sync(self.get_token_balances())

    def get_recent_events_sync(
        self,
        event_name: str | None = None,
        from_block: int | None = None,
        limit: int = 100,
    ) -> list[ProtocolEvent]:
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
