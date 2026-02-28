"""Chainlink Data Feed interaction layer."""

from web3 import Web3

from aegis.config import AGGREGATOR_V3_ABI, CHAINLINK_FEEDS
from aegis.models import PriceFeedData
from aegis.utils import now_seconds


def get_chainlink_price(feed_address: str, w3: Web3) -> PriceFeedData:
    """Get price from a Chainlink Data Feed on Base Sepolia."""
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
