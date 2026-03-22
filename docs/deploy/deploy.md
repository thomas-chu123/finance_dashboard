# 佈署文件 (Deployment Documentation)

本文件說明 Finance Dashboard 的環境設定、佈署流程以及營運維護相關注意事項。

## 1. 設計概念 (Design Concepts)

*   **程序管理 (PM2)**: 使用 PM2 監管後端與前端程序。支援自動重新啟動、日誌輪轉以及多實例管理。
*   **環境隔離**: 透過 `.env` 檔案管理敏感資訊 (DB URL, API Key)，區分開發環境與生產環境。
*   **虛擬環境**: 後端運行於獨立的 Python venv，避免全域套件衝突。
*   **靜態資源服務**: 前端在生產環境中通過 Node.js 服務 (`server.cjs`) 提供 build 過的靜態資源。

## 2. 佈署流程 (Deploy Process)

1.  **環境準備**:
    *   後端：安裝 Python 3.10+，建立 venv 並安裝 `requirements.txt`。
    *   前端：安裝 Node.js 18+，執行 `npm install` 並建立生產環境 build。
2.  **資料庫設定**:
    *   於 Supabase 建立專案。
    *   執行必要的 SQL Schema 腳本 (由 `/docs/line_setup.sql` 等參考)。
3.  **環境變數**:
    *   設置 `backend/app/.env`。
    *   設置 `frontend/.env.production`。
4.  **啟動服務**:
    *   使用 `pm2 start ecosystem.config.js` 一次性啟動前後端。
5.  **驗證**:
    *   檢查 `pm2 logs` 確保無報錯資訊。
    *   檢查存取端口 (預設 Backend: 8005, Frontend: 3100)。

## 3. 注意事項 (Precautions)

*   **端口管理**: 如果在同一台機器上佈署，需確保 8005 與 3100 端口未被其他程序佔用。
*   **自動更新備份**: 應定期執行 `npm run build` 以確保前端反映最新修改。
*   **監控與告警**: 前端設有日誌轉發功能，定期檢查 `backend.log` 與 `frontend.log`。
*   **Python 路徑**: `ecosystem.config.js` 中需指定正確的 venv Python 路徑。
*   **CORS 設定**: 生產環境域名必須加入後端的 `allow_origins` 清單中。
