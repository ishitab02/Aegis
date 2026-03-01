from aegis.blockchain.web3_client import get_web3, get_provider
from aegis.blockchain.chainlink_feeds import get_chainlink_price
from aegis.blockchain.contracts import (
    get_mock_protocol,
    get_protocol_tvl,
    is_protocol_paused,
)

__all__ = [
    "get_web3",
    "get_provider",
    "get_chainlink_price",
    "get_mock_protocol",
    "get_protocol_tvl",
    "is_protocol_paused",
]
