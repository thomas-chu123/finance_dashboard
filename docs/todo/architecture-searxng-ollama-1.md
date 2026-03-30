---
goal: Migration plan for replacing Tavily & Brave Search with deployed SearXNG (search.skyapp.org) + Ollama OpenWebUI (chat.skyapp.org / gpt-oss:20b)
version: 1.1
date_created: 2026-03-30
last_updated: 2026-03-30
owner: Platform Team
status: 'Planned'
tags: [architecture, migration, infrastructure, ai, chore]
---

# Introduction

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

本計畫評估並規劃將現有 **Brave Search API** / **Tavily Search API** 替換為已部署的 **SearXNG**（`https://search.skyapp.org`），並將 **Google Gemini API** / Tavily AI 摘要替換為已部署的 **Ollama OpenWebUI**（`https://chat.skyapp.org`，模型：`gpt-oss:20b`）。兩套服務已在 Linux 伺服器上運行，本計畫重點在於後端整合實作，無需重新部署基礎設施。

---

## 0. 現況分析

### 0.1 現有外部 API 依賴

| 服務 | 用途 | 費用 | 限制 |
|------|------|------|------|
| **Brave Search API** | 新聞搜尋（回傳 title/url/description） | Free: 2,000 req/月；Pro: $3/月 起 | 每月請求上限 |
| **Tavily Search API** | 新聞搜尋 + AI 合成摘要一次完成 | Free: 1,000 credits/月；Paid: $50+/月 | 每月 credits 上限 |
| **Google Gemini API** | 將 Brave 新聞轉成繁體中文市場摘要 | Free: 10 RPM；Paid: 150 RPM+ | Rate limit 10 RPM（免費版） |

### 0.2 現有程式架構

```
news_briefing_service.py (協調器)
    ├── AI_SUMMARY=BRAVE_GEMINI  →  brave_search_service.py + gemini_service.py
    └── AI_SUMMARY=TAVILY        →  tavily_service.py (搜尋+摘要一次完成)
```

**主要痛點：**
- Gemini 免費版 **10 RPM** 每次呼叫需 sleep 7 秒，20 個 symbols 需 ~140 秒
- Tavily/Brave 每月均有 API 配額上限，超量需付費
- 所有 AI 推理依賴外部雲端，存在隱私、可用性與費用風險

---

## 1. Requirements & Constraints

- **REQ-001**: 新聞搜尋功能必須回傳與現有格式相容的資料結構：`[{"title", "url", "description", "published_date"}]`
- **REQ-002**: AI 摘要必須能生成 **100-200 字繁體中文** 市場分析，品質不低於現有 Gemini 輸出
- **REQ-003**: 必須支援 `AI_SUMMARY` 環境變數切換，新增 `SEARXNG_OLLAMA` 選項，不破壞現有 `BRAVE_GEMINI` / `TAVILY` 路徑
- **REQ-004**: 單次 symbol 處理延遲（搜尋 + 摘要）不超過 **60 秒**（含外部 HTTPS 網路延遲）
- **REQ-005**: 20 個 symbols 的完整排程執行時間不超過 **15 分鐘**
- **CON-001**: SearXNG（`search.skyapp.org`）與 Ollama OpenWebUI（`chat.skyapp.org`）已部署，**本計畫不涉及基礎設施變更**
- **CON-002**: OpenWebUI 透過 `/v1/chat/completions` 端點提供 OpenAI 相容 API，需使用 Bearer token 認證（OpenWebUI API Key）
- **CON-003**: 不修改現有 `brave_search_service.py`、`tavily_service.py`、`gemini_service.py`（保留向後相容）
- **SEC-001**: `search.skyapp.org` 為公開 HTTPS 端點，後端呼叫時驗證 TLS 憑證，**不在 url 中傳遞敏感資料**
- **SEC-002**: `chat.skyapp.org` OpenWebUI API Key 存放於 `.env`，禁止 hardcode 於程式碼中
- **SEC-003**: `OLLAMA_API_KEY` 必須視同密鑰管理（不進 Git），遵循與 `SECRET_KEY` 相同的保護等級
- **GUD-001**: 所有新增環境變數需在 `config.py` 的 `Settings` 中宣告，提供合理預設值
- **PAT-001**: 新服務遵循現有 `services/` 模組架構（async, httpx, logger, try/except）

---

## 2. 可行性評估

### 2.1 SearXNG — 取代 Brave Search + Tavily 搜尋部分

