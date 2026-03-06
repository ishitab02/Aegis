"""Tests for the live monitoring routes (Aave V3 on Base Mainnet).

All external calls (Web3, Chainlink, Aave adapter) are mocked so the test
suite runs entirely offline.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from aegis.adapters.base import ProtocolEvent, TokenBalance
from aegis.api.routes import monitor as monitor_mod
from aegis.api.server import app
from aegis.models import (
    ActionRecommendation,
    ConsensusResult,
    DetectionResponse,
    PriceFeedData,
    SentinelVote,
    ThreatAssessment,
    ThreatLevel,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

FAKE_TVL = 500_000 * 10**18  # 500 k "units" in wei

FAKE_CHAINLINK = PriceFeedData(
    price=2500.0,
    updated_at=1709700000,
    decimals=8,
    feed_address="0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70",
)

FAKE_BALANCES: list[TokenBalance] = [
    TokenBalance(
        token_address="0xAAA",
        symbol="WETH",
        decimals=18,
        balance_raw=200_000 * 10**18,
        balance_formatted=200_000.0,
    ),
    TokenBalance(
        token_address="0xBBB",
        symbol="USDC",
        decimals=6,
        balance_raw=300_000 * 10**6,
        balance_formatted=300_000.0,
    ),
]

FAKE_EVENTS: list[ProtocolEvent] = [
    ProtocolEvent(
        event_name="Supply",
        block_number=12345678,
        transaction_hash="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        log_index=0,
        args={"amount": 10**18},
    ),
]


def _fake_detection(**_kwargs) -> DetectionResponse:
    ts = 1709700000
    vote = SentinelVote(
        sentinel_id="liquidity-sentinel-0",
        threat_level=ThreatLevel.NONE,
        confidence=0.95,
        timestamp=ts,
    )
    return DetectionResponse(
        consensus=ConsensusResult(
            consensus_reached=True,
            final_threat_level=ThreatLevel.NONE,
            agreement_ratio=1.0,
            votes=[vote],
            action_recommended=ActionRecommendation.NONE,
        ),
        assessments=[
            ThreatAssessment(
                threat_level=ThreatLevel.NONE,
                confidence=0.95,
                details="TVL stable",
                indicators=[],
                recommendation=ActionRecommendation.NONE,
                timestamp=ts,
                sentinel_id="liquidity-sentinel-0",
                sentinel_type="LIQUIDITY",
            ),
        ],
        timestamp=ts,
    )


def _mock_adapter():
    """Return a mock AaveV3Adapter with async helpers."""
    adapter = MagicMock()
    adapter.get_tvl = AsyncMock(return_value=FAKE_TVL)
    adapter.get_token_balances = AsyncMock(return_value=FAKE_BALANCES)
    adapter.get_recent_events = AsyncMock(return_value=FAKE_EVENTS)
    adapter.protocol_type = "aave_v3"
    return adapter


# ---------------------------------------------------------------------------
# Tests — /api/v1/monitor/aave
# ---------------------------------------------------------------------------


class TestMonitorAave:
    """Tests for GET /api/v1/monitor/aave."""

    @patch("aegis.api.routes.monitor.run_detection_cycle", side_effect=_fake_detection)
    @patch("aegis.api.routes.monitor.get_chainlink_price", return_value=FAKE_CHAINLINK)
    @patch("aegis.api.routes.monitor._get_aave_adapter")
    @patch("aegis.api.routes.monitor._get_base_mainnet_w3")
    def test_returns_live_data(
        self, mock_w3, mock_adapter_fn, mock_chainlink, mock_detection
    ):
        mock_w3.return_value = MagicMock()
        mock_adapter_fn.return_value = _mock_adapter()

        response = client.get("/api/v1/monitor/aave")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "live"
        assert data["protocol"] == "Aave V3"
        assert data["chain"] == "Base Mainnet"
        assert data["chain_id"] == 8453

    @patch("aegis.api.routes.monitor.run_detection_cycle", side_effect=_fake_detection)
    @patch("aegis.api.routes.monitor.get_chainlink_price", return_value=FAKE_CHAINLINK)
    @patch("aegis.api.routes.monitor._get_aave_adapter")
    @patch("aegis.api.routes.monitor._get_base_mainnet_w3")
    def test_includes_tvl(
        self, mock_w3, mock_adapter_fn, mock_chainlink, mock_detection
    ):
        mock_w3.return_value = MagicMock()
        mock_adapter_fn.return_value = _mock_adapter()

        data = client.get("/api/v1/monitor/aave").json()

        assert "tvl_wei" in data
        assert int(data["tvl_wei"]) == FAKE_TVL
        assert data["tvl_eth"] == FAKE_TVL / 10**18

    @patch("aegis.api.routes.monitor.run_detection_cycle", side_effect=_fake_detection)
    @patch("aegis.api.routes.monitor.get_chainlink_price", return_value=FAKE_CHAINLINK)
    @patch("aegis.api.routes.monitor._get_aave_adapter")
    @patch("aegis.api.routes.monitor._get_base_mainnet_w3")
    def test_includes_chainlink_price(
        self, mock_w3, mock_adapter_fn, mock_chainlink, mock_detection
    ):
        mock_w3.return_value = MagicMock()
        mock_adapter_fn.return_value = _mock_adapter()

        data = client.get("/api/v1/monitor/aave").json()

        assert data["chainlink_eth_usd"] == 2500.0
        assert data["chainlink_updated_at"] == 1709700000

    @patch("aegis.api.routes.monitor.run_detection_cycle", side_effect=_fake_detection)
    @patch("aegis.api.routes.monitor.get_chainlink_price", return_value=FAKE_CHAINLINK)
    @patch("aegis.api.routes.monitor._get_aave_adapter")
    @patch("aegis.api.routes.monitor._get_base_mainnet_w3")
    def test_includes_tvl_usd_estimate(
        self, mock_w3, mock_adapter_fn, mock_chainlink, mock_detection
    ):
        mock_w3.return_value = MagicMock()
        mock_adapter_fn.return_value = _mock_adapter()

        data = client.get("/api/v1/monitor/aave").json()

        expected_usd = (FAKE_TVL / 10**18) * 2500.0
        assert abs(data["tvl_usd_estimate"] - expected_usd) < 1.0

    @patch("aegis.api.routes.monitor.run_detection_cycle", side_effect=_fake_detection)
    @patch("aegis.api.routes.monitor.get_chainlink_price", return_value=FAKE_CHAINLINK)
    @patch("aegis.api.routes.monitor._get_aave_adapter")
    @patch("aegis.api.routes.monitor._get_base_mainnet_w3")
    def test_includes_token_balances(
        self, mock_w3, mock_adapter_fn, mock_chainlink, mock_detection
    ):
        mock_w3.return_value = MagicMock()
        mock_adapter_fn.return_value = _mock_adapter()

        data = client.get("/api/v1/monitor/aave").json()

        assert "token_balances" in data
        assert len(data["token_balances"]) <= 5
        symbols = {b["symbol"] for b in data["token_balances"]}
        assert "USDC" in symbols or "WETH" in symbols

    @patch("aegis.api.routes.monitor.run_detection_cycle", side_effect=_fake_detection)
    @patch("aegis.api.routes.monitor.get_chainlink_price", return_value=FAKE_CHAINLINK)
    @patch("aegis.api.routes.monitor._get_aave_adapter")
    @patch("aegis.api.routes.monitor._get_base_mainnet_w3")
    def test_includes_recent_events(
        self, mock_w3, mock_adapter_fn, mock_chainlink, mock_detection
    ):
        mock_w3.return_value = MagicMock()
        mock_adapter_fn.return_value = _mock_adapter()

        data = client.get("/api/v1/monitor/aave").json()

        assert "recent_events" in data
        assert len(data["recent_events"]) == 1
        assert data["recent_events"][0]["type"] == "Supply"

    @patch("aegis.api.routes.monitor.run_detection_cycle", side_effect=_fake_detection)
    @patch("aegis.api.routes.monitor.get_chainlink_price", return_value=FAKE_CHAINLINK)
    @patch("aegis.api.routes.monitor._get_aave_adapter")
    @patch("aegis.api.routes.monitor._get_base_mainnet_w3")
    def test_includes_threat_assessment(
        self, mock_w3, mock_adapter_fn, mock_chainlink, mock_detection
    ):
        mock_w3.return_value = MagicMock()
        mock_adapter_fn.return_value = _mock_adapter()

        data = client.get("/api/v1/monitor/aave").json()

        ta = data["threat_assessment"]
        assert ta["threat_level"] == "NONE"
        assert ta["action"] == "NONE"
        assert "assessments" in ta

    @patch("aegis.api.routes.monitor._get_base_mainnet_w3", side_effect=Exception("RPC down"))
    def test_returns_503_on_failure(self, mock_w3):
        response = client.get("/api/v1/monitor/aave")
        assert response.status_code == 503


# ---------------------------------------------------------------------------
# Tests — /api/v1/monitor/aave/history
# ---------------------------------------------------------------------------


class TestMonitorHistory:
    """Tests for GET /api/v1/monitor/aave/history."""

    def test_history_empty_initially(self):
        # Clear any state from previous tests
        monitor_mod._aave_history.clear()

        data = client.get("/api/v1/monitor/aave/history").json()

        assert data["protocol"] == "Aave V3"
        assert data["chain"] == "Base Mainnet"
        assert data["reading_count"] == 0
        assert data["readings"] == []

    def test_history_returns_readings(self):
        monitor_mod._aave_history.clear()
        monitor_mod._aave_history.append(
            {"tvl_wei": "100", "tvl_eth": 0.0001, "timestamp": 1709700000}
        )

        data = client.get("/api/v1/monitor/aave/history").json()

        assert data["reading_count"] == 1
        assert data["readings"][0]["tvl_wei"] == "100"


# ---------------------------------------------------------------------------
# Tests — /api/v1/monitor/status
# ---------------------------------------------------------------------------


class TestMonitorStatus:
    """Tests for GET /api/v1/monitor/status."""

    def test_status_endpoint(self):
        response = client.get("/api/v1/monitor/status")
        assert response.status_code == 200

        data = response.json()
        assert "background_monitor" in data
        assert "history_size" in data
        assert "interval_seconds" in data
        assert data["interval_seconds"] == 30


# ---------------------------------------------------------------------------
# Tests — TVL change tracking
# ---------------------------------------------------------------------------


class TestTVLChangeTracking:
    """Verify that tvl_change_percent is computed correctly across calls."""

    @patch("aegis.api.routes.monitor.run_detection_cycle", side_effect=_fake_detection)
    @patch("aegis.api.routes.monitor.get_chainlink_price", return_value=FAKE_CHAINLINK)
    @patch("aegis.api.routes.monitor._get_aave_adapter")
    @patch("aegis.api.routes.monitor._get_base_mainnet_w3")
    def test_first_call_has_zero_change(
        self, mock_w3, mock_adapter_fn, mock_chainlink, mock_detection
    ):
        """First call has no previous TVL so change should be 0."""
        # Reset global state
        monitor_mod._previous_tvl = 0

        mock_w3.return_value = MagicMock()
        mock_adapter_fn.return_value = _mock_adapter()

        data = client.get("/api/v1/monitor/aave").json()
        assert data["tvl_change_percent"] == 0.0

    @patch("aegis.api.routes.monitor.run_detection_cycle", side_effect=_fake_detection)
    @patch("aegis.api.routes.monitor.get_chainlink_price", return_value=FAKE_CHAINLINK)
    @patch("aegis.api.routes.monitor._get_aave_adapter")
    @patch("aegis.api.routes.monitor._get_base_mainnet_w3")
    def test_second_call_detects_change(
        self, mock_w3, mock_adapter_fn, mock_chainlink, mock_detection
    ):
        """With _previous_tvl already set, change percent should be non-zero when TVL differs."""
        monitor_mod._previous_tvl = 400_000 * 10**18  # smaller than FAKE_TVL

        mock_w3.return_value = MagicMock()
        mock_adapter_fn.return_value = _mock_adapter()

        data = client.get("/api/v1/monitor/aave").json()
        # 500k vs 400k = +25%
        assert data["tvl_change_percent"] == 25.0


# ---------------------------------------------------------------------------
# Tests — Background monitor helper functions
# ---------------------------------------------------------------------------


class TestBackgroundMonitor:
    """Tests for start/stop helpers (no real async loop needed)."""

    def test_stop_when_not_running(self):
        """stop_background_monitor should be a no-op when nothing is running."""
        monitor_mod._monitor_task = None
        monitor_mod.stop_background_monitor()
        assert monitor_mod._monitor_task is None

    def test_stop_cancels_running_task(self):
        """stop_background_monitor should cancel a running task."""
        fake_task = MagicMock()
        fake_task.done.return_value = False
        monitor_mod._monitor_task = fake_task

        monitor_mod.stop_background_monitor()

        fake_task.cancel.assert_called_once()
        assert monitor_mod._monitor_task is None
