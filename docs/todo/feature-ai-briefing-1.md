---
goal: 在 Dashboard 總覽實作 AI 每日市場早報功能（Brave Search + Gemini）
version: 1.0
date_created: 2026-03-27
last_updated: 2026-03-27
owner: Finance Dashboard Team
status: 'Planned'
tags: ['feature', 'AI', 'briefing', 'gemini', 'brave-search', 'scheduler', 'dashboard']
---

# AI 每日市場早報功能實作計畫

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

## 簡介

本計畫在 Dashboard 總覽頁面新增 **AI 每日市場早報 (AI Daily Market Briefing)** 功能。
系統每日於 **08:00、13:00、18:00（Asia/Taipei）** 自動啟動排程，使用 **Brave Search API** 抓取每個被追蹤指數的 Top 3 最新新聞，彙整後送至 **Google Gemini API** 生成繁體中文摘要，最終在 Dashboard 以可拖曳卡片形式呈現。

---

## 1. 需求與約束

- **REQ-001**：排程每日執行三次：08:00、13:00、18:00 (Asia/Taipei)，對應開盤前、午休、收盤後
- **REQ-002**：每次排程從 Supabase `tracked_indices` 表查詢所有使用者正在追蹤的唯一 symbol 清單（`is_active=True`）
- **REQ-003**：對每個 symbol，使用 Brave Search News API 搜尋 Top 3 最新新聞（含標題、URL、描述、發布日期）
- **REQ-004**：將每個 symbol 的 3 則新聞彙整為結構化 Prompt，呼叫 Google Gemini 1.5 Flash API 生成 100-150 字繁體中文摘要
- **REQ-005**：摘要結果與原始新聞 JSON 存入 Supabase `market_briefings` 表
- **REQ-006**：前端 Dashboard 新增可拖曳的「🤖 AI 市場早報」卡片，顯示最新一次排程的摘要
- **REQ-007**：提供手動觸發 API 端點 `POST /api/briefing/trigger` 供開發測試（需要 JWT auth）
- **REQ-008**：前端卡片支援展開/收合每個 symbol 的詳細新聞清單，並顯示新聞來源連結

- **SEC-001**：Brave Search API Key 與 Gemini API Key 只能存放於後端 `.env`，絕不暴露至前端或 logs
- **SEC-002**：`POST /api/briefing/trigger` 需要 JWT 認證（Authorization: Bearer Token）
- **SEC-003**：對外 API 請求使用 `httpx` 設定 `timeout=30.0`，避免排程無限等待
- **SEC-004**：Supabase `market_briefings` 表啟用 RLS，前端讀取只允許已認證使用者（authenticated role）

- **CON-001**：Brave Search 免費方案每月上限 2,000 次請求；計算：3 次/天 × 30 天 = 90 次排程，支援最多約 22 個 unique symbols，超過需升級方案
- **CON-002**：Gemini 1.5 Flash 免費方案限制每分鐘 15 個請求，每個 symbol 處理後需加入 `asyncio.sleep(1)` 間隔
- **CON-003**：不使用 `google-generativeai` SDK（避免增加大型依賴），改用 `httpx` 直接呼叫 Gemini REST API
- **CON-004**：向後相容，不修改任何現有資料表，`market_briefings` 為全新獨立表

- **GUD-001**：排程失敗時在 `market_briefings` 記錄 `status='failed'` 及 `error_message`，不拋出未捕獲異常影響其他 job
- **GUD-002**：前端卡片處理 loading / error state，避免空白畫面
- **PAT-001**：新服務層遵循現有 `app/services/` 分層架構（單一職責）
- **PAT-002**：新路由遵循現有 `app/routers/` 前綴規範（`/api/briefing`）

---

## 2. 實現步驟

### Phase 1：後端基礎建設（設定、資料庫、服務層）

- **GOAL-001**：建立 Brave Search 與 Gemini API 整合服務，並建立 `market_briefings` 資料表

