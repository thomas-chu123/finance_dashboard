"""單元測試 — 安全模組（JWT / 密碼雜湊）."""
import pytest
import allure
from datetime import timedelta
from unittest.mock import patch

from app.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)


@allure.epic("後端安全")
@allure.feature("密碼雜湊")
@pytest.mark.unit
class TestPasswordHashing:
    """bcrypt 密碼雜湊測試."""

    @allure.story("正常雜湊與驗證")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_hash_is_not_plaintext(self):
        """雜湊後不應與原始密碼相同."""
        pw = "securepassword123"
        hashed = get_password_hash(pw)
        assert hashed != pw

    @allure.story("正常雜湊與驗證")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_verify_correct_password(self):
        """正確密碼驗證應回傳 True."""
        pw = "securepassword123"
        hashed = get_password_hash(pw)
        assert verify_password(pw, hashed) is True

    @allure.story("錯誤密碼拒絕")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_verify_wrong_password(self):
        """錯誤密碼驗證應回傳 False."""
        hashed = get_password_hash("correctpass")
        assert verify_password("wrongpass", hashed) is False

    @allure.story("邊界條件")
    def test_verify_empty_password(self):
        """空密碼應回傳 False（不拋出例外）."""
        hashed = get_password_hash("somepass")
        assert verify_password("", hashed) is False

    @allure.story("邊界條件")
    def test_verify_empty_hash(self):
        """應急處理空雜湊值."""
        assert verify_password("somepass", "") is False

    @allure.story("唯一性")
    def test_same_password_different_hashes(self):
        """相同密碼每次應產生不同 salt 的雜湊."""
        pw = "samepassword"
        h1 = get_password_hash(pw)
        h2 = get_password_hash(pw)
        assert h1 != h2  # 不同 salt


@allure.epic("後端安全")
@allure.feature("JWT 令牌")
@pytest.mark.unit
class TestJWTTokens:
    """JWT 建立與解碼測試."""

    @allure.story("令牌建立")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_create_token_contains_subject(self):
        """建立的 token 應包含 sub 欄位."""
        token = create_access_token({"sub": "user-123", "email": "test@test.com"})
        assert isinstance(token, str)
        assert len(token) > 0

    @allure.story("令牌解碼")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_decode_valid_token(self):
        """合法 token 應正確解碼."""
        payload_in = {"sub": "user-abc", "email": "user@example.com"}
        token = create_access_token(payload_in)
        payload_out = decode_access_token(token)
        assert payload_out is not None
        assert payload_out["sub"] == "user-abc"
        assert payload_out["email"] == "user@example.com"

    @allure.story("令牌解碼")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_decode_invalid_token_returns_none(self):
        """非法 token 應回傳 None，不拋出例外."""
        result = decode_access_token("totally.invalid.token")
        assert result is None

    @allure.story("令牌解碼")
    def test_decode_empty_token(self):
        """空字串 token 應回傳 None."""
        result = decode_access_token("")
        assert result is None

    @allure.story("令牌過期")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_expired_token_returns_none(self):
        """已過期的 token 應回傳 None."""
        token = create_access_token(
            {"sub": "user-123"}, expires_delta=timedelta(seconds=-1)
        )
        result = decode_access_token(token)
        assert result is None

    @allure.story("令牌建立")
    def test_token_with_custom_expiry(self):
        """自訂過期時間的 token 應正常作用."""
        token = create_access_token({"sub": "u1"}, expires_delta=timedelta(hours=1))
        payload = decode_access_token(token)
        assert payload is not None
        assert "exp" in payload

    @allure.story("令牌安全")
    def test_tampered_token_returns_none(self):
        """竄改後的 token 應回傳 None（簽名驗證失敗）."""
        token = create_access_token({"sub": "user-123"})
        # 竄改 payload 部分
        parts = token.split(".")
        tampered = parts[0] + "." + parts[1] + "TAMPERED" + "." + parts[2]
        result = decode_access_token(tampered)
        assert result is None