**技術概述：**
SearXNG 是開源的 meta 搜尋引擎，可聚合 Google、Bing、DuckDuckGo、Yahoo News 等 70+ 個搜尋引擎結果，提供 JSON REST API。

| 評估項目 | 結果 | 說明 |
|----------|------|------|
| 部署狀態 | ✅ 已部署 | 運行於 `https://search.skyapp.org` |
| JSON API | ✅ 支援 | `GET https://search.skyapp.org/search?q=...&format=json&categories=news` |
| 新聞搜尋 | ✅ 良好 | 支援 `categories=news`，聚合多個新聞引擎 |
| 中文支援 | ✅ 良好 | 可設定 `language=zh-TW` |
| 費用 | ✅ 免費 | 自架，無 API 費用 |
| Rate limit | ✅ 無 | 受限於下游搜尋引擎，但分散來源 |
| HTTPS | ✅ 支援 | 公開 HTTPS 端點，TLS 加密傳輸 |
| 搜尋品質 | ⚠️ 變動 | 取決於下游引擎可用性，偶爾需換引擎組合 |

**結論：可行 ✅**

---

### 2.2 Ollama — 取代 Gemini + Tavily AI 摘要部分

**技術概述：**
Ollama 搭配 Open WebUI，部署於 `https://chat.skyapp.org`，使用模型 `gpt-oss:20b`（20B 參數），並透過 OpenWebUI 暴露 **OpenAI 相容 API**（`/v1/chat/completions`），需 Bearer token 認證。

#### 實際使用模型

| 模型 | 部署位置 | API 端點 | 認證方式 | 繁中品質 |
|------|----------|----------|----------|----------|
| `gpt-oss:20b` | `chat.skyapp.org`（Ollama + OpenWebUI） | `/v1/chat/completions` | Bearer token | ⭐⭐⭐⭐⭐（20B 高品質）|

**注意：** OpenWebUI 的 `/v1/chat/completions` 使用 `messages` 陣列傳遞對話（與 Gemini 不同），不使用 Ollama 原生的 `/api/generate`。

| 評估項目 | 結果 | 說明 |
|----------|------|------|
| 部署狀態 | ✅ 已部署 | 運行於 `https://chat.skyapp.org` |
| OpenAI 相容 API | ✅ 支援 | `POST /v1/chat/completions`（需 Bearer token）|
| 繁體中文品質 | ✅ 高 | 20B 模型，中文表現優異 |
| 費用 | ✅ 免費 | 伺服器已運行，無額外費用 |
| Rate limit | ✅ 無 | 自架推理，無外部配額限制 |
| HTTPS | ✅ 支援 | 公開 HTTPS 端點，TLS 加密傳輸 |
| 認證 | ⚠️ 需設定 | OpenWebUI API Key 需從管理員取得並存入 `.env` |

**結論：可行，基礎設施已就位，僅需程式端整合 ✅**

---

### 2.3 整體方案可行性總結

| 比較維度 | 現有方案（Brave+Gemini） | 新方案（SearXNG+Ollama OpenWebUI） |
|----------|--------------------------|---------------------------------|
| 月費 | $0-$53+（依用量） | $0（服務已部署） |
| Rate limit | Gemini 10 RPM + sleep 7s | 無限制 |
| 隱私 | 資料送至第三方雲端 | 自架服務（資料留在 skyapp.org） |
| 20 symbols 排程時間 | ~140 秒（因 sleep 7s） | ~60-120 秒（20B 模型 + HTTPS 延遲）|
| 維護複雜度 | 低（SaaS） | 中（需管理 search.skyapp.org / chat.skyapp.org）|
| 可用性 | 依賴 Brave/Tavily/Google SLA | 依賴 skyapp.org 服務健康 |
| 擴充性 | 受 API 配額限制 | 無上限 |
| 硬體需求 | 無（SaaS） | 已由伺服器承擔，本專案無需額外投入 |

**整體結論：基礎設施已就位，完全可行，本計畫僅需後端程式整合（約 2-3 個服務檔案修改）。**

---

## 3. Implementation Steps

### Implementation Phase 1 — 服務可用性確認

