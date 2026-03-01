"""Real Forensics Engine - Advanced transaction tracing and fund flow analysis.

This module provides production-grade forensic capabilities:
- Archive node connection with debug_traceTransaction support
- Deep internal call tracing with full call stack
- Transaction graph building for money movement visualization
- Known attacker address identification
- Multi-hop fund tracking
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field
from web3 import Web3

from aegis.models import (
    FundDestination,
    FundDestinationType,
    InternalCall,
    TokenTransfer,
    TransactionTrace,
)

if TYPE_CHECKING:
    from web3.types import TxReceipt

logger = logging.getLogger(__name__)

# ============ Known Addresses Database ============


class AddressLabel(str, Enum):
    """Labels for known addresses."""

    ATTACKER = "ATTACKER"
    CEX = "CEX"
    DEX = "DEX"
    MIXER = "MIXER"
    BRIDGE = "BRIDGE"
    FLASHLOAN_PROVIDER = "FLASHLOAN_PROVIDER"
    MEV_BOT = "MEV_BOT"
    CONTRACT = "CONTRACT"
    EOA = "EOA"
    UNKNOWN = "UNKNOWN"


# Known addresses database (expandable)
# In production, this would be fetched from an API like Etherscan labels
KNOWN_ADDRESSES: dict[str, tuple[str, AddressLabel]] = {
    # Mixers
    "0xD90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b": ("Tornado Cash Router", AddressLabel.MIXER),
    "0x722122dF12D4e14e13Ac3b6895a86e84145b6967": ("Tornado Cash 0.1 ETH", AddressLabel.MIXER),
    "0xDD4c48C0B24039969fC16D1cdF626eaB821d3384": ("Tornado Cash 1 ETH", AddressLabel.MIXER),
    "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b": ("Tornado Cash", AddressLabel.MIXER),
    # CEXs
    "0x28C6c06298d514Db089934071355E5743bf21d60": ("Binance 14", AddressLabel.CEX),
    "0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549": ("Binance 15", AddressLabel.CEX),
    "0xDFd5293D8e347dFe59E90eFd55b2956a1343963d": ("Binance 16", AddressLabel.CEX),
    "0x56Eddb7aa87536c09CCc2793473599fD21A8b17F": ("Binance 17", AddressLabel.CEX),
    "0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43": ("Coinbase 10", AddressLabel.CEX),
    "0x71660c4005BA85c37ccec55d0C4493E66Fe775d3": ("Coinbase 11", AddressLabel.CEX),
    "0x503828976D22510aad0201ac7EC88293211D23Da": ("Coinbase 2", AddressLabel.CEX),
    "0xddfAbCdc4D8FfC6d5beaf154f18B778f892A0740": ("Coinbase 3", AddressLabel.CEX),
    "0x3cD751E6b0078Be393132286c442345e5DC49699": ("Coinbase 4", AddressLabel.CEX),
    "0xb5d85CBf7cB3EE0D56b3bB207D5Fc4B82f43F511": ("Coinbase 5", AddressLabel.CEX),
    "0xEB2629a2734e272Bcc07BDA959863f316F4bD4Cf": ("Coinbase 6", AddressLabel.CEX),
    # Flash Loan Providers
    "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9": ("Aave V2 Pool", AddressLabel.FLASHLOAN_PROVIDER),
    "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2": ("Aave V3 Pool", AddressLabel.FLASHLOAN_PROVIDER),
    "0xBA12222222228d8Ba445958a75a0704d566BF2C8": ("Balancer Vault", AddressLabel.FLASHLOAN_PROVIDER),
    # DEXs
    "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D": ("Uniswap V2 Router", AddressLabel.DEX),
    "0xE592427A0AEce92De3Edee1F18E0157C05861564": ("Uniswap V3 Router", AddressLabel.DEX),
    "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45": ("Uniswap Universal Router", AddressLabel.DEX),
    "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F": ("SushiSwap Router", AddressLabel.DEX),
    "0x1111111254fb6c44bAC0beD2854e76F90643097d": ("1inch Router V4", AddressLabel.DEX),
    "0x1111111254EEB25477B68fb85Ed929f73A960582": ("1inch Router V5", AddressLabel.DEX),
    # Bridges
    "0x3ee18B2214AFF97000D974cf647E7C347E8fa585": ("Wormhole Portal", AddressLabel.BRIDGE),
    "0x99C9fc46f92E8a1c0deC1b1747d010903E884bE1": ("Optimism Bridge", AddressLabel.BRIDGE),
    "0x4Dbd4fc535Ac27206064B68FfCf827b0A60BAB3f": ("Arbitrum Bridge", AddressLabel.BRIDGE),
    "0x8315177aB297bA92A06054cE80a67Ed4DBd7ed3a": ("Arbitrum Bridge 2", AddressLabel.BRIDGE),
}

# Known attacker addresses (from past exploits)
KNOWN_ATTACKERS: dict[str, str] = {
    "0x9799b475dEc92Bd99bbdD943013325C36157f383": "Euler Exploiter",
    "0xE8f3540E7aE78a98a40B73a1e31C1Db7D9916a57": "Wintermute Exploiter",
    "0x148c05caf1Bb09B5670f00D511718f733C54bC4c": "Transit Finance Exploiter",
    "0xed3eD8BDb95419d4FA68B59d0a6Ac3C4A9cDF89A": "Nomad Exploiter",
    "0xB3764761E297D6f121e79C32A65829Cd1dDb4D32": "Ronin Exploiter",
}


# ============ Transaction Graph Models ============


class GraphNode(BaseModel):
    """A node in the transaction graph (an address)."""

    address: str
    label: AddressLabel = AddressLabel.UNKNOWN
    label_name: str = ""
    is_contract: bool = False
    is_attacker: bool = False
    total_received: int = 0
    total_sent: int = 0
    first_seen_block: int = 0


class GraphEdge(BaseModel):
    """An edge in the transaction graph (a transfer)."""

    from_address: str
    to_address: str
    value: int
    token: str = "ETH"  # ETH or token address
    token_symbol: str = "ETH"
    tx_hash: str
    block_number: int
    log_index: int = 0


class TransactionGraph(BaseModel):
    """A graph representing fund flows in a transaction or series of transactions."""

    nodes: dict[str, GraphNode] = Field(default_factory=dict)
    edges: list[GraphEdge] = Field(default_factory=list)
    root_tx: str = ""
    protocol_address: str = ""
    total_value_moved: int = 0
    attacker_addresses: list[str] = Field(default_factory=list)
    known_destinations: list[tuple[str, str, AddressLabel]] = Field(default_factory=list)


class TraceResult(BaseModel):
    """Complete result of a forensic trace."""

    trace: TransactionTrace
    graph: TransactionGraph
    analysis: dict[str, Any] = Field(default_factory=dict)
    timestamp: int = 0


# ============ Archive Node Connection ============


@dataclass
class ArchiveNodeConfig:
    """Configuration for archive node connection."""

    rpc_url: str
    supports_debug_trace: bool = True
    supports_trace_block: bool = False  # Parity/OpenEthereum style
    max_trace_depth: int = 100
    timeout_seconds: int = 30


class ArchiveNodeClient:
    """Client for interacting with archive nodes that support debug_traceTransaction."""

    def __init__(self, web3: Web3, config: ArchiveNodeConfig | None = None):
        self._web3 = web3
        self._config = config or ArchiveNodeConfig(
            rpc_url=str(web3.provider.endpoint_uri) if hasattr(web3.provider, 'endpoint_uri') else "",
            supports_debug_trace=True,
        )
        self._trace_support_checked = False
        self._has_trace_support = False

    @property
    def web3(self) -> Web3:
        return self._web3

    async def check_trace_support(self) -> bool:
        """Check if the connected node supports debug_traceTransaction."""
        if self._trace_support_checked:
            return self._has_trace_support

        try:
            # Try a simple trace on a known transaction
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._web3.provider.make_request(
                    "debug_traceTransaction",
                    ["0x" + "0" * 64, {"tracer": "callTracer"}],
                ),
            )
            # If we get an error about the tx not found, trace is supported
            self._has_trace_support = "error" in result and "not found" in str(result.get("error", "")).lower()
            if not self._has_trace_support:
                # Check if it's a valid response
                self._has_trace_support = "result" in result
        except Exception as e:
            logger.debug("Trace support check failed: %s", e)
            self._has_trace_support = False

        self._trace_support_checked = True
        logger.info("Archive node trace support: %s", self._has_trace_support)
        return self._has_trace_support

    async def trace_transaction(self, tx_hash: str) -> dict[str, Any]:
        """Execute debug_traceTransaction with callTracer."""
        loop = asyncio.get_event_loop()

        try:
            result = await loop.run_in_executor(
                None,
                lambda: self._web3.provider.make_request(
                    "debug_traceTransaction",
                    [tx_hash, {"tracer": "callTracer", "timeout": f"{self._config.timeout_seconds}s"}],
                ),
            )

            if "error" in result:
                raise ValueError(f"Trace failed: {result['error']}")

            return result.get("result", {})

        except Exception as e:
            logger.warning("debug_traceTransaction failed for %s: %s", tx_hash, e)
            return {}

    async def get_transaction_receipt(self, tx_hash: str) -> TxReceipt:
        """Get transaction receipt."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._web3.eth.get_transaction_receipt(tx_hash),
        )

    async def get_transaction(self, tx_hash: str) -> dict[str, Any]:
        """Get transaction details."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: dict(self._web3.eth.get_transaction(tx_hash)),
        )

    async def is_contract(self, address: str) -> bool:
        """Check if an address is a contract."""
        loop = asyncio.get_event_loop()
        try:
            code = await loop.run_in_executor(
                None,
                lambda: self._web3.eth.get_code(self._web3.to_checksum_address(address)),
            )
            return len(code) > 2  # "0x" is empty
        except Exception:
            return False

    async def get_block_number(self) -> int:
        """Get current block number."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._web3.eth.block_number)


