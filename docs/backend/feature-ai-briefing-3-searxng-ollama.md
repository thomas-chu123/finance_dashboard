---
goal: "實作 AI 每日市場早報 v3 — 以 SearXNG (search.skynetapp.org) 取代新聞搜尋、以 Ollama Direct API (192.168.0.26:11434) 取代 LLM 摘要"
version: 1.0
date_created: 2026-03-31
last_updated: 2026-03-31
owner: Platform Team
status: 'Planned'
tags: [feature, ai, briefing, searxng, ollama, infrastructure, chore]
---

# Feature: AI Market Briefing v3 — SearXNG + Ollama Direct

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

本文件為 AI 每日市場早報的**第三版實作規格**。前兩版分別為：
- **v1**（`feature-ai-briefing-1.md`）：Brave Search + Gemini（已實作）
- **v2 架構遷移**（`architecture-searxng-ollama-1.md`）：計畫改用 SearXNG + OpenWebUI（`chat.skyapp.org`）

本版（**v3**）在 v2 架構的基礎上做出以下重要修正：

| 項目 | v2 架構計畫 | **v3 本版（實作目標）** |
|------|-------------|------------------------|
| SearXNG URL | `https://search.skyapp.org` | **`https://search.skynetapp.org`** |
| Ollama 接入方式 | OpenWebUI proxy（`https://chat.skyapp.org`）+ Bearer token | **Direct Ollama API（`http://192.168.0.26:11434`）無需認證** |
| 網路位置 | 外部 HTTPS | **內網 HTTP（192.168.0.26）** |
| 認證 | OpenWebUI API Key | **無（Ollama 原生不驗證）** |

---

## 0. 現況分析

### 0.1 目前已實作的路徑（news_briefing_service.py）

```
news_briefing_service.py (協調器)
    ├── AI_SUMMARY=BRAVE_GEMINI  →  brave_search_service.py + gemini_service.py
    └── AI_SUMMARY=TAVILY        →  tavily_service.py (搜尋+摘要一次完成)
```

**主要痛點：**
- Gemini 免費版 **10 RPM** 限制，每次 `asyncio.sleep(7)`，20 個 symbols ≈ 140 秒
- Brave Search 每月 2,000 req 上限（免費方案）
- 所有推理依賴外部雲端 API

### 0.2 目標架構（v3 新增路徑）

```
news_briefing_service.py (協調器)
    ├── AI_SUMMARY=BRAVE_GEMINI  →  brave_search_service.py + gemini_service.py（不變）
    ├── AI_SUMMARY=TAVILY        →  tavily_service.py（不變）
    └── AI_SUMMARY=SEARXNG_OLLAMA →  searxng_service.py + ollama_service.py（本版新增）
```

### 0.3 服務端點驗證

- **SearXNG**: `https://search.skynetapp.org/search?q=test&format=json&categories=news`
- **Ollama Direct**: `http://192.168.0.26:11434/v1/chat/completions`（OpenAI 相容格式，Ollama ≥ 0.1.14 原生支援）

---

## 1. Requirements & Constraints