- GOAL-001: 確認 `search.skyapp.org` 與 `chat.skyapp.org` 可正常被後端呼叫，取得必要的 API Key

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | 驗證 SearXNG 搜尋 API：`curl "https://search.skyapp.org/search?q=VTI+ETF+stock&format=json&categories=news"` 確認回傳 JSON `results` 陣列 | ✅ | 2026-03-30 |
| TASK-002 | 從 OpenWebUI 管理員介面（`https://chat.skyapp.org`）產生 API Key，確認格式為 `sk-...` | | |
| TASK-003 | 驗證 Ollama OpenWebUI API：`curl https://chat.skyapp.org/v1/chat/completions -H "Authorization: Bearer <API_KEY>" -d '{"model":"gpt-oss:20b","messages":[{"role":"user","content":"你好"}]}'` 確認回傳正常 | | |
| TASK-004 | 確認後端伺服器可連通 `search.skyapp.org`（443/HTTPS）與 `chat.skyapp.org`（443/HTTPS）：`curl -I https://search.skyapp.org` | | |

### Implementation Phase 2 — 新增服務模組

- GOAL-002: 建立 `searxng_service.py` 與 `ollama_service.py`，遵循現有模組規範

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-007 | 建立 `backend/app/services/searxng_service.py`：實作 `search_news(query, count)` async 函式，回傳相容現有格式的 `list[dict]`，使用 httpx 呼叫本地 SearXNG JSON API | | |
| TASK-008 | 建立 `backend/app/services/ollama_service.py`：實作 `generate_market_summary(symbol, symbol_name, news_items, session_hour)` async 函式，使用 Ollama `/api/generate` 或 `/v1/chat/completions` 端點，保留相同 prompt 結構 | | |
| TASK-009 | 在 `backend/app/config.py` 的 `Settings` 中新增：`ollama_base_url: str = "https://chat.skyapp.org"`、`ollama_api_key: str = ""`、`ollama_model: str = "gpt-oss:20b"`、`searxng_base_url: str = "https://search.skyapp.org"` | | |

### Implementation Phase 3 — 整合 news_briefing_service

- GOAL-003: 在 `news_briefing_service.py` 中新增第三條 `SEARXNG_OLLAMA` 路徑，不破壞現有邏輯

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-010 | 在 `news_briefing_service.py` import `searxng_service.search_news` 與 `ollama_service.generate_market_summary` | | |
| TASK-011 | 在 `run_market_briefing_session()` 中新增 `use_local = settings.ai_summary.upper() == "SEARXNG_OLLAMA"` 分支，呼叫對應服務（**不移除** BRAVE_GEMINI 或 TAVILY 分支） | | |
| TASK-012 | 更新 `backend/app/config.py` 文件字串，說明 `ai_summary` 新增 `SEARXNG_OLLAMA` 選項 | | |

### Implementation Phase 4 — 環境變數設定

- GOAL-004: 在後端 `.env` 中設定指向已部署服務的連線參數；`docker-compose.yml` 無需修改（無需新增容器）

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-013 | 在 `.env` 新增以下環境變數（從 TASK-002 取得的 API Key 填入）：`AI_SUMMARY=SEARXNG_OLLAMA`、`SEARXNG_BASE_URL=https://search.skyapp.org`、`OLLAMA_BASE_URL=https://chat.skyapp.org`、`OLLAMA_API_KEY=sk-...`、`OLLAMA_MODEL=gpt-oss:20b` | | |
| TASK-014 | 確認 `.env` 已加入 `.gitignore`（`OLLAMA_API_KEY` 禁止進版本控制） | | |

### Implementation Phase 5 — 測試與驗證

- GOAL-005: 確認新路徑功能正確，品質達標

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-017 | 在 `tests/unit/` 新增 `test_searxng_service.py`：mock httpx 回應，測試 `search_news()` 格式轉換正確 | | |
| TASK-018 | 在 `tests/unit/` 新增 `test_ollama_service.py`：mock httpx 回應，測試 `generate_market_summary()` 回傳非空字串 | | |
| TASK-019 | 手動執行 `POST /api/briefing/trigger`，使用 `AI_SUMMARY=SEARXNG_OLLAMA`，比較摘要品質（字數、語意連貫性、是否繁體中文） | | |
| TASK-020 | 使用 `time` 指令測量 20 symbols 完整排程執行時間，確認在 10 分鐘內 | | |

---

## 4. Alternatives

- **ALT-001**: 使用 **DuckDuckGo ddgs Python 套件** 取代 SearXNG — 無需自架，但無 JSON API（需 Python 套件）、有非官方 rate limit 風險，穩定性不如自架 SearXNG
- **ALT-002**: 使用 **Bing News Search API** — 有官方 API，每月 1,000 次免費，但仍有外部依賴與費用上限
- **ALT-003**: 使用 **vLLM** 取代 Ollama — 高吞吐量推理，但安裝複雜、需 GPU，適合高負載生產環境（本專案規模不需要）
- **ALT-004**: 使用 **LM Studio** — 桌面應用，不適合 Linux headless 伺服器部署
- **ALT-005**: 使用 **Groq API（免費 LLM）** 取代 Gemini — 速度極快（100 tok/s+），有繁中支援，但仍是外部 API，不符合完全本地化目標

