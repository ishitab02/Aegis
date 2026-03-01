"""Forensics endpoints — trigger and retrieve forensic reports."""

import logging

from fastapi import APIRouter, HTTPException

from aegis.blockchain.web3_client import get_web3
from aegis.models import ForensicReport, ForensicsRequest
from aegis.sherlock.chain_sherlock import analyze_trace, trace_transaction
from aegis.utils import now_seconds

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory store of forensic reports
_reports: dict[str, ForensicReport] = {}


@router.post("")
async def request_forensic_analysis(request: ForensicsRequest) -> dict:
    """Request a forensic analysis for a transaction.

    Called by CRE forensic workflow or TypeScript API (with x402 payment).
    """
    try:
        w3 = get_web3()

        # Trace the transaction
        logger.info("Tracing transaction %s...", request.tx_hash)
        trace = trace_transaction(request.tx_hash, w3)

        # Analyze the trace
        logger.info("Analyzing trace for %s...", request.tx_hash)
        report = analyze_trace(trace, request.protocol)

        # Store the report
        _reports[report.report_id] = report

        return {
            "reportId": report.report_id,
            "status": "COMPLETE",
            "timestamp": now_seconds(),
            "report": report.model_dump(),
        }

    except Exception as e:
        logger.error("Forensic analysis failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}")
async def get_forensic_report(report_id: str) -> dict:
    """Get a forensic report by ID."""
    report = _reports.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    return {
        "reportId": report.report_id,
        "status": "COMPLETE",
        "report": report.model_dump(),
    }


@router.get("")
async def list_forensic_reports() -> dict:
    """List all forensic reports."""
    return {
        "reports": [
            {
                "reportId": r.report_id,
                "txHash": r.tx_hash,
                "protocol": r.protocol,
                "attackType": r.attack_classification.primary_type,
                "timestamp": r.timestamp,
            }
            for r in _reports.values()
        ],
        "total": len(_reports),
    }
