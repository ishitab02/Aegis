"""VRF Consumer contract interaction for tie-breaker selection."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import TYPE_CHECKING

from eth_account import Account
from web3 import Web3

from aegis.config import AEGIS_VRF_CONSUMER_ADDRESS, VRF_CONSUMER_ABI

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class VRFConsumerService:
    """Service to interact with the AegisVRFConsumer contract."""

    def __init__(self, w3: Web3, contract_address: str | None = None):
        self.w3 = w3
        self.address = Web3.to_checksum_address(
            contract_address or AEGIS_VRF_CONSUMER_ADDRESS
        )
        self.contract = w3.eth.contract(address=self.address, abi=VRF_CONSUMER_ABI)
        self._private_key = os.getenv("DEPLOYER_PRIVATE_KEY", "")

    def get_subscription_id(self) -> int:
        """Get the VRF subscription ID from the contract."""
        return self.contract.functions.s_subscriptionId().call()

    def get_tie_break_counter(self) -> int:
        """Get the current tie-break counter."""
        return self.contract.functions.s_tieBreakCounter().call()

    def get_last_request_id(self) -> int:
        """Get the last VRF request ID."""
        return self.contract.functions.s_lastRequestId().call()

    def get_last_random_word(self) -> int:
        """Get the last random word received."""
        return self.contract.functions.s_lastRandomWord().call()

    def get_last_selected_sentinel(self) -> int:
        """Get the last selected sentinel ID from VRF."""
        return self.contract.functions.getLastSelectedSentinel().call()

    def is_request_fulfilled(self, request_id: int) -> bool:
        """Check if a VRF request has been fulfilled."""
        return self.contract.functions.isRequestFulfilled(request_id).call()

    def get_request(self, request_id: int) -> dict:
        """Get details of a VRF request."""
        result = self.contract.functions.getRequest(request_id).call()
        return {
            "tie_breaker_id": result[0],
            "sentinel_ids": list(result[1]),
            "selected_sentinel_id": result[2],
            "random_word": result[3],
            "fulfilled": result[4],
        }

    def get_tie_break_result(self, tie_breaker_id: int) -> dict:
        """Get the result of a tie-break by its ID."""
        result = self.contract.functions.getTieBreakResult(tie_breaker_id).call()
        return {
            "tie_breaker_id": result[0],
            "sentinel_ids": list(result[1]),
            "selected_sentinel_id": result[2],
            "random_word": result[3],
            "fulfilled": result[4],
        }

    def request_tie_breaker(
        self,
        sentinel_ids: list[int],
    ) -> tuple[int, int, str]:
        """
        Request VRF randomness for tie-breaking.

        Args:
            sentinel_ids: List of sentinel IDs to choose from

        Returns:
            Tuple of (request_id, tie_breaker_id, tx_hash)
        """
        if not self._private_key:
            raise ValueError("DEPLOYER_PRIVATE_KEY not set - cannot send transactions")

        account = Account.from_key(self._private_key)
        nonce = self.w3.eth.get_transaction_count(account.address)

        # Build transaction
        tx = self.contract.functions.requestTieBreaker(sentinel_ids).build_transaction(
            {
                "from": account.address,
                "nonce": nonce,
                "gas": 500000,
                "gasPrice": self.w3.eth.gas_price,
            }
        )

        # Sign and send
        signed_tx = self.w3.eth.account.sign_transaction(tx, self._private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hash_hex = tx_hash.hex()

        logger.info("VRF tie-breaker request sent: %s", tx_hash_hex)

        # Wait for receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt["status"] != 1:
            raise RuntimeError(f"VRF request transaction failed: {tx_hash_hex}")

        # Get the request ID from the contract state
        request_id = self.get_last_request_id()
        tie_breaker_id = self.get_tie_break_counter()

        logger.info(
            "VRF request successful: request_id=%d, tie_breaker_id=%d",
            request_id,
            tie_breaker_id,
        )

        return request_id, tie_breaker_id, tx_hash_hex

    def wait_for_fulfillment(
        self,
        request_id: int,
        timeout_seconds: int = 300,
        poll_interval: int = 5,
    ) -> dict | None:
        """
        Wait for VRF fulfillment.

        Args:
            request_id: The VRF request ID
            timeout_seconds: Maximum time to wait
            poll_interval: Seconds between polls

        Returns:
            Request result dict if fulfilled, None if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            if self.is_request_fulfilled(request_id):
                result = self.get_request(request_id)
                logger.info(
                    "VRF fulfilled: selected_sentinel=%d, random_word=%d",
                    result["selected_sentinel_id"],
                    result["random_word"],
                )
                return result

            logger.debug("Waiting for VRF fulfillment... (%ds elapsed)", int(time.time() - start_time))
            time.sleep(poll_interval)

        logger.warning("VRF fulfillment timeout after %ds", timeout_seconds)
        return None

    async def wait_for_fulfillment_async(
        self,
        request_id: int,
        timeout_seconds: int = 300,
        poll_interval: int = 5,
    ) -> dict | None:
        """Async version of wait_for_fulfillment."""
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            if self.is_request_fulfilled(request_id):
                result = self.get_request(request_id)
                logger.info(
                    "VRF fulfilled: selected_sentinel=%d, random_word=%d",
                    result["selected_sentinel_id"],
                    result["random_word"],
                )
                return result

            await asyncio.sleep(poll_interval)

        logger.warning("VRF fulfillment timeout after %ds", timeout_seconds)
        return None


# Module-level cached instance
_vrf_service: VRFConsumerService | None = None


def get_vrf_service(w3: Web3 | None = None) -> VRFConsumerService:
    """Get or create a VRF consumer service instance."""
    global _vrf_service

    if _vrf_service is None:
        if w3 is None:
            from aegis.blockchain.web3_client import get_web3
            w3 = get_web3()
        _vrf_service = VRFConsumerService(w3)

    return _vrf_service


def request_vrf_tie_breaker(
    sentinel_ids: list[int],
    w3: Web3 | None = None,
) -> tuple[int, int, str]:
    """
    Convenience function to request VRF tie-breaker.

    Returns:
        Tuple of (request_id, tie_breaker_id, tx_hash)
    """
    service = get_vrf_service(w3)
    return service.request_tie_breaker(sentinel_ids)


def check_vrf_fulfillment(
    request_id: int,
    w3: Web3 | None = None,
) -> dict | None:
    """
    Check if a VRF request is fulfilled and get result.

    Returns:
        Request result dict if fulfilled, None otherwise
    """
    service = get_vrf_service(w3)

    if service.is_request_fulfilled(request_id):
        return service.get_request(request_id)

    return None


def get_vrf_status(w3: Web3 | None = None) -> dict:
    """Get overall VRF consumer status."""
    service = get_vrf_service(w3)

    return {
        "contract_address": service.address,
        "subscription_id": str(service.get_subscription_id()),
        "tie_break_counter": service.get_tie_break_counter(),
        "last_request_id": str(service.get_last_request_id()),
        "last_selected_sentinel": service.get_last_selected_sentinel(),
    }