| Task     | 描述                                                                                                                                                                                                                                                                                                                                                                                      | 完成 | 日期 |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- | ---- |
| TASK-001 | **修改 `backend/app/config.py`**：在 `Settings` class 中新增兩個欄位：`brave_search_api_key: str = ""` 與 `gemini_api_key: str = ""`                                                                                                                                                                                                                                                       |      |      |
| TASK-002 | **修改 `backend/.env`**：新增 `BRAVE_SEARCH_API_KEY=` 與 `GEMINI_API_KEY=` 兩個環境變數條目（值留空，由部署者填入）                                                                                                                                                                                                                                                                        |      |      |
| TASK-003 | **Supabase DDL**：建立 `market_briefings` 表，欄位：`id UUID PK DEFAULT gen_random_uuid()`、`session_time TIMESTAMPTZ NOT NULL`、`symbol VARCHAR(20) NOT NULL`、`symbol_name TEXT`、`news_json JSONB NOT NULL DEFAULT '[]'`、`summary_text TEXT`、`status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','completed','failed'))`、`error_message TEXT`、`created_at TIMESTAMPTZ DEFAULT NOW()`；建立索引 `CREATE INDEX idx_mb_session_time ON market_briefings(session_time DESC)`；啟用 RLS 並設定 `CREATE POLICY briefings_read FOR SELECT TO authenticated USING (true)` |      |      |
| TASK-004 | **新增 `backend/app/services/brave_search_service.py`**：實作 `async def search_news(query: str, count: int = 3) -> list[dict]`，使用 `httpx.AsyncClient(timeout=30)` 呼叫 `https://api.search.brave.com/res/v1/news/search`，Header：`X-Subscription-Token: {brave_search_api_key}` 及 `Accept: application/json`，Query params：`q={query}&count={count}&search_lang=zh-cht,en`，解析 response 回傳 `[{"title": str, "url": str, "description": str, "published_date": str}]`，API 失敗時 `logger.error` 並回傳空 list                           |      |      |
| TASK-005 | **新增 `backend/app/services/gemini_service.py`**：實作 `async def generate_market_summary(symbol: str, symbol_name: str, news_items: list[dict]) -> str`，使用 `httpx.AsyncClient(timeout=30)` POST 至 `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}`，request body 結構：`{"contents": [{"parts": [{"text": prompt}]}]}`，回傳 `candidates[0].content.parts[0].text`，失敗時 `logger.error` 回傳空字串；Prompt 設計詳見本文件末尾                                                            |      |      |
| TASK-006 | **新增 `backend/app/services/news_briefing_service.py`**：實作 `async def run_market_briefing_session() -> dict`，步驟：(1) Supabase `SELECT DISTINCT symbol, name FROM tracked_indices WHERE is_active=True`；(2) 計算 `session_time`（截至最近整點 08/13/18）；(3) 逐個 symbol 呼叫 `search_news(query=f"{name} {symbol}", count=3)`；(4) 呼叫 `generate_market_summary()`；(5) Upsert 結果至 `market_briefings`（`ON CONFLICT (session_time, symbol) DO UPDATE`）；(6) 每個 symbol 後 `await asyncio.sleep(1)`（保護 Gemini rate limit）；(7) 回傳 `{"total": n, "success": n, "failed": n}` |      |      |

### Phase 2：後端 API 路由與排程

- **GOAL-002**：建立 REST API 端點，整合至排程器與主應用

