"""E2E 測試 — 健康檢查端點."""
import pytest
import allure


@allure.epic("API 基礎設施")
@allure.feature("健康檢查")
@pytest.mark.e2e
class TestHealthEndpoint:
    """GET /api/health 端點測試."""

    @allure.story("服務狀態")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_health_returns_200(self, client):
        """Health endpoint 應回傳 HTTP 200."""
        resp = client.get("/api/health")
        assert resp.status_code == 200

    @allure.story("服務狀態")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_health_returns_ok_status(self, client):
        """Health endpoint 回應 JSON 應包含 status: ok."""
        resp = client.get("/api/health")
        data = resp.json()
        assert data.get("status") == "ok"

    @allure.story("服務狀態")
    def test_health_returns_version(self, client):
        """Health endpoint 應回傳版本資訊."""
        resp = client.get("/api/health")
        data = resp.json()
        assert "version" in data
        assert data["version"] != ""
