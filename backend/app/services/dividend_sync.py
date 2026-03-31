"""
Dividend Calendar Sync Service
Fetches ex-dividend / ex-right data from TWSE and upserts into Supabase.
Source: https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL
"""
import logging
import httpx
from datetime import datetime, timezone
from app.database import get_supabase

logger = logging.getLogger(__name__)

TWSE_DIVIDEND_URL = "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL"
HEADERS = {
    "accept": "application/json",
    "If-Modified-Since": "Mon, 26 Jul 1997 05:00:00 GMT",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


def _roc_to_iso_date(date_str: str) -> str | None:
    """Convert ROC date string 'YYYMMDD' to ISO date 'YYYY-MM-DD'.

    Example: '1150331' -> '2026-03-31'
    """
    try:
        year = int(date_str[:3]) + 1911
        month = date_str[3:5]
        day = date_str[5:7]
        return f"{year}-{month}-{day}"
    except (ValueError, IndexError):
        return None


async def sync_dividend_calendar() -> int:
    """Fetch dividend calendar from TWSE and upsert into dividend_calendar table.

    Returns:
        Number of records upserted.
    """
    logger.info("[Dividend Sync] Starting dividend calendar sync from TWSE...")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(TWSE_DIVIDEND_URL, headers=HEADERS)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.error(f"[Dividend Sync] Failed to fetch from TWSE: {e}")
        raise

    now = datetime.now(timezone.utc).isoformat()
    records = []
    for item in data:
        code = item.get("Code", "").strip()
        name = item.get("Name", "").strip()
        date_raw = item.get("Date", "").strip()
        ex_type = item.get("Exdividend", "").strip()

        if not code or not date_raw or not ex_type:
            continue

        ex_date = _roc_to_iso_date(date_raw)
        if not ex_date:
            logger.warning(f"[Dividend Sync] Invalid date format: {date_raw} for {code}")
            continue

        cash_raw = item.get("CashDividend", "").strip()
        cash_dividend = None
        if cash_raw:
            try:
                cash_dividend = float(cash_raw)
            except ValueError:
                pass

        sub_price_raw = item.get("SubscriptionPricePerShare", "").strip()
        subscription_price = None
        if sub_price_raw:
            try:
                subscription_price = float(sub_price_raw)
            except ValueError:
                pass

        records.append({
            "code": code,
            "name": name,
            "ex_date": ex_date,
            "ex_type": ex_type,
            "cash_dividend": cash_dividend,
            "stock_dividend_ratio": item.get("StockDividendRatio", "").strip(),
            "subscription_ratio": item.get("SubscriptionRatio", "").strip(),
            "subscription_price": subscription_price,
            "raw_data": item,
            "updated_at": now,
        })

    if not records:
        logger.warning("[Dividend Sync] No valid records parsed from TWSE response.")
        return 0

    sb = get_supabase()
    batch_size = 200
    total = 0
    for i in range(0, len(records), batch_size):
        batch = records[i: i + batch_size]
        try:
            sb.table("dividend_calendar").upsert(
                batch, on_conflict="code,ex_date,ex_type"
            ).execute()
            total += len(batch)
        except Exception as e:
            logger.error(f"[Dividend Sync] Error upserting batch at index {i}: {e}")
            continue

    logger.info(f"[Dividend Sync] Successfully upserted {total} dividend records.")
    return total
