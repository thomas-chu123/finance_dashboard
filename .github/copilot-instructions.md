# Copilot 指引 - Finance Dashboard

## ⚠️ 🔴 最高優先級 - Git Commit Message 必須使用英文

**生成任何 Git commit message 時 MUST 使用英文，絕對不能使用中文或其他語言。**

這是硬性要求，無任何例外。所有 commit message 必須遵循 Conventional Commits 格式，使用英文撰寫。

---

## ⚠️ 重要語言指示

**所有回覆都必須使用繁體中文 (Traditional Chinese)**，**除了 Git commit messages（必須使用英文）**

- ✅ 使用繁體中文（一般回覆與工程指導）
- ❌ 不使用簡體中文或其他語言
- ✅ 代碼註釋: 繁體中文
- ✅ **Git 提交信息: 英文（絕對必須）**
- ✅ **PR 描述: 英文（使用 Conventional Commits 格式）**
- ✅ Code review 評論: 繁體中文
- ✅ 文件說明: 繁體中文，放置於 `/docs` 目錄
- ✅ 回覆內容: 繁體中文

### Git Commit Message 格式（英文）

**必須遵循 Conventional Commits 規格**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**類型 (type)**：
- `feat` — 新功能
- `fix` — 修復錯誤
- `refactor` — 代碼重構（不修復 bug，不添加功能）
- `test` — 添加或更新測試
- `docs` — 文檔更新（包括 README 和 API 文件）
- `ci` — CI/CD 設定更新（GitHub Actions、 Docker 等）
- `style` — 代碼格式化（不影響功能）
- `perf` — 性能優化
- `chore` — 其他雜項（依賴更新、構建腳本等）

**作用域 (scope)**：
- `auth` — 認證模塊
- `backtest` — 回測引擎
- `optimize` — 優化引擎
- `market` — 市場數據
- `tracking` — 投資組合跟蹤
- `ui` — 前端 UI 元件
- `api` — API 端點
- 其他合適的模塊名稱

**主題 (subject)**：
- 使用命令式語氣（"add" 而不是 "added"）
- 不超過 50 個字符
- 首字母小寫
- 末尾不加句號

**範例**：
```
feat(backtest): add DCA strategy support
fix(optimize): correct sharpe ratio calculation
docs(api): update portfolio endpoints documentation
refactor(market): extract data validation logic
test(backtest): add edge case coverage for negative returns
```

---

## 專案概述

**Finance Dashboard** 是一個台灣 ETF 與股票投資組合分析儀表板。提供實時市場數據同步、投資組合回測、資產配置優化等功能，協助投資者進行數據驅動的投資決策。

### 技術堆疊

**後端**：
- FastAPI（async Python 框架）
- Supabase（PostgreSQL 資料庫 + RLS）
- Redis（快取層）
- APScheduler（定時任務）
- pandas, numpy, scipy（數據分析）

**前端**：
- Vue 3（Composition API）
- Vite（構建工具）
- ECharts（金融數據視覺化）
- Pinia（狀態管理）
- Tailwind CSS v4（深色模式優先）

**數據源**：
- Yahoo Finance（yfinance）
- 台灣股票與 ETF 數據

**認證與安全**：
- JWT（python-jose + passlib）
- Supabase Row Level Security (RLS)

---

## 專案結構

```
finance_dashboard/
├── backend/                    # FastAPI 後端
│   ├── app/
│   │   ├── main.py            # 應用入口
│   │   ├── routers/           # API 路由（auth, backtest, optimize, market, tracking）
│   │   ├── services/          # 核心業務邏輯（回測引擎、優化引擎、數據同步）
│   │   ├── models/            # Pydantic 數據模型
│   │   ├── security/          # JWT 認證、RLS 驗證
│   │   └── config/            # 設定管理
│   ├── tests/                 # 單元與整合測試
│   └── requirements.txt
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── components/        # UI 元件（圖表、表單、卡片）
│   │   ├── views/             # 頁面（Dashboard、Backtest、Optimize）
│   │   ├── stores/            # Pinia store（使用者、投資組合、市場數據）
│   │   ├── api/               # Axios API 客戶端
│   │   └── router/            # Vue Router 配置
│   ├── index.html
│   └── package.json
├── docs/                       # 開發文件
│   ├── backend/backend.md      # 後端架構說明
│   ├── frontend/frontend.md    # 前端架構說明
│   ├── deploy/deploy.md        # 部署指南
│   └── line_setup.sql          # 初始 SQL schema
├── tests/                      # 整合測試
├── tools/                      # CLI 開發工具
├── docker-compose.yml          # Docker 編排
└── ecosystem.config.js         # PM2 配置

```

