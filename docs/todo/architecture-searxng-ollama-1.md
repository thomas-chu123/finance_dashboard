---
goal: Feasibility assessment and migration plan for replacing Tavily & Brave Search with SearXNG + local Ollama on Linux server
version: 1.0
date_created: 2026-03-30
last_updated: 2026-03-30
owner: Platform Team
status: 'Planned'
tags: [architecture, migration, infrastructure, ai, chore]
---

# Introduction

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

本計畫評估在 Linux 伺服器上以 **SearXNG（自架搜尋引擎）** 取代 **Brave Search API** 與 **Tavily Search API** 的新聞搜尋功能，並以 **本地 Ollama（開源 LLM 推理）** 取代 **Google Gemini API** 與 Tavily 內建 AI 摘要的可行性，最終提供完整的遷移實作方案。

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
- **REQ-004**: 單次 symbol 處理延遲（搜尋 + 摘要）不超過 **30 秒**
- **REQ-005**: 20 個 symbols 的完整排程執行時間不超過 **10 分鐘**
- **CON-001**: Linux 伺服器需有足夠 RAM/GPU 資源執行 Ollama 模型
- **CON-002**: SearXNG 需要 Docker 或直接安裝，佔用額外 port（預設 8080）
- **CON-003**: 不修改現有 `brave_search_service.py`、`tavily_service.py`、`gemini_service.py`（保留向後相容）
- **SEC-001**: SearXNG 實例不應暴露到公開網際網路，僅允許內部存取（localhost 或內網）
- **SEC-002**: Ollama API 端點不應對外公開，使用 localhost binding
- **GUD-001**: 所有新增環境變數需在 `config.py` 的 `Settings` 中宣告，提供合理預設值
- **PAT-001**: 新服務遵循現有 `services/` 模組架構（async, httpx, logger, try/except）

---

## 2. 可行性評估

### 2.1 SearXNG — 取代 Brave Search + Tavily 搜尋部分

**技術概述：**
SearXNG 是開源的 meta 搜尋引擎，可聚合 Google、Bing、DuckDuckGo、Yahoo News 等 70+ 個搜尋引擎結果，提供 JSON REST API。

| 評估項目 | 結果 | 說明 |
|----------|------|------|
| 安裝難度 | ✅ 低 | `docker run searxng/searxng` 一行啟動 |
| JSON API | ✅ 支援 | `GET /search?q=...&format=json&categories=news` |
| 新聞搜尋 | ✅ 良好 | 支援 `categories=news`，聚合多個新聞引擎 |
| 中文支援 | ✅ 良好 | 可設定 `language=zh-TW` |
| 費用 | ✅ 免費 | 自架，無 API 費用 |
| Rate limit | ✅ 無 | 受限於下游搜尋引擎，但分散來源 |
| 維護成本 | ⚠️ 中 | 需定期更新 Docker image、監控健康狀態 |
| 搜尋品質 | ⚠️ 變動 | 取決於下游引擎可用性，偶爾需換引擎組合 |

**結論：可行 ✅**

---

### 2.2 Ollama — 取代 Gemini + Tavily AI 摘要部分

**技術概述：**
Ollama 是在本地執行開源 LLM 的推理框架，提供與 OpenAI API 相容的 REST 介面。

#### 推薦模型（依硬體需求排序）

| 模型 | 參數 | RAM 需求 | 繁中品質 | 速度（CPU） | 速度（GPU） |
|------|------|----------|----------|-------------|-------------|
| `qwen2.5:7b` | 7B | ~6 GB | ⭐⭐⭐⭐⭐ | ~30 秒/回應 | ~5 秒/回應 |
| `qwen2.5:14b` | 14B | ~12 GB | ⭐⭐⭐⭐⭐ | ~60 秒/回應 | ~10 秒/回應 |
| `gemma3:4b` | 4B | ~4 GB | ⭐⭐⭐⭐ | ~20 秒/回應 | ~3 秒/回應 |
| `llama3.2:3b` | 3B | ~3 GB | ⭐⭐⭐ | ~15 秒/回應 | ~2 秒/回應 |
| `mistral:7b` | 7B | ~6 GB | ⭐⭐⭐ | ~30 秒/回應 | ~5 秒/回應 |

**繁體中文市場摘要最佳推薦：`qwen2.5:7b`（阿里雲，原生中文訓練）**

| 評估項目 | 結果 | 說明 |
|----------|------|------|
| 安裝難度 | ✅ 低 | `curl https://ollama.ai/install.sh \| sh` |
| OpenAI 相容 API | ✅ 支援 | `POST /api/generate` 或 `/v1/chat/completions` |
| 繁體中文品質 | ✅ 良好 | qwen2.5 系列表現優異 |
| 費用 | ✅ 免費 | 僅需電費與硬體成本 |
| Rate limit | ✅ 無 | 本地執行，無外部配額限制 |
| 延遲 | ⚠️ 取決硬體 | CPU-only 較慢，GPU 顯著加速 |
| 離線能力 | ✅ 完整 | 不依賴任何外部服務 |
| 隱私 | ✅ 完整 | 所有資料留在本地 |