| ID | 類型 | 描述 |
|----|------|------|
| REQ-001 | 功能 | `searxng_service.search_news()` 回傳格式與現有 `brave_search_service.search_news()` 相容：`list[{"title", "url", "description", "published_date"}]` |
| REQ-002 | 功能 | `ollama_service.generate_market_summary()` 回傳 100-150 字**繁體中文**市場摘要字串，格式與 `gemini_service` 相容 |
| REQ-003 | 功能 | 新增 `AI_SUMMARY=SEARXNG_OLLAMA` 環境變數選項，**不修改**現有 `BRAVE_GEMINI` / `TAVILY` 路徑 |
| REQ-004 | 性能 | 20 個 symbols 完整排程執行時間 ≤ **5 分鐘**（移除 sleep 7s 限制） |
| REQ-005 | 性能 | 單 symbol 處理延遲（搜尋 + 摘要）≤ **60 秒** |
| CON-001 | 基礎設施 | `search.skynetapp.org` 與 `192.168.0.26:11434` 均已部署，**本計畫不涉及基礎設施變更** |
| CON-002 | 相容性 | Ollama 使用 OpenAI 相容 `/v1/chat/completions` 端點（`messages` 陣列格式），**不使用** Ollama 原生 `/api/generate` |
| CON-003 | 安全 | Ollama Direct 無需 API Key；`searxng_base_url` 與 `ollama_base_url` 存放於 `.env`，**不 hardcode** |
| CON-004 | 相容性 | 不修改 `brave_search_service.py`、`gemini_service.py`、`tavily_service.py` |
| SEC-001 | 安全 | `search.skynetapp.org` 為外部 HTTPS，TLS 憑證驗證**保持啟用** |
| SEC-002 | 安全 | Ollama `192.168.0.26:11434` 為**內網 HTTP**，僅限後端伺服器同網段存取（不得暴露至公網） |
| GUD-001 | 開發規範 | 新服務遵循現有 `services/` 模組架構：async, httpx, logger, try/except |
| GUD-002 | 開發規範 | 所有新環境變數在 `config.py` 的 `Settings` 中宣告，提供合理預設值 |

---

## 2. 技術設計

### 2.1 SearXNG 搜尋服務

**端點：** `https://search.skynetapp.org/search`

| 參數 | 值 | 說明 |
|------|----|------|
| `q` | `{symbol_name} {symbol} ETF stock` | 搜尋關鍵字 |
| `format` | `json` | 必填，取得 JSON 結構 |
| `categories` | `news` | 僅取新聞分類 |
| `language` | `zh-TW` | 優先中文結果 |
| `time_range` | `week` | 近一週新聞 |

**回應欄位對應：**

| SearXNG 欄位 | 對應輸出 | 說明 |
|-------------|---------|------|
| `title` | `title` | 新聞標題 |
| `url` | `url` | 來源連結 |
| `content` | `description` | 新聞摘要（SearXNG 用 `content`） |
| `publishedDate` | `published_date` | 發布時間（可能為空） |

### 2.2 Ollama Direct API

**端點：** `http://192.168.0.26:11434/v1/chat/completions`

| 參數 | 值 |
|------|----|
| 協定 | HTTP（內網，非 HTTPS） |
| 認證 | 無（不傳 `Authorization` header） |
| Content-Type | `application/json` |
| `model` | `gpt-oss:20b` |
| `temperature` | `0.3`（低隨機性，提升一致性） |
| `max_tokens` | `400` |
| `stream` | `false` |
| Timeout | `120s`（20B 模型冷啟動較慢） |

**Prompt 設計（與 v2 相同）：**
```
你是一位專業的金融市場分析師。
以下是關於 {symbol_name}（{symbol}）在 {session_label} 的最新 {n} 則新聞：

新聞 1：{title}
摘要：{description}
...

請根據上述新聞，以繁體中文（非簡體中文）撰寫一段 100-150 字的市場動態摘要。
格式：純文字，無需標題，包含：(1) 主要市場動態 (2) 潛在影響 (3) 投資者關注要點。
```

### 2.3 news_briefing_service.py 修改邏輯

```python
# 新增第三條路徑
use_searxng_ollama = settings.ai_summary.upper() == "SEARXNG_OLLAMA"

if use_tavily:
    # 現有 Tavily 路徑（不變）
    ...
elif use_searxng_ollama:
    # 新增：SearXNG + Ollama 路徑
    from app.services.searxng_service import search_news as searxng_search
    from app.services.ollama_service import generate_market_summary as ollama_summary
    news_items = await searxng_search(query=search_query, count=3)
    summary_text = await ollama_summary(...)
    # 無需 sleep：Ollama 無 rate limit
else:
    # 現有 Brave + Gemini 路徑（不變）
    ...
```

---

## 3. Implementation Steps

