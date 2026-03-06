#!/usr/bin/env python3
"""Analyze the Euler Finance flash loan attack using ChainSherlock.

This script demonstrates the forensic analysis capabilities of the AEGIS Protocol
by analyzing a real historical exploit: the March 13, 2023 Euler Finance attack.

Attack Summary:
  - Date: March 13, 2023
  - Amount: ~$197M
  - Method: Flash loan + donation inflation + liquidation attack
  - TX: 0xc310a0affe2169d1f6feec1c63dbc7f7c62a887fa48795d327d4d2da2d6b111d
  - Block: 16818057 (Ethereum mainnet)

Usage:
  python scripts/analyze-euler-hack.py [--archive-rpc URL] [--output FILE]

Examples:
  # Use default Ethereum RPC
  python scripts/analyze-euler-hack.py

  # Use Alchemy archive node
  python scripts/analyze-euler-hack.py --archive-rpc https://eth-mainnet.alchemyapi.io/v2/YOUR_KEY

  # Save to JSON file
  python scripts/analyze-euler-hack.py --output euler-analysis.json
"""

import asyncio
import json
import logging
import sys
from argparse import ArgumentParser
from pathlib import Path

from web3 import Web3

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from aegis.sherlock.tracer import ForensicTracer, ArchiveNodeConfig
from aegis.sherlock.chain_sherlock import analyze_trace

logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Euler Finance attack details
EULER_TX = "0xc310a0affe2169d1f6feec1c63dbc7f7c62a887fa48795d327d4d2da2d6b111d"
EULER_BLOCK = 16818057
EULER_POOL = "0xeB401B738f45ea2c97A001c4e16F54e6e14Fa7A1"

# RPC endpoints
DEFAULT_RPC = "https://eth.drpc.org"
DEFAULT_ALCHEMY_RPC = "https://eth-mainnet.alchemyapi.io/v2/demo"


async def analyze_euler_attack(archive_rpc: str | None = None) -> dict:
    """Analyze the Euler Finance attack using archive node data.

    Args:
        archive_rpc: RPC URL with debug_traceTransaction support

    Returns:
        Forensic analysis report
    """
    # Setup RPC connection
    rpc_url = archive_rpc or DEFAULT_RPC
    logger.info(f"Connecting to RPC: {rpc_url}")

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        logger.error("Failed to connect to RPC provider")
        return {"error": "RPC connection failed"}

    # Check if archive node supports tracing
    try:
        block = w3.eth.get_block(EULER_BLOCK)
        logger.info(f"Connected to block: {block.number} ({block.timestamp})")
    except Exception as e:
        logger.error(f"Failed to fetch block: {e}")
        return {"error": f"Block fetch failed: {e}"}

    # Setup forensic tracer with archive node
    config = ArchiveNodeConfig(rpc_url=rpc_url)
    tracer = ForensicTracer(w3)

    logger.info(f"Analyzing transaction: {EULER_TX}")
    logger.info(f"Protocol: Euler Finance (0x{EULER_POOL})")

    try:
        # Trace the transaction
        logger.info("Tracing transaction flow...")
        trace = await tracer.trace_transaction(EULER_TX)
        logger.info(f"Transaction traced: {len(trace.internal_calls)} internal calls")

        # Analyze the trace
        logger.info("Analyzing trace for attack patterns...")
        report = analyze_trace(trace, EULER_POOL)
        logger.info(f"Attack classified as: {report.attack_classification.primary_type}")

        # Build transaction graph
        logger.info("Building transaction graph...")
        graph = await tracer.build_transaction_graph(EULER_TX)
        logger.info(f"Graph built: {len(graph.nodes)} nodes, {len(graph.edges)} edges")

        # Generate summary
        summary = {
            "status": "COMPLETE",
            "attack": {
                "tx_hash": EULER_TX,
                "block": EULER_BLOCK,
                "protocol": "Euler Finance",
                "protocol_address": EULER_POOL,
                "date": "2023-03-13",
                "amount_lost": "$197,000,000",
            },
            "forensics": {
                "attack_type": report.attack_classification.primary_type,
                "severity": report.impact_assessment.severity.value,
                "confidence": report.confidence_score,
                "internal_calls": len(trace.internal_calls),
                "token_transfers": len(trace.token_transfers),
            },
            "transaction_graph": {
                "nodes": len(graph.nodes),
                "edges": len(graph.edges),
                "top_accounts": [
                    {
                        "address": node.address,
                        "label": node.label,
                        "inbound_value": node.inbound_value,
                        "outbound_value": node.outbound_value,
                    }
                    for node in sorted(
                        graph.nodes,
                        key=lambda n: n.inbound_value + n.outbound_value,
                        reverse=True,
                    )[:10]
                ],
            },
            "report": report.model_dump(),
        }

        logger.info("Analysis complete!")
        return summary

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return {"error": f"Analysis failed: {e}"}


def main():
    """Main entry point."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive-rpc",
        help=f"Archive node RPC URL (default: {DEFAULT_RPC})",
        type=str,
    )
    parser.add_argument(
        "--output",
        help="Output JSON file",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--verbose",
        help="Enable verbose logging",
        action="store_true",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run analysis
    logger.info("=" * 70)
    logger.info("AEGIS ChainSherlock — Euler Finance Attack Analysis")
    logger.info("=" * 70)
    logger.info("")

    result = asyncio.run(analyze_euler_attack(archive_rpc=args.archive_rpc))

    # Output results
    if "error" in result:
        logger.error(f"Error: {result['error']}")
        print(json.dumps(result, indent=2))
        return 1

    # Print summary
    attack = result["attack"]
    forensics = result["forensics"]

    print("")
    print(f"Attack: {attack['protocol']}")
    print(f"  TX: {attack['tx_hash']}")
    print(f"  Block: {attack['block']}")
    print(f"  Date: {attack['date']}")
    print(f"  Amount Lost: {attack['amount_lost']}")
    print("")
    print("Forensic Analysis:")
    print(f"  Attack Type: {forensics['attack_type']}")
    print(f"  Severity: {forensics['severity']}")
    print(f"  Confidence: {forensics['confidence']:.1%}")
    print(f"  Internal Calls: {forensics['internal_calls']}")
    print(f"  Token Transfers: {forensics['token_transfers']}")
    print("")
    print("Transaction Graph:")
    graph = result["transaction_graph"]
    print(f"  Nodes: {graph['nodes']}")
    print(f"  Edges: {graph['edges']}")
    print("")

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(result, indent=2))
        logger.info(f"Results saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
