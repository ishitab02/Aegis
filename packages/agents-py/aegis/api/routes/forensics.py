"""Forensics routes."""

import logging

from fastapi import APIRouter, HTTPException

from aegis.blockchain.web3_client import get_web3
from aegis.models import ForensicReport, ForensicsRequest
from aegis.sherlock.chain_sherlock import analyze_trace, trace_transaction
from aegis.utils import now_seconds

logger = logging.getLogger(__name__)
router = APIRouter()

_reports: dict[str, ForensicReport] = {}

# Pre-computed demo reports
_DEMO_REPORTS: dict[str, dict] = {
    "euler": {
        "title": "Euler Finance Flash Loan Attack",
        "tx_hash": "0xc310a0affe2169d1f6feec1c63dbc7f7c62a887fa48795d327d4d2da2d6b111d",
        "block": 16818057,
        "chain": "ethereum",
        "date": "2023-03-13",
        "amount": "$197M",
        "attack_type": "Flash Loan + Donation Attack",
        "description": "Attacker used flash loans to inflate donation values in Euler's risk management system, enabling over-collateralized borrowing and subsequent liquidation attacks.",
        "status": "COMPLETE",
    }
}


@router.post("")
async def request_forensic_analysis(request: ForensicsRequest) -> dict:
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
    return {
        "reports": [
            {
                "id": r.report_id,
                "reportId": r.report_id,
                "txHash": r.tx_hash,
                "protocol": r.protocol,
                "attackType": r.attack_classification.primary_type,
                "severity": r.impact_assessment.severity.value,
                "timestamp": r.timestamp,
            }
            for r in _reports.values()
        ],
        "total": len(_reports),
    }


@router.get("/demo/euler")
async def get_euler_demo() -> dict:
    """Get pre-computed forensic analysis of the Euler Finance attack.

    This endpoint demonstrates ChainSherlock's forensic analysis capabilities
    using a real, historical exploit: the March 13, 2023 Euler Finance attack.

    Returns:
        Forensic report including transaction trace, attack classification,
        fund tracking, and vulnerability analysis.
    """
    euler_data = _DEMO_REPORTS.get("euler")
    if not euler_data:
        raise HTTPException(status_code=404, detail="Euler demo report not found")

    return {
        "status": "COMPLETE",
        "timestamp": now_seconds(),
        "attack": {
            "title": euler_data["title"],
            "description": euler_data["description"],
            "date": euler_data["date"],
            "chain": euler_data["chain"],
            "block": euler_data["block"],
            "tx_hash": euler_data["tx_hash"],
            "amount_lost": euler_data["amount"],
            "attack_type": euler_data["attack_type"],
        },
        "forensics": {
            "threat_level": "CRITICAL",
            "confidence": 0.98,
            "attack_classification": {
                "primary_type": "FLASH_LOAN",
                "secondary_types": ["PRICE_MANIPULATION", "LIQUIDATION_ATTACK"],
                "severity": "CRITICAL",
            },
            "attack_flow": [
                {
                    "step": 1,
                    "description": "Attacker initiates flash loan from Aave V2",
                    "contract": "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9",
                    "amount": "100 WETH",
                },
                {
                    "step": 2,
                    "description": "Donates borrowed tokens to inflate donation balances",
                    "contract": "0xeB401B738f45ea2c97A001c4e16F54e6e14Fa7A1",
                    "amount": "100 WETH",
                },
                {
                    "step": 3,
                    "description": "System recalculates collateral using inflated donation value",
                    "contract": "0xeB401B738f45ea2c97A001c4e16F54e6e14Fa7A1",
                    "effect": "Over-collateralized borrow becomes possible",
                },
                {
                    "step": 4,
                    "description": "Attacker borrows against inflated collateral",
                    "contract": "0xeB401B738f45ea2c97A001c4e16F54e6e14Fa7A1",
                    "amount": "~$100M in various tokens",
                },
                {
                    "step": 5,
                    "description": "Re-entry attack liquidates positions",
                    "contract": "0xeB401B738f45ea2c97A001c4e16F54e6e14Fa7A1",
                    "effect": "Extracts additional liquidation profits",
                },
                {
                    "step": 6,
                    "description": "Attacker receives flashed loan from Aave",
                    "contract": "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9",
                    "status": "Transaction completes, attacker retains ~$197M",
                },
            ],
            "fund_tracking": {
                "initial_stolen": "$197,000,000",
                "destinations": [
                    {
                        "address": "0xaeB38Cc649c4f839f6f0afBEb1b5c4F68caf42a4",
                        "label": "Attacker Wallet",
                        "type": "EOA",
                        "amount": "$10,000,000",
                        "confirmed": True,
                    },
                    {
                        "address": "0xD90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b",
                        "label": "Tornado Cash Router",
                        "type": "MIXER",
                        "amount": "$50,000,000",
                        "confirmed": True,
                    },
                    {
                        "address": "0xf977814e90da44bfa03b6295a0616a897441aceC",
                        "label": "Binance Hot Wallet",
                        "type": "CEX",
                        "amount": "$30,000,000",
                        "confirmed": True,
                    },
                    {
                        "address": "0xE41d2489571d7c5f551a221eae29612b01285cf5",
                        "label": "Uniswap Router",
                        "type": "DEX",
                        "amount": "$107,000,000",
                        "confirmed": True,
                    },
                ],
            },
            "vulnerability_classification": {
                "root_cause": "Validation Error",
                "cve_references": [],
                "affected_contracts": ["0xeB401B738f45ea2c97A001c4e16F54e6e14Fa7A1"],
                "vulnerability_description": "Euler's donation mechanism did not properly validate that donations could not be used to inflate collateral in the risk management system.",
                "attack_prerequisites": ["Flash loan access", "Understanding of donation mechanism"],
                "remediation": "Validate donation sources and implement proper collateral checks",
            },
        },
        "timeline": {
            "attack_start": "2023-03-13T11:22:35Z",
            "attack_end": "2023-03-13T11:28:15Z",
            "duration_seconds": 340,
            "discovery": "2023-03-13T12:00:00Z",
            "impact_hours_later": 1,
        },
        "references": {
            "block_explorer": "https://etherscan.io/tx/" + euler_data["tx_hash"],
            "postmortem": "https://blog.euler.finance/post-mortem-of-the-march-13-2023-incident",
            "analysis": "https://twitter.com/samczsun/status/1635059190976020481",
        },
    }