### Phase 1：服務可用性確認

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | 驗證 SearXNG：`curl "https://search.skynetapp.org/search?q=VTI+ETF&format=json&categories=news"` 確認回傳含 `results` 陣列的 JSON | | |
| TASK-002 | 驗證 Ollama Direct：`curl http://192.168.0.26:11434/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"gpt-oss:20b","messages":[{"role":"user","content":"你好，用繁體中文回答"}],"stream":false}'` 確認回傳正常 | | |
| TASK-003 | 確認後端伺服器可連通 `search.skynetapp.org`（443/HTTPS）：`curl -I https://search.skynetapp.org` | | |
| TASK-004 | 確認後端伺服器可連通 `192.168.0.26:11434`（HTTP，同網段）：`curl http://192.168.0.26:11434/api/tags` 確認 Ollama 正常回應 | | |

### Phase 2：後端服務模組新增

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-005 | **新增 `backend/app/services/searxng_service.py`**：實作 `async def search_news(query: str, count: int = 3) -> list[dict]`，使用 httpx 呼叫 `{settings.searxng_base_url}/search`，回傳 `[{"title","url","description","published_date"}]` 格式；錯誤時回傳空 list 並記錄 warning | | |
| TASK-006 | **新增 `backend/app/services/ollama_service.py`**：實作 `async def generate_market_summary(symbol, symbol_name, news_items, session_hour) -> str`，呼叫 `{settings.ollama_base_url}/v1/chat/completions`，**不傳 Authorization header**（Ollama 無需認證）；timeout=120s；錯誤時回傳 `""` | | |
| TASK-007 | **修改 `backend/app/config.py`**：在 `Settings` 新增：`searxng_base_url: str = "https://search.skynetapp.org"`、`ollama_base_url: str = "http://192.168.0.26:11434"`、`ollama_model: str = "gpt-oss:20b"` | | |
| TASK-008 | **修改 `backend/app/services/news_briefing_service.py`**：新增 `SEARXNG_OLLAMA` 分支；移除 `SEARXNG_OLLAMA` 路徑中的 `asyncio.sleep(7)`（保留 `sleep(1)` 最小間隔）；更新 module docstring | | |

### Phase 3：設定與環境變數

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-009 | **修改 `.env`**（本機開發）：新增 `AI_SUMMARY=SEARXNG_OLLAMA`、`SEARXNG_BASE_URL=https://search.skynetapp.org`、`OLLAMA_BASE_URL=http://192.168.0.26:11434`、`OLLAMA_MODEL=gpt-oss:20b` | | |
| TASK-010 | **確認 `.gitignore`**：確認 `.env` 已排除（不含敏感端點至 Git）| | |

### Phase 4：測試

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-011 | **新增 `tests/unit/test_searxng_service.py`**：見 §5 測試規格 | | |
| TASK-012 | **新增 `tests/unit/test_ollama_service.py`**：見 §5 測試規格 | | |
| TASK-013 | **手動驗收**：設定 `AI_SUMMARY=SEARXNG_OLLAMA` 後呼叫 `POST /api/briefing/trigger`，檢查 Supabase `market_briefings` 表中是否寫入正確繁體中文摘要 | | |

---

## 4. 影響檔案清單

| 操作 | 檔案 | 說明 |
|------|------|------|
| **新增** | `backend/app/services/searxng_service.py` | SearXNG 新聞搜尋服務 |
| **新增** | `backend/app/services/ollama_service.py` | Ollama Direct API 摘要服務 |
| **新增** | `tests/unit/test_searxng_service.py` | SearXNG 單元測試 |
| **新增** | `tests/unit/test_ollama_service.py` | Ollama 單元測試 |
| **修改** | `backend/app/config.py` | 新增 `searxng_base_url`、`ollama_base_url`、`ollama_model` |
| **修改** | `backend/app/services/news_briefing_service.py` | 新增 `SEARXNG_OLLAMA` 分支 |
| **修改** | `.env`（本機） | 新增環境變數（不進 Git） |
| **不修改** | `brave_search_service.py` | 保留向後相容 |
| **不修改** | `gemini_service.py` | 保留向後相容 |
| **不修改** | `tavily_service.py` | 保留向後相容 |
| **不修改** | `routers/briefing.py` | API 層無需變更 |
| **不修改** | `frontend/` | 前端無需變更 |
| **不修改** | `docker-compose.yml` | 無需新增容器 |

