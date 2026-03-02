"""Sentinel routes."""

import logging

from fastapi import APIRouter, HTTPException

from aegis.models import SentinelType, ThreatAssessment
from aegis.utils import now_seconds

logger = logging.getLogger(__name__)
router = APIRouter()

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
_last_protocol_name: str = "MockProtocol"
_last_protocol_address: str = ""


def update_sentinel_assessment(assessment: ThreatAssessment) -> None:
    sentinel_id = assessment.sentinel_id
    if sentinel_id in _sentinel_statuses:
        _sentinel_statuses[sentinel_id]["last_heartbeat"] = now_seconds()
        _sentinel_statuses[sentinel_id]["last_assessment"] = assessment.model_dump()


def update_consensus(consensus_data: dict) -> None:
    global _last_consensus
    _last_consensus = consensus_data


def update_protocol_info(name: str, address: str) -> None:
    global _last_protocol_name, _last_protocol_address
    _last_protocol_name = name
    _last_protocol_address = address


@router.get("/aggregate")
async def get_sentinel_aggregate():
    assessments = [
        s["last_assessment"]
        for s in _sentinel_statuses.values()
        if s["last_assessment"] is not None
    ]

    return {
        "timestamp": now_seconds(),
        "protocol_name": _last_protocol_name,
        "protocol_address": _last_protocol_address,
        "assessments": assessments,
        "consensus": _last_consensus,
    }


@router.get("/{sentinel_id}")
async def get_sentinel_status(sentinel_id: str):
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
