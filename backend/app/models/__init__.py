"""Pydantic models for the API."""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


# ──────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


# ──────────────────────────────────────────────
# Profile / User
# ──────────────────────────────────────────────
class ProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    line_user_id: Optional[str] = None
    line_binding_code: Optional[str] = None
    line_binding_expires_at: Optional[str] = None
    notify_email: Optional[bool] = None
    notify_line: Optional[bool] = None
    dashboard_quotes: Optional[List[dict]] = None


class ProfileResponse(BaseModel):
    id: str
    email: Optional[str]
    display_name: Optional[str]
    line_user_id: Optional[str]
    line_binding_code: Optional[str] = None
    line_binding_expires_at: Optional[str] = None
    notify_email: bool
    notify_line: bool
    is_admin: bool
    dashboard_quotes: Optional[List[dict]] = None
    created_at: Optional[str]


# ──────────────────────────────────────────────
# Tracked Indices
# ──────────────────────────────────────────────
VALID_CATEGORIES = {"vix", "oil", "us_etf", "tw_etf", "index", "crypto"}
VALID_DIRECTIONS = {"above", "below"}
VALID_CHANNELS = {"email", "line", "both"}
VALID_TRIGGER_MODES = {"price", "rsi", "both", "either"}  # both=AND, either=OR


class RSITriggerConfig(BaseModel):
    """RSI 觸發條件配置."""
    rsi_period: int = 14
    rsi_below: Optional[float] = None  # 超賣閾值 (例: 30)
    rsi_above: Optional[float] = None  # 超買閾值 (例: 70)


class TrackingCreate(BaseModel):
    symbol: str
    name: str
    category: str = "us_etf"
    trigger_price: Optional[float] = None
    trigger_direction: str = "below"
    trigger_mode: str = "price"  # "price", "rsi", "both" (AND), "either" (OR)
    rsi_period: int = 14  # RSI 計算週期
    rsi_below: Optional[float] = None  # RSI 超賣閾值
    rsi_above: Optional[float] = None  # RSI 超買閾值
    notify_channel: str = "email"
    notes: Optional[str] = None


class TrackingUpdate(BaseModel):
    name: Optional[str] = None
    trigger_price: Optional[float] = None
    trigger_direction: Optional[str] = None
    trigger_mode: Optional[str] = None  # "price", "rsi", "both"
    rsi_period: Optional[int] = None
    rsi_below: Optional[float] = None
    rsi_above: Optional[float] = None
    notify_channel: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class TrackingResponse(BaseModel):
    id: str
    user_id: str
    symbol: str
    name: str
    category: str
    trigger_price: Optional[float]
    trigger_direction: str
    trigger_mode: str  # "price", "rsi", "both"
    rsi_period: int
    rsi_below: Optional[float]
    rsi_above: Optional[float]
    notify_channel: str
    is_active: bool
    current_price: Optional[float]
    current_rsi: Optional[float]  # 當前 RSI 值
    price_updated_at: Optional[str]
    last_notified_at: Optional[str]
    notes: Optional[str]
    created_at: str


class AddFromBacktestRequest(BaseModel):
    symbols: List[str]
    names: List[str]
    categories: List[str]


# ──────────────────────────────────────────────
# Backtest
# ──────────────────────────────────────────────
class BacktestItem(BaseModel):
    symbol: str
    name: Optional[str] = None
    weight: float  # 0-100
    category: str = "us_etf"


class BacktestRunRequest(BaseModel):
    items: List[BacktestItem]
    start_date: str  # YYYY-MM-DD
    end_date: str
    initial_amount: float = 100000


class BacktestSaveRequest(BaseModel):
    name: str
    items: List[BacktestItem]
    start_date: str
    end_date: str
    initial_amount: float = 100000
    results_json: Optional[dict] = None


class BacktestPortfolioResponse(BaseModel):
    id: str
    user_id: str
    name: str
    start_date: str
    end_date: str
    initial_amount: float
    results_json: Optional[dict]
    items: Optional[List[dict]] = None
    created_at: str
