from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from ..services.market_data import get_historical_prices
from ..services.optimization_engine import run_optimization
import asyncio
import pandas as pd
from fastapi_cache.decorator import cache

router = APIRouter(prefix="/api/optimize", tags=["Optimize"])

class OptimizeRequest(BaseModel):
    symbols: List[str]
    start_date: str
    end_date: str

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
