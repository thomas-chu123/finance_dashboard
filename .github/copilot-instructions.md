# Copilot 指引

## ⚠️ 重要語言指示

**所有回覆都必須使用繁體中文 (Traditional Chinese)**

- ✅ 使用繁體中文
- ❌ 不使用簡體中文、英文或其他語言
- ✅ 代碼註釋: 繁體中文
- ✅ Git 提交信息: 英文（按照專案慣例）
- ✅ PR 描述: 英文（按照專案慣例）
- ✅ Code review 評論: 繁體中文
- ✅ 文件說明: 繁體中文, 放置於 `/docs` 目錄
- ✅ 回覆內容: 繁體中文

---

## 專案概述

台灣 ETF 與股票投資組合分析儀表板。提供實時市場數據同步、投資組合回測、資產配置優化、市場警示等功能，協助投資者進行數據驅動的投資決策。

## 技術堆疊

- **後端**：FastAPI + APScheduler + Supabase（PostgreSQL）+ Redis（快取）
- **前端**：Vue 3 + Vite + ECharts（數據視覺化）+ Pinia（狀態管理）
- **數據源**：yfinance（市場數據）+ yfinance（美股/ETF）
- **數據分析**：pandas + numpy + scipy（統計分析）
- **認證**：JWT（python-jose + passlib）
- **通知**：Webhook + LINE Messaging API（可選）

## 指令

```bash（後端 + 前端）
# 終端 1 - 後端
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 終端 2 - 前端
cd frontend
npm install
npm run dev

# 或使用 Docker Compose
docker-compose up

# 執行後端測試
pytest tests/ -v --tb=short

# 執行特定測試
pytest tests/test_backtest_engine.py -v

# 執行所有測試含覆蓋率
pytest tests/ --cov=app --cov-report=html

# 同步 ETF 數據（需要伺服器運行中）
curl -X POST http://localhost:8000/api/market/sync-etf

# 執行回測
curl -X POST http://localhost:8000/api/backtest/run \
  -H "Content-Type: application/json" \
  -d '{"symbol":"VTI","start_date":"2020-01-01","end_date":"2024-01-01"}'
市場數據同步** (`app/services/tw_etf_sync.py` 與 `app/services/us_etf_sync.py`)：
   - 每日透過 yfinance 爬取台灣 ETF 與美股資料
   - 寫入 Supabase `market_data` 或 `portfolio_holdings` 表
   - 使用 Redis 快取最近的價格數據

2. **投資組合追蹤** (`app/routers/tracking.py`)：
   - 使用者建立投資組合並加入持倉
   - 即時計算組合價值、報酬率、波動度
   - 支持多個投資組合管理

3. **回測引擎** (`app/services/backtest_engine.py`)：
   - 使用歷史數據模擬投資策略
   - 計算累積報酬、夏普比例、最大回撤等指標
   - 支持定期定額 (DCA) 策略

4. **投資組合優化** (`app/services/optimization_engine.py`)：
   - 馬可維茲組合優化（Markowitz Portfolio Optimization）
   - 尋找最小風險或最大夏普比例的資產配置：
```python
result = await asyncio.to_thread(
    lambda: supabase.table("portfolio_holdings").select("*").eq("user_id", user_id).execute()
)
```

**設定值** 透過 `get_settings()`（`@lru_cache` 快取）從 `pydantic_settings.BaseSettings` 讀取，來源為環境變數或 `.env` 檔案。

**Redis 快取**：市場數據與計算結果快取於 Redis（TTL 基於數據類型）：
- 股票行情：5 分鐘
- ETF 清單：1 天
- 回測結果：30 分鐘（基於輸入參數）

**時間處理**：所有計算使用 UTC 時間戳記，但在前端顯示時轉換為使用者時區（預設台灣時間 UTC+8）。

**數據驗證**：所有 API 入參使用 Pydantic 模型驗證，避免無效數據進入業務邏輯。

### 資料庫結構（Supabase）

- `users` — 使用者帳戶與認證（JWT token 簽署）
- `portfolios` — 投資組合（名稱、描述、建立時間）
- `portfolio_holdings` — 投資組合持倉（股票/ETF 代號、數量、購買價格、日期）
- `market_data` — 帳務與技術數據（日期、開收高低、交易量、調整收盤價）
- `backtest_results` — 回測歷史結果（參數、報酬率、風險指標、回測數據）
- `optimization_results` — 優化結果（最優配置、高效前緣數據點）
- `price_alerts` — 價格警示規則（符號、條件、閾值、狀態）
- `notification_logs` — 通知記錄（發送時間、接收者、通知類型）

### API 結構

所有路由前綴為 `/api`。路由模組：
- `auth` — 使用者登錄與認證
- `users` — 使用者設定與個人資料
- `tracking` — 投資組合建立、修改、查询
- `backtest` — 回測策略執行
- `optimize` — 投資組合優化
- `fundamentals` — 基本面數據（盈益比、股利率等）
- `market` — 市場數據同步與查詢
- `notifications` — 警示與通知設定

認證依賴：一般路由使用 `get_current_user`，敏感操作使用額外擁有權驗證，皆位於 `app/security
**密碼雜湊**：bcrypt 前會將密碼截斷至 71 bytes，以避免 >72 bytes 的錯誤，此為刻意設計。

