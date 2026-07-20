# AGENTS.md - Finance Dashboard

本文件供 Codex 在本專案中工作時使用。除 Git commit message 與 PR 描述外，所有回覆、說明、code review 與文件內容都必須使用繁體中文。

## 最高優先級

- Git commit message 必須使用英文，且遵循 Conventional Commits。
- PR 描述必須使用英文，並維持清楚的工程語氣。
- 不要主動建立 git commit，除非使用者明確要求。
- 不要提交或輸出任何密鑰、token、service role key、JWT、資料庫憑證或其他敏感資訊。
- 不要回復簡體中文。

## Git Commit Message

格式：

```text
<type>(<scope>): <subject>
```

規則：

- `type` 使用 `feat`, `fix`, `refactor`, `test`, `docs`, `ci`, `style`, `perf`, `chore`。
- `scope` 可使用 `auth`, `backtest`, `optimize`, `market`, `tracking`, `ui`, `api` 或其他合適模組名稱。
- `subject` 使用英文命令式語氣，例如 `add`, `fix`, `update`。
- `subject` 首字母小寫，結尾不加句號，盡量不超過 50 字元。

範例：

```text
feat(backtest): add DCA strategy support
fix(optimize): correct sharpe ratio calculation
docs(api): update portfolio endpoints documentation
refactor(market): extract data validation logic
test(backtest): add edge case coverage for negative returns
```

## 專案概述

Finance Dashboard 是台灣 ETF 與股票投資組合分析儀表板，提供市場數據同步、投資組合追蹤、回測、資產配置優化、蒙地卡羅模擬、通知與 AI briefing 等功能。

主要技術：

- 後端：FastAPI、Supabase/PostgreSQL/RLS、Redis、APScheduler、pandas、numpy、scipy。
- 前端：Vue 3 Composition API、Vite、Pinia、Vue Router、ECharts、Tailwind CSS v4。
- 數據源：Yahoo Finance/yfinance、台灣股票與 ETF 資料。
- 認證：JWT、Supabase Row Level Security。

## 目錄結構

```text
backend/                 FastAPI 後端
backend/app/main.py      後端應用入口
backend/app/routers/     API 路由
backend/app/services/    核心業務邏輯與計算引擎
backend/app/models/      Pydantic 模型
frontend/                Vue 3 前端
frontend/src/views/      頁面
frontend/src/components/ UI 元件
frontend/src/stores/     Pinia stores
frontend/src/api/        Axios API 客戶端
frontend/src/router/     Vue Router 設定
docs/                    專案文件
tests/                   測試
tools/                   CLI 與開發工具
scripts/                 部署與維護腳本
```

重要文件：

- `README.md`
- `docs/backend/backend.md`
- `docs/frontend/frontend.md`
- `docs/deploy/deploy.md`
- `docker-compose.yml`
- `ecosystem.config.js`

## 常用開發命令

後端：

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

Docker Compose：

```bash
docker-compose up
```

測試：

```bash
venv/bin/pytest tests/ -v --tb=short
venv/bin/pytest tests/test_backtest_engine.py -v
venv/bin/pytest tests/ --cov=app --cov-report=html
```

pytest 安裝在專案根目錄的 `venv/`，應從專案根目錄執行 `venv/bin/pytest`。不要誤用 `backend/venv`，該虛擬環境目前未安裝 pytest。

若目前 shell 的 `DEBUG` 環境變數是 `release` 等非布林值，Pydantic Settings 會在測試載入階段失敗。此時使用明確的布林值執行：

```bash
DEBUG=false venv/bin/pytest tests/ -v --tb=short
```

前端建置：

```bash
cd frontend
npm run build
```

## API 結構

所有 API 以前綴 `/api` 提供。

- `auth`：使用者登入與認證，例如 `POST /api/auth/login`、`POST /api/auth/register`。
- `tracking`：投資組合管理，例如 `GET /api/tracking/indices/active`、`POST /api/tracking/add`。
- `backtest`：策略回測，例如 `POST /api/backtest/run`。
- `optimize`：組合優化，例如 `POST /api/optimize/run`。
- `market`：市場數據，例如 `GET /api/market/quotes`、`POST /api/market/sync-etf`。

## 資料庫與安全

- 使用 Supabase PostgreSQL 與 Row Level Security。
- 使用者只能存取自己的資料。
- 涉及資料庫 schema 變更時，優先新增或更新 `docs/migrations/` 下的 SQL migration。
- 修改資料庫相關邏輯前，先檢查既有 migration、router、service 與測試。
- `SUPABASE_SERVICE_KEY` 只能在後端使用，不得暴露給前端。
- 前端不得儲存敏感資訊，只保留運作必要的 JWT 或非敏感設定。

## 核心功能位置

- 市場數據同步：`backend/app/services/tw_etf_sync.py`、`backend/app/services/us_etf_sync.py`。
- 投資組合追蹤：`backend/app/routers/tracking.py`。
- 回測引擎：`backend/app/services/backtest_engine.py`。
- 投資組合優化：`backend/app/services/optimization_engine.py`。
- 蒙地卡羅模擬：`backend/app/services/monte_carlo_engine.py`。
- AI briefing/search：`backend/app/services/news_briefing_service.py`、`backend/app/services/searxng_service.py`、`backend/app/services/ollama_service.py`。
- 前端 API 客戶端：`frontend/src/api/`。
- 前端頁面：`frontend/src/views/`。
- 前端狀態管理：`frontend/src/stores/`。

