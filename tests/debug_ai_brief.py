"""AI Briefing Debug Tool — 手動觸發 / 查看 AI 早報結果.

使用方式：
  cd finance_dashboard

  # 觸發排程並等候 60 秒後顯示結果
  python tests/debug_ai_brief.py --trigger

  # 觸發並只等 30 秒
  python tests/debug_ai_brief.py --trigger --wait 30

  # 只顯示最新早報（不觸發）
  python tests/debug_ai_brief.py --latest

  # 列出最近 session 清單
  python tests/debug_ai_brief.py --sessions

  # 直接測試單一 symbol（不寫 DB，印出搜尋+摘要結果）— 自動讀取 .env 中的 AI_SUMMARY
  python tests/debug_ai_brief.py --test-symbol VTI
  python tests/debug_ai_brief.py --test-symbol 台積電 --category tw_etf

  # 強制指定提供商（不修改 .env，僅本次測試）
  python tests/debug_ai_brief.py --test-symbol VTI --ai-summary TAVILY
  python tests/debug_ai_brief.py --test-symbol VTI --ai-summary BRAVE_GEMINI

  # 顯示目前 .env 中的提供商設定
  python tests/debug_ai_brief.py --show-config

  # 指定帳密（否則自動讀 .env 中的 DEBUG_EMAIL / DEBUG_PASSWORD）
  python tests/debug_ai_brief.py --trigger --email me@example.com --password secret
"""

import argparse
import asyncio
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "http://localhost:8005"


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


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _request(method: str, path: str, token: str | None = None, body: dict | None = None) -> dict:
    url = BASE_URL + path
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print("[ERROR] HTTP %d: %s" % (e.code, e.read().decode()[:300]), file=sys.stderr)
        sys.exit(1)


def login(email: str, password: str) -> str:
    print("  -> Login %s ..." % email)
    result = _request("POST", "/api/auth/login", body={"email": email, "password": password})
    token = result.get("access_token") or result.get("token")
    if not token:
        print("[ERROR] Login failed: %s" % result, file=sys.stderr)
        sys.exit(1)
    print("  OK")
    return token


# ---------------------------------------------------------------------------
# .env helpers
# ---------------------------------------------------------------------------

