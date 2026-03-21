import httpx
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

TWSE_BWIBBU_URL = "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL"
TWSE_ETF_LIST_URL = "https://openapi.twse.com.tw/v1/exchangeReport/TWT53U"
TPEX_PE_URL = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_peratio_analysis"

async def fetch_fundamental_data() -> List[Dict]:
    """
    Fetches fundamental data from TWSE (Stocks and ETFs) and TPEx.
    """
    all_data = []
    
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        # 1. Fetch from TWSE Stocks
        try:
            response = await client.get(TWSE_BWIBBU_URL)
            if response.status_code == 200:
                twse_data = response.json()
                for item in twse_data:
                    all_data.append({
                        "code": item.get("Code"),
                        "name": item.get("Name"),
                        "pe_ratio": item.get("PEratio"),
                        "dividend_yield": item.get("DividendYield"),
                        "pb_ratio": item.get("PBratio"),
                        "source": "TWSE_Stock"
                    })
        except Exception as e:
            logger.error(f"Error fetching TWSE stock fundamental data: {e}")

        # 2. Fetch from TWSE ETFs (for name mapping at least)
        try:
            response = await client.get(TWSE_ETF_LIST_URL)
            if response.status_code == 200:
                etf_data = response.json()
                for item in etf_data:
                    all_data.append({
                        "code": item.get("Code"),
                        "name": item.get("Name"),
                        "pe_ratio": "N/A",
                        "dividend_yield": "N/A",
                        "pb_ratio": "N/A",
                        "source": "TWSE_ETF"
                    })
        except Exception as e:
            logger.error(f"Error fetching TWSE ETF data: {e}")

        # 3. Fetch from TPEx
        try:
            response = await client.get(TPEX_PE_URL)
            if response.status_code == 200:
                tpex_data = response.json()
                for item in tpex_data:
                    all_data.append({
                        "code": item.get("SecuritiesCompanyCode"),
                        "name": item.get("CompanyName"),
                        "pe_ratio": item.get("PriceEarningRatio"),
                        "dividend_yield": item.get("YieldRatio"),
                        "pb_ratio": item.get("PriceBookRatio"),
                        "source": "TPEx"
                    })
        except Exception as e:
            logger.error(f"Error fetching TPEx fundamental data: {e}")

    return all_data

async def get_fundamentals_for_symbols(symbols: List[str]) -> Dict[str, Dict]:
    """
    Given a list of symbol codes, returns a dictionary mapped by symbol with their fundamental data.
    """
    all_items = await fetch_fundamental_data()
    if not all_items:
        # Return empty fundamentals for each symbol instead of empty dict to avoid frontend errors
        return {s: {"name": "Unknown", "pe_ratio": "N/A", "dividend_yield": "N/A", "pb_ratio": "N/A"} for s in symbols}

    # Create a lookup dictionary by code
    lookup = {}
    for item in all_items:
        code = item.get("code")
        if not code:
            continue
        
        # Prioritization logic: 
        # If we already have a record for this code, only override it if the new record
        # has better data (e.g., pe_ratio is not "N/A").
        if code in lookup:
            existing = lookup[code]
            is_new_better = item.get("pe_ratio") != "N/A" and existing.get("pe_ratio") == "N/A"
            if is_new_better:
                lookup[code] = item
        else:
            lookup[code] = item
    
    result = {}
    for symbol in symbols:
        # Strip '.TW', '.TWO' or '.TW' if present
        clean_symbol = symbol.split('.')[0]
        
        if clean_symbol in lookup:
            item = lookup[clean_symbol]
            result[symbol] = {
                "name": item.get("name", ""),
                "pe_ratio": item.get("pe_ratio", "N/A"),
                "dividend_yield": item.get("dividend_yield", "N/A"),
                "pb_ratio": item.get("pb_ratio", "N/A")
            }
        else:
            result[symbol] = {
                "name": "Unknown",
                "pe_ratio": "N/A",
                "dividend_yield": "N/A",
                "pb_ratio": "N/A"
            }
    
    return result
