"""一週財經大事使用的結構化經濟數據來源。

優先讀取 BLS、Yahoo Finance 與 ISM 官方資料；CPI、非農與 WTI 在主要
來源失敗時使用 FRED CSV 備援。單一指標失敗不會阻止其他指標回傳。
"""
import asyncio
import csv
import io
import logging
import re
from datetime import datetime, timezone
from typing import Any

import httpx
import yfinance as yf
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
ISM_PMI_URL = (
    "https://www.ismworld.org/supply-management-news-and-reports/reports/"
    "ism-pmi-reports/pmi/{month}/"
)
JINA_READER_URL = "https://r.jina.ai/{url}"

BLS_CPI_SERIES = "CUSR0000SA0"
BLS_NONFARM_SERIES = "CES0000000001"
MACROMICRO_URLS = {
    "cpi": "https://www.macromicro.me/charts/10/cpi",
    "nonfarm": "https://www.macromicro.me/collections/4/us-employ-relative/6/employment-condition",
    "wti": "https://www.macromicro.me/charts/74/crude-oil-futures-mid14",
    "pmi": "https://www.macromicro.me/collections/8/us-industry-relative/54/ism",
}


def _period_to_date(year: str, period: str) -> str:
    """將 BLS 的年份與 M01..M12 轉成 YYYY-MM。"""
    return f"{year}-{int(period[1:]):02d}"


def _record(
    key: str,
    name: str,
    period: str,
    value: float,
    unit: str,
    source: str,
    source_url: str,
    **extra: Any,
) -> dict[str, Any]:
    """建立一致的經濟數據紀錄。"""
    return {
        "type": "economic_data",
        "key": key,
        "name": name,
        "period": period,
        "value": value,
        "unit": unit,
        "source": source,
        "source_url": source_url,
        "reference_url": MACROMICRO_URLS[key],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        **extra,
    }


