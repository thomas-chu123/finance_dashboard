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
    global_notify: Optional[bool] = None
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
    global_notify: bool = True
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


# ──────────────────────────────────────────────
# Admin - User Management
# ──────────────────────────────────────────────
class AdminUserResponse(BaseModel):
    """管理員查看的用戶信息"""
    id: str
    email: str
    display_name: Optional[str]
    is_admin: bool
    created_at: str
    last_login: Optional[str] = None


class AdminUserUpdate(BaseModel):
    """管理員編輯用戶的模型"""
    display_name: Optional[str] = None
    is_admin: Optional[bool] = None


class AdminPasswordReset(BaseModel):
    """管理員重設密碼"""
    new_password: str


# ──────────────────────────────────────────────
# Admin - Scheduler Management
# ──────────────────────────────────────────────
class SchedulerJobResponse(BaseModel):
    """Scheduler 任務信息"""
    id: str
    job_id: str
    job_name: str
    description: Optional[str]
    schedule_cron: Optional[str]
    is_enabled: bool
    last_run_at: Optional[str]
    next_run_at: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: str


class SchedulerJobRunResponse(BaseModel):
    """Scheduler 任務執行歷史"""
    id: str
    job_id: str
    started_at: Optional[str]
    completed_at: Optional[str]
    status: str
    duration_ms: Optional[int]
    error_message: Optional[str]
    created_at: str


# ──────────────────────────────────────────────
# Admin - Audit Logs
# ──────────────────────────────────────────────
class AuditLogResponse(BaseModel):
    """審計日誌信息"""
    id: str
    user_id: str
    action: str
    target_user_id: Optional[str]
    changes: Optional[dict]
    ip_address: Optional[str]
    created_at: str


# ──────────────────────────────────────────────
# Admin - System Stats
# ──────────────────────────────────────────────
class SystemStatsOverviewResponse(BaseModel):
    """系統概覽信息"""
    total_users_count: int
    active_users_count: int
    tracked_indices_count: int
    alerts_sent_count: int


class UserStatsResponse(BaseModel):
    """用戶統計信息"""
    today: int
    week: int
    month: int


class AlertStatsResponse(BaseModel):
    """警報統計信息"""
    sent_count: int
    failed_count: int


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
    id: Optional[str] = None
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
    start_date: Optional[str] = None  # ✅ 蒙地卡羅和優化不需要日期
    end_date: Optional[str] = None    # ✅ 蒙地卡羅和優化不需要日期
    initial_amount: float
    portfolio_type: Optional[str] = "backtest"  # ✅ 用於區分功能類型
    results_json: Optional[dict]
    items: Optional[List[dict]] = None
    created_at: str


class ComparePortfolioConfig(BaseModel):
    name: str
    items: List[BacktestItem]


class BacktestCompareRequest(BaseModel):
    portfolios: List[ComparePortfolioConfig]
    start_date: str
    end_date: str
    initial_amount: float = 10000

# ──────────────────────────────────────────────
# Monte Carlo Simulation
# ──────────────────────────────────────────────
class MonteCarloAsset(BaseModel):
    symbol: str
    weight: float  # 0.0 - 1.0


class MonteCarloRequest(BaseModel):
    assets: List[MonteCarloAsset]
    initial_amount: float = 100000
    years: int = 30
    simulations: int = 10000
    annual_contribution: float = 0
    annual_withdrawal: float = 0
    inflation_mean: float = 0.03
    inflation_std: float = 0.01
    adjust_for_inflation: bool = True


class MonteCarloResponse(BaseModel):
    summary: dict
    percentile_paths: dict
    history_years: int
    assets_used: List[str]
