from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional
from app.models import MonteCarloRequest, MonteCarloResponse
from app.routers.users import get_user_id
from app.services.monte_carlo_engine import run_monte_carlo_simulation
from app.database import get_supabase
from fastapi_cache.decorator import cache
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monte-carlo", tags=["monte-carlo"])

class MonteCarloItem(BaseModel):
    symbol: str
    name: Optional[str] = None
    weight: float
    category: str = "us_etf"

class MonteCarloSaveRequest(BaseModel):
    name: str
    items: List[MonteCarloItem]
    initial_amount: float
    years: int
    simulations: int
    annual_contribution: float = 0
    annual_withdrawal: float = 0
    inflation_mean: float = 0.02
    inflation_std: float = 0.01
    adjust_for_inflation: bool = True
    results_json: Optional[dict] = None
    portfolio_id: Optional[str] = None  # 用於自動儲存時關聯回原組合

@router.post("/run", response_model=MonteCarloResponse)
@cache(expire=3600)
async def run_monte_carlo_endpoint(body: MonteCarloRequest, authorization: str = Header(default="")):
    """
    Run a Monte Carlo simulation.
    Requires user authentication.
    """
    get_user_id(authorization) # Validate auth
    
    if not body.assets:
        raise HTTPException(status_code=400, detail="At least one asset is required")
    
    total_weight = sum(a.weight for a in body.assets)
    if abs(total_weight - 1.0) > 0.01:
        # We'll allow it but the engine will normalize it. 
        # However, it's better to warn or error if it's way off.
        pass

    assets_list = [a.model_dump() for a in body.assets]
    
    try:
        result = await run_monte_carlo_simulation(
            assets=assets_list,
            initial_amount=body.initial_amount,
            years=body.years,
            simulations=body.simulations,
            annual_contribution=body.annual_contribution,
            annual_withdrawal=body.annual_withdrawal,
            inflation_mean=body.inflation_mean,
            inflation_std=body.inflation_std,
            adjust_for_inflation=body.adjust_for_inflation
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
            
        return result
    except Exception as e:
        logger.error(f"Monte Carlo simulation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")

@router.post("/save")
async def save_monte_carlo(body: MonteCarloSaveRequest, authorization: str = Header(default="")):
    """儲存蒙地卡羅模擬結果."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        user_id = get_user_id(authorization)
        logger.info(f"[MONTE_CARLO SAVE] user_id extracted: {user_id}")
    except Exception as e:
        logger.error(f"[MONTE_CARLO SAVE] Failed to extract user_id: {e}")
        raise HTTPException(status_code=401, detail=f"認證失敗: {str(e)}")
    
    if not user_id:
        logger.error("[MONTE_CARLO SAVE] user_id is None or empty")
        raise HTTPException(status_code=401, detail="無法獲取用戶身份")
    
    sb = get_supabase()

    # ✅ 改為寫入 backtest_portfolios（共用表）
    # 蒙地卡羅模擬不使用 start_date/end_date，設為 None
    # ✅ 將配置參數包含在 results_json.config 中，以便前端加載時可以還原配置
    results_data = body.results_json or {}
    if not isinstance(results_data, dict):
        results_data = {}
    
    # ✅ 保存配置參數，前端加載時可以還原
    results_data["config"] = {
        "years": body.years,
        "simulations": body.simulations,
        "annual_contribution": body.annual_contribution,
        "annual_withdrawal": body.annual_withdrawal,
        "inflation_mean": body.inflation_mean,
        "inflation_std": body.inflation_std,
        "adjust_for_inflation": body.adjust_for_inflation,
    }
    
    mc_data = {
        "user_id": user_id,
        "name": body.name,
        "initial_amount": body.initial_amount,
        "start_date": None,  # ✅ 蒙地卡羅不定義特定日期範圍
        "end_date": None,    # ✅ 蒙地卡羅不定義特定日期範圍
        "portfolio_type": "monte_carlo",  # ✅ 標記為蒙地卡羅功能
        "results_json": results_data,  # ✅ 包含配置參數
    }
    
    logger.info(f"[MONTE_CARLO SAVE] Saving with data: {mc_data}")
    
    try:
        # 寫入 backtest_portfolios 表
        mc_res = sb.table("backtest_portfolios").insert(mc_data).execute()
    except Exception as e:
        logger.error(f"[MONTE_CARLO SAVE] Insert failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"無法儲存蒙地卡羅結果: {str(e)}")

    simulation_id = mc_res.data[0]["id"]
    items_data = [
        {
            "portfolio_id": simulation_id,  # ✅ 改為 portfolio_id（共用表的 FK）
            "symbol": it.symbol,
            "name": it.name,
            "weight": it.weight,
            "category": it.category,
        }
        for it in body.items
    ]
    # ✅ 改為寫入 backtest_portfolio_items（共用 items 表）
    sb.table("backtest_portfolio_items").insert(items_data).execute()
    return {"message": "蒙地卡羅結果已儲存", "monte_carlo_id": simulation_id}

@router.get("")
async def list_monte_carlo_results(authorization: str = Header(default="")):
    """列出已儲存的蒙地卡羅模擬結果."""
    user_id = get_user_id(authorization)
    sb = get_supabase()
    
    # ✅ 優化：使用單一查詢包含關聯數據，避免 N+1 問題
    # ✅ 從 backtest_portfolios 共用表讀取，過濾 portfolio_type='monte_carlo'
    results = (
        sb.table("backtest_portfolios")
        .select("*, backtest_portfolio_items(*)")
        .eq("user_id", user_id)
        .eq("portfolio_type", "monte_carlo")  # ✅ 只顯示蒙地卡羅結果
        .order("created_at", desc=True)
        .execute()
    )
    
    # 將嵌套的關聯數據重新映射為 items 欄位
    result = []
    for p in (results.data or []):
        # Supabase 回傳的結構中包含 backtest_portfolio_items 作為嵌套陣列
        if isinstance(p.get("backtest_portfolio_items"), list):
            p["items"] = p.pop("backtest_portfolio_items")
        else:
            p["items"] = []
        result.append(p)
    
    return result

@router.delete("/{monte_carlo_id}")
async def delete_monte_carlo(monte_carlo_id: str, authorization: str = Header(default="")):
    """刪除蒙地卡羅結果."""
    user_id = get_user_id(authorization)
    sb = get_supabase()
    # ✅ 從 backtest_portfolios 共用表刪除
    sb.table("backtest_portfolios").delete().eq("id", monte_carlo_id).eq("user_id", user_id).execute()
    return {"message": "蒙地卡羅結果已刪除"}