| Task     | 描述                                                                                                                                                                                                                                                                                                                                                                               | 完成 | 日期 |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- | ---- |
| TASK-007 | **新增 `backend/app/routers/briefing.py`**：定義 `router = APIRouter(prefix="/api/briefing", tags=["briefing"])`。端點一：`GET /latest`（需 JWT auth via `x-user-id` header）回傳最新 session_time 批次中所有 symbol 的摘要，JSON: `{"session_time": str, "items": [{"symbol", "symbol_name", "summary_text", "news_json", "status"}]}`；端點二：`GET /sessions`（需 JWT auth）回傳最近 10 次排程清單及 symbol 完成數；端點三：`POST /trigger`（需 JWT auth）使用 FastAPI BackgroundTasks 呼叫 `run_market_briefing_session()`，立即回傳 `{"status": "triggered", "message": "..."} 202 Accepted` |      |      |
| TASK-008 | **修改 `backend/app/main.py`**：加入 `from app.routers import briefing as briefing_router`，並在 router 區塊加入 `app.include_router(briefing_router.router)`                                                                                                                                                                                                                      |      |      |
| TASK-009 | **修改 `backend/app/scheduler.py`**：import `run_market_briefing_session`，新增包裝函數 `async def run_briefing_job()`（含 try/except logging），在 `start_scheduler()` 中加入三條 cron job：`hour=8, minute=0, id="briefing_0800"`、`hour=13, minute=0, id="briefing_1300"`、`hour=18, minute=0, id="briefing_1800"`，均設定 `replace_existing=True`                                |      |      |
| TASK-010 | **確認 `backend/requirements.txt`**：驗證 `httpx>=0.27.0` 已存在；本功能不需新增任何依賴                                                                                                                                                                                                                                                                                           |      |      |

### Phase 3：前端元件與 Store

- **GOAL-003**：實作前端 AI 早報卡片元件，整合至 Dashboard 可拖曳系統

| Task     | 描述                                                                                                                                                                                                                                                                                                                                                                             | 完成 | 日期 |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- | ---- |
| TASK-011 | **新增 `frontend/src/api/briefing.js`**：定義 `const API_BASE = import.meta.env.VITE_API_BASE_URL \|\| ''`，export `fetchLatestBriefing(token)` → `axios.get('/api/briefing/latest', {headers: {Authorization: \`Bearer ${token}\`}})`；export `triggerBriefing(token)` → `axios.post('/api/briefing/trigger', {}, {headers: {Authorization: \`Bearer ${token}\`}})` |      |      |
| TASK-012 | **新增 `frontend/src/stores/briefing.js`**（Pinia store）：`state: { items: [], sessionTime: null, loading: false, error: null }`；action `fetchLatestBriefing()` 呼叫 API 並更新 state；action `triggerRefresh()` 先呼叫 trigger API（背景）再重新 fetch                                                                                                                    |      |      |
| TASK-013 | **新增 `frontend/src/components/AIDailyBriefing.vue`**：標題列（「🤖 AI 市場早報」+ 格式化的上次更新時間 + 手動刷新按鈕）；loading 狀態（animate-pulse skeleton 佔位）；error 狀態（紅色提示）；briefing items 清單，每個 symbol card 顯示代碼 badge + 名稱 + AI 摘要文字；底部 collapsible section 列出 3 則新聞（標題超連結 + 描述前 80 字 + 發布時間）；樣式使用現有 `glass-card`、Tailwind CSS v4、深色模式相容；`onMounted` 呼叫 `briefingStore.fetchLatestBriefing()`                                     |      |      |
| TASK-014 | **修改 `frontend/src/stores/dashboard.js`**：在 `state.cardOrder` 預設陣列中新增 `'ai-briefing'`，插入於 `'tracking-table'` 之前（index 0 位置）                                                                                                                                                                                                                                |      |      |
| TASK-015 | **修改 `frontend/src/views/DashboardView.vue`**：在 `<script setup>` 中 import `AIDailyBriefing` 元件；在 `mainContentCards` 的 `v-for` loop 內新增 `v-if="cardId === 'ai-briefing'"` 對應的拖曳卡片 div（與其他卡片使用相同的 `draggable`、drag event handlers、`data-card-id` 模式），div 內渲染 `<AIDailyBriefing />`                                                         |      |      |

### Phase 4：資料庫遷移 SQL 文件

- **GOAL-004**：提供正式的 SQL migration 文件供 Supabase 執行

| Task     | 描述                                                                                                                                                                                                                                                            | 完成 | 日期 |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- | ---- |
| TASK-016 | **新增 `docs/migrations/20260327_market_briefings.sql`**：包含完整建表 DDL、`CREATE INDEX idx_mb_session_time`、`CREATE INDEX idx_mb_symbol`、`ENABLE ROW LEVEL SECURITY`、`CREATE POLICY briefings_read ON market_briefings FOR SELECT TO authenticated USING (true)` |      |      |

---

## 3. 備選方案

