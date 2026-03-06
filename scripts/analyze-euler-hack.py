#!/usr/bin/env python3
"""Analyze the Euler Finance hack (March 13, 2023).

This script demonstrates ChainSherlock analyzing a real historical exploit:
  TX:    0xc310a0affe2169d1f6feec1c63dbc7f7c62a887fa48795d327d4d2da2d6b111d
  Block: 16818057
  Loss:  ~$197M (DAI, USDC, USDT, WBTC, wstETH, stETH)

Usage:
    # With archive node (full trace):
    ALCHEMY_API_KEY=your-key python scripts/analyze-euler-hack.py

    # Without archive node (uses pre-computed report + on-chain receipt):
    python scripts/analyze-euler-hack.py

    # Quick mode — pre-computed report only, no RPC calls:
    python scripts/analyze-euler-hack.py --quick
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time

# Add the agents-py package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "agents-py"))

from aegis.models import (
    AttackType,
    ForensicReport,
)
from aegis.sherlock.chain_sherlock import analyze_trace
from aegis.sherlock.euler_analysis import (
    EULER_ATTACK_FLOW,
    EULER_ATTACKER_CONTRACT,
    EULER_ATTACKER_EOA,
    EULER_BLOCK,
    EULER_PROTOCOL,
    EULER_STOLEN_TOKENS,
    EULER_TRANSACTION_GRAPH,
    EULER_TX_HASH,
    get_euler_forensic_report,
)
from aegis.sherlock.tracer import (
    ForensicTracer,
    get_archive_web3,
    has_archive_node,
    identify_address,
)
from aegis.utils import short_address

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("euler-analysis")

# ── Formatting helpers ────────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
DIM = "\033[2m"


def header(text: str) -> None:
    print(f"\n{BOLD}{CYAN}{'═' * 70}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 70}{RESET}")


def subheader(text: str) -> None:
    print(f"\n{BOLD}{YELLOW}── {text} {'─' * max(0, 60 - len(text))}{RESET}")


def info(label: str, value: str) -> None:
    print(f"  {BOLD}{label}:{RESET} {value}")


def step_line(num: int, action: str, detail: str = "") -> None:
    print(f"  {BOLD}{GREEN}[Step {num}]{RESET} {action}")
    if detail:
        print(f"           {DIM}{detail}{RESET}")


def warn_line(text: str) -> None:
    print(f"  {YELLOW}⚠ {text}{RESET}")


def alert_line(text: str) -> None:
    print(f"  {RED}🚨 {text}{RESET}")


# ── Pre-computed analysis ─────────────────────────────────────────────

def print_precomputed_report() -> ForensicReport:
    """Print the pre-computed Euler forensic report."""
    report = get_euler_forensic_report()

    header("AEGIS ChainSherlock — Euler Finance Exploit Analysis")

    subheader("Exploit Summary")
    info("Transaction", EULER_TX_HASH)
    info("Block", str(EULER_BLOCK))
    info("Date", "March 13, 2023")
    info("Protocol", f"Euler Finance ({short_address(EULER_PROTOCOL)})")
    info("Attacker EOA", f"{short_address(EULER_ATTACKER_EOA)}")
    info("Attack Contract", f"{short_address(EULER_ATTACKER_CONTRACT)}")
    info("Total Stolen", f"~${EULER_STOLEN_TOKENS and sum(t['amount'] for t in EULER_STOLEN_TOKENS.values()):,.2f} USD (~$197M)")
    info("Attack Type", f"{RED}{report.attack_classification.primary_type.value}{RESET}")
    info("Confidence", f"{report.attack_classification.confidence:.0%}")
    info("Severity", f"{RED}CRITICAL{RESET}")

    subheader("Tokens Drained")
    for token, data in EULER_STOLEN_TOKENS.items():
        print(f"  • {BOLD}{token:8s}{RESET}: {data['amount']:>15,.2f}  ({short_address(data['address'])})")

    subheader("Attack Flow (9 Steps)")
    for step_data in EULER_ATTACK_FLOW:
        step_line(
            step_data["step"],
            str(step_data["action"]),
            str(step_data.get("detail", "")),
        )

    subheader("Root Cause")
    print(f"  {report.root_cause.vulnerability[:200]}...")
    print()
    info("Affected Code", report.root_cause.affected_code)

    subheader("Recommendations")
    for line in report.root_cause.recommendation.split("\n"):
        print(f"  {line.strip()}")

    subheader("Fund Tracking")
    recovery = EULER_TRANSACTION_GRAPH["fund_recovery"]
    info("Funds Returned", f"{GREEN}Yes{RESET} ({recovery['percent_returned']}%)")
    info("Return Date", str(recovery["return_date"]))
    info("Notes", str(recovery["notes"][:120]) + "...")

    subheader("Patterns Detected")
    for pattern in EULER_TRANSACTION_GRAPH["patterns_detected"]:
        print(f"  • {BOLD}{pattern['type']}{RESET}: confidence {pattern['confidence']:.0%}")
        if "detail" in pattern:
            print(f"    {DIM}{pattern['detail']}{RESET}")

    subheader("Risk Indicators")
    for indicator in EULER_TRANSACTION_GRAPH["risk_indicators"]:
        alert_line(f"{indicator['type']} — {indicator['detail']}")

    return report


# ── Live trace (requires archive node) ───────────────────────────────

async def run_live_trace() -> ForensicReport | None:
    """Trace the Euler hack transaction on a real archive node."""
    if not has_archive_node():
        warn_line("No archive node configured. Set ALCHEMY_API_KEY for live tracing.")
        return None

    subheader("Live Archive Node Trace")
    w3 = get_archive_web3("mainnet")

    if not w3.is_connected():
        warn_line("Cannot connect to archive node.")
        return None

    info("Connected", f"Chain ID {w3.eth.chain_id}")
    info("Latest Block", str(w3.eth.block_number))

    tracer = ForensicTracer(w3)

    print(f"\n  Tracing {short_address(EULER_TX_HASH)}...")
    start_time = time.time()

    try:
        result = await tracer.trace_with_graph(EULER_TX_HASH, EULER_PROTOCOL)
        elapsed = time.time() - start_time
        info("Trace Time", f"{elapsed:.2f}s")

        trace = result.trace
        graph = result.graph
        analysis = result.analysis

        subheader("On-Chain Trace Results")
        info("From", trace.from_address)
        info("To", trace.to)
        info("Value", f"{int(trace.value) / 10**18:.4f} ETH")
        info("Gas Used", f"{trace.gas_used:,}")
        info("Internal Calls", str(len(trace.internal_calls)))
        info("Token Transfers", str(len(trace.token_transfers)))

        subheader("Transaction Graph")
        info("Nodes", str(len(graph.nodes)))
        info("Edges", str(len(graph.edges)))
        info("Attacker Addresses Found", str(len(graph.attacker_addresses)))
        info("Known Destinations", str(len(graph.known_destinations)))

        if graph.attacker_addresses:
            print()
            for addr in graph.attacker_addresses:
                name, _, _ = identify_address(addr)
                alert_line(f"ATTACKER: {short_address(addr)} — {name}")

        if graph.known_destinations:
            print()
            for addr, name, label in graph.known_destinations[:10]:
                print(f"  • {label.value:20s} {short_address(addr)} — {name}")

        subheader("Analysis")
        patterns = analysis.get("patterns_detected", [])
        for p in patterns:
            info(p["type"], f"confidence {p.get('confidence', 'N/A')}")

        fund_summary = analysis.get("fund_flow_summary", {})
        if fund_summary:
            info("Total ETH Moved", f"{fund_summary.get('total_eth_formatted', 0):.4f} ETH")
            info("Unique Addresses", str(fund_summary.get("unique_addresses", 0)))
            info("Total Transfers", str(fund_summary.get("total_transfers", 0)))

        # Generate a proper ForensicReport from the live trace
        report = analyze_trace(trace, EULER_PROTOCOL)
        return report

    except Exception as e:
        logger.error("Live trace failed: %s", e, exc_info=True)
        warn_line(f"Live trace failed: {e}")
        return None


# ── Main ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="AEGIS ChainSherlock — Euler Finance Exploit Analysis"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Skip live tracing, use pre-computed report only",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the report as JSON instead of formatted text",
    )
    args = parser.parse_args()

    # Always print the pre-computed report
    report = print_precomputed_report()

    if args.json:
        subheader("JSON Report")
        print(json.dumps(report.model_dump(), indent=2, default=str))
        return

    # Attempt live trace if not in quick mode and archive node available
    if not args.quick:
        live_report = asyncio.run(run_live_trace())
        if live_report:
            subheader("Live Trace ForensicReport")
            info("Attack Type", live_report.attack_classification.primary_type.value)
            info("Confidence", f"{live_report.attack_classification.confidence:.0%}")
            info("Severity", live_report.impact_assessment.severity.value)

    header("Analysis Complete")
    print(f"  {GREEN}✓{RESET} Pre-computed Euler Finance report generated")
    if not args.quick and has_archive_node():
        print(f"  {GREEN}✓{RESET} Live archive node trace completed")
    elif not args.quick:
        print(f"  {YELLOW}○{RESET} Live trace skipped (no ALCHEMY_API_KEY)")
    else:
        print(f"  {DIM}○ Live trace skipped (--quick mode){RESET}")
    print(f"\n  Report ID: {report.report_id}")
    print(f"  View in AEGIS: GET /api/v1/forensics/demo/euler\n")


if __name__ == "__main__":
    main()
