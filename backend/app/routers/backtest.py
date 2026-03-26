"""Backtest management router."""
import asyncio
from fastapi import APIRouter, HTTPException, Header
from app.models import BacktestRunRequest, BacktestSaveRequest, BacktestPortfolioResponse, BacktestCompareRequest
from app.database import get_supabase
from app.routers.users import get_user_id
from app.services.backtest_engine import run_backtest
from app.services.market_data import fetch_tw_etf_list, fetch_us_etf_list, get_index_list
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
    result = await run_backtest(items, body.start_date, body.end_date, body.initial_amount)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("", response_model=list[BacktestPortfolioResponse])
async def list_portfolios(authorization: str = Header(default="")):
    user_id = get_user_id(authorization)
    sb = get_supabase()
    portfolios = (
        sb.table("backtest_portfolios")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    result = []
    for p in (portfolios.data or []):
        items_res = (
            sb.table("backtest_portfolio_items")
            .select("*")
            .eq("portfolio_id", p["id"])
            .execute()
        )
        p["items"] = items_res.data or []
        result.append(p)
    return result


@router.post("/save")
async def save_portfolio(body: BacktestSaveRequest, authorization: str = Header(default="")):
    user_id = get_user_id(authorization)
    sb = get_supabase()

    portfolio_data = {
        "user_id": user_id,
        "name": body.name,
        "start_date": body.start_date,
        "end_date": body.end_date,
        "initial_amount": body.initial_amount,
        "results_json": body.results_json,
    }
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
    sb.table("backtest_portfolio_items").insert(items_data).execute()
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
    tw_etfs, us_etfs = await asyncio.gather(
        fetch_tw_etf_list(),
        fetch_us_etf_list(),
    )
    indices = get_index_list()
    return {
        "tw_etf": tw_etfs,
        "us_etf": us_etfs,
        "indices": indices,
    }