- **ALT-001**：使用 `google-generativeai` Python SDK 取代直接 httpx REST 呼叫。優點：SDK 封裝較完整；缺點：增加 ~50MB 大型依賴，且 httpx 已覆蓋需求，選擇 REST 呼叫保持依賴一致性
- **ALT-002**：使用 OpenAI GPT-4o-mini 取代 Gemini 1.5 Flash。優點：語言模型品質穩定；缺點：無免費方案且成本較高，Gemini Flash 已足夠本場景
- **ALT-003**：為每個使用者獨立排程（基於各自 tracked symbols）。優點：精準過濾；缺點：若有多位使用者則 API 請求量倍增超過 Brave 限額，選擇全域唯一 symbol 策略再由前端過濾
- **ALT-004**：使用 WebSocket / Server-Sent Events 推送新早報至前端。優點：即時性高；缺點：架構複雜度大幅提升，早報每日僅 3 次更新，用戶端輪詢（onMounted + 手動刷新）已足夠
- **ALT-005**：使用 SerpAPI 取代 Brave Search。優點：地區語言支援更廣；缺點：免費方案僅 100 次/月，不足本功能需求

---

## 4. 相依性

- **DEP-001**：`httpx>=0.27.0` — 已在 `requirements.txt`，用於呼叫 Brave Search API 與 Gemini REST API
- **DEP-002**：`apscheduler==3.10.4` — 已在 `requirements.txt`，用於新增三個每日 cron job
- **DEP-003**：Brave Search API Key — 需至 https://brave.com/search/api/ 申請 Data for Search 方案（免費：2,000 次/月）
- **DEP-004**：Google Gemini API Key — 需至 https://makersuite.google.com/app/apikey 申請（免費：15 RPM、1,500 requests/day）
- **DEP-005**：Supabase `market_briefings` 表需在排程首次執行前完成建立（TASK-003 先於 TASK-009）

---

## 5. 受影響檔案

- **FILE-001**：`backend/app/config.py` — 新增 `brave_search_api_key` 與 `gemini_api_key` 設定欄位
- **FILE-002**：`backend/app/services/brave_search_service.py` — **新增** Brave Search 新聞搜尋服務
- **FILE-003**：`backend/app/services/gemini_service.py` — **新增** Gemini API 摘要生成服務
- **FILE-004**：`backend/app/services/news_briefing_service.py` — **新增** 早報主編排服務（orchestrator）
- **FILE-005**：`backend/app/routers/briefing.py` — **新增** `/api/briefing` REST 路由模組
- **FILE-006**：`backend/app/main.py` — 修改：新增 `briefing_router` 的 `include_router`
- **FILE-007**：`backend/app/scheduler.py` — 修改：新增三個早報 cron job（08:00 / 13:00 / 18:00）
- **FILE-008**：`backend/requirements.txt` — 驗證 `httpx` 版本（無須新增依賴）
- **FILE-009**：`frontend/src/api/briefing.js` — **新增** 前端 Axios API 客戶端
- **FILE-010**：`frontend/src/stores/briefing.js` — **新增** Pinia briefing store
- **FILE-011**：`frontend/src/components/AIDailyBriefing.vue` — **新增** 早報卡片 UI 元件
- **FILE-012**：`frontend/src/stores/dashboard.js` — 修改：`cardOrder` 新增 `'ai-briefing'`
- **FILE-013**：`frontend/src/views/DashboardView.vue` — 修改：新增早報卡片渲染邏輯
- **FILE-014**：`docs/migrations/20260327_market_briefings.sql` — **新增** Supabase migration SQL

---

## 6. 測試項目

