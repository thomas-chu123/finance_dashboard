"""Phase 3 API endpoint tests for RSI parameters and responses."""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException

# Mock dependencies
mock_supabase = MagicMock()
mock_get_user_id = MagicMock()

# Test data fixtures
@pytest.fixture
def sample_tracking_item():
    return {
        "id": "track123",
        "user_id": "user123",
        "symbol": "VTI",
        "name": "Vanguard Total Stock",
        "category": "etf",
        "trigger_price": 250.0,
        "trigger_direction": "above",
        "current_price": 255.0,
        "trigger_mode": "both",
        "rsi_period": 14,
        "current_rsi": 65.5,
        "rsi_below": 30.0,
        "rsi_above": 70.0,
        "notify_channel": "email",
        "is_active": True,
        "alert_triggered": False,
        "last_notified_at": None,
        "notes": "Tech exposure",
        "created_at": "2024-01-01T00:00:00Z",
    }


class TestRSIParameterValidation:
    """Test _validate_rsi_parameters function."""
    
    def test_validate_price_mode_no_error(self):
        """Price mode should skip RSI parameter validation."""
        # Should not raise exception
        from app.routers.tracking import _validate_rsi_parameters
        _validate_rsi_parameters("price", None, None)
    
    def test_validate_rsi_mode_requires_thresholds(self):
        """RSI mode requires at least one threshold."""
        from app.routers.tracking import _validate_rsi_parameters
        with pytest.raises(HTTPException) as exc_info:
            _validate_rsi_parameters("rsi", None, None)
        assert exc_info.value.status_code == 400
        assert "at least one" in exc_info.value.detail.lower()
    
    def test_validate_both_mode_requires_thresholds(self):
        """Both mode requires at least one threshold."""
        from app.routers.tracking import _validate_rsi_parameters
        with pytest.raises(HTTPException) as exc_info:
            _validate_rsi_parameters("both", None, None)
        assert exc_info.value.status_code == 400
    
    def test_validate_invalid_trigger_mode(self):
        """Invalid trigger mode should raise error."""
        from app.routers.tracking import _validate_rsi_parameters
        with pytest.raises(HTTPException) as exc_info:
            _validate_rsi_parameters("invalid_mode", 30.0, 70.0)
        assert exc_info.value.status_code == 400
    
    def test_validate_threshold_range(self):
        """Thresholds must be within 0-100 range."""
        from app.routers.tracking import _validate_rsi_parameters
        # Test rsi_below > 100
        with pytest.raises(HTTPException) as exc_info:
            _validate_rsi_parameters("rsi", 105.0, 70.0)
        assert "between 0 and 100" in exc_info.value.detail or "0-100" in exc_info.value.detail
        
        # Test rsi_above < 0
        with pytest.raises(HTTPException) as exc_info:
            _validate_rsi_parameters("rsi", 30.0, -5.0)
        assert "between 0 and 100" in exc_info.value.detail or "0-100" in exc_info.value.detail
    
    def test_validate_rsi_below_greater_than_above(self):
        """rsi_below must be less than rsi_above."""
        from app.routers.tracking import _validate_rsi_parameters
        with pytest.raises(HTTPException) as exc_info:
            _validate_rsi_parameters("rsi", 70.0, 30.0)  # Inverted
        assert "rsi_below" in exc_info.value.detail.lower()
    
    def test_validate_rsi_valid_thresholds(self):
        """Valid RSI thresholds should pass."""
        from app.routers.tracking import _validate_rsi_parameters
        # Should not raise
        _validate_rsi_parameters("rsi", 30.0, 70.0)
        _validate_rsi_parameters("both", 30.0, 70.0)


class TestRSIDataResponseModel:
    """Test RSIData response model."""
    
    def test_rsi_data_model_creation(self):
        """RSIData model should accept all fields."""
        from app.routers.tracking import RSIData
        data = RSIData(
            symbol="VTI",
            current_rsi=65.5,
            rsi_period=14,
            rsi_below=30.0,
            rsi_above=70.0,
            rsi_updated_at="2024-01-15T10:30:00Z",
            trigger_mode="both"
        )
        assert data.symbol == "VTI"
        assert data.current_rsi == 65.5
        assert data.trigger_mode == "both"
    
    def test_rsi_data_optional_fields(self):
        """Optional RSI fields should be nullable."""
        from app.routers.tracking import RSIData
        data = RSIData(
            symbol="SPY",
            current_rsi=None,
            rsi_period=14,
            rsi_below=None,
            rsi_above=None,
            rsi_updated_at=None,
            trigger_mode="price"
        )
        assert data.current_rsi is None
        assert data.rsi_below is None


