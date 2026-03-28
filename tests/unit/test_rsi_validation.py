"""單元測試 — RSI 參數驗證（tracking router 純函數）."""
import pytest
import allure
from fastapi import HTTPException

from app.routers.tracking import _validate_rsi_parameters


@allure.epic("Tracking API")
@allure.feature("RSI 參數驗證")
@pytest.mark.unit
class TestValidateRSIParameters:
    """_validate_rsi_parameters 函數完整邊界測試."""

    # ── price 模式：不驗證 RSI 參數 ─────────────────────────────────────────

    @allure.story("price 模式")
    def test_price_mode_accepts_null_rsi(self):
        """price 模式不需要 RSI 閾值，應正常通過."""
        _validate_rsi_parameters("price", None, None)  # 不應拋出

    @allure.story("price 模式")
    def test_price_mode_ignores_rsi_values(self):
        """price 模式即使提供 RSI 值也應正常通過."""
        _validate_rsi_parameters("price", 30.0, 70.0)  # 不應拋出

    # ── rsi 模式：需要至少一個閾值 ──────────────────────────────────────────

    @allure.story("rsi 模式 - 無閾值")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_rsi_mode_no_thresholds_raises_400(self):
        """rsi 模式未設閾值應拋出 400 錯誤."""
        with pytest.raises(HTTPException) as exc:
            _validate_rsi_parameters("rsi", None, None)
        assert exc.value.status_code == 400

    @allure.story("rsi 模式 - 只有下限")
    def test_rsi_mode_only_below_valid(self):
        """rsi 模式只設下限應通過."""
        _validate_rsi_parameters("rsi", 30.0, None)

    @allure.story("rsi 模式 - 只有上限")
    def test_rsi_mode_only_above_valid(self):
        """rsi 模式只設上限應通過."""
        _validate_rsi_parameters("rsi", None, 70.0)

    @allure.story("rsi 模式 - 雙向均設")
    def test_rsi_mode_both_thresholds_valid(self):
        """rsi 模式同時設上下限應通過."""
        _validate_rsi_parameters("rsi", 30.0, 70.0)

    # ── both/either 模式 ─────────────────────────────────────────────────────

    @allure.story("both 模式 - 無閾值")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_both_mode_no_thresholds_raises_400(self):
        """both 模式未設 RSI 閾值應拋出 400."""
        with pytest.raises(HTTPException) as exc:
            _validate_rsi_parameters("both", None, None)
        assert exc.value.status_code == 400

    @allure.story("either 模式 - 無閾值")
    def test_either_mode_no_thresholds_raises_400(self):
        """either 模式未設 RSI 閾值應拋出 400."""
        with pytest.raises(HTTPException) as exc:
            _validate_rsi_parameters("either", None, None)
        assert exc.value.status_code == 400

    # ── 閾值範圍驗證 ─────────────────────────────────────────────────────────

    @allure.story("閾值範圍")
    @allure.severity(allure.severity_level.NORMAL)
    def test_rsi_below_over_100_raises_400(self):
        """rsi_below > 100 應拋出 400."""
        with pytest.raises(HTTPException) as exc:
            _validate_rsi_parameters("rsi", 105.0, None)
        assert exc.value.status_code == 400

    @allure.story("閾值範圍")
    def test_rsi_above_negative_raises_400(self):
        """rsi_above < 0 應拋出 400."""
        with pytest.raises(HTTPException) as exc:
            _validate_rsi_parameters("rsi", None, -5.0)
        assert exc.value.status_code == 400

    @allure.story("閾值邏輯")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_rsi_below_greater_than_above_raises_400(self):
        """rsi_below >= rsi_above 時應拋出 400（邏輯錯誤）."""
        with pytest.raises(HTTPException) as exc:
            _validate_rsi_parameters("rsi", 70.0, 30.0)  # 顛倒
        assert exc.value.status_code == 400

    @allure.story("閾值邏輯")
    def test_rsi_below_equals_above_raises_400(self):
        """rsi_below == rsi_above 時應拋出 400."""
        with pytest.raises(HTTPException) as exc:
            _validate_rsi_parameters("rsi", 50.0, 50.0)
        assert exc.value.status_code == 400

    # ── 無效 trigger_mode ────────────────────────────────────────────────────

    @allure.story("無效模式")
    @allure.severity(allure.severity_level.NORMAL)
    def test_invalid_trigger_mode_raises_400(self):
        """無效的 trigger_mode 應拋出 400."""
        with pytest.raises(HTTPException) as exc:
            _validate_rsi_parameters("invalid_mode", 30.0, 70.0)
        assert exc.value.status_code == 400

    @allure.story("邊界值 - 合法")
    def test_rsi_boundary_values_valid(self):
        """RSI 閾值邊界值（0 與 100）應被接受."""
        _validate_rsi_parameters("rsi", 0.0, 100.0)  # 不應拋出
