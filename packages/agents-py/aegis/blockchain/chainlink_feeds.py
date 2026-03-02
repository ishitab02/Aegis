"""Chainlink Data Feed interaction layer.

Provides functions for reading prices from Chainlink Data Feeds on various networks.
Supports multiple feeds and parallel fetching for efficiency.
"""

from __future__ import annotations

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import TYPE_CHECKING

from web3 import Web3

from aegis.config import (
    AGGREGATOR_V3_ABI,
    CHAINLINK_FEEDS,
    CHAINLINK_FEEDS_BASE,
    CHAINLINK_FEEDS_MAINNET,
)
from aegis.models import PriceFeedData
from aegis.utils import now_seconds

if TYPE_CHECKING:
    from web3.contract import Contract

logger = logging.getLogger(__name__)

# ============ Constants ============

# Maximum age of a price feed before it's considered stale
DEFAULT_STALENESS_THRESHOLD_SECONDS = 3600  # 1 hour
HIGH_STALENESS_THRESHOLD_SECONDS = 1800  # 30 minutes (for alerting)

# Chainlink heartbeat intervals (seconds) for common feeds
FEED_HEARTBEATS = {
    "ETH/USD": 3600,  # 1 hour
    "BTC/USD": 3600,
    "LINK/USD": 3600,
    "USDC/USD": 86400,  # 24 hours (stablecoins have longer heartbeats)
    "DAI/USD": 3600,
    "USDT/USD": 86400,
}


# ============ Data Classes ============


@dataclass
class PriceFeedStatus:
    """Extended status for a price feed including staleness info."""

    pair: str
    price: float
    decimals: int
    updated_at: int
    feed_address: str
    is_stale: bool
    staleness_seconds: int
    heartbeat_seconds: int


@dataclass
class MultiplePricesResult:
    """Result of fetching multiple price feeds."""

    prices: dict[str, PriceFeedData]
    errors: dict[str, str]
    timestamp: int
    duration_ms: int


# ============ Core Functions ============


def get_chainlink_price(feed_address: str, w3: Web3) -> PriceFeedData:
    """Get price from a Chainlink Data Feed.

    Args:
        feed_address: Address of the Chainlink Aggregator contract
        w3: Web3 instance connected to the appropriate network

    Returns:
        PriceFeedData with price, timestamp, and metadata
    """
    feed = w3.eth.contract(
        address=Web3.to_checksum_address(feed_address),
        abi=AGGREGATOR_V3_ABI,
    )

    round_data = feed.functions.latestRoundData().call()
    decimals = feed.functions.decimals().call()

    answer = round_data[1]
    updated_at = round_data[3]

    return PriceFeedData(
        price=answer / (10**decimals),
        updated_at=updated_at,
        decimals=decimals,
        feed_address=feed_address,
    )


def get_eth_usd_price(w3: Web3) -> PriceFeedData:
    """Get ETH/USD price from Chainlink."""
    return get_chainlink_price(CHAINLINK_FEEDS["ETH/USD"], w3)


def get_btc_usd_price(w3: Web3) -> PriceFeedData:
    """Get BTC/USD price from Chainlink."""
    return get_chainlink_price(CHAINLINK_FEEDS["BTC/USD"], w3)


def get_link_usd_price(w3: Web3) -> PriceFeedData:
    """Get LINK/USD price from Chainlink."""
    return get_chainlink_price(CHAINLINK_FEEDS["LINK/USD"], w3)


def get_usdc_usd_price(w3: Web3) -> PriceFeedData:
    """Get USDC/USD price from Chainlink."""
    return get_chainlink_price(CHAINLINK_FEEDS["USDC/USD"], w3)


def get_price_by_pair(pair: str, w3: Web3) -> PriceFeedData:
    """Get price for a specific pair from Chainlink.

    Args:
        pair: Trading pair (e.g., "ETH/USD", "BTC/USD")
        w3: Web3 instance

    Returns:
        PriceFeedData for the requested pair

    Raises:
        ValueError: If the pair is not supported
    """
    feed_address = CHAINLINK_FEEDS.get(pair)
    if not feed_address:
        raise ValueError(f"Unsupported pair: {pair}. Available: {list(CHAINLINK_FEEDS.keys())}")

    return get_chainlink_price(feed_address, w3)


