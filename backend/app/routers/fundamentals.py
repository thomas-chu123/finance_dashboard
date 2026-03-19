from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict
from app.services.fundamentals import get_fundamentals_for_symbols
from fastapi_cache.decorator import cache

router = APIRouter(
    prefix="/api/fundamentals",
    tags=["fundamentals"]
)

@router.get("/tw", response_model=Dict[str, Dict])
@cache(expire=3600)  # Cache for 1 hour to prevent hitting TWSE rate limits
async def get_tw_fundamentals(symbols: List[str] = Query(..., description="List of symbols, e.g. 0050.TW, 2330.TW")):
    """
    Get Fundamental data (PE, Dividend Yield, PB) for a list of TWSE symbols.
    """
    try:
        data = await get_fundamentals_for_symbols(symbols)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
