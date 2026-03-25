"""Index tracking CRUD router — 支持 RSI 複合觸發條件."""
import logging
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from app.models import TrackingCreate, TrackingUpdate, TrackingResponse, AddFromBacktestRequest
from app.database import get_supabase
from app.routers.users import get_user_id
from app.services.rsi_service import get_rsi_calculation_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tracking", tags=["tracking"])


# ─── Response Models ──────────────────────────────────────────────────────────

class RSIData(BaseModel):
    """RSI 數據回應模型."""
    symbol: str
    current_rsi: Optional[float]
    rsi_period: int
    rsi_below: Optional[float]
    rsi_above: Optional[float]
    rsi_updated_at: Optional[str]
    trigger_mode: str


class TrackingRSIResponse(BaseModel):
    """包含 RSI 數據的追蹤項目回應."""
    id: str
    user_id: str
    symbol: str
    name: str
    category: str
    trigger_price: Optional[float]
    trigger_direction: str
    current_price: Optional[float]
    trigger_mode: str
    rsi_period: int
    current_rsi: Optional[float]
    rsi_below: Optional[float]
    rsi_above: Optional[float]
    notify_channel: str
    is_active: bool
    alert_triggered: bool
    last_notified_at: Optional[str]
    notes: Optional[str]
    created_at: str


# ─── Parameter Validation ────────────────────────────────────────────────────

def _validate_rsi_parameters(trigger_mode: str, rsi_below: Optional[float], rsi_above: Optional[float]) -> None:
    """
    驗證 RSI 相關參數.
    
    Args:
        trigger_mode: 觸發模式
        rsi_below: 超賣閾值
        rsi_above: 超買閾值
    
    Raises:
        HTTPException: 參數無效時
    """
    from app.models import VALID_TRIGGER_MODES
    
    if trigger_mode not in VALID_TRIGGER_MODES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid trigger_mode. Must be one of: {', '.join(VALID_TRIGGER_MODES)}"
        )
    
    if trigger_mode in ("rsi", "both"):
        # RSI 模式需要至少一個閾值
        if rsi_below is None and rsi_above is None:
            raise HTTPException(
                status_code=400,
                detail="RSI mode requires at least one threshold (rsi_below or rsi_above)"
            )
        
        # 驗證閾值範圍
        if rsi_below is not None and (rsi_below < 0 or rsi_below > 100):
            raise HTTPException(status_code=400, detail="rsi_below must be between 0 and 100")
        
        if rsi_above is not None and (rsi_above < 0 or rsi_above > 100):
            raise HTTPException(status_code=400, detail="rsi_above must be between 0 and 100")
        
        # 檢查邏輯一致性
        if rsi_below is not None and rsi_above is not None and rsi_below >= rsi_above:
            raise HTTPException(
                status_code=400,
                detail="rsi_below must be less than rsi_above"
            )


# ─── API Endpoints ────────────────────────────────────────────────────────────

@router.get("", response_model=list[TrackingRSIResponse])
async def list_tracking(authorization: str = Header(default="")):
    """列出使用者的所有追蹤項目（含 RSI 數據）."""
    user_id = get_user_id(authorization)
    sb = get_supabase()
    res = (
        sb.table("tracked_indices")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


@router.post("", response_model=TrackingRSIResponse)
async def create_tracking(body: TrackingCreate, authorization: str = Header(default="")):
    """建立新的追蹤項目（支援 RSI 觸發參數）."""
    try:
        user_id = get_user_id(authorization)
        sb = get_supabase()
        
        logger.info(f"[create_tracking] 開始創建追蹤項目: {body.symbol}, mode={body.trigger_mode}, user={user_id}")
        
        # 驗證 RSI 參數
        _validate_rsi_parameters(
            body.trigger_mode,
            body.rsi_below,
            body.rsi_above
        )
        
        # 插入數據
        data = body.model_dump()
        data["user_id"] = user_id
        data["is_active"] = True
        data["alert_triggered"] = False
        
        logger.debug(f"[create_tracking] 準備插入的數據: {data}")
        
        res = sb.table("tracked_indices").insert(data).execute()
        
        if not res.data:
            logger.error(f"[create_tracking] 插入失敗，無返回數據: {res}")
            raise HTTPException(status_code=500, detail="Create failed - no data returned from database")
        
        logger.info(f"✓ 新增追蹤項目: {body.symbol} (id={res.data[0].get('id')}, mode={body.trigger_mode}, user={user_id})")
        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[create_tracking] 發生異常: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create tracking: {str(e)}"
        )