def get_multiple_prices(
    pairs: list[str] | None = None,
    w3: Web3 = None,
) -> MultiplePricesResult:
    """Fetch multiple price feeds in parallel.

    Args:
        pairs: List of pairs to fetch (e.g., ["ETH/USD", "BTC/USD"]).
               If None, fetches all available pairs.
        w3: Web3 instance. If None, will attempt to get from web3_client.

    Returns:
        MultiplePricesResult with all fetched prices and any errors

    Example:
        >>> from aegis.blockchain.chainlink_feeds import get_multiple_prices
        >>> from aegis.blockchain.web3_client import get_web3
        >>> result = get_multiple_prices(["ETH/USD", "BTC/USD", "LINK/USD"], get_web3())
        >>> print(result.prices["ETH/USD"].price)
        2500.50
    """
    if w3 is None:
        from aegis.blockchain.web3_client import get_web3

        w3 = get_web3()

    if pairs is None:
        pairs = list(CHAINLINK_FEEDS.keys())

    start_time = time.time()
    prices: dict[str, PriceFeedData] = {}
    errors: dict[str, str] = {}

    def fetch_single(pair: str) -> tuple[str, PriceFeedData | None, str | None]:
        feed_address = CHAINLINK_FEEDS.get(pair)
        if not feed_address:
            return pair, None, f"Unsupported pair: {pair}"

        try:
            price_data = get_chainlink_price(feed_address, w3)
            return pair, price_data, None
        except Exception as e:
            logger.warning("Failed to fetch %s: %s", pair, e)
            return pair, None, str(e)

    # Use ThreadPoolExecutor for parallel fetching
    with ThreadPoolExecutor(max_workers=min(len(pairs), 10)) as executor:
        results = list(executor.map(fetch_single, pairs))

    for pair, price_data, error in results:
        if price_data:
            prices[pair] = price_data
        if error:
            errors[pair] = error

    duration_ms = int((time.time() - start_time) * 1000)

    logger.info(
        "Fetched %d/%d prices in %dms",
        len(prices),
        len(pairs),
        duration_ms,
    )

    return MultiplePricesResult(
        prices=prices,
        errors=errors,
        timestamp=now_seconds(),
        duration_ms=duration_ms,
    )


async def get_multiple_prices_async(
    pairs: list[str] | None = None,
    w3: Web3 = None,
) -> MultiplePricesResult:
    """Async version of get_multiple_prices.

    Fetches multiple price feeds concurrently using asyncio.
    """
    if w3 is None:
        from aegis.blockchain.web3_client import get_web3

        w3 = get_web3()

    if pairs is None:
        pairs = list(CHAINLINK_FEEDS.keys())

    start_time = time.time()
    prices: dict[str, PriceFeedData] = {}
    errors: dict[str, str] = {}

    async def fetch_single(pair: str) -> tuple[str, PriceFeedData | None, str | None]:
        feed_address = CHAINLINK_FEEDS.get(pair)
        if not feed_address:
            return pair, None, f"Unsupported pair: {pair}"

        loop = asyncio.get_event_loop()
        try:
            price_data = await loop.run_in_executor(
                None, lambda: get_chainlink_price(feed_address, w3)
            )
            return pair, price_data, None
        except Exception as e:
            logger.warning("Failed to fetch %s: %s", pair, e)
            return pair, None, str(e)

    results = await asyncio.gather(*[fetch_single(pair) for pair in pairs])

    for pair, price_data, error in results:
        if price_data:
            prices[pair] = price_data
        if error:
            errors[pair] = error

    duration_ms = int((time.time() - start_time) * 1000)

    return MultiplePricesResult(
        prices=prices,
        errors=errors,
        timestamp=now_seconds(),
        duration_ms=duration_ms,
    )


# ============ Staleness Checking ============


def check_feed_staleness(
    price_data: PriceFeedData,
    pair: str | None = None,
    threshold_seconds: int | None = None,
) -> tuple[bool, int]:
    """Check if a price feed is stale.

    Args:
        price_data: The PriceFeedData to check
        pair: Optional pair name for pair-specific heartbeat
        threshold_seconds: Override staleness threshold (default: 1 hour)

    Returns:
        Tuple of (is_stale, staleness_seconds)
    """
    current_time = now_seconds()
    staleness_seconds = current_time - price_data.updated_at

    if threshold_seconds is None:
        # Use pair-specific heartbeat if available
        if pair and pair in FEED_HEARTBEATS:
            threshold_seconds = FEED_HEARTBEATS[pair] * 2  # 2x heartbeat = stale
        else:
            threshold_seconds = DEFAULT_STALENESS_THRESHOLD_SECONDS

    is_stale = staleness_seconds > threshold_seconds

    return is_stale, staleness_seconds


