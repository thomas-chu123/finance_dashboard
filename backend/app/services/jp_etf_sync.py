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
JPX_ETF_JA_URL = "https://www.jpx.co.jp/equities/products/etfs/issues/01.html"
HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def _parse_jpx_etf_table(html: str, language: str = "en") -> list[dict]:
    """Parse the JPX ETF issues table into normalized records."""
    soup = BeautifulSoup(html, "html.parser")
    header_map = None
    data_rows = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for header_index, header_row in enumerate(rows):
            headers = [cell.get_text(" ", strip=True) for cell in header_row.find_all(["th", "td"])]
            candidate_map = {header: idx for idx, header in enumerate(headers)}
            if language == "en":
                has_required_headers = {"Code", "Fund Name"}.issubset(candidate_map)
            else:
                # JPX has used 「コード」/「銘柄名」, 「銘柄コード」 and
                # 「名称」 variants on the Japanese page over time.
                has_required_headers = (
                    any("コード" in header.replace(" ", "") for header in candidate_map)
                    and any("銘柄名" in header.replace(" ", "") or "名称" in header.replace(" ", "") for header in candidate_map)
                )
            if has_required_headers:
                header_map = candidate_map
                data_rows = rows[header_index + 1:]
                break
        if header_map is not None:
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

        if language == "en":
            code_header, name_header = "Code", "Fund Name"
        else:
            code_header = next(header for header in header_map if "コード" in header)
            name_header = next(header for header in header_map if "銘柄名" in header or "名称" in header)
        raw_code = cells[header_map[code_header]]
        symbol = "".join(ch for ch in raw_code if ch.isdigit())
        fund_name = cells[header_map[name_header]]

        if not symbol or not fund_name or symbol in seen_symbols:
            continue

        record = {
            "symbol": symbol,
            "name": fund_name,
            "updated_at": now,
        }
        if language == "en":
            record.update({
                "index_name": cells[header_map["Index"]] if "Index" in header_map else "",
                "management_company": cells[header_map["Management Company"]] if "Management Company" in header_map else "",
                "trading_unit": cells[header_map["Trading Unit"]] if "Trading Unit" in header_map else "",
            })
        else:
            record["name_ja"] = fund_name
        records.append(record)
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
            resp, ja_resp = await asyncio.gather(
                client.get(JPX_ETF_URL, headers=HEADERS),
                client.get(JPX_ETF_JA_URL, headers=HEADERS),
                return_exceptions=True,
            )
            if isinstance(resp, Exception):
                raise resp
            resp.raise_for_status()
            records = await asyncio.to_thread(_parse_jpx_etf_table, resp.text)
            # JPX's Japanese page supplies the localized fund names. If it is
            # unavailable, English records remain usable as a fallback.
            if not isinstance(ja_resp, Exception) and ja_resp.is_success:
                try:
                    ja_records = await asyncio.to_thread(_parse_jpx_etf_table, ja_resp.text, "ja")
                    ja_by_symbol = {row["symbol"]: row["name_ja"] for row in ja_records}
                    for row in records:
                        if row["symbol"] in ja_by_symbol:
                            row["name_ja"] = ja_by_symbol[row["symbol"]]
                except Exception as e:
                    logger.warning(f"[JP ETF Sync] Japanese JPX table could not be parsed; using English names: {e}")
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
