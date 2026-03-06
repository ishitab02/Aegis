"""Smart contract interaction helpers."""

from web3 import Web3

from aegis.config import MOCK_PROTOCOL_ABI, PROTOCOL_TO_MONITOR


def get_mock_protocol(w3: Web3, address: str | None = None):
    addr = address or PROTOCOL_TO_MONITOR
    return w3.eth.contract(
        address=Web3.to_checksum_address(addr),
        abi=MOCK_PROTOCOL_ABI,
    )


def get_protocol_tvl(w3: Web3, address: str | None = None) -> int:
    contract = get_mock_protocol(w3, address)
    return contract.functions.getTVL().call()


def is_protocol_paused(w3: Web3, address: str | None = None) -> bool:
    contract = get_mock_protocol(w3, address)
    return contract.functions.paused().call()