def _load_env() -> dict[str, str]:
    """讀取 .env 中所有 KEY=VALUE，回傳 dict."""
    env: dict[str, str] = {}
    env_paths = [
        Path(__file__).parent.parent / "backend" / "app" / ".env",
        Path(__file__).parent.parent / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    env.setdefault(k.strip(), v.strip())
    return env


def _load_env_credentials() -> tuple[str | None, str | None]:
    env = _load_env()
    return env.get("DEBUG_EMAIL"), env.get("DEBUG_PASSWORD")


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


# ---------------------------------------------------------------------------
# Print helpers
# ---------------------------------------------------------------------------

def print_latest(data: dict) -> None:
    session_time = data.get("session_time")
    items = data.get("items", [])
    if not session_time:
        print("\n[!] No briefing records (run migration or trigger first)")
        return
    print("\n=== Latest Briefing  session=%s  symbols=%d ===\n" % (session_time, len(items)))
    print("  %-14s %-22s %-10s %s" % ("SYMBOL", "NAME", "STATUS", "SUMMARY (60 chars)"))
    print("  " + "-" * 100)
    for item in items:
        symbol = item.get("symbol", "")
        name = (item.get("symbol_name") or "")[:20]
        status = item.get("status", "")
        summary = (item.get("summary_text") or item.get("error_message") or "(none)")[:60]
        news_cnt = len(item.get("news_json") or [])
        icon = "[OK]" if status == "completed" else ("[NG]" if status == "failed" else "[..]")
        print("  %-14s %-22s %s %-9s %s  [%d news]" % (symbol, name, icon, status, summary, news_cnt))


def print_sessions(sessions: list) -> None:
    print("\n=== Recent %d sessions ===\n" % len(sessions))
    print("  %-32s %6s %10s %7s" % ("session_time", "total", "completed", "failed"))
    print("  " + "-" * 62)
    for s in sessions:
        print("  %-32s %6d %10d %7d" % (
            s["session_time"], s["total"], s["completed"], s["failed"]
        ))


def show_config() -> None:
    """顯示目前 .env 中的 AI Briefing 相關設定."""
    env = _load_env()
    provider = env.get("AI_SUMMARY", "BRAVE_GEMINI (預設)")
    brave_key = env.get("BRAVE_SEARCH_API_KEY", "")
    gemini_key = env.get("GEMINI_API_KEY", "")
    tavily_key = env.get("TAVILY_SEARCH_API_KEY", "")
    searxng_url = env.get("SEARXNG_BASE_URL", "https://search.skynetapp.org")
    ollama_url = env.get("OLLAMA_BASE_URL", "http://192.168.0.26:11434")

    def mask(key: str) -> str:
        return (key[:6] + "..." + key[-4:]) if len(key) > 12 else ("(未設定)" if not key else key)

    print("\n=== AI Briefing 設定 ===\n")
    print(f"  AI_SUMMARY            : {provider}")
    print(f"  SEARXNG_BASE_URL      : {searxng_url}")
    print(f"  OLLAMA_BASE_URL       : {ollama_url}")
    print(f"  BRAVE_SEARCH_API_KEY  : {mask(brave_key)}")
    print(f"  GEMINI_API_KEY        : {mask(gemini_key)}")
    print(f"  TAVILY_SEARCH_API_KEY : {mask(tavily_key)}")
    print()

    if provider.upper() == "TAVILY":
        if not tavily_key:
            print("  [!] AI_SUMMARY=TAVILY 但 TAVILY_SEARCH_API_KEY 未設定！")
        else:
            print("  [OK] Tavily 已設定，將跳過 Brave+Gemini 呼叫")
    else:
        missing = []
        if not brave_key:
            missing.append("BRAVE_SEARCH_API_KEY")
        if not gemini_key:
            missing.append("GEMINI_API_KEY")
        if missing:
            print("  [!] 缺少必要 key：" + ", ".join(missing))
        else:
            print("  [OK] Brave+Gemini 均已設定")


# ---------------------------------------------------------------------------
# Direct single-symbol test（不需登入，直接在 backend 環境執行）
# ---------------------------------------------------------------------------

async def _test_symbol_async(
    symbol: str,
    symbol_name: str,
    category: str,
    ai_summary: str | None,
    searxng_url: str | None,
) -> None:
    """直接呼叫 service function 測試單一 symbol，不走 HTTP，不寫 DB."""
    # 動態設定 AI_SUMMARY 環境變數（若有指定 --ai-summary）
    env_map = _load_env()
    provider = (ai_summary or env_map.get("AI_SUMMARY", "BRAVE_GEMINI")).upper()

    # 把 .env 中的 key 補入環境（若尚未存在）
    for k, v in env_map.items():
        os.environ.setdefault(k, v)
    os.environ["AI_SUMMARY"] = provider
    if searxng_url:
        os.environ["SEARXNG_BASE_URL"] = searxng_url

    # 必須在設定環境後才匯入（避免 lru_cache 提前讀到空值）
    import importlib, sys as _sys

    # 清除 lru_cache 以讓 get_settings() 重新讀環境變數
    for mod_name in list(_sys.modules.keys()):
        if "app.config" in mod_name or "app.services" in mod_name:
            del _sys.modules[mod_name]

    # 設定 PYTHONPATH
    backend_path = str(Path(__file__).parent.parent / "backend")
    if backend_path not in _sys.path:
        _sys.path.insert(0, backend_path)

    query = _build_search_query(symbol, symbol_name, category)

    print(f"\n=== 直接測試 symbol={symbol}  provider={provider} ===")
    if provider == "SEARXNG_OLLAMA":
        print(f"  searxng_url: {os.environ.get('SEARXNG_BASE_URL', '')}")
    print(f"  query: {query}\n")

    if provider == "TAVILY":
        from app.services.tavily_service import search_and_summarize
        news_items, summary = await search_and_summarize(
            symbol=symbol,
            symbol_name=symbol_name,
            query=query,
            session_hour=8,
        )
    elif provider == "SEARXNG_OLLAMA":
        from app.services.searxng_service import search_news as searxng_search_news
        from app.services.ollama_service import generate_market_summary as ollama_generate
        news_items = await searxng_search_news(query=query, count=3)
        if not news_items:
            from app.services.brave_search_service import search_news as brave_search_news
            print("  [warn] SearXNG 無結果，改用 Brave fallback 搜尋")
            news_items = await brave_search_news(query=query, count=3)
        summary = await ollama_generate(
            symbol=symbol,
            symbol_name=symbol_name,
            news_items=news_items,
            session_hour=8,
        )
    else:
        from app.services.brave_search_service import search_news
        from app.services.gemini_service import generate_market_summary
        news_items = await search_news(query=query, count=3)
        summary = await generate_market_summary(
            symbol=symbol,
            symbol_name=symbol_name,
            news_items=news_items,
            session_hour=8,
        )

    print(f"  新聞數量：{len(news_items)}")
    for i, item in enumerate(news_items, 1):
        title = item.get("title", "(無標題)")[:80]
        url = item.get("url", "")[:80]
        date = item.get("published_date", "")
        print(f"  [{i}] {title}")
        print(f"       {url}  ({date})")

    print(f"\n  摘要（{len(summary)} 字）：")
    if summary:
        # 每 60 字換行顯示
        for i in range(0, len(summary), 60):
            print("    " + summary[i:i+60])
    else:
        print("    (無摘要)")
    print()


def test_symbol(
    symbol: str,
    symbol_name: str,
    category: str,
    ai_summary: str | None,
    searxng_url: str | None,
) -> None:
    asyncio.run(_test_symbol_async(symbol, symbol_name, category, ai_summary, searxng_url))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="AI Briefing Debug Tool")
    parser.add_argument("--trigger",     action="store_true", help="Manually trigger briefing session")
    parser.add_argument("--latest",      action="store_true", help="Show latest briefing result")
    parser.add_argument("--sessions",    action="store_true", help="List recent sessions")
    parser.add_argument("--show-config", action="store_true", help="Show current AI summary provider config")
    parser.add_argument("--test-symbol", metavar="SYMBOL",
                        help="Directly test search+summary for a single symbol (no DB write)")
    parser.add_argument("--name",     default=None,
                        help="Symbol display name for --test-symbol (default: same as symbol)")
    parser.add_argument("--category", default="us_etf",
                        choices=["us_etf", "tw_etf", "exchange", "index", "vix", "oil", "crypto", "rate", "interest_rate", "stock"],
                        help="Category for --test-symbol (default: us_etf)")
    parser.add_argument("--ai-summary", default=None,
                        choices=["TAVILY", "BRAVE_GEMINI", "SEARXNG_OLLAMA"],
                        help="Override AI_SUMMARY provider for --test-symbol only")
    parser.add_argument("--searxng-url", default=None,
                        help="Override SEARXNG_BASE_URL for --test-symbol only")
    parser.add_argument("--wait", type=int, default=60,
                        help="Seconds to wait after trigger before showing result (default: 60)")
    parser.add_argument("--email",    default=None, help="Login email")
    parser.add_argument("--password", default=None, help="Login password")
    args = parser.parse_args()

    # --show-config 和 --test-symbol 不需要 HTTP 登入
    if args.show_config:
        show_config()
        if not (args.trigger or args.latest or args.sessions or args.test_symbol):
            return

    if args.test_symbol:
        symbol_name = args.name or args.test_symbol
        test_symbol(args.test_symbol, symbol_name, args.category, args.ai_summary, args.searxng_url)
        if not (args.trigger or args.latest or args.sessions):
            return

    # 未指定 HTTP 動作時，預設顯示最新早報
    if not (args.trigger or args.latest or args.sessions or args.show_config or args.test_symbol):
        args.latest = True

    if not (args.trigger or args.latest or args.sessions):
        return

    email = args.email
    password = args.password
    if not email or not password:
        env_email, env_pass = _load_env_credentials()
        email = email or env_email
        password = password or env_pass
    if not email or not password:
        print(
            "[ERROR] Provide --email/--password, or set DEBUG_EMAIL/DEBUG_PASSWORD in .env",
            file=sys.stderr,
        )
        sys.exit(1)

    token = login(email, password)

    if args.sessions:
        sessions = _request("GET", "/api/briefing/sessions", token=token)
        print_sessions(sessions)

    if args.trigger:
        print("\n[*] Triggering briefing session...")
        resp = _request("POST", "/api/briefing/trigger", token=token, body={})
        print("  -> " + resp.get("message", str(resp)))
        if args.wait > 0:
            print("\n  [*] Waiting %ds for background job..." % args.wait)
            for elapsed in range(0, args.wait, 5):
                remaining = args.wait - elapsed
                print("      ~%ds remaining..." % remaining, end="\r", flush=True)
                time.sleep(min(5, remaining))
            print()
        args.latest = True

    if args.latest:
        data = _request("GET", "/api/briefing/latest", token=token)
        print_latest(data)


if __name__ == "__main__":
    main()
