# 前端開發文件 (Frontend Documentation)

本文件說明 Finance Dashboard 前端專案的設計概念、運作流程、主要 API 交互以及開發注意事項。

## 1. 設計概念 (Design Concepts)

*   **SPA 架構**: 使用 Vue 3 組合式 API (Composition API) 構建的單頁應用程式 (Single Page Application)。
*   **響應式設計**: 採用 Tailwind CSS (v4) 進行開發，確保在桌面端與行動端皆有良好的使用者體驗。
*   **深色模式優先**: 以深色調為核心設計，提供高級感且適合長時間監控金融數據。
*   **互動式圖表**: 使用 Apache ECharts (透過 `vue-echarts`) 呈現複雜的金融歷史數據與資產分配比例。
*   **狀態管理**: 使用 Pinia 處理使用者驗證狀態、資產列表及全局設定。

## 2. 運作流程 (Process)

1.  **使用者登入**: 透過 `/login` 頁面進行身份驗證，憑證儲存於 LocalStorage 並由 Pinia 管理。
2.  **路由保護**: 透過 `vue-router` 的全置守衛 (Navigation Guards) 確保僅已登入使用者可存取功能頁面。
3.  **數據存取**: 各視圖 (View) 元件掛載時，透過 Axios 向 Backend API 請求數據。
4.  **動態渲染**: 取得數據後，透過 Vue 的響應式系統更新 UI，並重新驅動 ECharts 圖表重繪。
5.  **即時監控**: Dashboard 會定期輪詢或接收最新的市場報價。

## 3. 主要 API 交互 (Main API Interaction)

前端透過自定義的 `api` 模組與後端進行通訊：

*   **Auth**: `POST /api/auth/login` - 取得 JWT Token。
*   **Tracking**: `GET /api/tracking/indices/active` - 取得目前追蹤的標的。
*   **Backtest**: `POST /api/backtest/run` - 傳送資產權重與時間區間進行回測計算。
*   **Optimize**: `POST /api/optimize/run` - 請求投資組合優化計算 (Markowitz Efficient Frontier)。
*   **Market**: `GET /api/market/quotes` - 取得熱門標的即時報價。

## 4. 注意事項 (Precautions)

*   **跨域問題 (CORS)**: 開發環境需確保 `VITE_API_BASE_URL` 與後端允許的 Origin 一致。
*   **圖表效能**: 當回測數據量大時 (數千個數據點)，應避免頻繁的重繪，善用 ECharts 的 `notMerge` 選項。
*   **環境變數**: 生產環境佈署前必須正確設定 `.env.production`。
*   **安全性**: 不要在前端儲存敏感資訊，僅保留運作所需的 JWT。