async def _fetch_bls_data(client: httpx.AsyncClient) -> dict[str, dict[str, Any]]:
    """一次向 BLS 取得 CPI 與非農，並計算常用變動率。"""
    now = datetime.now(timezone.utc)
    response = await client.post(
        BLS_API_URL,
        json={
            "seriesid": [BLS_CPI_SERIES, BLS_NONFARM_SERIES],
            "startyear": str(now.year - 1),
            "endyear": str(now.year),
        },
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") != "REQUEST_SUCCEEDED":
        raise ValueError(f"BLS request failed: {payload.get('message')}")

    series_map = {
        item["seriesID"]: [row for row in item.get("data", []) if row.get("period", "").startswith("M")]
        for item in payload.get("Results", {}).get("series", [])
    }
    result: dict[str, dict[str, Any]] = {}

    cpi_rows = series_map.get(BLS_CPI_SERIES, [])
    if len(cpi_rows) >= 2:
        latest = cpi_rows[0]
        latest_value = float(latest["value"])
        previous_value = float(cpi_rows[1]["value"])
        year_ago = next(
            (
                float(row["value"])
                for row in cpi_rows[1:]
                if row["period"] == latest["period"]
                and int(row["year"]) == int(latest["year"]) - 1
            ),
            None,
        )
        result["cpi"] = _record(
            "cpi",
            "美國 CPI（季調）",
            _period_to_date(latest["year"], latest["period"]),
            latest_value,
            "指數（1982–1984 年平均=100）",
            "BLS",
            "https://data.bls.gov/timeseries/CUSR0000SA0&output_view=pct_12mths",
            previous_value=previous_value,
            month_over_month_pct=(latest_value / previous_value - 1) * 100,
            year_over_year_pct=(latest_value / year_ago - 1) * 100 if year_ago else None,
        )

    payroll_rows = series_map.get(BLS_NONFARM_SERIES, [])
    if len(payroll_rows) >= 2:
        latest = payroll_rows[0]
        latest_value = float(latest["value"])
        previous_value = float(payroll_rows[1]["value"])
        result["nonfarm"] = _record(
            "nonfarm",
            "美國非農就業",
            _period_to_date(latest["year"], latest["period"]),
            latest_value,
            "千人",
            "BLS",
            "https://data.bls.gov/timeseries/CES0000000001",
            previous_value=previous_value,
            change=latest_value - previous_value,
            change_unit="千人",
        )
    return result


async def _fetch_fred_series(client: httpx.AsyncClient, series_id: str) -> list[tuple[str, float]]:
    """從免 API key 的 FRED CSV 端點取得有效觀測值（新到舊）。"""
    response = await client.get(FRED_CSV_URL, params={"id": series_id})
    response.raise_for_status()
    rows = []
    for row in csv.DictReader(io.StringIO(response.text)):
        raw_value = row.get(series_id)
        if not raw_value or raw_value == ".":
            continue
        rows.append((row["observation_date"], float(raw_value)))
    return list(reversed(rows))


async def _fetch_cpi_fred(client: httpx.AsyncClient) -> dict[str, Any]:
    rows = await _fetch_fred_series(client, "CPIAUCSL")
    if len(rows) < 2:
        raise ValueError("FRED CPI observations are insufficient")
    period, value = rows[0]
    previous_value = rows[1][1]
    year_ago_period = f"{int(period[:4]) - 1}{period[4:7]}"
    year_ago = next(
        (item_value for date, item_value in rows if date[:7] == year_ago_period),
        None,
    )
    return _record(
        "cpi", "美國 CPI（季調）", period[:7], value, "指數（1982–1984 年平均=100）", "FRED",
        "https://fred.stlouisfed.org/series/CPIAUCSL", previous_value=previous_value,
        month_over_month_pct=(value / previous_value - 1) * 100,
        year_over_year_pct=(value / year_ago - 1) * 100 if year_ago else None,
    )


async def _fetch_nonfarm_fred(client: httpx.AsyncClient) -> dict[str, Any]:
    rows = await _fetch_fred_series(client, "PAYEMS")
    if len(rows) < 2:
        raise ValueError("FRED payroll observations are insufficient")
    period, value = rows[0]
    return _record(
        "nonfarm", "美國非農就業", period[:7], value, "千人", "FRED",
        "https://fred.stlouisfed.org/series/PAYEMS", previous_value=rows[1][1],
        change=value - rows[1][1], change_unit="千人",
    )


def _fetch_wti_yahoo_sync() -> dict[str, Any]:
    """在線程內讀取 Yahoo WTI 期貨，避免阻塞事件迴圈。"""
    history = yf.Ticker("CL=F").history(period="5d", auto_adjust=False)
    closes = history["Close"].dropna()
    if closes.empty:
        raise ValueError("Yahoo WTI returned no prices")
    value = float(closes.iloc[-1])
    previous_value = float(closes.iloc[-2]) if len(closes) >= 2 else None
    period = closes.index[-1].date().isoformat()
    return _record(
        "wti", "WTI 原油期貨", period, value, "美元/桶", "Yahoo Finance",
        "https://finance.yahoo.com/quote/CL=F/", previous_value=previous_value,
        change=value - previous_value if previous_value is not None else None,
        change_pct=(value / previous_value - 1) * 100 if previous_value else None,
    )


async def _fetch_wti_fred(client: httpx.AsyncClient) -> dict[str, Any]:
    rows = await _fetch_fred_series(client, "DCOILWTICO")
    if not rows:
        raise ValueError("FRED WTI observations are insufficient")
    period, value = rows[0]
    previous_value = rows[1][1] if len(rows) >= 2 else None
    return _record(
        "wti", "WTI 原油現貨", period, value, "美元/桶", "FRED",
        "https://fred.stlouisfed.org/series/DCOILWTICO", previous_value=previous_value,
        change=value - previous_value if previous_value is not None else None,
        change_pct=(value / previous_value - 1) * 100 if previous_value else None,
    )


async def _fetch_ism_pmi(client: httpx.AsyncClient) -> dict[str, Any]:
    """解析 ISM 最近三個可能月份頁面，取最新的製造業 PMI。"""
    now = datetime.now(timezone.utc)
    candidates = []
    year, month = now.year, now.month - 1
    for _ in range(3):
        if month <= 0:
            month += 12
            year -= 1
        candidates.append((year, month))
        month -= 1

    for expected_year, expected_month in candidates:
        month_name = datetime(expected_year, expected_month, 1).strftime("%B").lower()
        url = ISM_PMI_URL.format(month=month_name)
        response = await client.get(url)
        text_candidates: list[tuple[str, str]] = []
        if response.status_code == 200:
            text_candidates.append(
                (BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True), "direct")
            )

        # ISM 的最新報告偶爾會對一般 HTTP client 回傳 404 或登入頁；
        # 若直接內容無法解析，再以只讀轉換服務讀取同一個 ISM 公開網址。
        direct_text = text_candidates[0][0] if text_candidates else ""
        direct_has_report = re.search(
            rf"{month_name.title()}\s+{expected_year}\s+ISM", direct_text, re.IGNORECASE
        )
        if not direct_has_report:
            reader_response = await client.get(JINA_READER_URL.format(url=url))
            if reader_response.status_code == 200:
                text_candidates.append((reader_response.text, "Jina Reader"))

        parsed = None
        for candidate_text, candidate_via in text_candidates:
            period_match = re.search(
                rf"{month_name.title()}\s+({expected_year})\s+ISM", candidate_text, re.IGNORECASE
            )
            value_match = re.search(
                r"Manufacturing\s+PMI(?:®|\s)*\s+at\s+(\d+(?:\.\d+)?)\s*%",
                candidate_text,
                re.IGNORECASE,
            )
            if period_match and value_match:
                parsed = (candidate_text, candidate_via, float(value_match.group(1)))
                break
        if not parsed:
            continue
        text, fetched_via, value = parsed
        previous_match = re.search(
            r"registered\s+\d+(?:\.\d+)?\s*percent.*?(\d+(?:\.\d+)?)\s+percentage points?\s+"
            r"(?:higher|lower).*?(?:in|than)\s+([A-Za-z]+)",
            text,
            re.IGNORECASE,
        )
        previous_value = None
        if previous_match:
            delta = float(previous_match.group(1))
            direction_match = re.search(
                r"registered\s+\d+(?:\.\d+)?\s*percent.*?percentage points?\s+(higher|lower)",
                text,
                re.IGNORECASE,
            )
            if direction_match:
                previous_value = value - delta if direction_match.group(1).lower() == "higher" else value + delta
        return _record(
            "pmi", "美國 ISM 製造業 PMI", f"{expected_year}-{expected_month:02d}", value,
            "指數", "ISM", url, previous_value=previous_value,
            change=value - previous_value if previous_value is not None else None,
            fetched_via=fetched_via,
        )
    raise ValueError("ISM PMI latest report could not be parsed")