---

## 5. 測試規格

### 5.1 `test_searxng_service.py`

| Test ID | 函式 | 測試情境 | 預期結果 |
|---------|------|---------|---------|
| TEST-001 | `test_search_news_returns_correct_format` | mock SearXNG 回傳含 3 則結果的 JSON | 回傳 `list[dict]` 且每項含 `title/url/description/published_date` |
| TEST-002 | `test_search_news_http_error_returns_empty` | mock HTTP 500 回應 | 回傳 `[]`，不拋例外 |
| TEST-003 | `test_search_news_no_base_url_returns_empty` | `searxng_base_url=""` | 回傳 `[]`，記錄 warning |
| TEST-004 | `test_search_news_timeout_returns_empty` | mock `httpx.TimeoutException` | 回傳 `[]`，不拋例外 |
| TEST-005 | `test_search_news_empty_results_returns_empty` | mock 回傳 `{"results": []}` | 回傳 `[]` |

### 5.2 `test_ollama_service.py`

| Test ID | 函式 | 測試情境 | 預期結果 |
|---------|------|---------|---------|
| TEST-006 | `test_generate_summary_returns_string` | mock Ollama 正常回應 | 回傳非空字串 |
| TEST-007 | `test_generate_summary_no_news_returns_empty` | `news_items=[]` | 回傳 `""`，不呼叫 Ollama |
| TEST-008 | `test_generate_summary_no_base_url_returns_empty` | `ollama_base_url=""` | 回傳 `""`，記錄 warning |
| TEST-009 | `test_generate_summary_http_error_returns_empty` | mock HTTP 500 | 回傳 `""`，不拋例外 |
| TEST-010 | `test_generate_summary_timeout_returns_empty` | mock `httpx.TimeoutException` | 回傳 `""`，不拋例外 |
| TEST-011 | `test_generate_summary_no_auth_header` | 正常呼叫 | 確認 httpx 請求 headers **不含** `Authorization` 欄位 |

---

## 6. 參考實作

### 6.1 `searxng_service.py`

```python
"""
SearXNG 自架搜尋服務 — 取代 brave_search_service（新聞搜尋部分）.

端點：https://search.skynetapp.org/search
認證：無（公開端點）
"""
import logging
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)


async def search_news(query: str, count: int = 3) -> list[dict]:
    """
    呼叫 SearXNG JSON API 搜尋新聞.

    Args:
        query: 搜尋關鍵字（如 "VTI ETF stock fund"）
        count: 回傳最多幾則新聞（預設 3）

    Returns:
        list[dict]，每項含 title/url/description/published_date；失敗回傳 []
    """
    settings = get_settings()
    base_url = settings.searxng_base_url
    if not base_url:
        logger.warning("[SearXNG] searxng_base_url 未設定，跳過搜尋")
        return []

    params = {
        "q": query,
        "format": "json",
        "categories": "news",
        "language": "zh-TW",
        "time_range": "week",
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{base_url}/search", params=params)
        if resp.status_code != 200:
            logger.error(f"[SearXNG] HTTP {resp.status_code} for query='{query}'")
            return []

        results = resp.json().get("results", [])[:count]
        news_items = [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("content", ""),  # SearXNG 使用 content 欄位
                "published_date": item.get("publishedDate", ""),
            }
            for item in results
        ]
        logger.info(f"[SearXNG] query='{query}' → {len(news_items)} 則新聞")
        return news_items
    except Exception as e:
        logger.error(f"[SearXNG] 搜尋失敗 query='{query}': {e}")
        return []
```

### 6.2 `ollama_service.py`

