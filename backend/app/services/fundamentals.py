import httpx
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

TWSE_BWIBBU_URL = "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL"

async def fetch_twse_fundamentals() -> List[Dict]:
    """
    Fetches fundamental data (PE ratio, Dividend Yield, PB ratio) 
    for all securities from TWSE OpenAPI.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(TWSE_BWIBBU_URL)
            response.raise_for_status()
            data = response.json()
            return data
    except Exception as e:
        logger.error(f"Error fetching TWSE fundamental data: {e}")
        return []

async def get_fundamentals_for_symbols(symbols: List[str]) -> Dict[str, Dict]:
    """
    Given a list of symbol codes (e.g., ['0050', '2330']),
    returns a dictionary mapped by symbol with their fundamental data.
    Note: TWSE symbols usually don't have the '.TW' suffix in the API, 
    so we need to strip it if present.
    """
    all_data = await fetch_twse_fundamentals()
    if not all_data:
        return {}

    # Create a lookup dictionary by Code
    lookup = {item["Code"]: item for item in all_data}
    
    result = {}
    for symbol in symbols:
        # Strip '.TW' or '.TWO' if present for TWSE matching
        clean_symbol = symbol.split('.')[0]
        if clean_symbol in lookup:
            result[symbol] = {
                "name": lookup[clean_symbol].get("Name", ""),
                "pe_ratio": lookup[clean_symbol].get("PEratio", "N/A"),
                "dividend_yield": lookup[clean_symbol].get("DividendYield", "N/A"),
                "pb_ratio": lookup[clean_symbol].get("PBratio", "N/A")
            }
        else:
            result[symbol] = {
                "name": "Unknown",
                "pe_ratio": "N/A",
                "dividend_yield": "N/A",
                "pb_ratio": "N/A"
            }
    
    return result
