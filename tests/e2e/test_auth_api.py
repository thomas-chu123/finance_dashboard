"""E2E 測試 — 認證端點（register / login / logout）."""
import pytest
import allure
from unittest.mock import patch, MagicMock

from tests.e2e.conftest import make_supabase_mock


@allure.epic("認證系統")
@allure.feature("使用者認證 API")
@pytest.mark.e2e
class TestRegisterEndpoint:
    """POST /api/auth/register 端點測試."""

    @allure.story("成功註冊")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_register_new_user_returns_200(self, client):
        """新使用者註冊應回傳 200 及 user_id."""
        # 模擬：email 不存在，insert 成功
        mock_sb = make_supabase_mock(rows=[])
        insert_result = MagicMock()
        insert_result.data = [{"id": "new-uid"}]
        mock_sb.table.return_value.insert.return_value.execute.return_value = insert_result

        with patch("app.routers.auth.get_supabase", return_value=mock_sb):
            resp = client.post(
                "/api/auth/register",
                json={"email": "newuser@test.com", "password": "securepass123"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "user_id" in data

    @allure.story("Email 已存在")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_register_duplicate_email_returns_400(self, client):
        """重複 email 註冊應回傳 400."""
        existing_user = [{"id": "existing-uid"}]
        mock_sb = make_supabase_mock(rows=existing_user)

        with patch("app.routers.auth.get_supabase", return_value=mock_sb):
            resp = client.post(
                "/api/auth/register",
                json={"email": "existing@test.com", "password": "pass123"},
            )
        assert resp.status_code == 400


@allure.epic("認證系統")
@allure.feature("使用者認證 API")
@pytest.mark.e2e
class TestLoginEndpoint:
    """POST /api/auth/login 端點測試."""

    @allure.story("成功登入")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_login_returns_access_token(self, client):
        """正確憑證登入應回傳 access_token。"""
        from app.security import get_password_hash
        hashed = get_password_hash("correctpass")
        user_row = [{
            "id": "user-001",
            "email": "user@test.com",
            "hashed_password": hashed,
        }]
        mock_sb = make_supabase_mock(rows=user_row)

        with patch("app.routers.auth.get_supabase", return_value=mock_sb):
            resp = client.post(
                "/api/auth/login",
                json={"email": "user@test.com", "password": "correctpass"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data.get("token_type") == "bearer"

    @allure.story("錯誤密碼")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_login_wrong_password_returns_401(self, client):
        """錯誤密碼應回傳 401 Unauthorized."""
        from app.security import get_password_hash
        hashed = get_password_hash("realpass")
        user_row = [{"id": "uid", "email": "u@t.com", "hashed_password": hashed}]
        mock_sb = make_supabase_mock(rows=user_row)

        with patch("app.routers.auth.get_supabase", return_value=mock_sb):
            resp = client.post(
                "/api/auth/login",
                json={"email": "u@t.com", "password": "wrongpass"},
            )
        assert resp.status_code == 401

    @allure.story("使用者不存在")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_login_nonexistent_user_returns_401(self, client):
        """不存在的使用者應回傳 401."""
        mock_sb = make_supabase_mock(rows=[])  # 查無使用者

        with patch("app.routers.auth.get_supabase", return_value=mock_sb):
            resp = client.post(
                "/api/auth/login",
                json={"email": "ghost@test.com", "password": "pass"},
            )
        assert resp.status_code == 401

    @allure.story("Token 結構")
    def test_login_token_is_decodable(self, client):
        """回傳的 JWT 應可被解碼驗證."""
        from app.security import get_password_hash, decode_access_token
        hashed = get_password_hash("mypass")
        mock_sb = make_supabase_mock(rows=[{
            "id": "u-decode", "email": "d@t.com", "hashed_password": hashed,
        }])

        with patch("app.routers.auth.get_supabase", return_value=mock_sb):
            resp = client.post("/api/auth/login", json={"email": "d@t.com", "password": "mypass"})

        token = resp.json().get("access_token")
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "u-decode"


@allure.epic("認證系統")
@allure.feature("使用者認證 API")
@pytest.mark.e2e
class TestLogoutEndpoint:
    """POST /api/auth/logout 端點測試."""

    @allure.story("登出")
    def test_logout_returns_200(self, client, auth_headers):
        """登出端點應回傳 200（JWT 為無狀態，主要由前端清除）."""
        resp = client.post("/api/auth/logout", headers=auth_headers)
        assert resp.status_code == 200