```python
"""
Ollama Direct API 摘要服務 — 取代 gemini_service.

端點：http://192.168.0.26:11434/v1/chat/completions（OpenAI 相容格式）
認證：無（Ollama 本地 API 不需要認證）
模型：gpt-oss:20b
"""
import logging
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)

SESSION_LABEL_MAP = {8: "開盤前早報", 13: "午間快報", 18: "收盤後晚報"}


async def generate_market_summary(
    symbol: str,
    symbol_name: str,
    news_items: list[dict],
    session_hour: int = 8,
) -> str:
    """
    呼叫 Ollama gpt-oss:20b 生成繁體中文市場摘要.

    Args:
        symbol: 股票/ETF 代碼（如 "VTI"）
        symbol_name: 中文名稱（如 "先鋒整體市場ETF"）
        news_items: 由 searxng_service 回傳的新聞 list
        session_hour: 排程小時（8/13/18），影響 prompt 標題

    Returns:
        100-150 字繁體中文摘要字串；失敗回傳 ""
    """
    settings = get_settings()
    base_url = settings.ollama_base_url
    model = settings.ollama_model

    if not base_url:
        logger.warning("[Ollama] ollama_base_url 未設定，跳過摘要生成")
        return ""
    if not news_items:
        logger.info(f"[Ollama] {symbol} 無新聞，跳過摘要生成")
        return ""

    session_label = SESSION_LABEL_MAP.get(session_hour, "市場快報")
    news_text = "\n\n".join(
        f"新聞 {i + 1}：{item.get('title', '')}\n摘要：{item.get('description', '')}"
        for i, item in enumerate(news_items)
    )
    user_message = (
        f"你是一位專業的金融市場分析師。"
        f"以下是關於 {symbol_name}（{symbol}）在 {session_label} 的最新 {len(news_items)} 則新聞：\n\n"
        f"{news_text}\n\n"
        "請根據上述新聞，以繁體中文（非簡體中文）撰寫一段 100-150 字的市場動態摘要。\n"
        "格式：純文字，無需標題，包含：(1) 主要市場動態 (2) 潛在影響 (3) 投資者關注要點。"
    )

    # 使用 OpenAI 相容 /v1/chat/completions（Ollama ≥ 0.1.14 原生支援）
    # 注意：不傳 Authorization header（Ollama Direct 無需認證）
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": user_message}],
        "temperature": 0.3,
        "max_tokens": 400,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{base_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
        if resp.status_code != 200:
            logger.error(f"[Ollama] HTTP {resp.status_code}: {resp.text[:200]}")
            return ""
        choices = resp.json().get("choices", [])
        if not choices:
            logger.error(f"[Ollama] 回應無 choices，symbol={symbol}")
            return ""
        summary = choices[0].get("message", {}).get("content", "").strip()
        logger.info(f"[Ollama] {symbol} 摘要生成成功（{len(summary)} 字）")
        return summary
    except Exception as e:
        logger.error(f"[Ollama] 摘要生成失敗 symbol={symbol}: {e}")
        return ""
```

### 6.3 `config.py` 修改（新增三個欄位）

```python
# AI Briefing — SearXNG + Ollama Direct 路徑
searxng_base_url: str = "https://search.skynetapp.org"
ollama_base_url: str = "http://192.168.0.26:11434"
ollama_model: str = "gpt-oss:20b"
```

### 6.4 `news_briefing_service.py` SEARXNG_OLLAMA 分支

```python
use_tavily = settings.ai_summary.upper() == "TAVILY"
use_searxng_ollama = settings.ai_summary.upper() == "SEARXNG_OLLAMA"

if use_tavily:
    # 現有 Tavily 路徑（不變）
    news_items, summary_text = await tavily_search_and_summarize(...)
elif use_searxng_ollama:
    # v3 新路徑：SearXNG + Ollama Direct
    from app.services.searxng_service import search_news as searxng_search_news
    from app.services.ollama_service import generate_market_summary as ollama_generate
    news_items = await searxng_search_news(query=search_query, count=3)
    summary_text = await ollama_generate(
        symbol=symbol,
        symbol_name=symbol_name,
        news_items=news_items,
        session_hour=session_hour,
    )
    # Ollama 無 rate limit，不需 sleep(7)，保留最小間隔 sleep(1)
else:
    # 現有 Brave + Gemini 路徑（不變）
    news_items = await search_news(query=search_query, count=3)
    summary_text = await generate_market_summary(...)
    if news_items:
        await asyncio.sleep(7)
```

---

## 7. .env 環境變數參考

