#!/bin/bash

# --- PM2 部署腳本 ---
# 此腳本會自動偵測專案根目錄並執行部署

set -e

# 取得腳本所在目錄及專案根目錄
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"
cd "$PROJECT_ROOT"

echo "🚀 開始 PM2 部署流程... (專案根目錄: $PROJECT_ROOT)"

# 1. 檢查必要的工具
command -v pm2 >/dev/null 2>&1 || { echo "❌ 錯誤: 請先安裝 pm2 (npm install -g pm2)"; exit 1; }

# 2. 更新及編譯 Frontend
echo "📦 正在編譯 Frontend..."
cd frontend
npm install
npm run build
cd ..

# 3. 更新 Backend 依賴
echo "🐍 正在更新 Backend 依賴..."
./venv/bin/pip install -r backend/requirements.txt

# 4. 啟動/重啟服務
echo "🔄 正在透過 PM2 啟動服務..."
pm2 startOrReload ecosystem.config.js

# 5. 儲存 PM2 狀態 (防止伺服器重啟後失效)
pm2 save

echo "✅ 部署完成！"
echo "📊 輸入 'pm2 status' 查看運行狀態。"
echo "📍 Frontend: http://localhost:3100"
echo "📍 Backend API: http://localhost:8005/api/health"