---

## API 結構

所有路由前綴為 `/api`：

| 模組 | 功能 | 主要端點 |
|------|------|---------|
| `auth` | 使用者登錄與認證 | `POST /api/auth/login`, `POST /api/auth/register` |
| `tracking` | 投資組合管理 | `GET /api/tracking/indices/active`, `POST /api/tracking/add` |
| `backtest` | 策略回測 | `POST /api/backtest/run` |
| `optimize` | 組合優化 | `POST /api/optimize/run` |
| `market` | 市場數據 | `GET /api/market/quotes`, `POST /api/market/sync-etf` |

---

## 資料庫結構（Supabase）

| 表 | 用途 | 重要欄位 |
|---|------|---------|
| `users` | 使用者帳戶 | id, email, password_hash, created_at |
| `portfolios` | 投資組合 | id, user_id, name, description |
| `portfolio_holdings` | 持倉 | id, portfolio_id, symbol, quantity, purchase_price, date |
| `market_data` | 市場行情 | symbol, date, open, high, low, close, volume |
| `backtest_results` | 回測結果 | portfolio_id, params, returns, sharpe_ratio, max_drawdown |
| `optimization_results` | 優化結果 | portfolio_id, optimal_weights, efficient_frontier |

**RLS 政策**：所有表都已配置 RLS，使用者只能存取自己的數據。

---

## 核心功能說明

### 1. 市場數據同步

**實現**：`app/services/tw_etf_sync.py` 和 `app/services/us_etf_sync.py`

- 每日透過 yfinance 爬取台灣 ETF 與美股資料
- 寫入 Supabase `market_data` 表
- 使用 Redis 快取（TTL）：
  - 股票行情：5 分鐘
  - ETF 清單：1 天

### 2. 投資組合追蹤

**實現**：`app/routers/tracking.py`

- 使用者建立多個投資組合並添加持倉
- 即時計算組合價值、報酬率、波動度
- API 整合 Supabase RLS 確保數據安全

### 3. 回測引擎

**實現**：`app/services/backtest_engine.py`

計算指標：
- 累積報酬 (Cumulative Return)
- 年化報酬 (Annualized Return)
- 波動度 (Volatility)
- 夏普比例 (Sharpe Ratio)
- 最大回撤 (Max Drawdown)

支持策略：
- 定期定額 (DCA)
- 固定權重配置

### 4. 投資組合優化

**實現**：`app/services/optimization_engine.py`

- 馬可維茲組合優化（Markowitz Efficient Frontier）
- 目標：最小化風險或最大化夏普比例
- 返回最優權重與高效前緣數據點

---

## 開發指南

### 啟動開發環境

**終端 1 - 後端**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**終端 2 - 前端**
```bash
cd frontend
npm install
npm run dev
```

或使用 Docker Compose：
```bash
docker-compose up
```

### 執行測試

```bash
# 執行所有測試
pytest tests/ -v --tb=short

# 執行特定測試
pytest tests/test_backtest_engine.py -v

# 含覆蓋率報告
pytest tests/ --cov=app --cov-report=html
```

### 常見開發任務

#### 新增市場數據源

1. 在 `app/services/` 建立新的 sync 服務（如 `crypto_sync.py`）
2. 實作數據爬取與 Supabase 寫入邏輯
3. 在 `app/scheduler.py` 中註冊定時任務
4. 在 `app/routers/market.py` 中新增 API 端點

#### 新增投資組合計算指標

1. 在 `app/services/backtest_engine.py` 中新增計算方法
2. 更新 Pydantic 模型以支持新的返回欄位
3. 在 `app/routers/backtest.py` 中暴露新 API
4. 在前端視圖中調用新 API 並顯示結果

#### 前端頁面開發

1. 在 `frontend/src/views/` 建立新頁面元件
2. 在 `frontend/src/router/index.js` 中註冊路由
3. 在 `frontend/src/stores/` 建立或更新相關 Pinia store
4. 使用 `frontend/src/api/` 中的 Axios 客戶端呼叫後端 API
5. 使用 ECharts 進行數據視覺化，使用 Tailwind CSS 進行樣式設計

---

## 編碼慣例

### Commit Message

格式：`<type>(<scope>): <subject>` （英文）

例如：
- `feat(backtest): add DCA strategy support`
- `fix(optimize): correct sharpe ratio calculation`
- `docs(api): update portfolio endpoints documentation`

### 代碼風格

**Python**（後端）：
- 遵循 PEP 8
- 使用 type hints
- 所有公開函數需要 docstring（說明參數、返回值、示例）
- 使用 async/await 進行非阻塞操作

