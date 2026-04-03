from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional
from ..services.market_data import get_historical_prices
from ..services.optimization_engine import run_optimization
from ..database import get_supabase
from ..routers.users import get_user_id
import asyncio
import pandas as pd
from fastapi_cache.decorator import cache

router = APIRouter(prefix="/api/optimize", tags=["Optimize"])

class OptimizeRequest(BaseModel):
    symbols: List[str]
    start_date: str
    end_date: str

class OptimizeItem(BaseModel):
    symbol: str
    name: Optional[str] = None
    category: str = "us_etf"

class OptimizeSaveRequest(BaseModel):
    name: str
    items: List[OptimizeItem]
    start_date: str
    end_date: str
    results_json: Optional[dict] = None
    portfolio_id: Optional[str] = None  # 用於自動儲存時關聯回原組合

@router.post("")
@cache(expire=3600)  # Cache identical requests for 1 hour
async def optimize_portfolio(req: OptimizeRequest):
    if len(req.symbols) < 2:
        raise HTTPException(status_code=400, detail="至少需要兩個以上的標的才能進行最佳化。")
    if len(req.symbols) > 15:
        raise HTTPException(status_code=400, detail="最多選擇 15 個標的進行最佳化。")

    # Fetch historical data concurrently
    tasks = [
        get_historical_prices(symbol, req.start_date, req.end_date)
        for symbol in req.symbols
    ]
    series_list = await asyncio.gather(*tasks)
    
    # Combine into a single DataFrame
    df = pd.DataFrame({s.name: s for s in series_list if not s.empty})
    df.dropna(inplace=True)

    if df.empty or len(df) < 30:
        raise HTTPException(status_code=400, detail="此日期區間內的有效交易資料過少。")
        
    # Run Markowitz Optimization
    results = run_optimization(df)
    if "error" in results:
        raise HTTPException(status_code=400, detail=results["error"])

    return {
        "status": "success",
        "results": results,
        "symbols": req.symbols,
        "date_range": {
            "start": req.start_date,
            "end": req.end_date
        }
    }

@router.post("/save")
async def save_optimization(body: OptimizeSaveRequest, authorization: str = Header(default="")):
    """儲存最佳化結果."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        user_id = get_user_id(authorization)
        logger.info(f"[OPTIMIZE SAVE] user_id extracted: {user_id}")
    except Exception as e:
        logger.error(f"[OPTIMIZE SAVE] Failed to extract user_id: {e}")
        raise HTTPException(status_code=401, detail=f"認證失敗: {str(e)}")
    
    if not user_id:
        logger.error("[OPTIMIZE SAVE] user_id is None or empty")
        raise HTTPException(status_code=401, detail="無法獲取用戶身份")
    
    sb = get_supabase()

    # ✅ 改為寫入 backtest_portfolios（共用表）
    optimization_data = {
        "user_id": user_id,
        "name": body.name,
        "start_date": body.start_date,
        "end_date": body.end_date,
        "initial_amount": 0,  # 優化沒有初始金額
        "portfolio_type": "optimize",  # ✅ 標記為優化功能
        "results_json": body.results_json,
    }
    
    logger.info(f"[OPTIMIZE SAVE] Saving with data: {optimization_data}")
    
    try:
        # 寫入 backtest_portfolios 表
        opt_res = sb.table("backtest_portfolios").insert(optimization_data).execute()
    except Exception as e:
        logger.error(f"[OPTIMIZE SAVE] Insert failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"無法儲存最佳化結果: {str(e)}")

    optimization_id = opt_res.data[0]["id"]
    items_data = [
        {
            "portfolio_id": optimization_id,  # ✅ 改為 portfolio_id（共用表的 FK）
            "symbol": it.symbol,
            "name": it.name,
            "weight": 0,  # ✅ 優化結果的權重在 results_json 中，item 單獨不儲存權重
            "category": it.category,
        }
        for it in body.items
    ]
    # ✅ 改為寫入 backtest_portfolio_items（共用 items 表）
    sb.table("backtest_portfolio_items").insert(items_data).execute()
    return {"message": "優化結果已儲存", "optimization_id": optimization_id}

@router.get("")
async def list_optimization_results(authorization: str = Header(default="")):
    """列出已儲存的最佳化結果."""
    user_id = get_user_id(authorization)
    sb = get_supabase()
    
    # ✅ 優化：使用單一查詢包含關聯數據，避免 N+1 問題
    # ✅ 從 backtest_portfolios 共用表讀取，過濾 portfolio_type='optimize'
    results = (
        sb.table("backtest_portfolios")
        .select("*, backtest_portfolio_items(*)")
        .eq("user_id", user_id)
        .eq("portfolio_type", "optimize")  # ✅ 只顯示優化結果
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

@router.delete("/{optimization_id}")
async def delete_optimization(optimization_id: str, authorization: str = Header(default="")):
    """刪除最佳化結果."""
    user_id = get_user_id(authorization)
    sb = get_supabase()
    # ✅ 從 backtest_portfolios 共用表刪除
    sb.table("backtest_portfolios").delete().eq("id", optimization_id).eq("user_id", user_id).execute()
    return {"message": "最佳化結果已刪除"}
