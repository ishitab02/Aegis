"""Tests for the FastAPI server endpoints."""

from fastapi.testclient import TestClient

from aegis.api.server import app

client = TestClient(app)


class TestRootEndpoint:
    def test_root_returns_status(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AEGIS Agent API"
        assert data["status"] == "running"


class TestHealthEndpoint:
    def test_health_returns_status(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("HEALTHY", "DEGRADED", "UNHEALTHY")
        assert "sentinels" in data
        assert data["sentinels"]["total"] == 3


class TestSentinelEndpoints:
    def test_sentinel_aggregate(self):
        response = client.get("/api/v1/sentinel/aggregate")
        assert response.status_code == 200
        data = response.json()
        assert "assessments" in data
        assert "consensus" in data
        assert "timestamp" in data

    def test_sentinel_by_id(self):
        response = client.get("/api/v1/sentinel/liquidity-sentinel-0")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "liquidity-sentinel-0"
        assert data["type"] == "LIQUIDITY"

    def test_sentinel_not_found(self):
        response = client.get("/api/v1/sentinel/nonexistent")
        assert response.status_code == 404


class TestForensicsEndpoints:
    def test_list_reports_empty(self):
        response = client.get("/api/v1/forensics")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_report_not_found(self):
        response = client.get("/api/v1/forensics/nonexistent")
        assert response.status_code == 404
