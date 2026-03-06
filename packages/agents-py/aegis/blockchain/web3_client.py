"""Cached Web3 provider."""

from functools import lru_cache

from web3 import Web3

from aegis.config import CHAIN_CONFIG


@lru_cache(maxsize=1)
def get_web3() -> Web3:
    rpc_url = CHAIN_CONFIG["base_sepolia"]["rpc"]
    return Web3(Web3.HTTPProvider(rpc_url))


def get_provider() -> Web3:
    return get_web3()
