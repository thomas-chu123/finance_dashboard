# Finance Dashboard

Finance Dashboard 是一個全端的金融資料視覺化與分析平台，提供使用者投資組合回測、資產配置最佳化、以及即時市場數據監控等功能。

## 🎯 核心功能

- **投資組合回測 (Backtesting)**：以歷史資料自訂多種資產配置比例，進行投資總報酬、年化報酬率、最大回檔 (Max Drawdown) 等指標分析。
- **資產配置最佳化 (Portfolio Optimization)**：利用效率前緣 (Efficient Frontier) 等演算法，為使用者計算並推薦不同風險屬性下的最佳資產配置比例。
- **蒙地卡羅模擬 (Monte Carlo Simulation)**：對未來的投資報酬路徑進行多重模擬，評估達到特定財富目標的機率分佈。
- **即時通知與監控**：支援設定特定的市場條件警報。
- **個人投資組合管理**：提供使用者儲存並管理多個個人的投資組合策略，以便進行後續對比與追蹤。

## 🛠 技術堆疊 (Tech Stack)

### 前端 (Frontend)
- **核心**：Vue 3 
- **建置工具**：Vite
- **狀態管理**：Pinia
- **路由**：Vue Router
- **視覺化**：ECharts (vue-echarts)
- **樣式**：Tailwind CSS

### 後端 (Backend)
- **核心**：FastAPI (Python)
- **資料處理與數值運算**：Pandas, NumPy, SciPy
- **金融數據源**：yfinance
- **認證與資料庫**：Supabase
- **快取**：Redis (fastapi-cache2)
- **排程與非同步**：APScheduler

## 🚀 快速開始 (Getting Started)

### 先決條件 (Prerequisites)
確保您的開發環境中已安裝以下工具：
- Node.js (v18+)
- Python (v3.10+)
- Docker & Docker Compose (選用，強烈建議作為生產環境建置)
- Redis

### 環境變數設定

在專案根目錄中創建一個 `.env` 檔案，並填入必要的環境變數：
```env
# 範例 (請根據實際需求替換)
REDIS_URL=redis://localhost:6379/0
# ...
```

### 後端啟動 (Backend)

1. 進入 `backend` 目錄：
   ```bash
   cd backend
   ```
2. 建立並啟動虛擬環境 (Virtual Environment)：
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS / Linux
   # 或 venv\Scripts\activate # Windows
   ```
3. 安裝依賴套件：
   ```bash
   pip install -r requirements.txt
   ```
4. 啟動 FastAPI 服務：
   ```bash
   uvicorn main:app --reload --port 8005
   ```
   *伺服器將執行於 http://localhost:8005，Swagger API 文件可於 http://localhost:8005/docs 檢視。*

### 前端啟動 (Frontend)

1. 進入 `frontend` 目錄：
   ```bash
   cd frontend
   ```
2. 安裝依賴套件：
   ```bash
   npm install
   ```
3. 啟動開發伺服器：
   ```bash
   npm run dev
   ```
   *前端畫面預設可以透過 http://localhost:5173 或終端機提示的連結存取。*

### 使用 Docker 啟動 (Docker Compose)

如果您想一次性啟動所有服務（包含 Redis 快取、Frontend、Backend），您可以使用 Docker：

```bash
docker-compose up --build -d
```
上述指令將建立三個容器：
- `finance_redis`：(Port 6379)
- `finance_backend`：(Port 8005)
- `finance_frontend`：(Port 3100)

## 📁 專案架構 (Project Structure)

```text
finance_dashboard/
├── backend/          # FastAPI 後端目錄
├── frontend/         # Vue 3 前端目錄
├── docs/             # 專案說明文件
├── tests/            # 測試腳本
├── scripts/          # 部署與維護相關腳本
├── docker-compose.yml# 容器化部署設定
└── README.md         # 此文件
```

## 🤝 貢獻指南 (Contributing)

歡迎提交 Pull Request (PR) 或是建立 Issue 來改善我們的專案。
所有 git commit 訊息應以 **英文** 撰寫，遵循一般 Git Commit 規範 (如 feat, fix, docs 等前綴)。