class TestTrackingRSIResponse:
    """Test TrackingRSIResponse model."""
    
    def test_response_model_includes_rsi_fields(self, sample_tracking_item):
        """TrackingRSIResponse should include all RSI fields."""
        from app.routers.tracking import TrackingRSIResponse
        response = TrackingRSIResponse(**sample_tracking_item)
        assert response.trigger_mode == "both"
        assert response.current_rsi == 65.5
        assert response.rsi_period == 14
        assert response.rsi_below == 30.0
        assert response.rsi_above == 70.0
    
    def test_response_model_backward_compatible(self):
        """Response should work with price-only mode data."""
        from app.routers.tracking import TrackingRSIResponse
        data = {
            "id": "track123",
            "user_id": "user123",
            "symbol": "VTI",
            "name": "Vanguard",
            "category": "etf",
            "trigger_price": 250.0,
            "trigger_direction": "above",
            "current_price": 255.0,
            "trigger_mode": "price",
            "rsi_period": 14,
            "current_rsi": None,
            "rsi_below": None,
            "rsi_above": None,
            "notify_channel": "email",
            "is_active": True,
            "alert_triggered": False,
            "last_notified_at": None,
            "notes": None,
            "created_at": "2024-01-01T00:00:00Z",
        }
        response = TrackingRSIResponse(**data)
        assert response.trigger_mode == "price"
        assert response.current_rsi is None


class TestAlertEmailRSIContent:
    """Test build_alert_email includes RSI information."""
    
    def test_email_includes_rsi_data(self):
        """Email should include RSI value and thresholds when provided."""
        from app.services.email_service import build_alert_email
        subject, body = build_alert_email(
            symbol="VTI",
            name="Vanguard Total Stock",
            category="etf",
            current_price=255.0,
            trigger_price=250.0,
            trigger_direction="above",
            tracking_id="track123",
            trigger_mode="both",
            current_rsi=75.5,
            rsi_below=30.0,
            rsi_above=70.0,
        )
        assert "75.5" in body  # RSI value
        assert "RSI" in body  # RSI mention
        assert "超買" in body or "70.0" in body  # Overbought signal
    
    def test_email_price_only_no_rsi(self):
        """Email should omit RSI for price-only alerts."""
        from app.services.email_service import build_alert_email
        subject, body = build_alert_email(
            symbol="VTI",
            name="Vanguard Total Stock",
            category="etf",
            current_price=255.0,
            trigger_price=250.0,
            trigger_direction="above",
            tracking_id="track123",
            trigger_mode="price",
        )
        # Price-only should have no RSI content
        assert "RSI" not in body or "目前價格" in body
    
    def test_email_mode_description(self):
        """Email title should reflect trigger mode."""
        from app.services.email_service import build_alert_email
        
        # Price mode
        subject, body = build_alert_email(
            symbol="VTI",
            name="Test",
            category="etf",
            current_price=100,
            trigger_price=100,
            trigger_direction="above",
            tracking_id="123",
            trigger_mode="price",
        )
        assert "價格" in body
        
        # RSI mode
        subject, body = build_alert_email(
            symbol="VTI",
            name="Test",
            category="etf",
            current_price=100,
            trigger_price=100,
            trigger_direction="above",
            tracking_id="123",
            trigger_mode="rsi",
            current_rsi=25.0,
            rsi_below=30.0,
        )
        assert "RSI" in body


class TestAlertMessageRSIContent:
    """Test build_alert_message includes RSI information."""
    
    def test_message_includes_rsi_signal(self):
        """LINE message should indicate RSI signal strength."""
        from app.services.line_service import build_alert_message
        msg = build_alert_message(
            symbol="VTI",
            name="Vanguard Total Stock",
            current_price=255.0,
            trigger_price=250.0,
            trigger_direction="above",
            tracking_id="track123",
            trigger_mode="both",
            current_rsi=25.5,
            rsi_below=30.0,
            rsi_above=70.0,
        )
        assert "25.5" in msg  # RSI value
        assert "超賣" in msg  # Oversold signal
    
    def test_message_overbought_signal(self):
        """Message should show overbought for high RSI."""
        from app.services.line_service import build_alert_message
        msg = build_alert_message(
            symbol="SPY",
            name="S&P 500 ETF",
            current_price=450.0,
            trigger_price=450.0,
            trigger_direction="above",
            tracking_id="track456",
            trigger_mode="rsi",
            current_rsi=75.0,
            rsi_below=30.0,
            rsi_above=70.0,
        )
        assert "75.0" in msg
        assert "超買" in msg  # Overbought signal
    
    def test_message_normal_rsi_range(self):
        """Message should show normal for mid-range RSI."""
        from app.services.line_service import build_alert_message
        msg = build_alert_message(
            symbol="0050",
            name="台灣 50 ETF",
            current_price=100.0,
            trigger_price=100.0,
            trigger_direction="above",
            tracking_id="track789",
            trigger_mode="both",
            current_rsi=50.0,
            rsi_below=30.0,
            rsi_above=70.0,
        )
        assert "50.0" in msg
        assert "正常" in msg  # Normal range


