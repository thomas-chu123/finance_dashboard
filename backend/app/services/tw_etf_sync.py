"""
TW ETF Sync Service
Fetches the Taiwan ETF list from the TWSE OpenAPI and upserts it into Supabase.
Endpoint: https://openapi.twse.com.tw/v1/opendata/t187ap47_L
"""
import logging
import httpx
from datetime import datetime, timezone
from app.database import get_supabase

logger = logging.getLogger(__name__)

TWSE_ETF_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap47_L"
HEADERS = {
    "accept": "application/json",
    "If-Modified-Since": "Mon, 26 Jul 1997 05:00:00 GMT",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


async def sync_tw_etf_list() -> int:
    """
    Fetch TW ETF list from TWSE and upsert into tw_etf_list table.
    Returns the number of records upserted.
    """
    logger.info("[TW ETF Sync] Starting ETF list sync from TWSE...")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(TWSE_ETF_URL, headers=HEADERS)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.error(f"[TW ETF Sync] Failed to fetch from TWSE: {e}")
        raise

    now = datetime.now(timezone.utc).isoformat()
    records = []
    for item in data:
        symbol = item.get("基金代號", "").strip()
        name = item.get("基金簡稱", "").strip()
        full_name = item.get("基金中文名稱", "").strip()
        fund_type = item.get("基金類型", "").strip()
        if not symbol or not name:
            continue
        records.append({
            "symbol": symbol,
            "name": name,
            "full_name": full_name,
            "fund_type": fund_type,
            "updated_at": now,
        })

    if not records:
        logger.warning("[TW ETF Sync] No valid records parsed from TWSE response.")
        return 0

    sb = get_supabase()
    # Upsert in batches of 200 to avoid payload limits
    batch_size = 200
    total = 0
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        sb.table("tw_etf_list").upsert(batch, on_conflict="symbol").execute()
        total += len(batch)

    logger.info(f"[TW ETF Sync] Successfully upserted {total} TW ETF records into Supabase.")
    return total