async def fetch_weekly_economic_data() -> list[dict[str, Any]]:
    """平行取得四項數據，主要來源失敗時逐項備援。"""
    timeout = httpx.Timeout(15.0, connect=8.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        bls_result, wti_result, pmi_result = await asyncio.gather(
            _fetch_bls_data(client),
            asyncio.to_thread(_fetch_wti_yahoo_sync),
            _fetch_ism_pmi(client),
            return_exceptions=True,
        )

        records = bls_result if isinstance(bls_result, dict) else {}
        fallback_jobs = []
        fallback_keys = []
        if "cpi" not in records:
            fallback_keys.append("cpi")
            fallback_jobs.append(_fetch_cpi_fred(client))
        if "nonfarm" not in records:
            fallback_keys.append("nonfarm")
            fallback_jobs.append(_fetch_nonfarm_fred(client))
        if isinstance(wti_result, Exception):
            fallback_keys.append("wti")
            fallback_jobs.append(_fetch_wti_fred(client))
        else:
            records["wti"] = wti_result
        if isinstance(pmi_result, Exception):
            logger.warning("[EconomicData] ISM PMI fetch failed: %s", pmi_result)
        else:
            records["pmi"] = pmi_result

        if fallback_jobs:
            fallback_results = await asyncio.gather(*fallback_jobs, return_exceptions=True)
            for key, result in zip(fallback_keys, fallback_results):
                if isinstance(result, Exception):
                    logger.warning("[EconomicData] %s fetch and fallback failed: %s", key, result)
                else:
                    records[key] = result

        if isinstance(bls_result, Exception):
            logger.warning("[EconomicData] BLS fetch failed: %s", bls_result)
        if isinstance(wti_result, Exception):
            logger.warning("[EconomicData] Yahoo WTI fetch failed: %s", wti_result)
        return [records[key] for key in ("cpi", "nonfarm", "wti", "pmi") if key in records]


def format_economic_data_for_prompt(records: list[dict[str, Any]]) -> str:
    """將結構化數據轉成要求模型逐字引用的精簡資料區塊。"""
    lines = []
    for item in records:
        value = f"{item['value']:.2f}" if item.get("key") == "wti" else str(item["value"])
        details = [f"實際值 {value} {item['unit']}"]
        if item.get("previous_value") is not None:
            previous_value = (
                f"{item['previous_value']:.2f}"
                if item.get("key") == "wti"
                else str(item["previous_value"])
            )
            details.append(f"前值 {previous_value} {item['unit']}")
        if item.get("month_over_month_pct") is not None:
            details.append(f"月增率 {item['month_over_month_pct']:.2f}%")
        if item.get("year_over_year_pct") is not None:
            details.append(f"年增率 {item['year_over_year_pct']:.2f}%")
        if item.get("change") is not None:
            change_unit = item.get("change_unit", item["unit"])
            details.append(f"較前值變動 {item['change']:+.2f} {change_unit}")
        if item.get("change_pct") is not None:
            details.append(f"漲跌幅 {item['change_pct']:+.2f}%")
        lines.append(
            f"- {item['name']}（{item['period']}）：{'；'.join(details)}；"
            f"來源 {item['source']}（{item['source_url']}）"
        )
    return "\n".join(lines) or "- 本次未成功取得結構化經濟數據。"
