"""Sentinel status endpoints."""

import logging

from fastapi import APIRouter, HTTPException

from aegis.models import SentinelType, ThreatAssessment, ThreatLevel
from aegis.utils import now_seconds

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory store of sentinel statuses (updated by detection cycles)
_sentinel_statuses: dict[str, dict] = {
    "liquidity-sentinel-0": {
        "id": "liquidity-sentinel-0",
        "type": SentinelType.LIQUIDITY,
        "status": "ACTIVE",
        "last_heartbeat": now_seconds(),
        "last_assessment": None,
    },
    "oracle-sentinel-0": {
        "id": "oracle-sentinel-0",
        "type": SentinelType.ORACLE,
        "status": "ACTIVE",
        "last_heartbeat": now_seconds(),
        "last_assessment": None,
    },
    "governance-sentinel-0": {
        "id": "governance-sentinel-0",
        "type": SentinelType.GOVERNANCE,
        "status": "ACTIVE",
        "last_heartbeat": now_seconds(),
        "last_assessment": None,
    },
}


_last_consensus: dict | None = None


def update_sentinel_assessment(assessment: ThreatAssessment) -> None:
    """Update a sentinel's status with its latest assessment."""
    sentinel_id = assessment.sentinel_id
    if sentinel_id in _sentinel_statuses:
        _sentinel_statuses[sentinel_id]["last_heartbeat"] = now_seconds()
        _sentinel_statuses[sentinel_id]["last_assessment"] = assessment.model_dump()


def update_consensus(consensus_data: dict) -> None:
    """Cache the latest consensus result for the aggregate endpoint."""
    global _last_consensus
    _last_consensus = consensus_data


@router.get("/aggregate")
async def get_sentinel_aggregate():
    """Get all sentinel assessments and consensus result.

    This is the primary endpoint the dashboard polls every 5 seconds.
    Returns assessments + consensus after a detection cycle has run.
    """
    assessments = [
        s["last_assessment"]
        for s in _sentinel_statuses.values()
        if s["last_assessment"] is not None
    ]

    return {
        "timestamp": now_seconds(),
        "assessments": assessments,
        "consensus": _last_consensus,
    }


@router.get("/{sentinel_id}")
async def get_sentinel_status(sentinel_id: str):
    """Get a single sentinel's status and latest assessment."""
    if sentinel_id not in _sentinel_statuses:
        raise HTTPException(status_code=404, detail=f"Sentinel {sentinel_id} not found")

    status = _sentinel_statuses[sentinel_id]
    return {
        "id": status["id"],
        "type": status["type"],
        "status": status["status"],
        "lastHeartbeat": status["last_heartbeat"],
        "assessment": status["last_assessment"],
    }