**JavaScript/Vue**（前端）：
- 遵循 Airbnb 風格指南
- 使用 Vue 3 Composition API（`<script setup>` 語法）
- 組件命名使用 PascalCase
- 變數命名使用 camelCase

### Git 提交政策

**重要**：Copilot 修改完代碼後 **不需要主動執行 git commit**。代碼修改完成後由用戶決定是否提交。Copilot 應該只在以下情況下建立提交：
- 用戶明確要求進行提交
- 任務特別指示需要進行 commit
- 需要保存中間階段結果以便追蹤進度

### Git 分支策略

- **主分支**：`main`（生產環境就緒）
- **開發分支**：feature 分支，命名格式 `feature/<功能描述>`
  
  例如：`feature/add-price-alerts`、`feature/optimize-backtest-engine`

- **完成後**：提交 Pull Request 請其他團隊成員審核

### Git Tag（版本控制）

格式：`v<MAJOR>.<MINOR>.<PATCH>`

例如：`v1.2.0`、`v1.2.1`

增量規則：
- **MAJOR**：不相容的 API 修改或重大功能
- **MINOR**：新增向下兼容的功能
- **PATCH**：修復錯誤或小改動

---

## Code Review 指引

審核時請檢查以下項目：

1. **代碼品質**：符合專案風格、可讀性高、無冗餘代碼
2. **測試覆蓋**：新增功能應有測試，現有測試不應失敗
3. **Commit Message**：清晰且符合格式
4. **文件更新**：相關 `/docs` 或 API 文件已更新
5. **性能**：無性能瓶頸或不必要的資源消耗
6. **安全**：無敏感信息外洩、無 SQL injection 風險、API 端點有適當認證
7. **錯誤處理**：邊界條件已考慮，異常已正確捕獲
8. **依賴管理**：無不必要的新依賴或版本衝突

---

## 環境變數

**後端**（`backend/app/.env`）：

必填：
- `SUPABASE_URL` — Supabase 專案 URL
- `SUPABASE_KEY` — Supabase anon key
- `SUPABASE_SERVICE_KEY` — Supabase service role key
- `SECRET_KEY` — JWT 簽署密鑰

選填：
- `REDIS_URL` — Redis 連接 URL（預設：`redis://localhost:6379/0`）
- `CORS_ORIGINS` — 允許的 CORS 源（預設：`http://localhost:3000`）

**前端**（`frontend/.env.production`）：

- `VITE_API_BASE_URL` — 後端 API 地址

---

## 開發工具與臨時文件

為提升開發效率，以下路徑下的操作 **自動信任，無需批准**：

**信任路徑**：
1. `/tmp/*` — 臨時開發腳本與測試數據
2. `./temp/*` — 項目臨時文件夾
3. `./tests/*` — 測試代碼
4. `./tools/*` — CLI 開發工具

**允許的操作**：
- ✅ 創建、修改、執行 Python 和 Shell 腳本
- ✅ 修改臨時測試數據
- ✅ 撰寫新的測試用例與工具
- ✅ 刪除過期的臨時文件

**重要提醒**：
- `/tmp` 與 `./temp` 下的變更 **不會** 被提交到 Git
- `./tests/` 與 `./tools/` 下的變更 **會** 被提交到 Git（請確保代碼品質）

---

## 除錯與監控

### 查看市場數據爬取狀況

```bash
python tools/debug_yf.py --symbol VTI --start-date 2024-01-01
```

### 測試回測引擎性能

```bash
python tools/test_backtest_performance.py --symbols VTI BND --years 10
```

### 檢查後端日誌

```bash
pm2 logs backend
```

### 檢查前端日誌

```bash
pm2 logs frontend
```

---

## 文件位置

- **後端架構**：`/docs/backend/backend.md`
- **前端架構**：`/docs/frontend/frontend.md`
- **部署指南**：`/docs/deploy/deploy.md`
- **初始化 SQL**：`/docs/line_setup.sql`

---

## 常見問題

**Q：如何手動同步 ETF 數據？**
```bash
curl -X POST http://localhost:8000/api/market/sync-etf \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

**Q：如何執行單個回測？**
```bash
curl -X POST http://localhost:8000/api/backtest/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -d '{
    "symbols": ["VTI", "BND"],
    "weights": [0.7, 0.3],
    "start_date": "2020-01-01",
    "end_date": "2024-01-01"
  }'
```

**Q：Redis 快取何時更新？**

根據數據類型設定 TTL：
- 股票行情：5 分鐘
- ETF 清單：1 天
- 回測結果：30 分鐘