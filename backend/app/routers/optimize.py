from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional, Dict
from ..services.market_data import get_historical_prices
from ..services.optimization_engine import run_optimization, _portfolio_performance
from ..database import get_supabase
from ..routers.users import get_user_id
import asyncio
import pandas as pd
import numpy as np
from fastapi_cache.decorator import cache

TRADING_DAYS = 252
RISK_FREE_RATE = 0.02

router = APIRouter(prefix="/api/optimize", tags=["Optimize"])

class OptimizeRequest(BaseModel):
    symbols: List[str]
    start_date: str
    end_date: str
    display_currency: str = "TWD"  # USD 或 TWD，預設為 TWD

class OptimizeItem(BaseModel):
    symbol: str
    name: Optional[str] = None
    category: str = "us_etf"
    weight: float = 0  # ✅ 添加權重字段

class OptimizeSaveRequest(BaseModel):
    id: Optional[str] = None  # ✅ 用於 upsert：如提供 id，則更新；否則新增
    name: str
    items: List[OptimizeItem]
    start_date: str
    end_date: str
    display_currency: str = "TWD"  # USD 或 TWD，預設為 TWD
    results_json: Optional[dict] = None

class PortfolioPerformanceRequest(BaseModel):
    symbols: List[str]
    weights: Dict[str, float]
    start_date: str
    end_date: str
    display_currency: str = "TWD"

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
    results = run_optimization(df, req.display_currency)
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

    # ✅ 方案 A：參數存儲於結果 JSONB
    optimize_results = body.results_json.copy() if body.results_json else {}
    optimize_results.update({
        "start_date": body.start_date,
        "end_date": body.end_date,
        "initial_amount": body.initial_amount,
    })
    
    optimization_data = {
        "user_id": user_id,
        "name": body.name,
        "start_date": body.start_date,      # 根層日期（可能由 Backtest 設定）
        "end_date": body.end_date,
        "initial_amount": body.initial_amount,
        "optimize_results_json": optimize_results,  # ✅ 在結果中也存儲參數
        "portfolio_type": "optimize",  # 保留以支持向後兼容
    }
    
    # ✅ 支持 upsert：如果提供 id，則更新；否則建立新組合
    if body.id:
        optimization_data["id"] = body.id
        try:
            opt_res = sb.table("backtest_portfolios").upsert(optimization_data).execute()
        except Exception as e:
            logger.error(f"[OPTIMIZE SAVE] Upsert failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"無法儲存最佳化結果: {str(e)}")
        # ✅ 更新時刪除舊的 items，稍後重新插入新的
        try:
            sb.table("backtest_portfolio_items").delete().eq("portfolio_id", body.id).execute()
        except Exception as e:
            logger.error(f"[OPTIMIZE SAVE] Delete items failed: {str(e)}", exc_info=True)
        optimization_id = body.id
    else:
        try:
            opt_res = sb.table("backtest_portfolios").insert(optimization_data).execute()
        except Exception as e:
            logger.error(f"[OPTIMIZE SAVE] Insert failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"無法儲存最佳化結果: {str(e)}")
        if not opt_res.data:
            raise HTTPException(status_code=500, detail="無法儲存最佳化結果")
        optimization_id = opt_res.data[0]["id"]
    
    logger.info(f"[OPTIMIZE SAVE] Saving with data: {optimization_data}")
    
    # ✅ 使用前端傳來的 body.items 的權重，而不是從 results_json 重新提取
    # 前端已經計算好均勻分配或優化權重，直接使用
    items_data = []
    for it in body.items:
        weight = it.weight
        if weight > 0:  # ✅ 只儲存權重 > 0 的項目
            items_data.append({
                "portfolio_id": optimization_id,
                "symbol": it.symbol,
                "name": it.name,
                "weight": weight,
                "category": it.category,
            })
    
    logger.info(f"[OPTIMIZE SAVE] Inserting {len(items_data)} items with valid weights")
    
    if items_data:
        try:
            sb.table("backtest_portfolio_items").insert(items_data).execute()
        except Exception as e:
            logger.error(f"[OPTIMIZE SAVE] Insert items failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"無法儲存組合項目: {str(e)}")
    
    return {"message": "優化結果已儲存", "optimization_id": optimization_id}

@router.get("")
async def list_optimization_results(authorization: str = Header(default="")):
    """列出已儲存的最佳化結果."""
    user_id = get_user_id(authorization)
    sb = get_supabase()
    
    # ✅ 新架構：調用共享的 backtest 列表端點
    # 優化模塊使用相同的 profile 列表，只是顯示 optimize_results_json
    results = (
        sb.table("backtest_portfolios")
        .select("*, backtest_portfolio_items(*)")
        .eq("user_id", user_id)
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
        
        # ✅ 新架構適配層：為向後兼容，將 optimize_results_json 映射到 results_json
        if p.get("optimize_results_json") and not p.get("results_json"):
            p["results_json"] = p.get("optimize_results_json")
        
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

@router.post("/calculate-custom-portfolio")
@cache(expire=3600)
async def calculate_portfolio_performance(req: PortfolioPerformanceRequest):
    """計算自定義權重組合的風險和報酬，用於圖表上的點位標記."""
    if len(req.symbols) < 2:
        raise HTTPException(status_code=400, detail="至少需要兩個以上的標的。")
    
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
    
    # Calculate returns and covariance
    returns = df.pct_change().dropna()
    mean_returns = returns.mean() * TRADING_DAYS
    cov_matrix = returns.cov() * TRADING_DAYS
    
     # Convert weights from dict to numpy array (same order as symbols, convert from % to decimal)
    weights_array = np.array([req.weights.get(sym, 0) / 100.0 for sym in req.symbols])
    
    # Verify weights sum to approximately 1（允許浮點誤差）
    weight_sum = weights_array.sum()
    # 如果權重和偏離 1.0 超過 5%，則進行歸一化
    if weight_sum > 0 and abs(weight_sum - 1.0) > 0.05:
        weights_array = weights_array / weight_sum
    elif weight_sum == 0:
        raise HTTPException(status_code=400, detail="所有權重都為零，無法計算組合性能。")
    
    # Calculate portfolio performance
    portfolio_ret, portfolio_std, portfolio_sharpe = _portfolio_performance(
        weights_array, mean_returns, cov_matrix
    )
    
    return {
        "status": "success",
        "portfolio": {
            "return": round(portfolio_ret * 100, 4),
            "volatility": round(portfolio_std * 100, 4),
            "sharpe_ratio": round(portfolio_sharpe, 4)
        },
        "symbols": req.symbols,
        "weights": req.weights
    }