**最低硬體需求（`qwen2.5:7b`）：**
- CPU: 4 核心以上
- RAM: 16 GB（8 GB 勉強可行，但需關閉其他服務）
- 儲存: 8 GB（模型檔案）
- GPU（選用）: NVIDIA 8GB VRAM 可大幅加速（CUDA）

**結論：可行，但延遲取決硬體 ✅⚠️**

---

### 2.3 整體方案可行性總結

| 比較維度 | 現有方案（Brave+Gemini） | 替代方案（SearXNG+Ollama） |
|----------|--------------------------|---------------------------|
| 月費 | $0-$53+（依用量） | $0（硬體電費） |
| Rate limit | Gemini 10 RPM | 無 |
| 隱私 | 資料送至雲端 | 完全本地 |
| 20 symbols 排程時間 | ~140 秒（因 sleep 7s） | ~60-600 秒（依硬體） |
| 維護複雜度 | 低（SaaS） | 中（自架 SearXNG + Ollama 更新） |
| 可用性 | 依賴外部服務 SLA | 依賴本地服務健康 |
| 擴充性 | 受 API 配額限制 | 無上限 |

**整體結論：在有足夠硬體（16 GB RAM，最好有 NVIDIA GPU）的 Linux 伺服器上，完全可行。**

---

## 3. Implementation Steps

### Implementation Phase 1 — 基礎設施準備

- GOAL-001: 在 Linux 伺服器上安裝並設定 SearXNG 與 Ollama

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | 在 Linux 伺服器安裝 Ollama：`curl -fsSL https://ollama.com/install.sh \| sh` | | |
| TASK-002 | 下載推薦模型：`ollama pull qwen2.5:7b`（或 gemma3:4b 若 RAM 不足） | | |
| TASK-003 | 驗證 Ollama API：`curl http://localhost:11434/api/generate -d '{"model":"qwen2.5:7b","prompt":"你好"}'` | | |
| TASK-004 | 在 `docker-compose.yml` 新增 SearXNG service（port 8888 對內，不對外暴露） | | |
| TASK-005 | 建立 `searxng/settings.yml`，啟用 `news` 類別，設定 `server.secret_key`，關閉 `ui.query_in_title` | | |
| TASK-006 | 驗證 SearXNG API：`curl "http://localhost:8888/search?q=VTI+ETF&format=json&categories=news"` | | |

### Implementation Phase 2 — 新增服務模組

- GOAL-002: 建立 `searxng_service.py` 與 `ollama_service.py`，遵循現有模組規範

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-007 | 建立 `backend/app/services/searxng_service.py`：實作 `search_news(query, count)` async 函式，回傳相容現有格式的 `list[dict]`，使用 httpx 呼叫本地 SearXNG JSON API | | |
| TASK-008 | 建立 `backend/app/services/ollama_service.py`：實作 `generate_market_summary(symbol, symbol_name, news_items, session_hour)` async 函式，使用 Ollama `/api/generate` 或 `/v1/chat/completions` 端點，保留相同 prompt 結構 | | |
| TASK-009 | 在 `backend/app/config.py` 的 `Settings` 中新增：`ollama_base_url: str = "http://localhost:11434"`、`ollama_model: str = "qwen2.5:7b"`、`searxng_base_url: str = "http://localhost:8888"` | | |

### Implementation Phase 3 — 整合 news_briefing_service

- GOAL-003: 在 `news_briefing_service.py` 中新增第三條 `SEARXNG_OLLAMA` 路徑，不破壞現有邏輯

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-010 | 在 `news_briefing_service.py` import `searxng_service.search_news` 與 `ollama_service.generate_market_summary` | | |
| TASK-011 | 在 `run_market_briefing_session()` 中新增 `use_local = settings.ai_summary.upper() == "SEARXNG_OLLAMA"` 分支，呼叫對應服務（**不移除** BRAVE_GEMINI 或 TAVILY 分支） | | |
| TASK-012 | 更新 `backend/app/config.py` 文件字串，說明 `ai_summary` 新增 `SEARXNG_OLLAMA` 選項 | | |

### Implementation Phase 4 — Docker Compose 整合

- GOAL-004: 更新 `docker-compose.yml` 整合 SearXNG；Ollama 依伺服器條件選擇 host 模式或 service 模式

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-013 | 在 `docker-compose.yml` 新增 `searxng` service（image: `searxng/searxng:latest`，volume 掛載 `./searxng:/etc/searxng`，network: internal only） | | |
| TASK-014 | （GPU 伺服器）在 `docker-compose.yml` 新增 `ollama` service（image: `ollama/ollama:latest`，`deploy.resources.reservations.devices: [{driver: nvidia, count: 1, capabilities: [gpu]}]`） | | |
| TASK-015 | （CPU-only 伺服器）Ollama 以 systemd service 形式在 host 執行，`backend` container 透過 `host.docker.internal` 或 `172.17.0.1` 呼叫 Ollama | | |
| TASK-016 | 在 `.env` 新增對應環境變數：`AI_SUMMARY=SEARXNG_OLLAMA`、`SEARXNG_BASE_URL=http://searxng:8888`、`OLLAMA_BASE_URL=http://ollama:11434`、`OLLAMA_MODEL=qwen2.5:7b` | | |

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

