"""
AI 每日市場早報主編排服務 — 協調 Brave Search + Gemini / Tavily / SearXNG + Ollama + Supabase 寫入.

提供商由 .env 中的 AI_SUMMARY 環境變數控制：
  AI_SUMMARY=BRAVE_GEMINI    (預設) — 使用 Brave Search 取新聞 + Gemini 生成摘要
  AI_SUMMARY=TAVILY          — 使用 Tavily Search API（一次呼叫同時完成搜尋和摘要）
  AI_SUMMARY=SEARXNG_OLLAMA  — 使用自架 SearXNG 搜尋 + Ollama Direct API 生成摘要（v3）
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta

from app.config import get_settings
from app.database import get_supabase
from app.services.brave_search_service import search_news
from app.services.gemini_service import generate_market_summary
from app.services.tavily_service import search_and_summarize as tavily_search_and_summarize

logger = logging.getLogger(__name__)
settings = get_settings()

# Brave Search 免費方案限制：每次排程最多處理 20 個 unique symbols
MAX_SYMBOLS_PER_SESSION = 20

# 對應三個排程時間點（Asia/Taipei）
VALID_SESSION_HOURS = (8, 13, 18)

SPECIAL_BRIEF_ITEMS = (
    {"symbol": "AI_WEEK", "name": "一週財經大事"},
    {"symbol": "AI_TW_FCST", "name": "當日台股大盤風向與指數預測"},
)


# 依 category 補強搜尋語意，降低抓到同名非金融內容的機率。
CATEGORY_FINANCE_HINTS: dict[str, str] = {
    "tw_etf": "台股 ETF 台灣 股票 基金",
    "us_etf": "美股 ETF 美國 股票 基金",
    "exchange": "外匯 匯率 金融 貨幣",  # 預設外匯提示（會被動態覆蓋）
    "index": "指數 大盤 股市",
    "vix": "VIX 波動率 恐慌指數",
    "oil": "原油 油價 能源 期貨",
    "crypto": "加密貨幣 比特幣 以太幣",
    "rate": "利率 央行 殖利率",
    "interest_rate": "利率 央行 殖利率",
}

# 外匯 ticker 到中文貨幣名稱的映射（用於改進搜尋提示）
CURRENCY_NAMES: dict[str, str] = {
    "USD": "美元",
    "TWD": "台幣",
    "JPY": "日圓",
    "EUR": "歐元",
    "GBP": "英鎊",
    "CNY": "人民幣",
    "HKD": "港幣",
    "SGD": "新加坡幣",
    "AUD": "澳幣",
    "CAD": "加幣",
    "CHF": "瑞士法郎",
    "NZD": "紐西蘭幣",
    "INR": "印度盧比",
    "RMB": "人民幣",
    "KRW": "韓圓",
    "SEK": "瑞典克朗",
    "NOK": "挪威克朗",
    "MXN": "墨西哥披索",
    "ZAR": "南非蘭特",
    "BRL": "巴西雷亞爾",
    "RUB": "俄羅斯盧布",
    "TRY": "土耳其里拉",
}


def _parse_exchange_pair(symbol: str) -> tuple[str, str] | None:
    """
    解析外匯 ticker (如 TWDJPY=X) 為 (base_curr, quote_curr)。
    
    常見格式：XXX[YYY] 其中 XXX 和 YYY 各為 3 字母貨幣代碼，加上 =X 後綴。
    
    Returns:
        (base_code, quote_code) 如 ("TWD", "JPY")，或 None 若無法解析
    """
    base_symbol = symbol.replace("=X", "").upper()
    if len(base_symbol) != 6:
        return None
    base_curr = base_symbol[:3]
    quote_curr = base_symbol[3:6]
    return (base_curr, quote_curr)


def _build_finance_hint(category: str, symbol: str = "") -> str:
    """依類別回傳搜尋提示詞（含中英文金融詞）."""
    key = (category or "").strip().lower()
    
    # 若為外匯類別且 symbol 可解析，動態生成貨幣對提示
    if key == "exchange" and symbol:
        pair = _parse_exchange_pair(symbol)
        if pair:
            base_code, quote_code = pair
            base_name = CURRENCY_NAMES.get(base_code, base_code)
            quote_name = CURRENCY_NAMES.get(quote_code, quote_code)
            # 避免出現「美元 美元」這類重複
            if base_name != quote_name:
                return f"外匯 匯率 {base_name} {quote_name} finance market"
    
    hint = CATEGORY_FINANCE_HINTS.get(key)
    if hint:
        return f"{hint} finance market"
    return "金融 市場 股票 ETF 指數 finance market"


def _build_search_query(symbol: str, symbol_name: str, category: str) -> str:
    """組合搜尋字串：name + symbol + category hint（避免重複）."""
    finance_hint = _build_finance_hint(category, symbol=symbol)
    if symbol_name == symbol:
        return f"{symbol_name} {finance_hint}"
    return f"{symbol_name} {symbol} {finance_hint}"


def _get_nearest_session_time() -> datetime:
    """
    計算最近一次有效排程時間（08:00、13:00 或 18:00 Asia/Taipei）.

    Returns:
        最近整點排程的 UTC datetime
    """
    # Asia/Taipei = UTC+8
    taipei_offset = timedelta(hours=8)
    now_utc = datetime.now(timezone.utc)
    now_taipei = now_utc + taipei_offset

    # 找最近已過的排程時間
    today_sessions = [
        now_taipei.replace(hour=h, minute=0, second=0, microsecond=0)
        for h in VALID_SESSION_HOURS
    ]
    past_sessions = [t for t in today_sessions if t <= now_taipei]

    if past_sessions:
        nearest_taipei = max(past_sessions)
    else:
        # 今天尚無排程執行，取前一天 18:00
        yesterday = now_taipei - timedelta(days=1)
        nearest_taipei = yesterday.replace(hour=18, minute=0, second=0, microsecond=0)

    # 轉回 UTC
    return nearest_taipei - taipei_offset


def _pct_change(price: float | None, prev_close: float | None) -> float | None:
    if price is None or prev_close in (None, 0):
        return None
    return (price - prev_close) / prev_close * 100


def _fmt_num(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.{digits}f}"


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"


async def _fetch_weekly_market_signals() -> list[dict]:
    """取得判斷台股短線方向所需的跨市場即時訊號。"""
    from app.services.market_data import get_quote_data

    quote_specs = [
        ("TAIEX", "index", "台灣加權指數"),
        ("WTX&", "index", "台指期夜盤"),
        ("TSM", "index", "台積電 ADR"),
        ("^SOX", "index", "費城半導體指數"),
        ("^VIX", "vix", "VIX 恐慌指數"),
        ("TWD=X", "exchange", "USD/TWD"),
    ]
    results = await asyncio.gather(
        *[get_quote_data(symbol, category) for symbol, category, _name in quote_specs],
        return_exceptions=True,
    )
    signals = []
    for (symbol, _category, name), result in zip(quote_specs, results):
        if isinstance(result, Exception):
            logger.warning("[WeeklyBrief] market signal failed symbol=%s: %s", symbol, result)
            continue
        price = result.get("price")
        prev_close = result.get("prev_close")
        change_pct = _pct_change(price, prev_close)
        if price is None or change_pct is None:
            continue
        signals.append(
            {
                "symbol": symbol,
                "name": name,
                "price": price,
                "prev_close": prev_close,
                "change_pct": change_pct,
            }
        )
    return signals


def _format_weekly_market_signals(signals: list[dict]) -> str:
    """將跨市場訊號整理為模型可核對的文字。"""
    if not signals:
        return "- 本次未成功取得跨市場行情。"
    return "\n".join(
        f"- {item['name']}（{item['symbol']}）：現值 {_fmt_num(item['price'], 3)}；"
        f"前值 {_fmt_num(item['prev_close'], 3)}；單日漲跌 {_fmt_pct(item['change_pct'])}"
        for item in signals
    )


def _build_weekly_assessment(
    economic_data: list[dict], market_signals: list[dict]
) -> dict[str, str | int]:
    """以可重現規則先產生景氣、通膨與台股方向，避免交由模型猜測。"""
    economic_by_key = {item.get("key"): item for item in economic_data}
    economy_score = 0.0
    reasons = []

    pmi = economic_by_key.get("pmi")
    if pmi:
        pmi_value = float(pmi["value"])
        pmi_change = pmi.get("change")
        economy_score += 1.0 if pmi_value >= 50 else -1.0
        if pmi_change is not None:
            economy_score += 0.5 if pmi_change > 0 else -0.5
        reasons.append(f"PMI {pmi_value:.1f}，{'仍在擴張區' if pmi_value >= 50 else '落在收縮區'}")

    nonfarm = economic_by_key.get("nonfarm")
    if nonfarm and nonfarm.get("change") is not None:
        payroll_change = float(nonfarm["change"])
        economy_score += 1.0 if payroll_change >= 100 else (-1.0 if payroll_change < 0 else 0.0)
        reasons.append(f"非農就業較前期變動 {payroll_change:+.0f} 千人")

    if economy_score >= 1.5:
        economy_state = "溫和擴張"
    elif economy_score <= -1.0:
        economy_state = "成長動能偏弱"
    else:
        economy_state = "成長訊號分歧"

    cpi = economic_by_key.get("cpi")
    if cpi and cpi.get("year_over_year_pct") is not None:
        cpi_yoy = float(cpi["year_over_year_pct"])
        cpi_mom = cpi.get("month_over_month_pct")
        if cpi_yoy <= 2.5 and (cpi_mom is None or cpi_mom <= 0.2):
            inflation_state = "通膨壓力降溫"
        elif cpi_yoy >= 3.5 or (cpi_mom is not None and cpi_mom >= 0.4):
            inflation_state = "通膨壓力偏高"
        else:
            inflation_state = "通膨緩慢降溫"
        reasons.append(f"CPI 年增率 {cpi_yoy:.2f}%")
    else:
        inflation_state = "通膨資料不足"

    weights = {"TAIEX": 0.20, "WTX&": 0.20, "TSM": 0.20, "^SOX": 0.20, "^VIX": 0.10, "TWD=X": 0.10}
    weighted_score = 0.0
    available_weight = 0.0
    directional_signals = []
    for item in market_signals:
        symbol = item["symbol"]
        if symbol not in weights:
            continue
        raw_signal = max(-1.0, min(1.0, float(item["change_pct"]) / 1.5))
        if symbol in {"^VIX", "TWD=X"}:
            raw_signal *= -1
        weight = weights[symbol]
        weighted_score += raw_signal * weight
        available_weight += weight
        if abs(raw_signal) >= 0.15:
            directional_signals.append(1 if raw_signal > 0 else -1)

    normalized_score = weighted_score / available_weight if available_weight else 0.0
    if normalized_score >= 0.15:
        tw_direction = "偏多"
    elif normalized_score <= -0.15:
        tw_direction = "偏空"
    else:
        tw_direction = "震盪"

    if directional_signals:
        dominant = 1 if sum(directional_signals) >= 0 else -1
        agreement = sum(signal == dominant for signal in directional_signals) / len(directional_signals)
    else:
        agreement = 0.0
    coverage = available_weight / sum(weights.values())
    confidence = round(min(90, coverage * 55 + agreement * 35))
    market_reason = "、".join(
        f"{item['name']} {_fmt_pct(item['change_pct'])}" for item in market_signals[:4]
    ) or "跨市場行情不足"

    return {
        "economy_state": economy_state,
        "inflation_state": inflation_state,
        "tw_direction": tw_direction,
        "confidence": confidence,
        "data_coverage": f"{len(economic_data) + len(market_signals)}/10",
        "macro_reason": "；".join(reasons) or "總體數據不足",
        "market_reason": market_reason,
    }


def _format_weekly_assessment(assessment: dict[str, str | int]) -> str:
    """建立固定置頂的週報結論區塊。"""
    return (
        "【本週總判斷】\n"
        f"經濟狀態：{assessment['economy_state']}\n"
        f"通膨狀態：{assessment['inflation_state']}\n"
        f"台股方向：{assessment['tw_direction']}\n"
        f"信心指數：{assessment['confidence']}/100\n"
        f"資料完整度：{assessment['data_coverage']}\n"
        f"判斷摘要：{assessment['macro_reason']}；{assessment['market_reason']}"
    )


async def _upsert_special_brief(
    sb,
    session_time: datetime,
    symbol: str,
    symbol_name: str,
    news_items: list[dict],
    summary_text: str,
    error_message: str | None = None,
) -> bool:
    status = "completed" if summary_text else "failed"
    sb.table("market_briefings").upsert(
        {
            "session_time": session_time.isoformat(),
            "symbol": symbol,
            "symbol_name": symbol_name,
            "news_json": news_items,
            "summary_text": summary_text,
            "status": status,
            "error_message": error_message if error_message else (None if summary_text else "特殊早報生成失敗"),
        },
        on_conflict="session_time,symbol",
    ).execute()
    return status == "completed"


async def _generate_weekly_finance_events() -> tuple[list[dict], str]:
    """先建立可重現的景氣與台股判斷，再交由 Ollama 解釋本週事件。"""
    from app.services.economic_data_service import (
        fetch_weekly_economic_data,
        format_economic_data_for_prompt,
    )
    from app.services.searxng_service import search_news as searxng_search_news
    from app.services.ollama_service import generate_custom_brief

    taipei_today = (datetime.now(timezone.utc) + timedelta(hours=8)).date().isoformat()
    economic_data, market_signals = await asyncio.gather(
        fetch_weekly_economic_data(),
        _fetch_weekly_market_signals(),
    )
    economic_data_lines = format_economic_data_for_prompt(economic_data)
    market_signal_lines = _format_weekly_market_signals(market_signals)
    assessment = _build_weekly_assessment(economic_data, market_signals)
    assessment_lines = _format_weekly_assessment(assessment)
    query = (
        f"本週 財經 大事 台股 展望 {taipei_today} FOMC 利率 CPI PCE PMI GDP 台積電 費半 "
        "外資 美債 殖利率 economic calendar market events this week"
    )
    searched_news = await searxng_search_news(query=query, count=5, time_range="week")
    if not searched_news:
        searched_news = await search_news(query=query, count=5)

    source_lines = "\n".join(
        f"{idx}. {item.get('title', '')} - {item.get('description', '')} ({item.get('url', '')})"
        for idx, item in enumerate(searched_news[:5], start=1)
    )
    prompt = (
        "你是台灣投資人使用的總體與市場策略編輯。程式已先依結構化數據產生"
        "『本週總判斷』，你必須沿用該判斷，不得擅自改變經濟狀態、通膨狀態、"
        "台股方向或信心指數。請解釋判斷依據與可能失效的條件。"
        "優先包含 FOMC、央行利率決議、通膨、就業、GDP、PMI、重要財報或地緣政治事件。"
        "禁止只做 CPI、非農、WTI 或 PMI 的名詞解釋。"
        "每個成功取得的指標都必須在正文中至少出現一次，並明確寫出期間、實際值與單位；"
        "有前值或變動率時也必須引用並說明市場意義。"
        "不得修改、推測或補造數據區塊中的數值。"
        "若搜尋結果不足，請明確標示資料有限，不要捏造精確日期。\n\n"
        f"今天（台北時間）是 {taipei_today}。\n\n"
        f"程式產生的本週總判斷：\n{assessment_lines}\n\n"
        f"已取得的實際經濟數據：\n{economic_data_lines}\n\n"
        f"台股與跨市場訊號：\n{market_signal_lines}\n\n"
        f"SearXNG／備援搜尋結果：\n{source_lines or '- 沒有可用搜尋結果'}\n\n"
        "輸出繁體中文，格式：\n"
        "【判斷依據】分成利多、利空與主要矛盾，每項都引用具體數值。\n"
#        "【台股傳導】說明費半、台積電 ADR、台指期、匯率或 VIX 如何傳導至台股。\n"
        "【本週五大財經大事】每項說明事件、已知數據、影響及市場觀察。\n"
#        "【風險提醒】指出資料限制，且不得使用保證獲利語句。\n"
        "不要輸出【本週總判斷】、【原始數據】或【本週情境】段落。"
    )
    summary_text = await generate_custom_brief(prompt, label="weekly_finance_events", num_predict=900)
    if not summary_text:
        bullets = []
        for idx, item in enumerate(searched_news[:5], start=1):
            title = item.get("title") or "未命名事件"
            desc = item.get("description") or "請留意後續公布資訊。"
            bullets.append(f"{idx}. {title}：{desc[:90]}")
        summary_text = (
            "【判斷依據】\n"
            + f"{assessment['macro_reason']}；{assessment['market_reason']}\n\n"
            + "【本週五大財經大事】\n"
            + ("\n".join(bullets) if bullets else "搜尋資料暫時不足，請稍後重試。")
        )
    economic_news_items = [
        {
            "title": (
                f"{item['name']}：{item['value']:.2f} {item['unit']}"
                if item.get("key") == "wti"
                else f"{item['name']}：{item['value']} {item['unit']}"
            ),
            "url": item["source_url"],
            "description": (
                f"期間 {item['period']}；來源 {item['source']}；"
                f"參考頁面 {item['reference_url']}"
            ),
            "published_date": item["period"],
            "economic_data": item,
        }
        for item in economic_data
    ]
    market_news_items = [
        {
            "title": f"{item['name']}：{_fmt_num(item['price'], 3)}（{_fmt_pct(item['change_pct'])}）",
            "url": "",
            "description": f"前值 {_fmt_num(item['prev_close'], 3)}；用於台股方向判斷",
            "published_date": taipei_today,
            "market_signal": item,
        }
        for item in market_signals
    ]
    news_items = economic_news_items + market_news_items + searched_news
    return news_items, summary_text


async def _generate_tw_market_forecast() -> tuple[list[dict], str]:
    """依台指期夜盤、台積電 ADR、SOX 與匯率生成當日台股預測。"""
    from app.services.market_data import get_quote_data
    from app.services.ollama_service import generate_custom_brief

    quote_specs = [
        ("WTX&", "index", "台指期夜盤"),
        ("TSM", "index", "台積電 ADR"),
        ("^SOX", "index", "費城半導體指數"),
        ("TWD=X", "exchange", "USD/TWD"),
        ("2330.TW", "tw_etf", "台積電台股"),
        ("TAIEX", "index", "台灣加權指數"),
    ]
    quote_results = await asyncio.gather(
        *[get_quote_data(symbol, category) for symbol, category, _ in quote_specs],
        return_exceptions=True,
    )

    quotes: dict[str, dict] = {}
    for (symbol, _category, name), result in zip(quote_specs, quote_results):
        if isinstance(result, Exception):
            logger.warning(f"[Briefing] quote fetch failed symbol={symbol}: {result}")
            result = {"price": None, "prev_close": None, "change": None, "success": False}
        price = result.get("price")
        prev_close = result.get("prev_close")
        pct = _pct_change(price, prev_close)
        quotes[symbol] = {
            "name": name,
            "price": price,
            "prev_close": prev_close,
            "change": result.get("change"),
            "change_pct": pct,
            "success": bool(result.get("success")),
        }

    adr_price = quotes["TSM"]["price"]
    usd_twd = quotes["TWD=X"]["price"]
    tsm_tw_prev = quotes["2330.TW"]["prev_close"] or quotes["2330.TW"]["price"]
    adr_theoretical = adr_price * usd_twd / 5 if adr_price and usd_twd else None
    tsm_est_pct = _pct_change(adr_theoretical, tsm_tw_prev)
    taiex_impact_pct = tsm_est_pct * 0.33 if tsm_est_pct is not None else None

    data_lines = [
        f"台指期夜盤 WTX&：現價 {_fmt_num(quotes['WTX&']['price'])}，昨收 {_fmt_num(quotes['WTX&']['prev_close'])}，漲跌幅 {_fmt_pct(quotes['WTX&']['change_pct'])}",
        f"台積電 ADR TSM：現價 USD {_fmt_num(quotes['TSM']['price'])}，昨收 USD {_fmt_num(quotes['TSM']['prev_close'])}，漲跌幅 {_fmt_pct(quotes['TSM']['change_pct'])}",
        f"費城半導體 ^SOX：現價 {_fmt_num(quotes['^SOX']['price'])}，昨收 {_fmt_num(quotes['^SOX']['prev_close'])}，漲跌幅 {_fmt_pct(quotes['^SOX']['change_pct'])}",
        f"USD/TWD：{_fmt_num(usd_twd, 3)}",
        f"台積電台股 2330.TW：現價 {_fmt_num(quotes['2330.TW']['price'])}，昨收 {_fmt_num(quotes['2330.TW']['prev_close'])}",
        f"加權指數 TAIEX：現價 {_fmt_num(quotes['TAIEX']['price'])}，昨收 {_fmt_num(quotes['TAIEX']['prev_close'])}",
        f"ADR 換算台積電理論價格：{_fmt_num(adr_theoretical)} TWD",
        f"台積電預估漲跌幅：{_fmt_pct(tsm_est_pct)}",
        f"台積電對加權指數估算影響：{_fmt_pct(taiex_impact_pct)}",
    ]
    prompt = (
        "根據以下數據建立「台股預測報告」。\n\n"
        "請綜合以下數據：\n\n"
        "1. 台積電ADR\n"
        "2. 台指期夜盤\n"
        "3. 費城半導體指數\n"
        "5. 美元兌台幣\n\n"
        "並使用下列權重：\n\n"
        "- 夜盤 50%\n"
        "- ADR 35%\n"
        "- 費半 15%\n\n"
        "即時數據：\n"
        + "\n".join(data_lines)
        + "\n\n"
        "輸出格式請固定如下，每一項都要保留題目名稱，並在結果後補一句短說明：\n\n"
        "A. 市場方向：看多/中性/看空 - 用一句話說明主要原因。\n"
        "B. 信心指數：0~100 - 用一句話說明信心高低依據。\n"
        "C. 預估開盤點位：點位或區間 - 用一句話說明夜盤/ADR如何影響開盤。\n"
        "D. 預估收盤區間：點位區間 - 用一句話說明盤中可能變化。\n"
        "E. 台積電預估價格：價格或區間 - 用一句話說明ADR換算與權值影響。\n"
        "F. 影響最大的三個因素：因素1、因素2、因素3 - 用一句話說明哪個因素權重最大。\n\n"
        "最後請用一句話總結：\n"
        "「台股今天最可能的劇本」。\n\n"
        "限制：不要輸出 Step、公式或計算過程；不要只給答案，必須包含每一項題目名稱與少量說明。"
    )
    summary_text = await generate_custom_brief(prompt, label="tw_market_forecast", num_predict=650)
    if not summary_text:
        direction = "偏多" if ((quotes["WTX&"]["change_pct"] or 0) * 0.5 + (quotes["TSM"]["change_pct"] or 0) * 0.35 + (quotes["^SOX"]["change_pct"] or 0) * 0.15) > 0 else "偏空"
        summary_text = (
            "【結論】\n"
            f"方向：{direction}\n"
            "信心：低，因 AI 彙整暫時無法完成，以下僅依即時報價機械估算。\n"
            f"開盤區間：參考台指期夜盤 {_fmt_pct(quotes['WTX&']['change_pct'])} 與 ADR 換算 {_fmt_pct(tsm_est_pct)}\n"
            f"收盤區間：留意台積電影響約 {_fmt_pct(taiex_impact_pct)} 及電子權值股續航。"
        )

    news_items = [
        {"title": row, "url": "", "description": "", "published_date": ""}
        for row in data_lines
    ]
    return news_items, summary_text


async def _generate_special_brief_items(sb, session_time: datetime) -> dict:
    stats = {"total": len(SPECIAL_BRIEF_ITEMS), "success": 0, "failed": 0}

    generators = [
        ("AI_WEEK", "一週財經大事", _generate_weekly_finance_events),
        ("AI_TW_FCST", "當日台股大盤風向與指數預測", _generate_tw_market_forecast),
    ]
    for symbol, name, generator in generators:
        try:
            news_items, summary_text = await generator()
            ok = await _upsert_special_brief(sb, session_time, symbol, name, news_items, summary_text)
            if ok:
                stats["success"] += 1
            else:
                stats["failed"] += 1
        except Exception as e:
            logger.error(f"[Briefing] 特殊早報 {symbol} 生成失敗: {e}")
            stats["failed"] += 1
            try:
                await _upsert_special_brief(sb, session_time, symbol, name, [], "", str(e))
            except Exception as db_err:
                logger.error(f"[Briefing] 特殊早報 {symbol} 寫入失敗狀態也失敗: {db_err}")

    return stats


async def run_special_brief_items(session_time: datetime) -> dict:
    """單獨生成固定 AI brief 項目，供 API 在舊批次缺資料時背景補齊。"""
    sb = get_supabase()
    return await _generate_special_brief_items(sb, session_time)


async def run_market_briefing_session(override_session_time: datetime | None = None) -> dict:
    """
    執行一次市場早報排程：
      1. 查詢 tracked_indices 中所有 is_active=True 的唯一 symbol
      2. 計算本次 session_time（若 override_session_time 提供則使用之，否則計算最近排程時間）
      3. 對每個 symbol 呼叫設定的搜尋 + AI 摘要提供商
      4. Upsert 結果至 market_briefings 表
      5. 回傳統計 {"total": n, "success": n, "failed": n}

    Args:
        override_session_time: 若提供，強制使用此時間戳記（用於手動觸發，方便前端 polling 追蹤）

    Returns:
        {"total": int, "success": int, "failed": int}
    """
    sb = get_supabase()
    session_time = override_session_time if override_session_time is not None else _get_nearest_session_time()
    session_hour = (session_time + timedelta(hours=8)).hour  # 轉回 Taipei hour 供 prompt 使用

    logger.info(f"[Briefing] 排程開始，session_time={session_time.isoformat()}")

    special_stats = await _generate_special_brief_items(sb, session_time)

    # 1. 查詢所有 is_active=True 的唯一 symbol
    try:
        res = sb.table("tracked_indices").select("symbol, name, category").eq("is_active", True).execute()
    except Exception as e:
        logger.error(f"[Briefing] 查詢 tracked_indices 失敗: {e}")
        return special_stats

    if not res.data:
        logger.info("[Briefing] 無 is_active=True 的追蹤項目，僅完成固定 AI brief 項目")
        return special_stats

    # 去重（同 symbol 可能被多位使用者追蹤）
    seen: set[str] = set()
    symbols: list[dict] = []
    for row in res.data:
        sym = row.get("symbol", "")
        if sym and sym not in seen:
            seen.add(sym)
            symbols.append({
                "symbol": sym,
                "name": row.get("name", sym),
                "category": row.get("category", "us_etf"),
            })

    # 限制上限
    if len(symbols) > MAX_SYMBOLS_PER_SESSION:
        logger.warning(
            f"[Briefing] unique symbol 數量 {len(symbols)} 超過上限 {MAX_SYMBOLS_PER_SESSION}，"
            "截斷超額 symbols"
        )
        symbols = symbols[:MAX_SYMBOLS_PER_SESSION]

    total = len(symbols) + special_stats["total"]
    success_count = special_stats["success"]
    failed_count = special_stats["failed"]

    use_tavily = settings.ai_summary.upper() == "TAVILY"
    use_searxng_ollama = settings.ai_summary.upper() == "SEARXNG_OLLAMA"

    if use_tavily:
        provider_label = "Tavily"
    elif use_searxng_ollama:
        provider_label = "SearXNG+Ollama"
    else:
        provider_label = "Brave+Gemini"
    logger.info(f"[Briefing] 使用摘要提供商：{provider_label}")

    # 2. 逐個 symbol 處理
    for item in symbols:
        symbol = item["symbol"]
        symbol_name = item["name"]
        category = item.get("category", "us_etf")
        try:
            search_query = _build_search_query(symbol, symbol_name, category)

            if use_tavily:
                # --- Tavily 路徑：搜尋 + 摘要一次完成 ---
                news_items, summary_text = await tavily_search_and_summarize(
                    symbol=symbol,
                    symbol_name=symbol_name,
                    query=search_query,
                    session_hour=session_hour,
                )
            elif use_searxng_ollama:
                # --- SearXNG + Ollama Direct 路徑（v3）---
                from app.services.searxng_service import search_news as searxng_search_news
                from app.services.ollama_service import generate_market_summary as ollama_generate
                news_items = await searxng_search_news(query=search_query, count=3)
                if not news_items:
                    # 保底：SearXNG 被 403 或無結果時，改由 Brave 補新聞來源。
                    logger.warning(
                        f"[Briefing] SearXNG 無結果，改用 Brave fallback symbol={symbol}"
                    )
                    news_items = await search_news(query=search_query, count=3)
                summary_text = await ollama_generate(
                    symbol=symbol,
                    symbol_name=symbol_name,
                    news_items=news_items,
                    session_hour=session_hour,
                )
                # Ollama 無 rate limit，不需 sleep(7)
            else:
                # --- Brave + Gemini 路徑（原有邏輯）---
                news_items = await search_news(
                    query=search_query,
                    count=3,
                )

                # 生成 AI 摘要
                summary_text = await generate_market_summary(
                    symbol=symbol,
                    symbol_name=symbol_name,
                    news_items=news_items,
                    session_hour=session_hour,
                )

                # Gemini free tier 限制 10 RPM，每次呼叫後等 7 秒（≈ 8.5 RPM）
                if news_items:
                    await asyncio.sleep(7)

            status = "completed" if summary_text else "failed"
            error_message = None if summary_text else f"{provider_label} 回傳空摘要"

            # Upsert 至 market_briefings
            sb.table("market_briefings").upsert(
                {
                    "session_time": session_time.isoformat(),
                    "symbol": symbol,
                    "symbol_name": symbol_name,
                    "news_json": news_items,
                    "summary_text": summary_text,
                    "status": status,
                    "error_message": error_message,
                },
                on_conflict="session_time,symbol",
            ).execute()

            if status == "completed":
                success_count += 1
            else:
                failed_count += 1

        except Exception as e:
            logger.error(f"[Briefing] 處理 {symbol} 失敗: {e}")
            failed_count += 1
            # 記錄失敗狀態
            try:
                sb.table("market_briefings").upsert(
                    {
                        "session_time": session_time.isoformat(),
                        "symbol": symbol,
                        "symbol_name": symbol_name,
                        "news_json": [],
                        "summary_text": None,
                        "status": "failed",
                        "error_message": str(e),
                    },
                    on_conflict="session_time,symbol",
                ).execute()
            except Exception as db_err:
                logger.error(f"[Briefing] 寫入失敗狀態至 DB 也失敗 {symbol}: {db_err}")

        # 保護 Brave+Gemini rate limit；Tavily 不需要此延遲但保留最小間隔
        await asyncio.sleep(1 if not use_tavily else 0.2)

    stats = {"total": total, "success": success_count, "failed": failed_count}
    logger.info(f"[Briefing] 排程完成: {stats}")
    return stats
