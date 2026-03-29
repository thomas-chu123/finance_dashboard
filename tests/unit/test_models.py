"""單元測試 — Pydantic 模型驗證."""
import pytest
import allure
from pydantic import ValidationError

from app.models import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    TrackingCreate,
    TrackingUpdate,
    BacktestRunRequest,
    ProfileUpdate,
    ProfileResponse,
)


@allure.epic("資料模型")
@allure.feature("認證模型")
@pytest.mark.unit
class TestAuthModels:
    """RegisterRequest / LoginRequest / TokenResponse 模型測試."""

    @allure.story("RegisterRequest")
    def test_register_request_minimal(self):
        """最少字段（email + password）應有效."""
        req = RegisterRequest(email="user@test.com", password="pass123")
        assert req.email == "user@test.com"
        assert req.display_name is None

    @allure.story("RegisterRequest")
    def test_register_request_with_display_name(self):
        """含 display_name 的 RegisterRequest 應有效."""
        req = RegisterRequest(email="u@t.com", password="pw", display_name="Alice")
        assert req.display_name == "Alice"

    @allure.story("LoginRequest")
    def test_login_request_valid(self):
        """LoginRequest 應接受 email + password."""
        req = LoginRequest(email="u@t.com", password="pw")
        assert req.email == "u@t.com"

    @allure.story("TokenResponse")
    def test_token_response_defaults(self):
        """TokenResponse token_type 預設為 bearer."""
        resp = TokenResponse(
            access_token="tok123",
            user_id="uid",
            email="u@t.com",
        )
        assert resp.token_type == "bearer"


@allure.epic("資料模型")
@allure.feature("追蹤模型")
@pytest.mark.unit
class TestTrackingModels:
    """TrackingCreate / TrackingUpdate 模型測試."""

    @allure.story("TrackingCreate 預設值")
    def test_tracking_create_defaults(self):
        """TrackingCreate 應有合理的預設值."""
        t = TrackingCreate(symbol="VTI", name="Vanguard Total")
        assert t.category == "us_etf"
        assert t.trigger_direction == "below"
        assert t.trigger_mode == "price"
        assert t.rsi_period == 14

    @allure.story("TrackingCreate RSI 欄位")
    def test_tracking_create_with_rsi_fields(self):
        """包含 RSI 參數的追蹤項目應有效."""
        t = TrackingCreate(
            symbol="0050.TW",
            name="元大台灣50",
            category="tw_etf",
            trigger_mode="rsi",
            rsi_period=14,
            rsi_below=30.0,
            rsi_above=70.0,
        )
        assert t.rsi_below == 30.0
        assert t.rsi_above == 70.0
        assert t.trigger_mode == "rsi"

    @allure.story("TrackingCreate 複合模式")
    @pytest.mark.parametrize("mode", ["price", "rsi", "both", "either"])
    def test_valid_trigger_modes(self, mode):
        """所有合法的 trigger_mode 值應可接受."""
        t = TrackingCreate(symbol="VTI", name="Test", trigger_mode=mode)
        assert t.trigger_mode == mode

    @allure.story("TrackingUpdate 可選字段")
    def test_tracking_update_all_optional(self):
        """TrackingUpdate 所有字段應為可選（允許空更新）."""
        t = TrackingUpdate()
        # 不應拋出例外


@allure.epic("資料模型")
@allure.feature("回測模型")
@pytest.mark.unit
class TestBacktestModels:
    """BacktestRunRequest 模型測試."""

    @allure.story("BacktestRunRequest 有效")
    def test_backtest_run_request_valid(self):
        """有效的回測請求應正常建立."""
        from app.models import BacktestItem
        req = BacktestRunRequest(
            items=[BacktestItem(symbol="VTI", name="Vanguard", weight=70.0, category="us_etf"),
                   BacktestItem(symbol="BND", name="Vanguard Bond", weight=30.0, category="us_etf")],
            start_date="2020-01-01",
            end_date="2024-01-01",
            initial_amount=100000.0,
        )
        assert len(req.items) == 2
        assert req.initial_amount == 100000.0

    @allure.story("BacktestRunRequest 預設金額")
    def test_backtest_default_initial_amount(self):
        """initial_amount 預設值應為 100000."""
        from app.models import BacktestItem
        req = BacktestRunRequest(
            items=[BacktestItem(symbol="VTI", name="V", weight=100.0, category="us_etf")],
            start_date="2020-01-01",
            end_date="2024-01-01",
        )
        assert req.initial_amount == 100000.0


@allure.epic("資料模型")
@allure.feature("使用者資料模型")
@pytest.mark.unit
class TestProfileModels:
    """ProfileUpdate / ProfileResponse 模型測試."""

    @allure.story("ProfileUpdate 選填字段")
    def test_profile_update_optional_fields(self):
        """ProfileUpdate 全部字段均為選填."""
        p = ProfileUpdate(display_name="Alice")
        assert p.display_name == "Alice"
        assert p.notify_email is None

    @allure.story("ProfileResponse 預設值")
    def test_profile_response_defaults(self):
        """ProfileResponse notify_line / notify_email 預設為 False."""
        p = ProfileResponse(
            id="uid",
            email="u@t.com",
            display_name="Alice",
            line_user_id=None,
            notify_email=False,
            notify_line=False,
            is_admin=False,
            created_at="2024-01-01T00:00:00Z",
        )
        assert p.global_notify is True  # 預設值
        assert p.is_admin is False
