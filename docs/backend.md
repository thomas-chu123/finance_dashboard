# 後端開發文件 (Backend Documentation)

本文件說明 Finance Dashboard 後端 API 服務的設計架構、運作流程、主要功能模組以及技術注意事項。

## 1. 設計概念 (Design Concepts)

*   **FastAPI 框架**: 使用非同步 Python 框架 FastAPI，提供高效能且具備自動化 OpenAPI 文件 (Swagger) 的支援。
*   **模組化服務**: 核心邏輯 (計算引擎、外部數據獲取) 拆分為獨立的 Service 模組，易於維護與擴展。
*   **Supabase 整合**: 使用 Supabase 作為 PostgreSQL 資料庫及身份驗證後端，簡化資料持久化與使用者管理。
*   **計算引擎隔離**: 回測 (Backtest) 與優化 (Optimization) 邏輯完全解耦，可支援多種不同的演算法。
*   **快取機制**: 整合 Redis 或記憶體內快取，減少重複性高且耗時的金融數據請求。

## 2. 運作流程 (Process)

1.  **請求驗證**: 所有需要授權的 API 都會透過相依性注入 (Dependency Injection) 驗證 JWT 持有者身份。
2.  **路由轉發**: 根據請求類型路由至對應的模組 (如 `backtest.py`, `optimize.py`)。
3.  **數據準備**: 由 `market_data.py` 向外部來源 (Yahoo Finance, FinMind) 獲取最新或歷史數據。
4.  **邏輯運算**: 引擎根據輸入參數執行複雜的金融計算 (如年化報酬率、Max Drawdown、共變異矩陣)。
5.  **同步/異步任務**: 使用 `BackgroundTasks` 處理耗時的 ETF 清單同步。
6.  **結果回傳**: 回傳符合前端預期的 JSON 格式，並附帶正確的 HTTP 狀態碼。

## 3. 主要 API 模組 (Main API Modules)

*   `app.routers.auth`: 身份驗證邏輯封裝。
*   `app.routers.backtest`: 提供投資組合回測功能。
*   `app.routers.optimize`: 投資組合權重優化與效率前緣計算。
*   `app.routers.market`: 即時市場數據獲取。
*   `app.routers.tracking`: 使用者追蹤標的管理。

## 4. 注意事項 (Precautions)

*   **API 頻率限制**: 頻繁呼叫 Yahoo Finance 或 FinMind 可能導致封包被封鎖，必須合理使用快取。
*   **金融精確率**: 在處理利潤與比例計算時，應留意浮點數偏差问题，必要時使用 `Decimal`。
*   **資料庫存取**: 使用 Supabase 管理 RLS (Row Level Security)，確保使用者只能存取自身數據。
*   **擴展性**: 當使用者增長時，後端應考慮將計算任務遷移至 Celery 等職責更重的工作隊列。