- **TEST-001**：`tests/test_brave_search_service.py` — 單元測試 `search_news()`：mock httpx response，驗證回傳格式為 `[{"title", "url", "description", "published_date"}]`；驗證 API Key 為空字串時回傳空 list 不拋出異常；驗證 HTTP 非 200 時記錄 error 並回傳空 list
- **TEST-002**：`tests/test_gemini_service.py` — 單元測試 `generate_market_summary()`：mock httpx response，驗證 Prompt 包含 symbol 名稱與新聞標題；驗證 API 失敗（HTTP 500/429）時回傳空字串不拋出異常
- **TEST-003**：`tests/test_news_briefing_service.py` — 整合測試 `run_market_briefing_session()`：mock Supabase query（回傳 2 個 symbols）、mock Brave Search、mock Gemini；驗證 stats dict `{"total": 2, "success": 2, "failed": 0}`；驗證 `asyncio.sleep(1)` 被呼叫 2 次
- **TEST-004**：`tests/test_briefing_api.py` — API 端點測試：`GET /api/briefing/latest` 無 Token 回傳 401；有效 Token 回傳 200 含 `session_time` 與 `items` 欄位；`POST /api/briefing/trigger` 有效 Token 回傳 202
- **TEST-005**：前端手動測試：Dashboard 卡片顯示「🤖 AI 市場早報」標題；展開 symbol 卡片顯示 3 則新聞；手動刷新按鈕觸發 API call 並顯示 loading 狀態

---

## 7. 風險與假設

- **RISK-001**：Brave Search 2,000 次/月上限。若追蹤 unique symbol 超過 22 個，月配額耗盡。**緩解**：在 `news_briefing_service.py` 加入 `MAX_SYMBOLS_PER_SESSION = 20` 常數，超過時記錄 warning 並跳過超額 symbol
- **RISK-002**：Gemini 15 RPM 限制。若 symbol 數量超過 15 且不加間隔，會觸發 HTTP 429。**緩解**：每個 symbol 後強制 `await asyncio.sleep(1)` 確保每分鐘不超過 15 個請求
- **RISK-003**：台灣 ETF（如 00878）中文新聞搜尋覆蓋率可能不足。**緩解**：搜尋 query 同時包含英文 symbol 代碼與中文名稱（`f"{symbol_name} {symbol}"`），並設定 `search_lang=zh-cht,en`
- **RISK-004**：排程執行時間長（20 個 symbol 約 60-200 秒）。**緩解**：排程在背景非同步執行，不阻塞主應用；log 執行時間供監控
- **RISK-005**：Gemini 免費方案每日 1,500 次上限。本功能每日消耗 `3 排程 × 20 symbol = 60 次`，遠低於上限，無風險

- **ASSUMPTION-001**：Gemini Prompt 使用繁體中文指令，Gemini 1.5 Flash 能穩定回應繁體中文摘要
- **ASSUMPTION-002**：Brave Search News API 回應格式為 `{"results": [{"title": str, "url": str, "description": str, "age": str}]}`
- **ASSUMPTION-003**：Gemini REST endpoint 格式為 `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=<KEY>`，request body 符合標準 `generateContent` JSON 格式

---

## Prompt 設計（參考）

```
你是一位專業的金融市場分析師。以下是關於 {symbol_name}（{symbol}）在 {session_label} 的最新 {count} 則新聞：

新聞 1：{title_1}
摘要：{description_1}

新聞 2：{title_2}
摘要：{description_2}

新聞 3：{title_3}
摘要：{description_3}

請根據上述新聞，以繁體中文撰寫一段 100-150 字的市場動態摘要。
格式：純文字，無需標題，包含：(1) 主要市場動態 (2) 潛在影響 (3) 投資者關注要點。
```

---

## 8. 相關規格 / 延伸閱讀

- [docs/todo/future_plan.md](../docs/todo/future_plan.md) — Phase 3 AI 市場分析師原始藍圖
- [plan/feature-rsi-alerts-1.md](feature-rsi-alerts-1.md) — RSI 警報功能計畫（service 層模式參考）
- [backend/app/scheduler.py](../backend/app/scheduler.py) — 現有排程器實作
- [backend/app/services/line_service.py](../backend/app/services/line_service.py) — 現有通知服務架構（service 層模式參考）
- [frontend/src/stores/dashboard.js](../frontend/src/stores/dashboard.js) — Dashboard 卡片拖曳 store
- Brave Search News API 文件：https://api.search.brave.com/app/documentation/news-search
- Google Gemini generateContent API 文件：https://ai.google.dev/api/generate-content