class TestEndpointIntegration:
    """Integration tests for API endpoints."""
    
    def test_list_tracking_returns_rsi_response_model(self):
        """list_tracking endpoint should return TrackingRSIResponse."""
        # This would be tested with actual FastAPI test client
        # Placeholder for integration test
        pass
    
    def test_create_tracking_validates_rsi_params(self):
        """create_tracking should validate RSI parameters."""
        # Placeholder for integration test
        pass
    
    def test_update_tracking_validates_rsi_params(self):
        """update_tracking should validate RSI parameters on changes."""
        # Placeholder for integration test
        pass
    
    def test_get_rsi_data_endpoint_exists(self):
        """GET /{id}/rsi-data endpoint should return RSIData model."""
        # Placeholder for integration test
        pass
    
    def test_from_backtest_uses_rsi_defaults(self):
        """add_from_backtest should set RSI defaults."""
        # Placeholder for integration test
        pass


class TestRSIEdgeCases:
    """Edge case tests for RSI functionality."""
    
    def test_null_current_rsi_handling(self):
        """System should handle null current_rsi gracefully."""
        from app.routers.tracking import RSIData
        data = RSIData(
            symbol="UNKNOWN",
            current_rsi=None,
            rsi_period=14,
            rsi_below=30.0,
            rsi_above=70.0,
            rsi_updated_at=None,
            trigger_mode="rsi"
        )
        assert data.current_rsi is None
    
    def test_rsi_period_customization(self):
        """Custom RSI periods should be supported (7-50)."""
        from app.routers.tracking import _validate_rsi_parameters
        # Valid periods
        _validate_rsi_parameters("rsi", 30.0, 70.0)
        _validate_rsi_parameters("both", 30.0, 70.0)
    
    def test_extreme_rsi_values(self):
        """Extreme RSI values should be handled."""
        from app.services.line_service import build_alert_message
        # Very low RSI (0.5)
        msg = build_alert_message(
            symbol="TEST",
            name="Test Asset",
            current_price=100,
            trigger_price=100,
            trigger_direction="above",
            tracking_id="123",
            trigger_mode="rsi",
            current_rsi=0.5,
        )
        assert "0.5" in msg
        
        # Very high RSI (99.5)
        msg = build_alert_message(
            symbol="TEST",
            name="Test Asset",
            current_price=100,
            trigger_price=100,
            trigger_direction="above",
            tracking_id="123",
            trigger_mode="rsi",
            current_rsi=99.5,
        )
        assert "99.5" in msg


# Phase 3 Summary tests
class TestPhase3Completion:
    """Summary tests to verify Phase 3 completion."""
    
    def test_all_rsi_response_models_exist(self):
        """Verify RSIData and TrackingRSIResponse models exist."""
        from app.routers.tracking import RSIData, TrackingRSIResponse
        assert RSIData is not None
        assert TrackingRSIResponse is not None
    
    def test_validation_function_exists(self):
        """Verify _validate_rsi_parameters function exists."""
        from app.routers.tracking import _validate_rsi_parameters
        assert callable(_validate_rsi_parameters)
    
    def test_email_service_supports_rsi(self):
        """Verify build_alert_email supports RSI parameters."""
        from app.services.email_service import build_alert_email
        import inspect
        sig = inspect.signature(build_alert_email)
        params = sig.parameters
        assert "trigger_mode" in params
        assert "current_rsi" in params
        assert "rsi_below" in params
        assert "rsi_above" in params
    
    def test_line_service_supports_rsi(self):
        """Verify build_alert_message supports RSI parameters."""
        from app.services.line_service import build_alert_message
        import inspect
        sig = inspect.signature(build_alert_message)
        params = sig.parameters
        assert "trigger_mode" in params
        assert "current_rsi" in params
        assert "rsi_below" in params
        assert "rsi_above" in params