def get_feed_status(pair: str, w3: Web3) -> PriceFeedStatus:
    """Get detailed status for a price feed including staleness.

    Args:
        pair: Trading pair (e.g., "ETH/USD")
        w3: Web3 instance

    Returns:
        PriceFeedStatus with price, staleness, and metadata
    """
    price_data = get_price_by_pair(pair, w3)
    is_stale, staleness_seconds = check_feed_staleness(price_data, pair)
    heartbeat = FEED_HEARTBEATS.get(pair, DEFAULT_STALENESS_THRESHOLD_SECONDS)

    return PriceFeedStatus(
        pair=pair,
        price=price_data.price,
        decimals=price_data.decimals,
        updated_at=price_data.updated_at,
        feed_address=price_data.feed_address,
        is_stale=is_stale,
        staleness_seconds=staleness_seconds,
        heartbeat_seconds=heartbeat,
    )


def get_all_feed_statuses(w3: Web3) -> dict[str, PriceFeedStatus]:
    """Get status for all available price feeds.

    Returns:
        Dictionary mapping pair names to their PriceFeedStatus
    """
    statuses = {}
    for pair in CHAINLINK_FEEDS:
        try:
            statuses[pair] = get_feed_status(pair, w3)
        except Exception as e:
            logger.warning("Failed to get status for %s: %s", pair, e)

    return statuses


# ============ Price Deviation Checking ============


def check_price_deviation(
    reported_price: float,
    chainlink_price: float,
    threshold_percent: float = 5.0,
) -> tuple[bool, float]:
    """Check if a reported price deviates significantly from Chainlink.

    Args:
        reported_price: The price reported by a protocol
        chainlink_price: The reference price from Chainlink
        threshold_percent: Deviation threshold (default: 5%)

    Returns:
        Tuple of (is_deviated, deviation_percent)
    """
    if chainlink_price == 0:
        return True, 100.0

    deviation_percent = abs(reported_price - chainlink_price) / chainlink_price * 100

    return deviation_percent > threshold_percent, deviation_percent


def verify_protocol_price(
    protocol_price: float,
    pair: str,
    w3: Web3,
    threshold_percent: float = 5.0,
) -> dict:
    """Verify a protocol's price against Chainlink.

    Args:
        protocol_price: The price reported by the protocol
        pair: The trading pair (e.g., "ETH/USD")
        w3: Web3 instance
        threshold_percent: Deviation threshold

    Returns:
        Dictionary with verification results
    """
    chainlink_data = get_price_by_pair(pair, w3)
    is_deviated, deviation_percent = check_price_deviation(
        protocol_price, chainlink_data.price, threshold_percent
    )
    is_stale, staleness_seconds = check_feed_staleness(chainlink_data, pair)

    return {
        "pair": pair,
        "protocol_price": protocol_price,
        "chainlink_price": chainlink_data.price,
        "deviation_percent": round(deviation_percent, 4),
        "is_deviated": is_deviated,
        "is_chainlink_stale": is_stale,
        "staleness_seconds": staleness_seconds,
        "chainlink_updated_at": chainlink_data.updated_at,
        "verification_passed": not is_deviated and not is_stale,
    }


# ============ Network-Specific Helpers ============


def get_feeds_for_network(chain_id: int) -> dict[str, str]:
    """Get available Chainlink feeds for a specific network.

    Args:
        chain_id: The chain ID

    Returns:
        Dictionary of pair names to feed addresses
    """
    feeds_by_chain = {
        1: CHAINLINK_FEEDS_MAINNET,
        8453: CHAINLINK_FEEDS_BASE,
        84532: CHAINLINK_FEEDS,  # Base Sepolia
    }

    return feeds_by_chain.get(chain_id, CHAINLINK_FEEDS)


def get_chainlink_price_for_network(
    pair: str,
    w3: Web3,
) -> PriceFeedData:
    """Get price using the correct feed address for the connected network.

    Args:
        pair: Trading pair (e.g., "ETH/USD")
        w3: Web3 instance

    Returns:
        PriceFeedData for the pair on the connected network
    """
    chain_id = w3.eth.chain_id
    feeds = get_feeds_for_network(chain_id)

    feed_address = feeds.get(pair)
    if not feed_address:
        raise ValueError(
            f"Pair {pair} not available on chain {chain_id}. "
            f"Available: {list(feeds.keys())}"
        )

    return get_chainlink_price(feed_address, w3)
