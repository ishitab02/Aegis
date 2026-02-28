"""ChainSherlock - AI forensic analyst for blockchain exploits.

Ported from packages/agents/src/sherlock/actions/traceTransaction.ts
"""

import logging
from typing import Any

from crewai import Agent
from web3 import Web3

from aegis.models import (
    AttackClassification,
    AttackStep,
    AttackType,
    ForensicReport,
    FundDestination,
    FundDestinationType,
    FundTracking,
    ImpactAssessment,
    InternalCall,
    RecoveryPossibility,
    RootCause,
    ThreatLevel,
    TokenTransfer,
    TransactionTrace,
)
from aegis.utils import generate_threat_id, now_seconds

logger = logging.getLogger(__name__)

# ERC-20 Transfer event topic
TRANSFER_TOPIC = Web3.keccak(text="Transfer(address,address,uint256)").hex()


def trace_transaction(tx_hash: str, w3: Web3) -> TransactionTrace:
    """Trace a transaction to extract the full call graph and token transfers."""
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    tx = w3.eth.get_transaction(tx_hash)

    # Try debug_traceTransaction for internal calls
    internal_calls: list[InternalCall] = []
    try:
        trace = w3.provider.make_request(
            "debug_traceTransaction",
            [tx_hash, {"tracer": "callTracer"}],
        )
        if "result" in trace:
            internal_calls = _parse_internal_calls(trace["result"])
    except Exception:
        logger.warning(
            "debug_traceTransaction not available, skipping internal call trace"
        )

    # Extract ERC-20 transfers from logs
    token_transfers = _extract_token_transfers(receipt.get("logs", []))

    return TransactionTrace(
        tx_hash=tx_hash,
        **{"from": tx["from"]},
        to=tx.get("to", "") or "",
        value=str(tx["value"]),
        gas_used=receipt["gasUsed"],
        internal_calls=internal_calls,
        token_transfers=token_transfers,
    )


def analyze_trace(trace: TransactionTrace, protocol_address: str) -> ForensicReport:
    """Analyze a transaction trace and produce a forensic report.

    This provides a rule-based classification. In production,
    Claude AI would be used for deeper analysis via the CrewAI agent.
    """
    # Classify attack type based on patterns
    attack_type = AttackType.OTHER
    description = "Unknown attack vector"
    attack_flow: list[AttackStep] = []

    # Check for reentrancy patterns (repeated calls to same address)
    call_targets = [c.to for c in trace.internal_calls]
    for target in set(call_targets):
        if call_targets.count(target) > 2:
            attack_type = AttackType.REENTRANCY
            description = (
                f"Reentrancy detected: {target} called {call_targets.count(target)} "
                f"times within a single transaction"
            )
            break

    # Check for flash loan patterns (large token transfers in/out)
    if len(trace.token_transfers) >= 4:
        first_transfer = trace.token_transfers[0]
        last_transfer = trace.token_transfers[-1]
        if (
            first_transfer.to == trace.from_address
            and last_transfer.from_address == trace.from_address
        ):
            attack_type = AttackType.FLASH_LOAN
            description = "Flash loan attack pattern detected"

    # Build attack flow
    for i, call in enumerate(trace.internal_calls[:10]):
        attack_flow.append(
            AttackStep(
                step=i + 1,
                action=f"{call.type} to {call.to[:10]}... value={call.value}",
                contract=call.to,
            )
        )

    # Estimate impact from token transfers
    total_value = sum(int(t.amount) for t in trace.token_transfers if t.amount.isdigit())

    # Track fund destinations
    destinations: list[FundDestination] = []
    seen_addresses: set[str] = set()
    for transfer in trace.token_transfers:
        if transfer.to not in seen_addresses and transfer.to != protocol_address:
            seen_addresses.add(transfer.to)
            destinations.append(
                FundDestination(
                    address=transfer.to,
                    amount=transfer.amount,
                    type=FundDestinationType.UNKNOWN,
                )
            )

    report_id = generate_threat_id(protocol_address, now_seconds(), trace.tx_hash)

    return ForensicReport(
        report_id=report_id,
        tx_hash=trace.tx_hash,
        protocol=protocol_address,
        attack_classification=AttackClassification(
            primary_type=attack_type,
            confidence=0.75,
            description=description,
        ),
        attack_flow=attack_flow,
        root_cause=RootCause(
            vulnerability=f"Potential {attack_type.value.lower().replace('_', ' ')} vulnerability",
            affected_code="See transaction trace for affected functions",
            recommendation="Implement reentrancy guards and validate all external calls",
        ),
        impact_assessment=ImpactAssessment(
            funds_at_risk=str(total_value),
            affected_users="Unknown",
            severity=ThreatLevel.HIGH,
        ),
        fund_tracking=FundTracking(
            destinations=destinations[:5],
            recovery_possibility=RecoveryPossibility.MEDIUM,
        ),
        timestamp=now_seconds(),
    )


def _parse_internal_calls(trace: dict[str, Any], depth: int = 0) -> list[InternalCall]:
    """Recursively parse internal calls from a call trace."""
    calls: list[InternalCall] = []

    if "calls" in trace:
        for call in trace["calls"]:
            calls.append(
                InternalCall(
                    **{"from": call.get("from", "")},
                    to=call.get("to", ""),
                    value=call.get("value", "0x0"),
                    input=call.get("input", ""),
                    output=call.get("output", ""),
                    type=call.get("type", "CALL"),
                    depth=depth,
                )
            )
            calls.extend(_parse_internal_calls(call, depth + 1))

    return calls


def _extract_token_transfers(logs: list[dict[str, Any]]) -> list[TokenTransfer]:
    """Extract ERC-20 token transfers from transaction logs."""
    transfers: list[TokenTransfer] = []

    for log in logs:
        topics = log.get("topics", [])
        if len(topics) >= 3:
            topic_hex = topics[0].hex() if isinstance(topics[0], bytes) else topics[0]
            if topic_hex == TRANSFER_TOPIC:
                from_topic = topics[1].hex() if isinstance(topics[1], bytes) else topics[1]
                to_topic = topics[2].hex() if isinstance(topics[2], bytes) else topics[2]
                data = log.get("data", "0x0")
                if isinstance(data, bytes):
                    data = data.hex()

                transfers.append(
                    TokenTransfer(
                        token=log["address"],
                        **{"from": Web3.to_checksum_address("0x" + from_topic[-40:])},
                        to=Web3.to_checksum_address("0x" + to_topic[-40:]),
                        amount=str(int(data, 16)) if data != "0x0" else "0",
                    )
                )

    return transfers


# ============ CrewAI Agent ============

_chain_sherlock: Agent | None = None


def get_chain_sherlock() -> Agent:
    """Lazy-load the CrewAI agent (requires LLM API key at runtime)."""
    global _chain_sherlock
    if _chain_sherlock is None:
        _chain_sherlock = Agent(
            role="ChainSherlock Forensic Analyst",
            goal=(
                "Perform real-time forensic analysis of blockchain exploits. "
                "Trace transaction call graphs, classify vulnerabilities, "
                "track stolen funds, and generate actionable reports."
            ),
            backstory=(
                "You are ChainSherlock, a meticulous, deductive, and thorough AI forensic "
                "analyst for blockchain exploits. You specialize in transaction graph analysis, "
                "vulnerability classification, fund tracking, and attack vector identification. "
                "You produce structured forensic reports that can be used by protocol teams "
                "and law enforcement to understand and respond to exploits."
            ),
            verbose=False,
            allow_delegation=False,
        )
    return _chain_sherlock