### 新增醫院

1. 在 `app/scrapers/` 建立繼承 `BaseScraper` 的新爬蟲類別
2. 設定 `HOSPITAL_CODE` 類別屬性（用於查詢 DB 中的醫院記錄）
3. 實作三個抽象方法
4. 在 `app/scheduler.py` 的 `run_cmuh_master_data()` 與 `run_tracked_appointments()` 中，將新爬蟲加入 `scrapers` 列表

### 資料庫結構（Supabase）

- `hospitals`、`departments`、`doctors` — 主資料
- `ap CLI 工具協助開發和除錯，所有工具位於 `tools/` 目錄：

| 工具 | 用途 | 路徑 |
|------|------|------|
| `test_backtest_performance.py` | 回測引擎性能測試 | `tools/test_backtest_performance.py` |
| `debug_yf.py` | yfinance 數據爬取除錯 | `tools/debug_yf.py` |

### 環境變數

**必填**：
- `SUPABASE_URL` — Supabase 專案 URL
- `SUPABASE_KEY` — Supabase anon key
- `SUPABASE_SERVICE_KEY` — Supabase service role key
- `SECRET_KEY` — JWT 簽署密鑰

**選填**：
- `REDIS_URL` — Redis 連接 URL（預設：`redis://localhost:6379/0`）
- `SMTP_*` — 郵件伺服器設定（發送通知時使用）
- `LINE_CHANNEL_ACCESS_TOKEN` — LINE Bot 頻道 Token
- `LINE_CHANNEL_SECRET` — LINE Bot 頻道密鑰
python tools/tool_supabase.py <command> [options]
python tools/tool_notion.py <command> [options]