---

## 5. Dependencies

- **DEP-001**: `Ollama + OpenWebUI` — 已部署於 `https://chat.skyapp.org`，無需安裝，需由管理員提供 API Key
- **DEP-002**: `SearXNG` — 已部署於 `https://search.skyapp.org`，無需安裝
- **DEP-003**: Python `httpx` — 已在 `requirements.txt` 中，無需新增
- **DEP-004**: 硬體需求 — 由 skyapp.org 伺服器承擔，本專案無額外硬體需求

---

## 6. Files

- **FILE-001**: `backend/app/services/searxng_service.py` — **新建**，SearXNG 新聞搜尋服務
- **FILE-002**: `backend/app/services/ollama_service.py` — **新建**，Ollama 本地 LLM 摘要服務
- **FILE-003**: `backend/app/config.py` — **修改**，新增 `ollama_base_url`、`ollama_api_key`、`ollama_model`、`searxng_base_url` 欄位
- **FILE-004**: `backend/app/services/news_briefing_service.py` — **修改**，新增 `SEARXNG_OLLAMA` 分支
- **FILE-005**: `.env` — **修改**，新增 `SEARXNG_BASE_URL`、`OLLAMA_BASE_URL`、`OLLAMA_API_KEY`、`OLLAMA_MODEL`
- **FILE-006**: `docker-compose.yml` — **不需修改**（無需新增容器，使用外部已部署服務）
- **FILE-008**: `tests/unit/test_searxng_service.py` — **新建**，單元測試
- **FILE-009**: `tests/unit/test_ollama_service.py` — **新建**，單元測試

---

## 7. Testing

- **TEST-001**: `test_searxng_service.py::test_search_news_returns_correct_format` — mock SearXNG JSON 回應，驗證輸出為 `list[dict]` 且含 `title/url/description/published_date` 欄位
- **TEST-002**: `test_searxng_service.py::test_search_news_api_error_returns_empty_list` — mock HTTP 500，驗證回傳空 list 不拋例外
- **TEST-003**: `test_searxng_service.py::test_search_news_no_base_url_returns_empty_list` — `searxng_base_url=""` 時回傳空 list 並記錄 warning
- **TEST-004**: `test_ollama_service.py::test_generate_summary_returns_string` — mock Ollama `/api/generate` 回應，驗證回傳非空字串
- **TEST-005**: `test_ollama_service.py::test_generate_summary_no_news_returns_empty` — 空 `news_items` 時回傳 `""`
- **TEST-006**: `test_ollama_service.py::test_generate_summary_api_error_returns_empty` — mock 連線失敗，驗證回傳 `""` 不拋例外

---

## 8. Risks & Assumptions

- **RISK-001**: **`chat.skyapp.org` 服務中斷** — Ollama OpenWebUI 出現故障時摘要功能失效。**緩解方案**：`ollama_service.py` 捕獲所有例外並回傳 `""`，`news_briefing_service.py` 記錄 `status=failed`，不中斷整個排程；告警監控由伺服器管理員負責
- **RISK-002**: **SearXNG 下游引擎被封鎖** — Google/Bing 可能封鎖爬蟲，導致搜尋結果為空。**緩解方案**：`search.skyapp.org` 管理員設定多個引擎來源（Yahoo News、Reuters、Bing News）
- **RISK-003**: **繁體中文摘要品質** — `gpt-oss:20b` 為 20B 模型，中文能力預期優異，但仍需在 TASK-019 手動驗收；Prompt 明確要求「繁體中文（非簡體中文）」
- **RISK-004**: **API Key 洩漏風險** — `OLLAMA_API_KEY` 若不小心 commit 到 Git 將造成安全問題。**緩解方案**：確認 `.env` 在 `.gitignore`，CI/CD pipeline 使用 secret 環境變數，不在 log 中印出 API Key
- **RISK-005**: **HTTPS 憑證過期** — `search.skyapp.org` 或 `chat.skyapp.org` 憑證過期將導致 `httpx` TLS 驗證失敗。**緩解方案**：由伺服器管理員設定 certbot 自動更新
- **ASSUMPTION-001**: `search.skyapp.org` 的 SearXNG 已啟用 `format=json` 與 `categories=news`
- **ASSUMPTION-002**: `chat.skyapp.org` 的 OpenWebUI 已啟用 API Key 功能，且 `gpt-oss:20b` 模型已載入
- **ASSUMPTION-003**: 後端伺服器的 outbound HTTPS（port 443）防火牆規則允許呼叫 `search.skyapp.org` 與 `chat.skyapp.org`

