# 🚀 Finance Dashboard - Code Review & Future Plan

**日期**：2026年3月26日  
**最後更新**：2026年3月27日  
**狀態**：📝 規劃中  

本文件基於對目前 `finance_dashboard` 專案（Vue 3 + FastAPI + Supabase + Redis）的架構與功能審查，提出系統優化建議與未來中長期的功能發展藍圖。

---

## 🔍 1. 現有架構 Code Review 與優化建議

### ✅ 優點 (Strengths)
1. **現代化科技棧**：前端使用 Vue 3 (Composition API) + Vite + Tailwind CSS，後端使用 FastAPI，效能與開發體驗佳。
2. **模組化設計**：後端嚴格遵循 `routers`, `services`, `models` 的分層架構，職責分離明確。
3. **快取機制優良**：廣泛使用 Redis 與 `fastapi-cache2` 來減少對外部 API（如 yfinance, TWSE）的頻繁請求，有效防止 Rate Limit。
4. **非同步整合**：使用了 `asyncio.gather` 進行併發抓取（例如在最佳化模組中），並且整合了 APScheduler 處理背景警報檢測。

### ⚠️ 潛在風險與優化方向 (Tech Debt & Improvements)
1. **外部 API 依賴過重 (Data Infrastructure)**：
   - **痛點**：目前高度依賴 `yfinance` 即時抓取歷史資料。這在進行大型回測 (Backtest) 或投組最佳化 (Optimize) 時，容易因為網路延遲或 Yahoo API 變更而失敗。
   - **建議**：建立**資料管線 (Data Pipeline)**。利用排程在每日收盤後，將台股與美股的 OHLCV 歷史日線資料定時寫入資料庫 (Supabase/PostgreSQL)。前端回測時直接讀取資料庫，大幅提升回測速度與穩定性。
2. **單點故障處理 (Error Handling)**：
   - **痛點**：在 `optimize.py` 等路由中，若部分標的抓取失敗會導致整個最佳化請求被拋棄或資料長度不齊。
   - **建議**：實作更彈性的資料對齊對齊邏輯 (Data Imputation/Forward Fill)，確保部分 API 失敗時系統仍能進行降級運作。
3. **測試覆蓋率 (Testing)**：
   - **建議**：由於這是一個涉及真實金融數據與警報的系統，強烈建議導入 Cypress 或 Playwright 進行 E2E 測試（尤其是警報設定、拖曳儀表板等核心交互），以及針對核心計算邏輯（例如 Markowitz 最佳化、技術指標計算）增加 Pytest 單元測試。

---

## 🎯 2. 未來功能發展藍圖 (Future Features Plan)

基於目前已有的「儀表板拖曳」、「回測」、「條件警報(價格/RSI)」、「投組最佳化」等功能，建議未來可朝以下幾個維度擴展：

### Phase 1: 核心體驗與交易管理提升 (Short-term)
1. **📦 真實投資組合追蹤 (Portfolio Tracker)**
   - **描述**：允許使用者輸入真實交易紀錄（買入/賣出日期、價格、股數）。
   - **功能**：計算每日未實現損益 (Unrealised PnL)、實現損益、總報酬率，並以圓餅圖顯示資產配置 (Asset Allocation)。可與目前的基準 (Benchmark) 進行走勢對比。
2. **📊 進階技術線圖與指標 (Advanced Charting & TA)**
   - **描述**：將單純的折線圖升級為 K線圖 (Candlestick Charts)。
   - **功能**：整合如 TradingView Lightweight Charts，並加入 MACD、Bollinger Bands、EMA/SMA 等技術指標，除了可視化也可作為新的警報觸發條件。

### Phase 2: 數據深度與篩選工具 (Medium-term)
3. **🔍 股票 / ETF 篩選器 (Stock Screener)**
   - **描述**：延伸目前的 `fundamentals.py`。
   - **功能**：提供一個篩選介面，讓使用者可以設定條件（例如：殖利率 > 5%、本益比 < 15、PB < 1.5），快速找出符合條件的台股或美股標的，並一鍵加入追蹤清單。
4. **📅 財報與除權息日曆 (Earnings & Dividend Calendar)**
   - **描述**：在前台新增日曆視圖。
   - **功能**：整合台股與美股的除權息日期、財報公佈日。可設定在除息日或財報公佈前一天透過 LINE 或 Email 發送提醒。

### Phase 3: 智慧化與社交化 (Long-term)
5. **🤖 AI 專屬市場分析師 (AI Market Briefing)**
   - **描述**：整合 Brave Search + Google Gemini API。
   - **功能**：系統每日於 **08:00、13:00、18:00（Asia/Taipei）** 自動排程，抓取使用者追蹤指數的 Top 3 最新新聞，利用 Gemini 1.5 Flash 生成繁體中文摘要，顯示於 Dashboard 可拖曳卡片。
   - **狀態**：✅ 已規劃 — 詳見 [`plan/feature-ai-briefing-1.md`](../../plan/feature-ai-briefing-1.md)
   - **技術設計**：
     - 後端新增 `services/brave_search_service.py`、`services/gemini_service.py`、`services/news_briefing_service.py`
     - 新增 `routers/briefing.py`（`GET /api/briefing/latest`、`POST /api/briefing/trigger`）
     - APScheduler 新增三條 cron job（08:00 / 13:00 / 18:00）
     - Supabase 新增 `market_briefings` 表（含 RLS）
     - 前端新增 `components/AIDailyBriefing.vue` 可拖曳卡片
     - **零新依賴**：直接使用現有 `httpx` 呼叫 Brave Search 與 Gemini REST API
6. **🔗 回測與投組分享功能 (Social Sharing)**
   - **描述**：讓使用者能將自己設定好的回測參數或最佳化投組公開。
   - **功能**：產生一個 Snapshot 唯讀連結（如 `finance.skynetapp.org/share/abc-123`），方便使用者在社群論壇上分享自己的投資策略與回報圖表。
7. **行動端優化 (PWA 支援)**
   - **描述**：將前端 Vue 專案轉換為 Progressive Web App (PWA)。
   - **功能**：讓使用者可以直接將此儀表板安裝至手機首頁，獲得近似原生 APP 的體驗，更方便隨時查看推播通知與投資組合。

---

## 📝 總結
目前的系統底層架構非常扎實，針對警報與即時資料抓取的整合也相當完整。下一步的最佳發力點在於**「降低對即時三方 API 的依賴（建立自有資料庫）」**，以及**「增加使用者黏著度（Portfolio Tracker 與 AI 早報）」**，這將使此系統從一個單純的報價看板，升級為一站式的個人化量化理財平台。