# 帶 cd 進項目目錄
cd /path/to/medical_help
python tools/tool_supabase.py list_hospitals
```

#### 在 Copilot Chat 中使用工具

1. **查詢數據**：直接要求工具執行查詢
   ```
   "查詢馬偕醫院的眼科醫生"
   → Copilot 會自動執行: python tools/tool_supabase.py list_doctors --department_id <眼科ID>
   ```

2. **修改數據**：明確指定更新內容
   ```
   "更新用戶 user123 的追蹤設定"
   → Copilot 會執行 update 或 upsert 操作
   ```

3. **調試問題**：使用工具驗證數據
   ```
   "檢查為什麼眼科沒有醫生"
   → Copilot 會查詢相關表格並分析
   ```
其他慣例

**commit message 格式**: 使用英文書寫，格式為 `<type>(<scope>): <subject>`。例如：`feat(backtest): add DCA strategy support`。

**chat response 格式**：使用繁體中文，保持專業且簡潔。回答應直接針對問題。

**git 分支策略**：使用 feature 分支開發新功能，命名格式為 `feature/<功能描述>`，例如 `feature/add-price-alerts`。

**git tag 策略**：使用語義化版本控制，tag 格式為 `v<MAJOR>.<MINOR>.<PATCH>`。

**代碼風格**：
- Python：遵循 PEP 8，使用 type hints
- JavaScript/Vue：遵循 Airbnb 風格指南
- 所有公開函數應包含 docstring （格式：參數、返回值、示例
- ❌ 不適合批量操作（超過 100 個項目）
- ❌ 不適合複雜的關聯邏輯（應在 FastAPI 程式碼中實作）

### 環境變數

必填：`SUPABASE_URL`、`SUPABASE_SERVICE_ROLE_KEY`、`SUPABASE_ANON_KEY`、`SECRET_KEY`  
選填：`SMTP_*` 相關變數、`LINE_CHANNEL_ACCESS_TOKEN`、`LINE_CHANNEL_SECRET`、`SCRAPE_INTERVAL_MINUTES`（預設：3）、`NOTION_API`（Notion 整合 Token，tool_notion.py 必填）

### 其他

commit message 格式: 使用英文書寫，格式為 `<type>(<scope>): <subject>`，其中 `<type>` 為 feat、fix、docs、style、refactor、test、chore 之一，`<scope>` 為相關模組或功能的簡短描述，`<subject>` 為具體的變更說明（不超過 72 字）。例如：`feat(scheduler): add new hospital scraper`。

chat response 格式：請使用中文撰寫，保持專業且簡潔。回答應直接針對問題，避免冗長的背景說明或不必要的細節。

git 分支策略：使用 feature 分支開發新功能，命名格式為 `feature/<功能描述>`，例如 `feature/add-notification-logs`。完成後透過 pull request 合併至 main 分支，並由其他團隊成員進行 code review。

git tag 策略：使用語義化版本控制，tag 格式為 `v<MAJOR>.<MINOR>.<PATCH>`，例如 `v1.2.0`。當有重大變更或不相容的 API 修改時增加 MAJOR 版本；當新增功能但保持向下兼容時增加 MINOR 版本；當修復錯誤或進行小改動時增加 PATCH 版本。

code review 指引：在 code review 時，請檢查以下幾點：
1. 代碼是否符合專案的程式碼風格和最佳實踐。
2. 變更是否有適當的測試覆蓋。
3. 變更是否有清晰的 commit message 和 pull request 描述。
4. 變更是否有適當的文件更新（如有必要）。
5. 變更是否有潛在的性能問題或安全風險。
6. 變更是否有適當的錯誤處理和邊界條件考慮。
7. 變更是否有適當的抽象和模組化，避免重複代碼。
8. 變更是否有適當的日誌記錄（如有必要）。
9. 變更是否有適當的資源管理（如有必要），避免內存洩漏或資源浪費。
10. 變更是否有適當的用戶體驗考慮（如有必要），確保功能易於使用且符合用戶需求。
11. 變更是否有適當的國際化和本地化考慮（如有必要），確保功能適用於不同地區和語言的用戶。
12. 變更是否有適當的可維護性和可擴展考慮，確保代碼易於理解和修改。
13. 變更是否有適當的依賴管理，確保不引入不必要的依賴或版本衝突。
14. 變更是否有適當的性能優化，確保不引入性能瓶頸或資源浪費。
15. 變更是否有適當的安全考慮，確保不引入安全漏洞或敏感信息泄露。
16. 變更是否有適當的合規性考慮，確保不違反相關法律法規或行業標準。
17. 變更是否有適當的可測試性考慮，確保代碼易於編寫和執行測試。
18. 變更是否有適當的可讀性考慮，確保
代碼清晰易懂，使用有意義的變量和函數名稱。
19. 變更是否有適當的可重用性考慮，確
保代碼可以在不同上下文中重用，避免硬編碼和緊耦合。
20. 變更是否有適當的文檔更新，確保代碼
的功能和使用方式有清晰的文檔說明，便於其他開發者理解和使用。
21. 變更是否有適當的回滾計劃，確保在發現問題時可以快速回滾到穩定版本。

/docs 相關：請確保所有公共 API 和重要功能都有適當的文檔說明，使用 docstring 格式，並包含參數說明、返回值說明和示例（如有必要）。文檔應該清晰、簡潔且易於理解，避免使用過於技術性的術語或行話。

### 開發工具與臨時文件信任設定

為了提升開發效率，以下路徑下的所有操作 **自動信任，無需批准**：

**信任路徑**：
1. `/tmp/*` — 臨時檔案和開發腳本（自動批准理由：純粹開發輔助工具，不影響項目代碼）
2. `./temp/*` — 項目本地臨時文件夾
3. `*/cache/*` — 快取相關文件
4. `./tests/*` — 測試文件和測試腳本（自動批准理由：測試代碼，驗證功能不破壞核心邏輯）
5. `./tools/*` — CLI 工具和開發輔助指令（自動批准理由：開發工具，協助資料庫查詢和項目管理）

**允許的操作**：
- ✅ 創建、修改、更新 Python 和 Shell 腳本
- ✅ 修改臨時測試數據或日誌文件
- ✅ 執行 `/tmp`、`./tests/`、`./tools/` 目錄下的任何腳本或命令（包括資料庫查詢、API 測試等）
- ✅ 刪除過期的臨時文件和舊的測試文件
- ✅ 撰寫新的測試用例和測試工具
- ✅ 新增或更新 CLI 工具指令

**重要提醒**：
- `/tmp` 下的所有變更 **都不會被提交到 Git**（此目錄已在 `.gitignore` 中）
- `./tests/` 和 `./tools/` 目錄下的變更 **會被提交到 Git**（請確保代碼品質）
- 臨時腳本完成後應移至 `tools/` 目錄或刪除，避免重複代碼
- 不適用於項目核心代碼的修改（`app/` 仍需適當審查）

`./temp` 放置臨時文件或測試腳本，請確保這些文件不會被提交到版本控制系統中，並且在不再需要時及時清理。`./tests` 和 `./tools` 目錄下的變更會被納入版本控制，請確保代碼品質和文檔完整性。

## 爬蟲調試指南

### 常見問題與解決方案

#### 1. 科室列表為空或不完整
**症狀**：爬蟲無法獲取科室列表，導致 `fetch_departments()` 返回空列表。

**檢查步驟**：
1. 使用工具驗證數據庫中是否有科室記錄：
   ```bash
   python tools/tool_supabase.py list_departments --hospital_id <hospital_id>
   ```
2. 查看爬蟲日誌中的 `[HOSPITAL] Built dynamic registration ID map` 信息
3. 檢查目標網站是否使用 JavaScript 動態加載內容（可使用 Chrome 開發者工具查看）

**根本原因**：
- 目標網站使用 JavaScript 動態加載（常見的 Cloudflare DDoS 保護、Vue.js 等框架）
- httpx 無法執行 JavaScript，因此無法獲得實際內容

**解決方案**：
- 使用 Selenium 或 Playwright 代替 httpx 以支持 JavaScript 執行
- 或改用其他數據源（如 API endpoint、HTML 伺服器端渲染的部分）

#### 2. 醫生列表為空

**症狀**：科室正確，但無法獲取該科室的醫生列表。

**檢查步驟**：
1. 驗證科室代碼是否正確：
   ```bash
   python tools/tool_supabase.py select doctors --filter department_id eq <dept_id> --limit 10
   ```
2. 檢查爬蟲日誌中 `fetch_schedule` 的輸出，查看是否成功解析了 HTML
3. 使用調試腳本直接抓取網頁： 
   ```python
   import httpx
   import re
   from bs4 import BeautifulSoup
   
   # 直接抓取醫生排班頁面 HTML，檢查表格結構
   resp = httpx.get("https://hospital.com/schedule?dept=45")
   soup = BeautifulSoup(resp.text, "lxml")
   table = soup.find("table", id="tblSch")
   if table:
       rows = table.find_all("tr")
       print(f"Found {len(rows)} rows")
   ```

**根本原因**：
- HTML 表格結構已改變（網站更新）
- 科室代碼映射不匹配（使用了錯誤的 depid）
- 該科室確實沒有醫生排班（如某些特殊門診）

**解決方案**：
1. 檢查網站的實際 HTML 結構並更新爬蟲的解析邏輯
2. 驗證科室代碼是否正確（可對比網站上的 URL 參數）
3. 確認該科室是否為有效的臨床科室

#### 3. 特定醫院爬蟲失敗

**症狀**：某個醫院的爬蟲無法正常工作。

**診斷步驟**：
1. 檢查該醫院是否已啟用：
   ```bash
   python tools/tool_supabase.py select hospitals --filter code eq HOSPITAL_CODE
   ```
2. 查看 `app/scheduler.py` 中是否包含該醫院的爬蟲
3. 檢查 `.env` 中是否設定了 `ENABLED_HOSPITALS`
4. 查看最近的爬蟲日誌，找出具體的錯誤信息

**常見原因**：
- 爬蟲未在 scheduler 中註冊
- 醫院代碼與數據庫中的代碼不匹配
- 網站結構已改變，爬蟲的 HTML 解析邏輯過時
 常見開發任務

### 新增市場數據源

1. 在 `app/services/` 建立新的 sync 服務（如 `crypto_sync.py`）
2. 實作數據爬取與 Supabase 寫入邏輯
3. 在 `app/scheduler.py` 中註冊排程任務
4. 在 `app/routers/market.py` 中新增 API 端點

### 新增投資組合計算指標

1. 在 `app/services/backtest_engine.py` 或 `optimization_engine.py` 中新增計算方法
2. 更新 Pydantic 模型以支持新的返回欄位
3. 在 `app/routers/backtest.py` 或 `app/routers/optimize.py` 中暴露新 API
4. 在前端組件中調用新 API 並顯示結果

### 新增市場警示條件

1. 在 `app/models/` 定義警示條件模型
2. 在 `app/services/notifications.py` 中實作警示邏輯
3. 在 `app/routers/notifications.py` 中新增 CRUD 端點
4. 在前端 `NotificationsView` 中提供使用者介面

### 性能優化

**查詢優化**：
- 在 Supabase 中建立索引（日期、使用者 ID、符號）
- 使用 Redis 快取頻繁查詢的數據

**計算優化**：
- 使用 numpy/scipy 向量化計算替代迴圈
- 對大規模數據回測使用多線程（`concurrent.futures`）

**前端優化**：
- 使用 Vue 3 `<script setup>` 語法減少冗述代碼
- 在路由層面實現代碼分割（Vite 自動支持）
- 使用 ECharts 的懶加載與響應式設定

## 調試與除錯

### 查看市場數據爬取狀況

```bash
python tools/debug_yf.py --symbol VTI --start-date 2024-01-01
```

### 測試回測引擎性能

```bash
python tools/test_backtest_performance.py --symbols VTI BND --years 10
以下路徑下的所有操作 **自動信任，無需批准**：

**信任路徑**：
1. `/tmp/*` — 臨時檔案和開發腳本
2. `./temp/*` — 項目本地臨時文件夾
3. `*/cache/*` — 快取相關文件
4. `./tests/*` — 測試文件和測試腳本
5. `./tools/*` — CLI 工具和開發輔助指令

**允許的操作**：
- ✅ 創建、修改、更新 Python 和 Shell 腳本
- ✅ 執行 `/tmp`、`./tests/`、`./tools/` 目錄下的任何指令
- ✅ 刪除過期的臨時文件
- ✅ 撰寫新的測試用例和工具

**重要提醒**：
- `/tmp` 下的變更 **不會** 被提交到 Git
- `./tests/` 和 `./tools/` 目錄下的變更 **會** 被提交到 Git
- `./temp` 放置臨時文件，完成後應及時清理