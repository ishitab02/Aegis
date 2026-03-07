"""Tests for live_mode detection flow."""

from unittest.mock import MagicMock

from aegis.coordinator.crew import (
    _live_monitor_data,
    get_all_live_monitor_data,
    get_live_monitor_data,
    run_detection_cycle,
)
from aegis.models import ThreatLevel


class TestLiveModeDetection:
    """Tests for the live_mode parameter in run_detection_cycle."""

    def setup_method(self):
        _live_monitor_data.clear()

    def test_live_mode_false_default(self):
        """live_mode defaults to False and produces a valid response."""
        result = run_detection_cycle(
            protocol_address="0x0000000000000000000000000000000000000001",
            protocol_name="TestProtocol",
        )
        assert result.consensus is not None
        assert result.timestamp > 0
        assert len(result.assessments) >= 1

    def test_live_mode_with_mock_adapter(self):
        """live_mode=True with a mock adapter records history and populates monitor data."""
        adapter = MagicMock()
        adapter.protocol_type = "mock_v1"
        adapter.get_tvl_sync.return_value = 500_000 * 10**18

        result = run_detection_cycle(
            protocol_address="0xLiveTestAddr",
            protocol_name="LiveTest",
            live_mode=True,
            adapter=adapter,
        )

        assert result.consensus is not None
        assert len(result.assessments) >= 1
        adapter.get_tvl_sync.assert_called()

    def test_live_mode_records_monitor_data(self):
        """live_mode populates the _live_monitor_data cache."""
        addr = "0xMonitorDataTest"
        adapter = MagicMock()
        adapter.protocol_type = "aave_v3"
        adapter.get_tvl_sync.return_value = 1_000_000 * 10**18

        run_detection_cycle(
            protocol_address=addr,
            protocol_name="MonitorTest",
            live_mode=True,
            adapter=adapter,
        )

        data = get_live_monitor_data(addr)
        assert data is not None
        assert data["protocol_address"] == addr
        assert data["tvl_wei"] == 1_000_000 * 10**18
        assert data["adapter_type"] == "aave_v3"
        assert data["timestamp"] > 0

    def test_live_mode_computes_tvl_change(self):
        """When previous history exists, live_mode computes change percent."""
        addr = "0xChangeTest"
        adapter = MagicMock()
        adapter.protocol_type = "aave_v3"

        # First call: 1M ETH TVL
        adapter.get_tvl_sync.return_value = 1_000_000 * 10**18
        run_detection_cycle(
            protocol_address=addr,
            protocol_name="ChangeTest",
            live_mode=True,
            adapter=adapter,
        )

        # Second call: 900K ETH TVL (10% drop)
        adapter.get_tvl_sync.return_value = 900_000 * 10**18
        run_detection_cycle(
            protocol_address=addr,
            protocol_name="ChangeTest",
            live_mode=True,
            adapter=adapter,
        )

        data = get_live_monitor_data(addr)
        assert data is not None
        # tvl_change_percent should be roughly -10%
        assert data["tvl_change_percent"] is not None
        assert data["tvl_change_percent"] < 0

    def test_get_live_monitor_data_none_for_unknown(self):
        """get_live_monitor_data returns None for unknown addresses."""
        assert get_live_monitor_data("0xUnknown") is None

    def test_get_all_live_monitor_data_empty(self):
        """get_all_live_monitor_data returns empty dict when nothing tracked."""
        assert get_all_live_monitor_data() == {}

    def test_simulation_overrides_live_mode(self):
        """Simulation parameters still work even when live_mode=True."""
        result = run_detection_cycle(
            protocol_address="0xSimOverride",
            protocol_name="SimTest",
            simulate_tvl_drop_percent=25.0,
            live_mode=True,
        )

        # Should get a CRITICAL from the 25% TVL drop simulation
        liquidity = [a for a in result.assessments if a.sentinel_type == "LIQUIDITY"]
        assert len(liquidity) == 1
        assert liquidity[0].threat_level == ThreatLevel.CRITICAL


class TestLiveModeAPIEndpoints:
    """Tests for the /detect/monitor/* endpoints."""

    def test_monitor_aave_endpoint(self):
        from fastapi.testclient import TestClient

        from aegis.api.server import app

        client = TestClient(app)
        response = client.get("/api/v1/detect/monitor/aave")
        assert response.status_code == 200
        data = response.json()
        # Will either have live data or 'unavailable' status
        assert "protocol_address" in data
        assert "timestamp" in data

    def test_monitor_unknown_protocol(self):
        from fastapi.testclient import TestClient

        from aegis.api.server import app

        client = TestClient(app)
        _live_monitor_data.clear()
        response = client.get("/api/v1/detect/monitor/0xUnknownProtocol")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unavailable"

    def test_monitor_list_endpoint(self):
        from fastapi.testclient import TestClient

        from aegis.api.server import app

        client = TestClient(app)
        response = client.get("/api/v1/detect/monitor")
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        assert "timestamp" in data

    def test_detect_with_live_mode(self):
        from fastapi.testclient import TestClient

        from aegis.api.server import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/detect",
            json={
                "protocol_address": "0x0000000000000000000000000000000000000001",
                "protocol_name": "TestLive",
                "live_mode": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "consensus" in data
        assert "assessments" in data
