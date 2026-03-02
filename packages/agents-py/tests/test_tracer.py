"""Tests for the forensic tracer module."""

from unittest.mock import MagicMock

import pytest

from aegis.sherlock.tracer import (
    KNOWN_ADDRESSES,
    KNOWN_ATTACKERS,
    AddressLabel,
    ArchiveNodeClient,
    ForensicTracer,
    GraphEdge,
    GraphNode,
    TransactionGraph,
    get_address_label,
    get_forensic_tracer,
    identify_address,
    is_known_attacker,
)


class TestAddressIdentification:
    def test_identify_known_cex(self):
        # binance 14
        name, label, is_attacker = identify_address("0x28C6c06298d514Db089934071355E5743bf21d60")
        assert label == AddressLabel.CEX
        assert "Binance" in name
        assert not is_attacker

    def test_identify_known_mixer(self):
        # tornado cash
        name, label, is_attacker = identify_address("0x722122dF12D4e14e13Ac3b6895a86e84145b6967")
        assert label == AddressLabel.MIXER
        assert "Tornado" in name
        assert not is_attacker

    def test_identify_known_dex(self):
        # uniswap v2 router
        name, label, is_attacker = identify_address("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")
        assert label == AddressLabel.DEX
        assert "Uniswap" in name
        assert not is_attacker

    def test_identify_known_attacker(self):
        # euler exploiter
        name, label, is_attacker = identify_address("0x9799b475dEc92Bd99bbdD943013325C36157f383")
        assert label == AddressLabel.ATTACKER
        assert "Euler" in name
        assert is_attacker

    def test_identify_unknown_address(self):
        name, label, is_attacker = identify_address("0x0000000000000000000000000000000000000001")
        assert label == AddressLabel.UNKNOWN
        assert name == ""
        assert not is_attacker

    def test_is_known_attacker_true(self):
        assert is_known_attacker("0x9799b475dEc92Bd99bbdD943013325C36157f383")

    def test_is_known_attacker_false(self):
        assert not is_known_attacker("0x0000000000000000000000000000000000000001")

    def test_get_address_label(self):
        label = get_address_label("0x28C6c06298d514Db089934071355E5743bf21d60")
        assert label == AddressLabel.CEX




class TestGraphNode:
    def test_create_graph_node(self):
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
        node = GraphNode(address="0x1234")
        assert node.label == AddressLabel.UNKNOWN
        assert node.label_name == ""
        assert not node.is_contract
        assert not node.is_attacker
        assert node.total_received == 0




class TestGraphEdge:
    def test_create_graph_edge(self):
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




class TestTransactionGraph:
    def test_create_empty_graph(self):
        graph = TransactionGraph()
        assert graph.nodes == {}
        assert graph.edges == []
        assert graph.attacker_addresses == []

    def test_graph_with_data(self):
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




class TestForensicTracer:
    def test_create_tracer(self):
        mock_web3 = MagicMock()
        mock_web3.provider.endpoint_uri = "https://example.com"
        mock_web3.to_checksum_address = lambda x: x

        tracer = ForensicTracer(mock_web3)
        assert tracer.web3 == mock_web3

    def test_tracer_identify_address(self):
        mock_web3 = MagicMock()
        mock_web3.to_checksum_address = lambda x: x

        tracer = ForensicTracer(mock_web3)

        # test known cex
        name, label, is_attacker = tracer.identify_address(
            "0x28C6c06298d514Db089934071355E5743bf21d60"
        )
        assert label == AddressLabel.CEX
        assert not is_attacker

        # test known attacker
        name, label, is_attacker = tracer.identify_address(
            "0x9799b475dEc92Bd99bbdD943013325C36157f383"
        )
        assert label == AddressLabel.ATTACKER
        assert is_attacker

    def test_get_forensic_tracer_factory(self):
        mock_web3 = MagicMock()
        mock_web3.provider.endpoint_uri = "https://example.com"

        tracer = get_forensic_tracer(mock_web3)
        assert isinstance(tracer, ForensicTracer)




class TestArchiveNodeClient:
    def test_create_client(self):
        mock_web3 = MagicMock()
        mock_web3.provider.endpoint_uri = "https://example.com"

        client = ArchiveNodeClient(mock_web3)
        assert client.web3 == mock_web3

    @pytest.mark.asyncio
    async def test_is_contract_true(self):
        mock_web3 = MagicMock()
        mock_web3.eth.get_code = MagicMock(return_value=b'0x608060405...')
        mock_web3.to_checksum_address = lambda x: x

        client = ArchiveNodeClient(mock_web3)
        result = await client.is_contract("0x1234")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_contract_false(self):
        mock_web3 = MagicMock()
        mock_web3.eth.get_code = MagicMock(return_value=b'0x')
        mock_web3.to_checksum_address = lambda x: x

        client = ArchiveNodeClient(mock_web3)
        result = await client.is_contract("0x1234")
        assert result is False




class TestTracerAnalysis:
    def test_analyze_graph_detects_mixer(self):
        mock_web3 = MagicMock()
        mock_web3.to_checksum_address = lambda x: x
        mock_web3.provider.endpoint_uri = "https://example.com"

        tracer = ForensicTracer(mock_web3)

        # Create a graph with a mixer destination
        from aegis.models import TokenTransfer, TransactionTrace

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
                    to="0x722122dF12D4e14e13Ac3b6895a86e84145b6967",  # tornado cash
                    amount="1000000",
                )
            ],
        )

        # create graph with mixer node
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
        mock_web3 = MagicMock()
        mock_web3.to_checksum_address = lambda x: x
        mock_web3.provider.endpoint_uri = "https://example.com"

        tracer = ForensicTracer(mock_web3)

        from aegis.models import InternalCall, TransactionTrace

        # create trace with multiple calls to same address (reentrancy pattern)
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
                    to="0x3333",  # same target
                    value="0x0",
                    input="0x",
                    output="0x",
                    type="CALL",
                    depth=1,
                ),
                InternalCall(
                    **{"from": "0x3333"},
                    to="0x3333",  # same target
                    value="0x0",
                    input="0x",
                    output="0x",
                    type="CALL",
                    depth=2,
                ),
                InternalCall(
                    **{"from": "0x3333"},
                    to="0x3333",  # same target (4th call triggers detection)
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

        # should detect reentrancy
        assert any(
            p.get("type") == "REENTRANCY"
            for p in analysis.get("patterns_detected", [])
        )




class TestKnownAddressesDatabase:
    def test_known_addresses_not_empty(self):
        assert len(KNOWN_ADDRESSES) > 0

    def test_known_attackers_not_empty(self):
        assert len(KNOWN_ATTACKERS) > 0

    def test_all_known_addresses_have_labels(self):
        for addr, (name, label) in KNOWN_ADDRESSES.items():
            assert isinstance(label, AddressLabel)
            assert name != ""

    def test_all_known_attackers_have_names(self):
        for addr, name in KNOWN_ATTACKERS.items():
            assert name != ""
            assert addr.startswith("0x")
