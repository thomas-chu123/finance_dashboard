"""
US ETF Sync Service
Fetches ALL US ETFs from Nasdaq API and upserts them into Supabase.
Source: https://api.nasdaq.com/api/screener/etf?tableonly=true&limit=5000&offset=0
"""
import logging
import asyncio
from datetime import datetime, timezone

import httpx
from app.database import get_supabase

logger = logging.getLogger(__name__)

# Nasdaq API for all ETFs
NASDAQ_SOURCE_URL = "https://api.nasdaq.com/api/screener/etf?tableonly=true&limit=5000&offset=0"

# Nasdaq often requires these headers to avoid being blocked
HEADERS = {
    "authority": "api.nasdaq.com",
    "accept": "application/json, text/plain, */*",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


async def sync_us_etf_list() -> int:
    """
    Fetch comprehensive US ETF list from Nasdaq and upsert into us_etf_list table.
    Returns the number of records upserted.
    """
    logger.info(f"[US ETF Sync] Starting full US ETF sync from Nasdaq API")

    all_rows = []
    offset = 0
    limit = 50  # Nasdaq API seems to cap at 50 even if we ask for more
    total_records = 0

    async with httpx.AsyncClient(timeout=60) as client:
        while True:
            url = f"https://api.nasdaq.com/api/screener/etf?tableonly=true&limit={limit}&offset={offset}"
            try:
                resp = await client.get(url, headers=HEADERS)
                resp.raise_for_status()
                data = resp.json()
                
                records_data = data.get("data", {}).get("records", {})
                if not total_records:
                    try:
                        total_records = int(records_data.get("totalrecords", 0))
                        logger.info(f"[US ETF Sync] Total records to fetch: {total_records}")
                    except (ValueError, TypeError):
                        total_records = 0

                rows = records_data.get("data", {}).get("rows", [])
                if not rows:
                    break
                
                all_rows.extend(rows)
                logger.debug(f"[US ETF Sync] Fetched {len(all_rows)} / {total_records}")
                
                if total_records and len(all_rows) >= total_records:
                    break
                
                if len(rows) < limit:
                    break
                    
                offset += limit
                # Polite delay to avoid being blocked
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"[US ETF Sync] Error fetching page at offset {offset}: {e}")
                break

    if not all_rows:
        logger.warning("[US ETF Sync] No rows found in Nasdaq response.")
        return 0

    logger.info(f"[US ETF Sync] Total fetched {len(all_rows)} potential ETF records.")

    now = datetime.now(timezone.utc).isoformat()
    records = []
    
    for row in all_rows:
        symbol = row.get("symbol", "").strip()
        name = row.get("companyName", "").strip()
        
        if not symbol:
            continue
            
        records.append({
            "symbol": symbol,
            "name": name if name else symbol,
            "exchange": "US",
            "updated_at": now,
        })

    if not records:
        logger.warning("[US ETF Sync] No valid records parsed from Nasdaq.")
        return 0

    # Upsert into Supabase in batches of 500
    sb = get_supabase()
    batch_size = 500
    total = 0
    for i in range(0, len(records), batch_size):
        batch = records[i: i + batch_size]
        try:
            sb.table("us_etf_list").upsert(batch, on_conflict="symbol").execute()
            total += len(batch)
            logger.info(f"[US ETF Sync] Upserted batch {i//batch_size + 1}: {len(batch)} records.")
        except Exception as e:
            logger.error(f"[US ETF Sync] Error upserting batch starting at {i}: {e}")
            continue

    logger.info(f"[US ETF Sync] Successfully completed. Total upserted: {total} US ETF records.")
    return total
