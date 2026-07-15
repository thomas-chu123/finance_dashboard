"""
JP ETF Sync Service.

Fetches the Japan ETF list from JPX and upserts it into Supabase.
Source: https://www.jpx.co.jp/english/equities/products/etfs/issues/01.html
"""
import asyncio
import logging
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from app.database import get_supabase

logger = logging.getLogger(__name__)

JPX_ETF_URL = "https://www.jpx.co.jp/english/equities/products/etfs/issues/01.html"
HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def _parse_jpx_etf_table(html: str) -> list[dict]:
    """Parse the JPX ETF issues table into normalized records."""
    soup = BeautifulSoup(html, "html.parser")
    header_map = None
    data_rows = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue

        headers = [cell.get_text(" ", strip=True) for cell in rows[0].find_all(["th", "td"])]
        candidate_map = {header: idx for idx, header in enumerate(headers)}
        if {"Code", "Fund Name"}.issubset(candidate_map):
            header_map = candidate_map
            data_rows = rows[1:]
            break

    if header_map is None:
        raise ValueError("JPX ETF table with Code and Fund Name columns was not found")

    now = datetime.now(timezone.utc).isoformat()
    records = []
    seen_symbols = set()

    for row in data_rows:
        cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["td", "th"])]
        if len(cells) <= max(header_map.values()):
            continue

        raw_code = cells[header_map["Code"]]
        symbol = "".join(ch for ch in raw_code if ch.isdigit())
        fund_name = cells[header_map["Fund Name"]]

        if not symbol or not fund_name or symbol in seen_symbols:
            continue

        records.append({
            "symbol": symbol,
            "name": fund_name,
            "index_name": cells[header_map["Index"]] if "Index" in header_map else "",
            "management_company": cells[header_map["Management Company"]] if "Management Company" in header_map else "",
            "trading_unit": cells[header_map["Trading Unit"]] if "Trading Unit" in header_map else "",
            "updated_at": now,
        })
        seen_symbols.add(symbol)

    return records


async def sync_jp_etf_list() -> int:
    """
    Fetch JP ETF list from JPX and upsert into jp_etf_list table.

    Returns:
        Number of records upserted.
    """
    logger.info("[JP ETF Sync] Starting ETF list sync from JPX...")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(JPX_ETF_URL, headers=HEADERS)
            resp.raise_for_status()
            records = await asyncio.to_thread(_parse_jpx_etf_table, resp.text)
    except Exception as e:
        logger.error(f"[JP ETF Sync] Failed to fetch or parse JPX ETF list: {e}")
        raise

    if not records:
        logger.warning("[JP ETF Sync] No valid records parsed from JPX response.")
        return 0

    sb = get_supabase()
    batch_size = 200
    total = 0
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        try:
            sb.table("jp_etf_list").upsert(batch, on_conflict="symbol").execute()
            total += len(batch)
            logger.info(f"[JP ETF Sync] Upserted batch {i // batch_size + 1}: {len(batch)} records.")
        except Exception as e:
            logger.error(f"[JP ETF Sync] Error upserting batch starting at {i}: {e}")

    logger.info(f"[JP ETF Sync] Successfully completed. Total upserted: {total} JP ETF records.")
    return total
