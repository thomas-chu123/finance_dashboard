"""E2E 測試 — Tracking CRUD 端點."""
import pytest
import allure
from unittest.mock import patch, MagicMock

from tests.e2e.conftest import make_supabase_mock


@allure.epic("Tracking API")
@allure.feature("投資追蹤管理")
@pytest.mark.e2e
class TestListTracking:
    """GET /api/tracking — 列出使用者追蹤項目."""

    @allure.story("未授權存取")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_list_tracking_no_auth_returns_401_or_422(self, client):
        """未帶 Authorization 應被拒絕（401 或 422）."""
        resp = client.get("/api/tracking")
        assert resp.status_code in (401, 403, 422)

    @allure.story("成功列出（空列表）")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_list_tracking_empty_returns_200(self, client, auth_headers):
        """合法授權且無追蹤項目時應回傳 200 空陣列."""
        mock_sb = make_supabase_mock(rows=[])
        with patch("app.routers.tracking.get_supabase", return_value=mock_sb):
            resp = client.get("/api/tracking", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    @allure.story("成功列出（有資料）")
    def test_list_tracking_with_data(self, client, auth_headers, sample_tracking_row):
        """有追蹤項目時應回傳非空陣列."""
        mock_sb = make_supabase_mock(rows=[sample_tracking_row])
        with patch("app.routers.tracking.get_supabase", return_value=mock_sb):
            resp = client.get("/api/tracking", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["symbol"] == "VTI"


@allure.epic("Tracking API")
@allure.feature("投資追蹤管理")
@pytest.mark.e2e
class TestCreateTracking:
    """POST /api/tracking — 新增追蹤項目."""

    @allure.story("成功新增 price 模式")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_create_tracking_price_mode(self, client, auth_headers, sample_tracking_row):
        """price 模式新增應回傳 200 及建立的項目."""
        mock_sb = make_supabase_mock(rows=[sample_tracking_row])
        with patch("app.routers.tracking.get_supabase", return_value=mock_sb):
            resp = client.post(
                "/api/tracking",
                headers=auth_headers,
                json={
                    "symbol": "VTI",
                    "name": "Vanguard Total Stock",
                    "category": "us_etf",
                    "trigger_price": 250.0,
                    "trigger_direction": "above",
                    "trigger_mode": "price",
                    "notify_channel": "email",
                },
            )
        assert resp.status_code in (200, 201)

    @allure.story("新增 rsi 模式 - 有閾值")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_tracking_rsi_mode_with_threshold(self, client, auth_headers, sample_tracking_row):
        """rsi 模式含閾值新增應成功."""
        rsi_row = {**sample_tracking_row, "trigger_mode": "rsi", "rsi_below": 30.0}
        mock_sb = make_supabase_mock(rows=[rsi_row])
        with patch("app.routers.tracking.get_supabase", return_value=mock_sb):
            resp = client.post(
                "/api/tracking",
                headers=auth_headers,
                json={
                    "symbol": "0050.TW",
                    "name": "元大台灣50",
                    "category": "tw_etf",
                    "trigger_mode": "rsi",
                    "rsi_period": 14,
                    "rsi_below": 30.0,
                    "notify_channel": "email",
                },
            )
        assert resp.status_code in (200, 201)

    @allure.story("新增 rsi 模式 - 無閾值")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_tracking_rsi_mode_no_threshold_returns_400(self, client, auth_headers):
        """rsi 模式未提供 RSI 閾值應回傳 400."""
        mock_sb = make_supabase_mock(rows=[])
        with patch("app.routers.tracking.get_supabase", return_value=mock_sb):
            resp = client.post(
                "/api/tracking",
                headers=auth_headers,
                json={
                    "symbol": "VTI",
                    "name": "Vanguard",
                    "trigger_mode": "rsi",
                    # 未設 rsi_below / rsi_above
                },
            )
        assert resp.status_code == 400

    @allure.story("無授權新增")
    def test_create_tracking_no_auth_rejected(self, client):
        """未授權不應允許新增."""
        resp = client.post(
            "/api/tracking",
            json={"symbol": "VTI", "name": "Test", "trigger_mode": "price"},
        )
        assert resp.status_code in (401, 403, 422)


@allure.epic("Tracking API")
@allure.feature("投資追蹤管理")
@pytest.mark.e2e
class TestUpdateTracking:
    """PUT /api/tracking/{id} — 更新追蹤項目."""

    @allure.story("成功更新")
    def test_update_tracking_price(self, client, auth_headers, sample_tracking_row):
        """更新觸發價格應回傳 200."""
        updated = {**sample_tracking_row, "trigger_price": 260.0}
        mock_sb = make_supabase_mock(rows=[updated])
        with patch("app.routers.tracking.get_supabase", return_value=mock_sb):
            resp = client.put(
                "/api/tracking/tracking-001",
                headers=auth_headers,
                json={"trigger_price": 260.0},
            )
        assert resp.status_code == 200

    @allure.story("無授權更新")
    def test_update_tracking_no_auth_rejected(self, client):
        """未授權不應允許更新."""
        resp = client.put(
            "/api/tracking/tracking-001",
            json={"trigger_price": 260.0},
        )
        assert resp.status_code in (401, 403, 422)


@allure.epic("Tracking API")
@allure.feature("投資追蹤管理")
@pytest.mark.e2e
class TestDeleteTracking:
    """DELETE /api/tracking/{id} — 刪除追蹤項目."""

    @allure.story("成功刪除")
    def test_delete_tracking_returns_200(self, client, auth_headers):
        """合法授權刪除應回傳 200."""
        mock_sb = make_supabase_mock(rows=[])
        with patch("app.routers.tracking.get_supabase", return_value=mock_sb):
            resp = client.delete("/api/tracking/tracking-001", headers=auth_headers)
        assert resp.status_code == 200
