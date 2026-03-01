from aegis.sherlock.chain_sherlock import get_chain_sherlock, trace_transaction, analyze_trace
from aegis.sherlock.prompts import FORENSIC_ANALYSIS_PROMPT, REPORT_GENERATION_PROMPT
from aegis.sherlock.tracer import (
    AddressLabel,
    ArchiveNodeClient,
    ForensicTracer,
    GraphEdge,
    GraphNode,
    KNOWN_ADDRESSES,
    KNOWN_ATTACKERS,
    TraceResult,
    TransactionGraph,
    get_address_label,
    get_forensic_tracer,
    identify_address,
    is_known_attacker,
)

__all__ = [
    # chain_sherlock (legacy)
    "get_chain_sherlock",
    "trace_transaction",
    "analyze_trace",
    "FORENSIC_ANALYSIS_PROMPT",
    "REPORT_GENERATION_PROMPT",
    # tracer (new)
    "AddressLabel",
    "ArchiveNodeClient",
    "ForensicTracer",
    "GraphEdge",
    "GraphNode",
    "KNOWN_ADDRESSES",
    "KNOWN_ATTACKERS",
    "TraceResult",
    "TransactionGraph",
    "get_address_label",
    "get_forensic_tracer",
    "identify_address",
    "is_known_attacker",
]