# ============ Forensic Tracer ============


class ForensicTracer:
    """Advanced forensic tracer for blockchain transactions.

    Capabilities:
    - Deep transaction tracing with full call stack
    - Transaction graph building for fund flow visualization
    - Known address identification (CEX, DEX, mixers, attackers)
    - Multi-hop fund tracking
    """

    # ERC-20 Transfer event topic
    TRANSFER_TOPIC = Web3.keccak(text="Transfer(address,address,uint256)").hex()

    def __init__(self, web3: Web3):
        self._client = ArchiveNodeClient(web3)
        self._web3 = web3

    @property
    def web3(self) -> Web3:
        return self._web3

    def identify_address(self, address: str) -> tuple[str, AddressLabel, bool]:
        """Identify a known address.

        Returns:
            Tuple of (label_name, label_type, is_attacker)
        """
        address_lower = address.lower()
        address_checksum = self._web3.to_checksum_address(address)

        # Check known attackers first
        if address_checksum in KNOWN_ATTACKERS:
            return KNOWN_ATTACKERS[address_checksum], AddressLabel.ATTACKER, True
        if address_lower in KNOWN_ATTACKERS:
            return KNOWN_ATTACKERS[address_lower], AddressLabel.ATTACKER, True

        # Check known addresses
        if address_checksum in KNOWN_ADDRESSES:
            name, label = KNOWN_ADDRESSES[address_checksum]
            return name, label, False
        if address_lower in KNOWN_ADDRESSES:
            name, label = KNOWN_ADDRESSES[address_lower]
            return name, label, False

        return "", AddressLabel.UNKNOWN, False

    async def trace_transaction(self, tx_hash: str) -> TransactionTrace:
        """Trace a transaction to extract the full call graph and token transfers."""
        # Get basic transaction data
        tx, receipt = await asyncio.gather(
            self._client.get_transaction(tx_hash),
            self._client.get_transaction_receipt(tx_hash),
        )

        # Try to get internal calls via debug_traceTransaction
        internal_calls: list[InternalCall] = []
        if await self._client.check_trace_support():
            trace_result = await self._client.trace_transaction(tx_hash)
            if trace_result:
                internal_calls = self._parse_internal_calls(trace_result)

        # Extract ERC-20 transfers from logs
        token_transfers = self._extract_token_transfers(receipt.get("logs", []))

        return TransactionTrace(
            tx_hash=tx_hash,
            **{"from": tx["from"]},
            to=tx.get("to", "") or "",
            value=str(tx["value"]),
            gas_used=receipt["gasUsed"],
            internal_calls=internal_calls,
            token_transfers=token_transfers,
        )

    async def build_transaction_graph(
        self,
        tx_hash: str,
        protocol_address: str = "",
        max_hops: int = 3,
    ) -> TransactionGraph:
        """Build a transaction graph showing fund flows.

        Args:
            tx_hash: Transaction hash to analyze
            protocol_address: Address of the affected protocol
            max_hops: Maximum number of hops to trace (for multi-tx tracking)

        Returns:
            TransactionGraph with nodes (addresses) and edges (transfers)
        """
        trace = await self.trace_transaction(tx_hash)
        receipt = await self._client.get_transaction_receipt(tx_hash)
        block_number = receipt["blockNumber"]

        graph = TransactionGraph(
            root_tx=tx_hash,
            protocol_address=protocol_address,
        )

        # Add sender as first node
        sender = trace.from_address
        sender_label, sender_type, sender_is_attacker = self.identify_address(sender)
        graph.nodes[sender] = GraphNode(
            address=sender,
            label=sender_type,
            label_name=sender_label,
            is_contract=await self._client.is_contract(sender),
            is_attacker=sender_is_attacker,
            first_seen_block=block_number,
        )

        if sender_is_attacker:
            graph.attacker_addresses.append(sender)

        # Process ETH transfers from internal calls
        for call in trace.internal_calls:
            value = int(call.value, 16) if call.value.startswith("0x") else int(call.value)
            if value > 0:
                await self._add_edge_to_graph(
                    graph,
                    from_addr=call.from_address,
                    to_addr=call.to,
                    value=value,
                    token="ETH",
                    token_symbol="ETH",
                    tx_hash=tx_hash,
                    block_number=block_number,
                )

        # Process ERC-20 transfers
        for i, transfer in enumerate(trace.token_transfers):
            amount = int(transfer.amount) if transfer.amount.isdigit() else 0
            await self._add_edge_to_graph(
                graph,
                from_addr=transfer.from_address,
                to_addr=transfer.to,
                value=amount,
                token=transfer.token,
                token_symbol=transfer.symbol or "TOKEN",
                tx_hash=tx_hash,
                block_number=block_number,
                log_index=i,
            )

        # Calculate total value moved
        graph.total_value_moved = sum(e.value for e in graph.edges)

        # Identify known destinations
        for addr, node in graph.nodes.items():
            if node.label != AddressLabel.UNKNOWN:
                graph.known_destinations.append((addr, node.label_name, node.label))

        return graph

    async def _add_edge_to_graph(
        self,
        graph: TransactionGraph,
        from_addr: str,
        to_addr: str,
        value: int,
        token: str,
        token_symbol: str,
        tx_hash: str,
        block_number: int,
        log_index: int = 0,
    ) -> None:
        """Add an edge (transfer) to the graph, creating nodes if needed."""
        # Ensure nodes exist
        for addr in [from_addr, to_addr]:
            if addr not in graph.nodes:
                label_name, label_type, is_attacker = self.identify_address(addr)
                graph.nodes[addr] = GraphNode(
                    address=addr,
                    label=label_type,
                    label_name=label_name,
                    is_contract=await self._client.is_contract(addr),
                    is_attacker=is_attacker,
                    first_seen_block=block_number,
                )
                if is_attacker and addr not in graph.attacker_addresses:
                    graph.attacker_addresses.append(addr)

        # Update node totals
        graph.nodes[from_addr].total_sent += value
        graph.nodes[to_addr].total_received += value

        # Add edge
        graph.edges.append(
            GraphEdge(
                from_address=from_addr,
                to_address=to_addr,
                value=value,
                token=token,
                token_symbol=token_symbol,
                tx_hash=tx_hash,
                block_number=block_number,
                log_index=log_index,
            )
        )

    async def trace_with_graph(
        self,
        tx_hash: str,
        protocol_address: str = "",
    ) -> TraceResult:
        """Perform a complete forensic trace with graph analysis.

        Returns:
            TraceResult containing trace, graph, and analysis
        """
        trace = await self.trace_transaction(tx_hash)
        graph = await self.build_transaction_graph(tx_hash, protocol_address)

        # Perform analysis
        analysis = self._analyze_graph(trace, graph)

        return TraceResult(
            trace=trace,
            graph=graph,
            analysis=analysis,
            timestamp=int(time.time()),
        )

    def _analyze_graph(
        self,
        trace: TransactionTrace,
        graph: TransactionGraph,
    ) -> dict[str, Any]:
        """Analyze the transaction graph for attack patterns."""
        analysis: dict[str, Any] = {
            "patterns_detected": [],
            "risk_indicators": [],
            "fund_flow_summary": {},
        }

        # Check for reentrancy
        call_counts: dict[str, int] = {}
        for call in trace.internal_calls:
            call_counts[call.to] = call_counts.get(call.to, 0) + 1

        for target, count in call_counts.items():
            if count > 2:
                analysis["patterns_detected"].append({
                    "type": "REENTRANCY",
                    "target": target,
                    "call_count": count,
                    "confidence": min(0.9, 0.5 + count * 0.1),
                })

        # Check for flash loan patterns
        if len(trace.token_transfers) >= 4:
            first = trace.token_transfers[0]
            last = trace.token_transfers[-1]
            if first.to == trace.from_address and last.from_address == trace.from_address:
                analysis["patterns_detected"].append({
                    "type": "FLASH_LOAN",
                    "token": first.token,
                    "amount": first.amount,
                    "confidence": 0.85,
                })

        # Check for mixer usage
        mixer_destinations = [
            (addr, node.label_name)
            for addr, node in graph.nodes.items()
            if node.label == AddressLabel.MIXER
        ]
        if mixer_destinations:
            analysis["risk_indicators"].append({
                "type": "MIXER_USAGE",
                "destinations": mixer_destinations,
                "severity": "HIGH",
            })

        # Check for bridge usage
        bridge_destinations = [
            (addr, node.label_name)
            for addr, node in graph.nodes.items()
            if node.label == AddressLabel.BRIDGE
        ]
        if bridge_destinations:
            analysis["risk_indicators"].append({
                "type": "BRIDGE_USAGE",
                "destinations": bridge_destinations,
                "severity": "MEDIUM",
            })

        # Summarize fund flow
        total_eth = sum(e.value for e in graph.edges if e.token == "ETH")
        token_totals: dict[str, int] = {}
        for edge in graph.edges:
            if edge.token != "ETH":
                token_totals[edge.token_symbol] = token_totals.get(edge.token_symbol, 0) + edge.value

        analysis["fund_flow_summary"] = {
            "total_eth_wei": total_eth,
            "total_eth_formatted": total_eth / 10**18,
            "token_totals": token_totals,
            "unique_addresses": len(graph.nodes),
            "total_transfers": len(graph.edges),
            "known_destinations_count": len(graph.known_destinations),
            "attacker_addresses_count": len(graph.attacker_addresses),
        }

        return analysis

    def _parse_internal_calls(
        self,
        trace: dict[str, Any],
        depth: int = 0,
    ) -> list[InternalCall]:
        """Recursively parse internal calls from a call trace."""
        calls: list[InternalCall] = []

        if "calls" in trace:
            for call in trace["calls"]:
                calls.append(
                    InternalCall(
                        **{"from": call.get("from", "")},
                        to=call.get("to", ""),
                        value=call.get("value", "0x0"),
                        input=call.get("input", "")[:200],  # Truncate for storage
                        output=call.get("output", "")[:200],
                        type=call.get("type", "CALL"),
                        depth=depth,
                    )
                )
                calls.extend(self._parse_internal_calls(call, depth + 1))

        return calls

    def _extract_token_transfers(
        self,
        logs: list[dict[str, Any]],
    ) -> list[TokenTransfer]:
        """Extract ERC-20 token transfers from transaction logs."""
        transfers: list[TokenTransfer] = []

        for log in logs:
            topics = log.get("topics", [])
            if len(topics) >= 3:
                topic_hex = topics[0].hex() if isinstance(topics[0], bytes) else topics[0]
                if topic_hex == self.TRANSFER_TOPIC:
                    from_topic = topics[1].hex() if isinstance(topics[1], bytes) else topics[1]
                    to_topic = topics[2].hex() if isinstance(topics[2], bytes) else topics[2]
                    data = log.get("data", "0x0")
                    if isinstance(data, bytes):
                        data = data.hex()

                    transfers.append(
                        TokenTransfer(
                            token=log["address"],
                            **{"from": self._web3.to_checksum_address("0x" + from_topic[-40:])},
                            to=self._web3.to_checksum_address("0x" + to_topic[-40:]),
                            amount=str(int(data, 16)) if data != "0x0" else "0",
                        )
                    )

        return transfers

    # Sync wrappers for integration with non-async code
    def trace_transaction_sync(self, tx_hash: str) -> TransactionTrace:
        """Synchronous version of trace_transaction."""
        return self._run_sync(self.trace_transaction(tx_hash))

    def build_transaction_graph_sync(
        self,
        tx_hash: str,
        protocol_address: str = "",
    ) -> TransactionGraph:
        """Synchronous version of build_transaction_graph."""
        return self._run_sync(self.build_transaction_graph(tx_hash, protocol_address))

    def trace_with_graph_sync(
        self,
        tx_hash: str,
        protocol_address: str = "",
    ) -> TraceResult:
        """Synchronous version of trace_with_graph."""
        return self._run_sync(self.trace_with_graph(tx_hash, protocol_address))

    def _run_sync(self, coro):
        """Run an async coroutine synchronously."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)


# ============ Factory Functions ============


def get_forensic_tracer(web3: Web3) -> ForensicTracer:
    """Create a ForensicTracer instance."""
    return ForensicTracer(web3)


def identify_address(address: str) -> tuple[str, AddressLabel, bool]:
    """Identify a known address without creating a tracer.

    Returns:
        Tuple of (label_name, label_type, is_attacker)
    """
    address_lower = address.lower()

    # Check known attackers
    for addr, name in KNOWN_ATTACKERS.items():
        if addr.lower() == address_lower:
            return name, AddressLabel.ATTACKER, True

    # Check known addresses
    for addr, (name, label) in KNOWN_ADDRESSES.items():
        if addr.lower() == address_lower:
            return name, label, False

    return "", AddressLabel.UNKNOWN, False


def is_known_attacker(address: str) -> bool:
    """Check if an address is a known attacker."""
    address_lower = address.lower()
    return any(addr.lower() == address_lower for addr in KNOWN_ATTACKERS)


def get_address_label(address: str) -> AddressLabel:
    """Get the label type for an address."""
    _, label, _ = identify_address(address)
    return label
