"""Backtest management router."""
import asyncio
from fastapi import APIRouter, HTTPException, Header
from app.models import BacktestRunRequest, BacktestSaveRequest, BacktestPortfolioResponse, BacktestCompareRequest
from app.database import get_supabase
from app.routers.users import get_user_id
from app.services.backtest_engine import run_backtest
from app.services.market_data import fetch_tw_etf_list, fetch_us_etf_list, get_index_list, get_fund_list
from fastapi_cache.decorator import cache

router = APIRouter(prefix="/api/backtest", tags=["backtest"])
MAX_ETF = 10


@router.post("/run")
@cache(expire=3600)
async def run_backtest_endpoint(body: BacktestRunRequest, authorization: str = Header(default="")):
    """Run backtest calculation (requires login)."""
    get_user_id(authorization)  # validate auth

    if len(body.items) < 1:
        raise HTTPException(status_code=400, detail="At least 1 symbol required")
    if len(body.items) > MAX_ETF:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_ETF} symbols allowed")

    total_weight = sum(it.weight for it in body.items)
    if abs(total_weight - 100.0) > 0.5:
        raise HTTPException(status_code=400, detail=f"Weights must sum to 100% (got {total_weight:.1f}%)")

    items = [it.model_dump() for it in body.items]
    result = await run_backtest(items, body.start_date, body.end_date, body.initial_amount, body.display_currency)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("", response_model=list[BacktestPortfolioResponse])
async def list_portfolios(authorization: str = Header(default="")):
    user_id = get_user_id(authorization)
    sb = get_supabase()
    
    # ✅ 優化：使用單一查詢包含關聯數據，避免 N+1 問題
    # ✅ 過濾 portfolio_type='backtest'，只顯示回測結果，避免與優化/蒙地卡羅結果混淆
    portfolios = (
        sb.table("backtest_portfolios")
        .select("*, backtest_portfolio_items(*)")  # 在一個查詢中獲取 items
        .eq("user_id", user_id)
        .eq("portfolio_type", "backtest")  # ✅ 只顯示回測結果
        .order("created_at", desc=True)
        .execute()
    )
    
    # 將嵌套的關聯數據重新映射為 items 欄位
    result = []
    for p in (portfolios.data or []):
        # Supabase 回傳的結構中包含 backtest_portfolio_items 作為嵌套陣列
        if isinstance(p.get("backtest_portfolio_items"), list):
            p["items"] = p.pop("backtest_portfolio_items")
        else:
            p["items"] = []
        result.append(p)
    
    return result


@router.post("/save")
async def save_portfolio(body: BacktestSaveRequest, authorization: str = Header(default="")):
    user_id = get_user_id(authorization)
    sb = get_supabase()

    # ✅ 添加 portfolio_type='backtest' 以支持多功能共用表
    portfolio_data = {
        "user_id": user_id,
        "name": body.name,
        "start_date": body.start_date,
        "end_date": body.end_date,
        "initial_amount": body.initial_amount,
        "portfolio_type": "backtest",  # ✅ 標記為回測功能
        "results_json": body.results_json,
    }

    if body.id:
        portfolio_data["id"] = body.id
        port_res = sb.table("backtest_portfolios").upsert(portfolio_data).execute()
        sb.table("backtest_portfolio_items").delete().eq("portfolio_id", body.id).execute()
        portfolio_id = body.id
    else:
        port_res = sb.table("backtest_portfolios").insert(portfolio_data).execute()
        if not port_res.data:
            raise HTTPException(status_code=500, detail="Failed to save portfolio")
        portfolio_id = port_res.data[0]["id"]

    items_data = [
        {
            "portfolio_id": portfolio_id,
            "symbol": it.symbol,
            "name": it.name,
            "weight": it.weight,
            "category": "index" if it.category == "indices" else it.category,
        }
        for it in body.items
    ]
    
    # ✅ 添加詳細的錯誤處理
    try:
        sb.table("backtest_portfolio_items").insert(items_data).execute()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"[BACKTEST SAVE] Insert items failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"無法儲存組合項目: {str(e)}")
    
    return {"message": "Portfolio saved", "portfolio_id": portfolio_id}


@router.delete("/{portfolio_id}")
async def delete_portfolio(portfolio_id: str, authorization: str = Header(default="")):
    user_id = get_user_id(authorization)
    sb = get_supabase()
    sb.table("backtest_portfolios").delete().eq("id", portfolio_id).eq("user_id", user_id).execute()
    return {"message": "Deleted successfully"}


@router.post("/compare")
async def compare_portfolios(body: BacktestCompareRequest, authorization: str = Header(default="")):
    """Run multiple backtests in parallel for comparison (requires login)."""
    get_user_id(authorization)

    if not (2 <= len(body.portfolios) <= 4):
        raise HTTPException(status_code=400, detail="需要 2–4 個組合進行比較")

    tasks = [
        run_backtest(
            [it.model_dump() for it in p.items],
            body.start_date,
            body.end_date,
            body.initial_amount,
        )
        for p in body.portfolios
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []
    for p, r in zip(body.portfolios, results):
        if isinstance(r, Exception):
            output.append({"name": p.name, "error": str(r)})
        elif "error" in r:
            output.append({"name": p.name, "error": r["error"]})
        else:
            output.append({
                "name": p.name,
                "metrics": r.get("metrics"),
                "portfolio_value_series": r.get("portfolio_value_series"),
                "annual_returns": r.get("annual_returns"),
                "drawdown_series": r.get("drawdown_series"),
            })
    return output


@router.get("/symbols")
async def get_symbols():
    """Return available symbols for selection."""
    tw_etfs, us_etfs, funds = await asyncio.gather(
        fetch_tw_etf_list(),
        fetch_us_etf_list(),
        get_fund_list(),
    )
    indices = get_index_list()
    return {
        "tw_etf": tw_etfs,
        "us_etf": us_etfs,
        "indices": indices,
        "funds": funds,
    }