@router.put("/{tracking_id}", response_model=TrackingRSIResponse)
async def update_tracking(tracking_id: str, body: TrackingUpdate, authorization: str = Header(default="")):
    """更新追蹤項目的觸發條件（支援 RSI 參數）."""
    user_id = get_user_id(authorization)
    sb = get_supabase()
    
    # 驗證權限
    check = (
        sb.table("tracked_indices")
        .select("id")
        .eq("id", tracking_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    
    if not check.data:
        raise HTTPException(status_code=404, detail="Tracking not found or not owned by user")
    
    # 準備更新數據
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    # 如果更新了 trigger_mode 或 RSI 相關參數，驗證
    if "trigger_mode" in update_data or any(k in update_data for k in ["rsi_below", "rsi_above"]):
        # 取得現有的觸發模式
        current = check.data
        trigger_mode = update_data.get("trigger_mode", current.get("trigger_mode", "price"))
        rsi_below = update_data.get("rsi_below", current.get("rsi_below"))
        rsi_above = update_data.get("rsi_above", current.get("rsi_above"))
        
        _validate_rsi_parameters(trigger_mode, rsi_below, rsi_above)
    
    # 執行更新
    res = (
        sb.table("tracked_indices")
        .update(update_data)
        .eq("id", tracking_id)
        .eq("user_id", user_id)
        .execute()
    )
    
    if not res.data:
        raise HTTPException(status_code=500, detail="Update failed")
    
    logger.info(f"✓ 已更新追蹤項目: {tracking_id}")
    return res.data[0]


@router.delete("/{tracking_id}")
async def delete_tracking(tracking_id: str, authorization: str = Header(default="")):
    """刪除追蹤項目 (需由擁有者執行)."""
    user_id = get_user_id(authorization)
    sb = get_supabase()
    
    # 驗證權限
    check = (
        sb.table("tracked_indices")
        .select("id")
        .eq("id", tracking_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    
    if not check.data:
        raise HTTPException(status_code=404, detail="Tracking not found or not owned by user")
    
    # 執行刪除
    sb.table("tracked_indices").delete().eq("id", tracking_id).eq("user_id", user_id).execute()
    logger.info(f"✓ 已刪除追蹤項目: {tracking_id}")
    return {"message": "Deleted successfully"}


@router.get("/{tracking_id}/rsi-data", response_model=RSIData)
async def get_rsi_data(tracking_id: str, authorization: str = Header(default="")):
    """獲取特定追蹤項目的最新 RSI 數據."""
    user_id = get_user_id(authorization)
    sb = get_supabase()
    
    # 驗證權限並取得數據
    res = (
        sb.table("tracked_indices")
        .select(
            "symbol, current_rsi, rsi_period, rsi_below, rsi_above, rsi_updated_at, trigger_mode"
        )
        .eq("id", tracking_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Tracking not found or not owned by user")
    
    data = res.data
    return {
        "symbol": data.get("symbol"),
        "current_rsi": data.get("current_rsi"),
        "rsi_period": data.get("rsi_period", 14),
        "rsi_below": data.get("rsi_below"),
        "rsi_above": data.get("rsi_above"),
        "rsi_updated_at": data.get("rsi_updated_at"),
        "trigger_mode": data.get("trigger_mode", "price"),
    }


@router.get("/{tracking_id}/rsi-history")
async def get_rsi_history(tracking_id: str, authorization: str = Header(default="")):
    """獲取追蹤項目過去 30 天的歷史 RSI 數據 (用於圖表)."""
    user_id = get_user_id(authorization)
    sb = get_supabase()
    rsi_service = get_rsi_calculation_service()
    
    # 驗證權限並取得追蹤項目
    res = (
        sb.table("tracked_indices")
        .select("symbol, category, rsi_period")
        .eq("id", tracking_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Tracking not found or not owned by user")
    
    item = res.data
    symbol = item["symbol"]
    category = item["category"]
    rsi_period = item.get("rsi_period", 14)
    
    try:
        # 獲取歷史 RSI 數據
        history_data = await rsi_service.get_historical_rsi_data(
            symbol, category, rsi_period, days=30
        )
        
        if not history_data:
            raise HTTPException(status_code=500, detail=f"Unable to fetch RSI history for {symbol}")
        
        return history_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[get_rsi_history] 錯誤: {tracking_id} - {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching RSI history: {str(e)}")


@router.post("/{tracking_id}/calculate-rsi", response_model=TrackingRSIResponse)
async def calculate_rsi_now(tracking_id: str, authorization: str = Header(default="")):
    """手動計算追蹤項目的 RSI 值 (使用者啟動的手動計算)."""
    user_id = get_user_id(authorization)
    sb = get_supabase()
    rsi_service = get_rsi_calculation_service()
    
    # 驗證權限並取得追蹤項目
    res = (
        sb.table("tracked_indices")
        .select("*")
        .eq("id", tracking_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Tracking not found or not owned by user")
    
    item = res.data
    symbol = item["symbol"]
    category = item["category"]
    rsi_period = item.get("rsi_period", 14)
    
    logger.info(f"[calculate_rsi_now] 開始計算 RSI: {symbol} (category={category}, period={rsi_period})")
    
    try:
        # 強制刷新 RSI 計算
        success = await rsi_service.update_rsi_for_tracked_index(
            tracking_id, symbol, category, rsi_period, force_refresh=True
        )
        
        logger.info(f"[calculate_rsi_now] 計算結果: success={success}, symbol={symbol}")
        
        if not success:
            logger.error(f"[calculate_rsi_now] RSI 計算失敗: {symbol} (可能是缺乏歷史數據)")
            raise HTTPException(status_code=500, detail=f"RSI calculation failed for {symbol} - insufficient historical data or API error")
        
        # 刷新數據以返回最新的 RSI 值
        updated_res = (
            sb.table("tracked_indices")
            .select("*")
            .eq("id", tracking_id)
            .single()
            .execute()
        )
        if updated_res.data:
            rsi_value = updated_res.data.get('current_rsi')
            logger.info(f"✓ 手動計算 RSI 完成: {symbol} (rsi={rsi_value})")
            return updated_res.data[0] if isinstance(updated_res.data, list) else updated_res.data
        else:
            logger.error(f"[calculate_rsi_now] 無法刷新數據: {tracking_id}")
            raise HTTPException(status_code=500, detail="Failed to refresh tracking data after calculation")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[calculate_rsi_now] 異常: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"RSI calculation error: {type(e).__name__}: {str(e)}")


@router.post("/from-backtest")
async def add_from_backtest(body: AddFromBacktestRequest, authorization: str = Header(default="")):
    """One-click add ETFs from backtest results into tracking (with RSI defaults)."""
    user_id = get_user_id(authorization)
    sb = get_supabase()
    created = []
    
    for symbol, name, category in zip(body.symbols, body.names, body.categories):
        # 檢查是否已追蹤
        existing = (
            sb.table("tracked_indices")
            .select("id")
            .eq("user_id", user_id)
            .eq("symbol", symbol)
            .execute()
        )
        if existing.data:
            continue
        
        # 使用 RSI 默認值：price 觸發模式，標準 14 期型，30/70 閾值
        data = {
            "user_id": user_id,
            "symbol": symbol,
            "name": name,
            "category": category,
            "is_active": True,
            "trigger_mode": "price",  # 回測項目默認使用 price 模式
            "rsi_period": 14,
            "rsi_below": 30.0,
            "rsi_above": 70.0,
        }
        res = sb.table("tracked_indices").insert(data).execute()
        if res.data:
            created.append(res.data[0])
            logger.info(f"✓ 從回測新增追蹤: {symbol}")
    
    return {"message": f"Added {len(created)} tracking entries", "created": created}



@router.get("/alerts")
async def get_alert_logs(authorization: str = Header(default="")):
    user_id = get_user_id(authorization)
    sb = get_supabase()
    res = (
        sb.table("alert_logs")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return res.data or []
