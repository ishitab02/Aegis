"""Utility helpers."""

import time

from web3 import Web3

from aegis.config import AGGREGATOR_V3_ABI


def get_chainlink_price(
    feed_address: str, w3: Web3
) -> dict:

    feed = w3.eth.contract(
        address=Web3.to_checksum_address(feed_address),
        abi=AGGREGATOR_V3_ABI,
    )

    round_data = feed.functions.latestRoundData().call()
    decimals = feed.functions.decimals().call()

    answer = round_data[1]
    updated_at = round_data[3]

    return {
        "price": answer / (10**decimals),
        "updated_at": updated_at,
        "decimals": decimals,
        "feed_address": feed_address,
    }


def calculate_change_percent(old_val: int, new_val: int) -> float:

    if old_val == 0:
        return 0.0
    return ((new_val - old_val) * 10000 // old_val) / 100


def generate_threat_id(protocol: str, timestamp: int, details: str) -> str:

    return Web3.keccak(text=f"{protocol}-{timestamp}-{details}").hex()


def short_address(address: str) -> str:

    return f"{address[:6]}...{address[-4:]}"


def now_seconds() -> int:

    return int(time.time())


def wei_to_ether(wei: int) -> float:

    return wei / 10**18


def ether_to_wei(ether: float) -> int:

    return int(ether * 10**18)