```dotenv
# AI Briefing 提供商選擇
# 可選：BRAVE_GEMINI（預設）| TAVILY | SEARXNG_OLLAMA
AI_SUMMARY=SEARXNG_OLLAMA

# SearXNG（v3 更新域名）
SEARXNG_BASE_URL=https://search.skynetapp.org

# Ollama Direct（內網，無需 API Key）
OLLAMA_BASE_URL=http://192.168.0.26:11434
OLLAMA_MODEL=gpt-oss:20b
```

> ⚠️ `OLLAMA_BASE_URL` 為內網 HTTP 端點，**後端伺服器須與 `192.168.0.26` 在同一網段**，此端點不得暴露至公網。

---

## 8. Risks & Assumptions

| ID | 類型 | 描述 | 緩解方案 |
|----|------|------|---------|
| RISK-001 | 可用性 | Ollama `192.168.0.26` 主機關機或重啟時摘要失效 | `ollama_service` 捕獲例外回傳 `""`；briefing 記錄 `status=failed`，不影響排程整體 |
| RISK-002 | 網路 | 後端伺服器與 `192.168.0.26` 不在同網段（防火牆攔截） | 部署前執行 TASK-004 驗證連通性；如不通則改用 v2 OpenWebUI 方案 |
| RISK-003 | 品質 | SearXNG 下游引擎（Google/Bing）偶爾被封鎖，新聞結果為空 | SearXNG 管理員設定多個備用引擎（Yahoo News、Reuters）；`searxng_service` 空結果回傳 `[]` 不中斷排程 |
| RISK-004 | 性能 | `gpt-oss:20b` 20B 模型首次推理可能需 60-90s（冷啟動） | timeout 設為 120s；冷啟動後續呼叫明顯加速 |
| RISK-005 | 域名 | `search.skynetapp.org` TLS 憑證過期導致 httpx TLS 驗證失敗 | 由伺服器管理員設定 certbot 自動更新 |
| ASSUMPTION-001 | 假設 | `search.skynetapp.org` 的 SearXNG 已啟用 `format=json` 與 `categories=news` | 執行 TASK-001 驗證 |
| ASSUMPTION-002 | 假設 | `192.168.0.26:11434` 的 Ollama 已載入 `gpt-oss:20b` 模型 | 執行 TASK-002 驗證 |
| ASSUMPTION-003 | 假設 | Ollama 版本 ≥ 0.1.14（支援 `/v1/chat/completions` OpenAI 相容端點） | `curl http://192.168.0.26:11434/api/version` 確認版本 |

---

## 9. 效能對比（預估）

| 指標 | v1 Brave+Gemini | v2 Tavily | **v3 SearXNG+Ollama（本版）** |
|------|-----------------|-----------|-------------------------------|
| 20 symbols 總時間 | ~140s（sleep 7s） | ~40s | **~60-120s**（20B 推理，無 sleep） |
| 月費 | $0-$3（Brave Free） | $0-$50+ | **$0（完全自架）** |
| Rate limit | Gemini 10 RPM | Tavily 1,000 credits/月 | **無** |
| 隱私 | 雲端第三方 | 雲端第三方 | **完全自架，資料不離開 skynetapp.org** |
| 繁中品質 | ⭐⭐⭐⭐（Gemini） | ⭐⭐⭐（Tavily） | **⭐⭐⭐⭐⭐（gpt-oss:20b 20B）** |
| 離線可用 | ❌ | ❌ | **✅（內網可用）** |

---

## 10. Related Specifications / Further Reading

- [docs/todo/feature-ai-briefing-1.md](./feature-ai-briefing-1.md) — v1 AI 每日早報（Brave Search + Gemini）
- [docs/todo/architecture-searxng-ollama-1.md](./architecture-searxng-ollama-1.md) — v2 架構遷移計畫（SearXNG + OpenWebUI）
- [docs/todo/future_plan.md](./future_plan.md) — 專案未來功能藍圖
- [SearXNG JSON API 文件](https://docs.searxng.org/dev/search_api.html)
- [Ollama OpenAI 相容 API](https://github.com/ollama/ollama/blob/main/docs/openai.md)