- **DEP-001**: `ollama` — Linux 伺服器安裝：`curl -fsSL https://ollama.com/install.sh | sh`（約 500 MB 安裝程式 + 模型檔 4-14 GB）
- **DEP-002**: `searxng/searxng` Docker image — `docker pull searxng/searxng:latest`（約 400 MB）
- **DEP-003**: Python `httpx` — 已在 `requirements.txt` 中，無需新增
- **DEP-004**: 硬體需求：Linux 伺服器需 **16 GB RAM**（最低 8 GB）；GPU 為選用但強烈建議（NVIDIA CUDA）

---

## 6. Files

- **FILE-001**: `backend/app/services/searxng_service.py` — **新建**，SearXNG 新聞搜尋服務
- **FILE-002**: `backend/app/services/ollama_service.py` — **新建**，Ollama 本地 LLM 摘要服務
- **FILE-003**: `backend/app/config.py` — **修改**，新增 `ollama_base_url`、`ollama_model`、`searxng_base_url` 欄位
- **FILE-004**: `backend/app/services/news_briefing_service.py` — **修改**，新增 `SEARXNG_OLLAMA` 分支
- **FILE-005**: `docker-compose.yml` — **修改**，新增 `searxng` service（及可選的 `ollama` service）
- **FILE-006**: `searxng/settings.yml` — **新建**，SearXNG 設定檔
- **FILE-007**: `.env` — **修改**，新增 `SEARXNG_BASE_URL`、`OLLAMA_BASE_URL`、`OLLAMA_MODEL`
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

- **RISK-001**: **CPU-only 伺服器延遲過高** — `qwen2.5:7b` 在 CPU-only 環境每次摘要約 30-60 秒，20 symbols 約 10-20 分鐘，超過目標。**緩解方案**：使用更小模型（`gemma3:4b`）或增設 GPU
- **RISK-002**: **SearXNG 下游引擎被封鎖** — Google/Bing 可能封鎖爬蟲，導致搜尋結果為空。**緩解方案**：設定多個引擎來源（Yahoo News、Reuters、Bing News），並設定 SearXNG `request_timeout` 降低阻塞
- **RISK-003**: **繁體中文摘要品質下降** — 小模型（3B/4B）可能生成簡體中文或品質不佳的摘要。**緩解方案**：Prompt 中明確要求「繁體中文」，並在 TASK-019 手動品質驗收
- **RISK-004**: **Ollama 記憶體佔用影響其他服務** — 載入 7B 模型佔用約 6-8 GB RAM，可能影響 PostgreSQL、Redis 等服務效能。**緩解方案**：設定 `OLLAMA_MAX_LOADED_MODELS=1`，並在非排程時段主動 unload 模型
- **ASSUMPTION-001**: Linux 伺服器有 Docker 與 Docker Compose 已安裝
- **ASSUMPTION-002**: 伺服器可正常存取 Docker Hub 及 Ollama 模型倉庫（下載模型）
- **ASSUMPTION-003**: 現有 `docker-compose.yml` 使用自定義 network，SearXNG 可透過 service name 解析

---

## 9. SearXNG Settings.yml 參考設定

```yaml
# searxng/settings.yml
use_default_settings: true

server:
  secret_key: "change-me-to-random-string"
  bind_address: "0.0.0.0"
  port: 8888
  limiter: false          # 關閉限速（內部使用）

search:
  safe_search: 0
  default_lang: "zh-TW"
  ban_time_on_fail: 5
  max_ban_time_on_fail: 120

engines:
  - name: bing news
    engine: bing_news
    categories: news
    disabled: false
  - name: yahoo news
    engine: yahoo_news
    categories: news
    disabled: false
  - name: google news
    engine: google_news
    categories: news
    disabled: false

ui:
  static_use_hash: true
  query_in_title: false
  infinite_scroll: false

enabled_plugins:
  - Basic Calculator
  - Hash plugin
  - Self Information
```

---

## 10. ollama_service.py 參考實作

```python
"""
Ollama 本地 LLM 服務 — 生成市場新聞摘要（取代 gemini_service）.
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
    prompt = (
        f"你是一位專業的金融市場分析師。"
        f"以下是關於 {symbol_name}（{symbol}）在 {session_label} 的最新 {len(news_items)} 則新聞：\n\n"
        f"{news_text}\n\n"
        "請根據上述新聞，以繁體中文（非簡體中文）撰寫一段 100-150 字的市場動態摘要。\n"
        "格式：純文字，無需標題，包含：(1) 主要市場動態 (2) 潛在影響 (3) 投資者關注要點。"
    )

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 300},
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{base_url}/api/generate", json=payload)
        if resp.status_code != 200:
            logger.error(f"[Ollama] HTTP {resp.status_code}: {resp.text[:200]}")
            return ""
        return resp.json().get("response", "").strip()
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
- [Ollama API Reference](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [qwen2.5 模型頁面](https://ollama.com/library/qwen2.5)