---

## 9. .env 環境變數參考設定

```dotenv
# AI Briefing — SearXNG + Ollama OpenWebUI 路徑
AI_SUMMARY=SEARXNG_OLLAMA

# SearXNG（已部署）
SEARXNG_BASE_URL=https://search.skyapp.org

# Ollama OpenWebUI（已部署）
OLLAMA_BASE_URL=https://chat.skyapp.org
OLLAMA_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OLLAMA_MODEL=gpt-oss:20b
```

> ⚠️ `OLLAMA_API_KEY` 不得 commit 至 Git，請確認 `.env` 已列入 `.gitignore`。

---

## 10. ollama_service.py 參考實作

```python
"""
Ollama OpenWebUI 服務 — 透過 OpenAI 相容 API 生成市場新聞摘要.

端點：https://chat.skyapp.org/v1/chat/completions
認證：Bearer token（OLLAMA_API_KEY）
模型：gpt-oss:20b
"""
import logging
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SESSION_LABEL_MAP = {8: "開盤前早報", 13: "午間快報", 18: "收盤後晚報"}


async def generate_market_summary(
    symbol: str,
    symbol_name: str,
    news_items: list[dict],
    session_hour: int = 8,
) -> str:
    base_url = settings.ollama_base_url
    api_key = settings.ollama_api_key
    model = settings.ollama_model

    if not base_url:
        logger.warning("[Ollama] base_url 未設定，跳過摘要生成")
        return ""
    if not news_items:
        logger.info(f"[Ollama] {symbol} 無新聞，跳過摘要生成")
        return ""

    session_label = SESSION_LABEL_MAP.get(session_hour, "市場快報")
    news_text = "\n\n".join(
        f"新聞 {i+1}：{item.get('title','')}\n摘要：{item.get('description','')}"
        for i, item in enumerate(news_items)
    )
    user_message = (
        f"你是一位專業的金融市場分析師。"
        f"以下是關於 {symbol_name}（{symbol}）在 {session_label} 的最新 {len(news_items)} 則新聞：\n\n"
        f"{news_text}\n\n"
        "請根據上述新聞，以繁體中文（非簡體中文）撰寫一段 100-150 字的市場動態摘要。\n"
        "格式：純文字，無需標題，包含：(1) 主要市場動態 (2) 潛在影響 (3) 投資者關注要點。"
    )

    # OpenWebUI 使用 OpenAI 相容格式（messages 陣列），非 Ollama 原生 /api/generate
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": user_message}],
        "temperature": 0.3,
        "max_tokens": 400,
        "stream": False,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}" if api_key else "",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
            )
        if resp.status_code != 200:
            logger.error(f"[Ollama] HTTP {resp.status_code}: {resp.text[:200]}")
            return ""
        choices = resp.json().get("choices", [])
        if not choices:
            logger.error(f"[Ollama] 回應無 choices，symbol={symbol}")
            return ""
        return choices[0].get("message", {}).get("content", "").strip()
    except Exception as e:
        logger.error(f"[Ollama] 摘要生成失敗 symbol={symbol}: {e}")
        return ""
```

---

## 11. searxng_service.py 參考實作

```python
"""
SearXNG 自架搜尋服務 — 取代 brave_search_service（新聞搜尋部分）.
"""
import logging
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def search_news(query: str, count: int = 3) -> list[dict]:
    base_url = settings.searxng_base_url
    if not base_url:
        logger.warning("[SearXNG] base_url 未設定，跳過搜尋")
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
                "description": item.get("content", ""),
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

---

## 12. Related Specifications / Further Reading

- [docs/todo/future_plan.md](../docs/todo/future_plan.md) — 專案未來功能藍圖
- [docs/todo/feature-ai-briefing-1.md](../docs/todo/feature-ai-briefing-1.md) — AI 每日早報功能規格
- [SearXNG 官方文件](https://docs.searxng.org/)
- [Ollama 官方文件](https://ollama.com/library)
- [OpenWebUI API 文件](https://docs.openwebui.com/getting-started/api-endpoints/)
- [OpenWebUI API Key 設定](https://docs.openwebui.com/features/api-key/)

