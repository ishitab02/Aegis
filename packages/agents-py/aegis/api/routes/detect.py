"""Detection routes."""

import logging
import time

from fastapi import APIRouter, HTTPException

from aegis.api.routes.sentinel import (
    update_consensus,
    update_protocol_info,
    update_sentinel_assessment,
)
from aegis.coordinator.crew import (
    get_all_live_monitor_data,
    get_live_monitor_data,
    run_detection_cycle,
)
from aegis.models import DetectionRequest, DetectionResponse

logger = logging.getLogger(__name__)
router = APIRouter()

_last_result: DetectionResponse | None = None
_previous_tvl: int = 0


@router.post("", response_model=DetectionResponse)
async def trigger_detection(request: DetectionRequest) -> DetectionResponse:
    global _last_result, _previous_tvl

    try:
        result = run_detection_cycle(
            protocol_address=request.protocol_address,
            protocol_name=request.protocol_name,
            previous_tvl=_previous_tvl,
            simulate_tvl_drop_percent=request.simulate_tvl_drop_percent,
            simulate_price_deviation_percent=request.simulate_price_deviation_percent,
            simulate_short_voting_period=request.simulate_short_voting_period,
            live_mode=request.live_mode,
            use_vrf_on_tie=request.use_vrf_on_tie,
        )

        for assessment in result.assessments:
            if assessment.sentinel_type == "LIQUIDITY" and "ETH" in assessment.details:
                pass

        _last_result = result

        for assessment in result.assessments:
            update_sentinel_assessment(assessment)
        update_consensus(result.consensus.model_dump())
        update_protocol_info(request.protocol_name, request.protocol_address)

        return result

    except Exception as e:
        logger.error("Detection cycle failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest", response_model=DetectionResponse | None)
async def get_latest_detection() -> DetectionResponse | None:
    return _last_result


# ------------------------------------------------------------------
# Live monitoring endpoints
# ------------------------------------------------------------------

# Default Aave V3 Pool on Base
AAVE_V3_BASE = "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"


@router.get("/monitor/aave")
async def get_live_aave_monitor():
    """Return live Aave V3 monitoring data.

    Triggers a live_mode detection cycle against the Aave V3 pool on Base
    and returns enriched TVL / price / anomaly data for the frontend.
    """
    try:
        # Run a quick live-mode cycle to refresh data
        run_detection_cycle(
            protocol_address=AAVE_V3_BASE,
            protocol_name="Aave V3 (Base)",
            live_mode=True,
        )

        data = get_live_monitor_data(AAVE_V3_BASE)
        if data is None:
            return {
                "protocol_address": AAVE_V3_BASE,
                "protocol_name": "Aave V3 (Base)",
                "status": "unavailable",
                "message": "Live data not yet available. Adapter may not be reachable.",
                "timestamp": int(time.time()),
            }

        return data

    except Exception as e:
        logger.error("Live Aave monitor failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitor/{protocol_address}")
async def get_live_protocol_monitor(protocol_address: str):
    """Return cached live monitoring data for any protocol."""
    data = get_live_monitor_data(protocol_address)
    if data is None:
        return {
            "protocol_address": protocol_address,
            "status": "unavailable",
            "message": "No live data for this protocol. Run a live_mode detection first.",
            "timestamp": int(time.time()),
        }
    return data


@router.get("/monitor")
async def list_live_monitors():
    """Return all actively-monitored protocols."""
    return {
        "protocols": get_all_live_monitor_data(),
        "timestamp": int(time.time()),
    }
