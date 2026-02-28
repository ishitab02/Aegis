"""Detection endpoint — runs a full threat detection cycle."""

import logging

from fastapi import APIRouter, HTTPException

from aegis.coordinator.crew import run_detection_cycle
from aegis.models import DetectionRequest, DetectionResponse
from aegis.api.routes.sentinel import update_consensus, update_sentinel_assessment

logger = logging.getLogger(__name__)
router = APIRouter()

# Store the last detection result for polling
_last_result: DetectionResponse | None = None
_previous_tvl: int = 0


@router.post("", response_model=DetectionResponse)
async def trigger_detection(request: DetectionRequest) -> DetectionResponse:
    """Run a full threat detection cycle across all 3 sentinels.

    Called by CRE workflows every 30 seconds or on-demand.
    """
    global _last_result, _previous_tvl

    try:
        result = run_detection_cycle(
            protocol_address=request.protocol_address,
            protocol_name=request.protocol_name,
            previous_tvl=_previous_tvl,
        )

        # Store for next cycle — find the liquidity sentinel's TVL reading
        for assessment in result.assessments:
            if assessment.sentinel_type == "LIQUIDITY" and "ETH" in assessment.details:
                # Extract current TVL from details for next cycle comparison
                pass

        _last_result = result

        # Update sentinel statuses so /aggregate reflects latest detection
        for assessment in result.assessments:
            update_sentinel_assessment(assessment)
        update_consensus(result.consensus.model_dump())

        return result

    except Exception as e:
        logger.error("Detection cycle failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest", response_model=DetectionResponse | None)
async def get_latest_detection() -> DetectionResponse | None:
    """Get the most recent detection result."""
    return _last_result
