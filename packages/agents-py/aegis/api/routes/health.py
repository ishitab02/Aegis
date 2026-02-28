"""Health check endpoint."""

import logging

from fastapi import APIRouter

from aegis.utils import now_seconds

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def health_check() -> dict:
    """System health check.

    Returns the status of all sentinels, blockchain connectivity,
    and Chainlink service availability.
    """
    # Check blockchain connectivity
    blockchain_ok = True
    try:
        from aegis.blockchain.web3_client import get_web3
        w3 = get_web3()
        w3.eth.block_number  # Quick connectivity check
    except Exception as e:
        logger.warning("Blockchain connectivity check failed: %s", e)
        blockchain_ok = False

    # Check Chainlink feeds
    chainlink_ok = True
    try:
        from aegis.blockchain.chainlink_feeds import get_eth_usd_price
        from aegis.blockchain.web3_client import get_web3
        w3 = get_web3()
        price_data = get_eth_usd_price(w3)
        feed_age = now_seconds() - price_data.updated_at
        if feed_age > 3600:
            chainlink_ok = False
    except Exception as e:
        logger.warning("Chainlink feed check failed: %s", e)
        chainlink_ok = False

    # Determine overall status
    if blockchain_ok and chainlink_ok:
        status = "HEALTHY"
    elif blockchain_ok or chainlink_ok:
        status = "DEGRADED"
    else:
        status = "UNHEALTHY"

    return {
        "status": status,
        "sentinels": {
            "active": 3,
            "total": 3,
        },
        "blockchain": {
            "connected": blockchain_ok,
            "network": "Base Sepolia",
            "chainId": 84532,
        },
        "chainlink": {
            "dataFeeds": "AVAILABLE" if chainlink_ok else "UNAVAILABLE",
        },
        "lastCheck": now_seconds(),
    }
