"""Tests for the forensic tracer module.

These tests verify the tracer functionality using mocked Web3 responses.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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


# ============ Address Identification Tests ============


class TestAddressIdentification:
    """Tests for address identification functions."""

    def test_identify_known_cex(self):
        """Test identifying a known CEX address."""
        # Binance 14
        name, label, is_attacker = identify_address("0x28C6c06298d514Db089934071355E5743bf21d60")
        assert label == AddressLabel.CEX
        assert "Binance" in name
        assert not is_attacker

    def test_identify_known_mixer(self):
        """Test identifying a known mixer address."""
        # Tornado Cash
        name, label, is_attacker = identify_address("0x722122dF12D4e14e13Ac3b6895a86e84145b6967")
        assert label == AddressLabel.MIXER
        assert "Tornado" in name
        assert not is_attacker

    def test_identify_known_dex(self):
        """Test identifying a known DEX address."""
        # Uniswap V2 Router
        name, label, is_attacker = identify_address("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")
        assert label == AddressLabel.DEX
        assert "Uniswap" in name
        assert not is_attacker

    def test_identify_known_attacker(self):
        """Test identifying a known attacker address."""
        # Euler Exploiter
        name, label, is_attacker = identify_address("0x9799b475dEc92Bd99bbdD943013325C36157f383")
        assert label == AddressLabel.ATTACKER
        assert "Euler" in name
        assert is_attacker

    def test_identify_unknown_address(self):
        """Test that unknown addresses return UNKNOWN label."""
        name, label, is_attacker = identify_address("0x0000000000000000000000000000000000000001")
        assert label == AddressLabel.UNKNOWN
        assert name == ""
        assert not is_attacker

    def test_is_known_attacker_true(self):
        """Test is_known_attacker returns True for known attackers."""
        assert is_known_attacker("0x9799b475dEc92Bd99bbdD943013325C36157f383")

    def test_is_known_attacker_false(self):
        """Test is_known_attacker returns False for non-attackers."""
        assert not is_known_attacker("0x0000000000000000000000000000000000000001")

    def test_get_address_label(self):
        """Test get_address_label convenience function."""
        label = get_address_label("0x28C6c06298d514Db089934071355E5743bf21d60")
        assert label == AddressLabel.CEX


# ============ GraphNode Tests ============


class TestGraphNode:
    """Tests for GraphNode model."""

    def test_create_graph_node(self):
        """Test creating a GraphNode."""
        node = GraphNode(
            address="0x1234567890123456789012345678901234567890",
            label=AddressLabel.CEX,
            label_name="Test CEX",
            is_contract=False,
            is_attacker=False,
            total_received=1000,
            total_sent=500,
            first_seen_block=12345678,
        )
        assert node.address == "0x1234567890123456789012345678901234567890"
        assert node.label == AddressLabel.CEX
        assert node.total_received == 1000

    def test_graph_node_defaults(self):
        """Test GraphNode default values."""
        node = GraphNode(address="0x1234")
        assert node.label == AddressLabel.UNKNOWN
        assert node.label_name == ""
        assert not node.is_contract
        assert not node.is_attacker
        assert node.total_received == 0


# ============ GraphEdge Tests ============


class TestGraphEdge:
    """Tests for GraphEdge model."""

    def test_create_graph_edge(self):
        """Test creating a GraphEdge."""
        edge = GraphEdge(
            from_address="0x1111111111111111111111111111111111111111",
            to_address="0x2222222222222222222222222222222222222222",
            value=1000000000000000000,  # 1 ETH
            token="ETH",
            token_symbol="ETH",
            tx_hash="0xabc123",
            block_number=12345678,
        )
        assert edge.value == 1000000000000000000
        assert edge.token == "ETH"

    def test_graph_edge_defaults(self):
        """Test GraphEdge default values."""
        edge = GraphEdge(
            from_address="0x1111",
            to_address="0x2222",
            value=100,
            tx_hash="0xabc",
            block_number=123,
        )
        assert edge.token == "ETH"
        assert edge.token_symbol == "ETH"
        assert edge.log_index == 0


# ============ TransactionGraph Tests ============


class TestTransactionGraph:
    """Tests for TransactionGraph model."""

    def test_create_empty_graph(self):
        """Test creating an empty TransactionGraph."""
        graph = TransactionGraph()
        assert graph.nodes == {}
        assert graph.edges == []
        assert graph.attacker_addresses == []

    def test_graph_with_data(self):
        """Test TransactionGraph with nodes and edges."""
        node1 = GraphNode(address="0x1111", label=AddressLabel.EOA)
        node2 = GraphNode(address="0x2222", label=AddressLabel.CONTRACT)
        edge = GraphEdge(
            from_address="0x1111",
            to_address="0x2222",
            value=100,
            tx_hash="0xabc",
            block_number=123,
        )

        graph = TransactionGraph(
            nodes={"0x1111": node1, "0x2222": node2},
            edges=[edge],
            root_tx="0xabc",
            total_value_moved=100,
        )

        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        assert graph.total_value_moved == 100


# ============ ForensicTracer Tests ============


class TestForensicTracer:
    """Tests for ForensicTracer class."""

    def test_create_tracer(self):
        """Test creating a ForensicTracer."""
        mock_web3 = MagicMock()
        mock_web3.provider.endpoint_uri = "https://example.com"
        mock_web3.to_checksum_address = lambda x: x

        tracer = ForensicTracer(mock_web3)
        assert tracer.web3 == mock_web3

    def test_tracer_identify_address(self):
        """Test ForensicTracer.identify_address method."""
        mock_web3 = MagicMock()
        mock_web3.to_checksum_address = lambda x: x

        tracer = ForensicTracer(mock_web3)

        # Test known CEX
        name, label, is_attacker = tracer.identify_address(
            "0x28C6c06298d514Db089934071355E5743bf21d60"
        )
        assert label == AddressLabel.CEX
        assert not is_attacker

        # Test known attacker
        name, label, is_attacker = tracer.identify_address(
            "0x9799b475dEc92Bd99bbdD943013325C36157f383"
        )
        assert label == AddressLabel.ATTACKER
        assert is_attacker

    def test_get_forensic_tracer_factory(self):
        """Test get_forensic_tracer factory function."""
        mock_web3 = MagicMock()
        mock_web3.provider.endpoint_uri = "https://example.com"

        tracer = get_forensic_tracer(mock_web3)
        assert isinstance(tracer, ForensicTracer)


# ============ ArchiveNodeClient Tests ============


class TestArchiveNodeClient:
    """Tests for ArchiveNodeClient class."""

    def test_create_client(self):
        """Test creating an ArchiveNodeClient."""
        mock_web3 = MagicMock()
        mock_web3.provider.endpoint_uri = "https://example.com"

        client = ArchiveNodeClient(mock_web3)
        assert client.web3 == mock_web3

    @pytest.mark.asyncio
    async def test_is_contract_true(self):
        """Test is_contract returns True for contract addresses."""
        mock_web3 = MagicMock()
        mock_web3.eth.get_code = MagicMock(return_value=b'0x608060405...')
        mock_web3.to_checksum_address = lambda x: x

        client = ArchiveNodeClient(mock_web3)
        result = await client.is_contract("0x1234")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_contract_false(self):
        """Test is_contract returns False for EOA addresses."""
        mock_web3 = MagicMock()
        mock_web3.eth.get_code = MagicMock(return_value=b'0x')
        mock_web3.to_checksum_address = lambda x: x

        client = ArchiveNodeClient(mock_web3)
        result = await client.is_contract("0x1234")
        assert result is False


# ============ Integration Tests ============


class TestTracerAnalysis:
    """Tests for tracer analysis capabilities."""

    def test_analyze_graph_detects_mixer(self):
        """Test that analysis detects mixer usage."""
        mock_web3 = MagicMock()
        mock_web3.to_checksum_address = lambda x: x
        mock_web3.provider.endpoint_uri = "https://example.com"

        tracer = ForensicTracer(mock_web3)

        # Create a graph with a mixer destination
        from aegis.models import TransactionTrace, InternalCall, TokenTransfer

        trace = TransactionTrace(
            tx_hash="0xtest",
            **{"from": "0x1111"},
            to="0x2222",
            value="0",
            gas_used=100000,
            internal_calls=[],
            token_transfers=[
                TokenTransfer(
                    token="0xtoken",
                    **{"from": "0x1111"},
                    to="0x722122dF12D4e14e13Ac3b6895a86e84145b6967",  # Tornado Cash
                    amount="1000000",
                )
            ],
        )

        # Create graph with mixer node
        graph = TransactionGraph(
            nodes={
                "0x1111": GraphNode(address="0x1111"),
                "0x722122dF12D4e14e13Ac3b6895a86e84145b6967": GraphNode(
                    address="0x722122dF12D4e14e13Ac3b6895a86e84145b6967",
                    label=AddressLabel.MIXER,
                    label_name="Tornado Cash 0.1 ETH",
                ),
            },
            edges=[],
        )

        analysis = tracer._analyze_graph(trace, graph)
        assert any(
            ri.get("type") == "MIXER_USAGE"
            for ri in analysis.get("risk_indicators", [])
        )

    def test_analyze_graph_detects_reentrancy(self):
        """Test that analysis detects reentrancy patterns."""
        mock_web3 = MagicMock()
        mock_web3.to_checksum_address = lambda x: x
        mock_web3.provider.endpoint_uri = "https://example.com"

        tracer = ForensicTracer(mock_web3)

        from aegis.models import TransactionTrace, InternalCall

        # Create trace with multiple calls to same address (reentrancy pattern)
        trace = TransactionTrace(
            tx_hash="0xtest",
            **{"from": "0x1111"},
            to="0x2222",
            value="0",
            gas_used=100000,
            internal_calls=[
                InternalCall(
                    **{"from": "0x1111"},
                    to="0x3333",
                    value="0x0",
                    input="0x",
                    output="0x",
                    type="CALL",
                    depth=0,
                ),
                InternalCall(
                    **{"from": "0x3333"},
                    to="0x3333",  # Same target
                    value="0x0",
                    input="0x",
                    output="0x",
                    type="CALL",
                    depth=1,
                ),
                InternalCall(
                    **{"from": "0x3333"},
                    to="0x3333",  # Same target
                    value="0x0",
                    input="0x",
                    output="0x",
                    type="CALL",
                    depth=2,
                ),
                InternalCall(
                    **{"from": "0x3333"},
                    to="0x3333",  # Same target (4th call triggers detection)
                    value="0x0",
                    input="0x",
                    output="0x",
                    type="CALL",
                    depth=3,
                ),
            ],
            token_transfers=[],
        )

        graph = TransactionGraph()
        analysis = tracer._analyze_graph(trace, graph)

        # Should detect reentrancy
        assert any(
            p.get("type") == "REENTRANCY"
            for p in analysis.get("patterns_detected", [])
        )


# ============ Known Addresses Database Tests ============


class TestKnownAddressesDatabase:
    """Tests for known addresses database."""

    def test_known_addresses_not_empty(self):
        """Test that KNOWN_ADDRESSES has entries."""
        assert len(KNOWN_ADDRESSES) > 0

    def test_known_attackers_not_empty(self):
        """Test that KNOWN_ATTACKERS has entries."""
        assert len(KNOWN_ATTACKERS) > 0

    def test_all_known_addresses_have_labels(self):
        """Test that all known addresses have valid labels."""
        for addr, (name, label) in KNOWN_ADDRESSES.items():
            assert isinstance(label, AddressLabel)
            assert name != ""

    def test_all_known_attackers_have_names(self):
        """Test that all known attackers have names."""
        for addr, name in KNOWN_ATTACKERS.items():
            assert name != ""
            assert addr.startswith("0x")