## 編碼慣例

Python：

- 遵循 PEP 8。
- 使用 type hints。
- 公開函式需要 docstring，說明參數、回傳值與重要行為。
- FastAPI 端點與 I/O 操作優先使用 async/await。
- 金融比例、報酬、價格與精度敏感計算需留意浮點誤差，必要時使用 `Decimal` 或明確的四捨五入策略。

JavaScript/Vue：

- 使用 Vue 3 Composition API 與 `<script setup>`。
- Vue 元件使用 PascalCase。
- 變數與函式使用 camelCase。
- 狀態管理使用 Pinia。
- API 呼叫集中放在 `frontend/src/api/`，避免在元件中散落 axios 細節。
- 圖表使用 ECharts/vue-echarts；大量資料重繪時注意效能。

文件：

- 專案文件放在 `docs/`。
- 一般文件使用繁體中文。
- 文件更新應與實際程式行為同步。

## 前端 UI 指引

- 維持深色模式優先的金融儀表板風格。
- 介面應適合長時間監控與快速掃描。
- 桌面與行動端都要保持可用與清楚。
- 使用 Tailwind CSS v4 與既有樣式慣例。
- 新增圖表或數據面板時，注意 loading、empty、error 狀態。
- 不要在畫面上顯示敏感 token 或後端錯誤堆疊。

## 常見開發任務

新增市場數據源：

1. 在 `backend/app/services/` 新增同步服務。
2. 實作資料抓取、驗證、快取與 Supabase 寫入邏輯。
3. 在 `backend/app/scheduler.py` 註冊排程。
4. 在 `backend/app/routers/market.py` 新增或更新 API。
5. 補上單元測試或整合測試。

新增投資組合計算指標：

1. 在 `backend/app/services/backtest_engine.py` 或相關 service 增加計算邏輯。
2. 更新 Pydantic 模型與 API 回傳欄位。
3. 更新 router。
4. 更新前端 API 客戶端、store 與視圖。
5. 新增測試並更新文件。

新增前端頁面：

1. 在 `frontend/src/views/` 建立頁面元件。
2. 在 `frontend/src/router/index.js` 註冊路由。
3. 視需要新增或更新 `frontend/src/stores/`。
4. 透過 `frontend/src/api/` 呼叫後端。
5. 加入 loading、empty、error 與權限狀態。

## 測試與驗證

- pytest 必須優先使用專案根目錄的 `venv/bin/pytest`；不要僅因 `backend/venv` 找不到 pytest 就判定專案沒有安裝測試工具。
- 測試載入若出現 `debug` 布林解析錯誤，先以 `DEBUG=false` 重跑，並將環境設定問題與程式測試失敗分開回報。
- 後端邏輯變更後，至少執行相關 pytest。
- 前端 UI 或 API client 變更後，至少執行 `npm run build`。
- 跨前後端流程變更時，優先增加或更新整合測試。
- 修 bug 時，盡可能補上會在修復前失敗的測試。
- 若無法執行測試，最終回覆必須說明原因。

## Code Review 指引

進行 review 時，優先指出：

- 可能的 bug、行為回歸或資料不一致。
- 認證、授權、RLS 或敏感資訊外洩風險。
- 金融計算錯誤、精度問題或邊界條件。
- 缺少測試或文件更新。
- 不必要的新依賴或效能風險。

## 環境變數

後端常見環境變數：

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_KEY`
- `SECRET_KEY`
- `REDIS_URL`
- `CORS_ORIGINS`

前端：

- `VITE_API_BASE_URL`

不要把 `.env`、密鑰或憑證內容寫入回覆、測試 snapshot 或文件範例中。

## 快取與外部服務注意事項

- Yahoo Finance、FinMind 或其他金融資料源可能有頻率限制。
- 股票行情快取 TTL 通常為 5 分鐘。
- ETF 清單快取 TTL 通常為 1 天。
- 回測結果快取可依情境使用較短 TTL。
- 新增外部 API 時，處理 timeout、重試、錯誤訊息與 fallback。

## 工作方式

- 開始修改前先閱讀相關 router、service、model、store、view 與測試。
- 優先沿用既有架構與命名，不為小改動引入大型抽象。
- 使用 `rg` 搜尋檔案與符號。
- 修改範圍保持精準，不順手重構無關程式。
- 既有未提交變更可能是使用者的工作，不要覆蓋或回復。
- 可在 `tests/` 與 `tools/` 新增必要測試或輔助工具，但要保持可維護性。
- `temp/` 可放臨時資料；不要假設其中內容會提交。

## 除錯命令

市場資料除錯：

```bash
python tools/debug_yf.py --symbol VTI --start-date 2024-01-01
```

後端日誌：

```bash
pm2 logs backend
```

前端日誌：

```bash
pm2 logs frontend
```

## MCP 與外部工具

原 Copilot 指引提到 Supabase、GitHub、NotebookLM、Notion MCP。Codex 只有在當前環境實際提供對應工具時才能使用。

- 若有 Supabase MCP：DDL 使用 migration，查詢或 DML 使用 SQL 工具，操作前先檢查 schema。
- 若有 GitHub MCP：可用於查 PR、issue、commit、workflow，但不要自行建立 PR 或 commit，除非使用者明確要求。
- 若有 Notion 或 NotebookLM MCP：僅在使用者要求文件、知識庫或筆記本操作時使用。
- 若工具不可用，改用本地檔案、測試與使用者提供的資訊完成任務。
