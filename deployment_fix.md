# 部署修復步驟

## 問題分析
- 前端生產環境缺少 `.env.production` → 使用本地 localhost URL
- 後端 CORS 設定基於舊的 `.env` 配置
- 生成圖片時 CORS 被阻擋

## 修復內容

### 1. ✅ 前端環境配置
- 新增 `.env.production`：`VITE_API_BASE_URL=https://webhook.skynetapp.org/api`

### 2. ✅ 後端環境配置  
- 更新 `.env`：
  - `APP_BASE_URL=https://finance.skynetapp.org`
  - `BACKEND_BASE_URL=https://webhook.skynetapp.org`
- 更新 CORS 頭部支持：添加 `Content-Type`

### 3. 部署步驟（在遠端伺服器執行）

#### 步驟 1：拉取最新代碼
\`\`\`bash
cd /path/to/finance_dashboard
git pull origin dev
\`\`\`

#### 步驟 2：重新構建前端
\`\`\`bash
cd frontend
npm ci  # 或 npm install --legacy-peer-deps
npm run build  # 構建成 dist/
\`\`\`

#### 步驟 3：重啟後端服務
\`\`\`bash
# 如果使用 PM2
pm2 restart backend

# 或重新啟動
pm2 delete backend
cd /path/to/finance_dashboard/backend
uvicorn app.main:app --host 0.0.0.0 --port 8005
\`\`\`

#### 步驟 4：驗證部署
- 檢查後端日誌是否顯示新 CORS 配置：
  \`\`\`
  Allowed CORS origins: [..., 'https://finance.skynetapp.org']
  \`\`\`
- 在 https://finance.skynetapp.org 中嘗試生成分享圖片

## CORS 流程
1. 前端 (https://finance.skynetapp.org) 發送 OPTIONS preflight 請求
2. 後端檢查 Origin: https://finance.skynetapp.org
3. 驗證列表包含此 origin → 返回 CORS headers
4. 前端收到 CORS 許可 → 發送 POST 上傳圖片
