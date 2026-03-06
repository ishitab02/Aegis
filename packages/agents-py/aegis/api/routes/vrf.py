"""VRF tie-breaker routes."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from aegis.blockchain.vrf_consumer import (
    check_vrf_fulfillment,
    get_vrf_service,
    get_vrf_status,
    request_vrf_tie_breaker,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class VRFTieBreakRequest(BaseModel):
    """Request to initiate a VRF tie-breaker."""
    sentinel_ids: list[int]


class VRFTieBreakResponse(BaseModel):
    """Response from VRF tie-breaker request."""
    request_id: str
    tie_breaker_id: int
    tx_hash: str
    sentinel_ids: list[int]
    status: str


class VRFStatusResponse(BaseModel):
    """VRF consumer status."""
    contract_address: str
    subscription_id: str
    tie_break_counter: int
    last_request_id: str
    last_selected_sentinel: int


class VRFFulfillmentResponse(BaseModel):
    """VRF fulfillment result."""
    request_id: str
    fulfilled: bool
    selected_sentinel_id: Optional[int] = None
    random_word: Optional[str] = None
    sentinel_ids: list[int] = []


@router.get("/status", response_model=VRFStatusResponse)
async def get_vrf_consumer_status():
    """Get the VRF consumer contract status."""
    try:
        status = get_vrf_status()
        return VRFStatusResponse(
            contract_address=status["contract_address"],
            subscription_id=status["subscription_id"],
            tie_break_counter=status["tie_break_counter"],
            last_request_id=status["last_request_id"],
            last_selected_sentinel=status["last_selected_sentinel"],
        )
    except Exception as e:
        logger.error("Failed to get VRF status: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/request", response_model=VRFTieBreakResponse)
async def request_tie_breaker(request: VRFTieBreakRequest):
    """
    Request a VRF tie-breaker for the given sentinel IDs.

    This sends a VRF request on-chain. The result will be available
    once Chainlink VRF nodes fulfill the request (typically 1-5 minutes
    on testnet).
    """
    if len(request.sentinel_ids) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 sentinel IDs required for tie-breaker",
        )

    try:
        request_id, tie_breaker_id, tx_hash = request_vrf_tie_breaker(
            request.sentinel_ids
        )

        return VRFTieBreakResponse(
            request_id=str(request_id),
            tie_breaker_id=tie_breaker_id,
            tx_hash=tx_hash,
            sentinel_ids=request.sentinel_ids,
            status="pending",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("VRF request failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/request/{request_id}", response_model=VRFFulfillmentResponse)
async def get_vrf_fulfillment(request_id: str):
    """
    Check the fulfillment status of a VRF request.

    Returns the result if fulfilled, or pending status if not yet fulfilled.
    """
    try:
        request_id_int = int(request_id)
        result = check_vrf_fulfillment(request_id_int)

        if result is None:
            return VRFFulfillmentResponse(
                request_id=request_id,
                fulfilled=False,
                sentinel_ids=[],
            )

        return VRFFulfillmentResponse(
            request_id=request_id,
            fulfilled=result["fulfilled"],
            selected_sentinel_id=result["selected_sentinel_id"] if result["fulfilled"] else None,
            random_word=str(result["random_word"]) if result["fulfilled"] else None,
            sentinel_ids=result["sentinel_ids"],
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID")
    except Exception as e:
        logger.error("Failed to check VRF fulfillment: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tie-break/{tie_breaker_id}")
async def get_tie_break_result(tie_breaker_id: int):
    """
    Get the result of a tie-break by its ID.
    """
    try:
        service = get_vrf_service()
        result = service.get_tie_break_result(tie_breaker_id)

        return {
            "tie_breaker_id": result["tie_breaker_id"],
            "sentinel_ids": result["sentinel_ids"],
            "selected_sentinel_id": result["selected_sentinel_id"],
            "random_word": str(result["random_word"]),
            "fulfilled": result["fulfilled"],
        }
    except Exception as e:
        logger.error("Failed to get tie-break result: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/last-selected")
async def get_last_selected_sentinel():
    """Get the last sentinel selected by VRF."""
    try:
        service = get_vrf_service()
        sentinel_id = service.get_last_selected_sentinel()
        random_word = service.get_last_random_word()

        return {
            "selected_sentinel_id": sentinel_id,
            "last_random_word": str(random_word),
        }
    except Exception as e:
        logger.error("Failed to get last selected sentinel: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
