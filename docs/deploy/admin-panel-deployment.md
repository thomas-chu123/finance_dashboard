# Admin Panel 部署指南

## 目錄

- [概述](#概述)
- [前置條件](#前置條件)
- [開發環境部署](#開發環境部署)
- [生產環境部署](#生產環境部署)
- [環境配置](#環境配置)
- [驗證與測試](#驗證與測試)
- [故障排除](#故障排除)
- [監控與維護](#監控與維護)

---

## 概述

本指南涵蓋 **Admin Panel** 在開發和生產環境中的完整部署流程。

### 架構概覽

```
┌──────────────────┐
│   Nginx/Caddy    │  Web 服務器
├──────────────────┤
│   FastAPI        │  後端 API（/api/admin/*)
├──────────────────┤
│   Supabase       │  數據庫 + 認證
│   Redis          │  快取
└──────────────────┘

┌──────────────────┐
│   Vue 3 Frontend │  前端應用（Admin Panel）
├──────────────────┤
│   npm build      │  靜態資源（HTML/CSS/JS）
└──────────────────┘
```

---

## 前置條件

### 系統要求

- **Node.js** ≥ 18.0（前端）
- **Python** ≥ 3.10（後端）
- **PostgreSQL** ≥ 14（Supabase）
- **Redis** ≥ 6.0（快取層）

### 帳號與憑證

- ✅ Supabase 項目 URL
- ✅ Supabase anon key
- ✅ Supabase service role key
- ✅ SSH 金鑰（若使用自託管）

### 依賴檢查

```bash
# 檢查 Node.js
node --version  # v18+

# 檢查 Python
python3 --version  # 3.10+

# 檢查 npm
npm --version  # 8+

# 檢查 PostgreSQL 客戶端
psql --version  # 14+
```

---

## 開發環境部署

### 1. 後端設置

```bash
# 進入後端目錄
cd backend

# 建立虛擬環境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# 安裝依賴
pip install -r requirements.txt

# 配置 .env 檔案
cat > .env << EOF
# 環境
ENVIRONMENT=development

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# 應用設定
SECRET_KEY=your-secret-key-min-32-chars
DEBUG=1
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Redis
REDIS_URL=redis://localhost:6379/0
EOF

# 應用數據庫遷移（如有）
# psql postgresql://... -f /path/to/migrations.sql

# 啟動後端
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**驗證後端**：
```bash
curl http://localhost:8000/api/health
# 返回: {"status": "healthy"}
```

### 2. 前端設置

```bash
# 進入前端目錄
cd frontend

# 安裝依賴
npm install

# 配置 .env.development
cat > .env.development << EOF
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_ENV=development
EOF

# 啟動開發伺服器
npm run dev
```

**訪問前端**：
```
http://localhost:5173
```

### 3. Redis 設置（開發）

```bash
# 使用 Docker 快速啟動
docker run -d -p 6379:6379 redis:latest

# 或本地安裝
brew install redis  # macOS
sudo apt-get install redis  # Ubuntu

# 驗證 Redis
redis-cli ping
# 返回: PONG
```

### 4. 驗證整合

```bash
# 後端健康檢查
curl http://localhost:8000/api/health

# 前端健康檢查
curl http://localhost:5173

# 數據庫連接
python3 << EOF
from app.config import get_settings
from app.database import get_supabase_client

settings = get_settings()
client = get_supabase_client()
result = client.table("profiles").select("count").limit(1).execute()
print(f"Database connected: {result}")
EOF
```

---

## 生產環境部署

### 1. 服務器準備

```bash
# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝系統依賴
sudo apt install -y \
  python3.11 \
  python3-pip \
  nodejs \
  npm \
  postgresql-client \
  redis-server \
  nginx \
  git \
  curl

# 安裝 PM2（進程管理）
sudo npm install -g pm2
```

### 2. 克隆與配置

```bash
# 克隆倉庫
git clone https://github.com/your-org/finance_dashboard.git
cd finance_dashboard

# 後端配置
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 生產 .env
cat > .env << EOF
ENVIRONMENT=production
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=${SUPABASE_KEY}
SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
SECRET_KEY=${SECRET_KEY}
DEBUG=0
CORS_ORIGINS=https://yourdomain.com
REDIS_URL=redis://localhost:6379/0
EOF

cd ../frontend
npm install
npm run build  # 構建生產版本
```

### 3. PM2 配置

```javascript
// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: 'finance-backend',
      script: 'uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port 8000',
      cwd: './backend',
      env: {
        NODE_ENV: 'production'
      },
      instances: 2,
      exec_mode: 'cluster',
      max_memory_restart: '1G',
      merge_logs: true,
      out_file: './logs/backend.log',
      error_file: './logs/backend-error.log'
    },
    {
      name: 'finance-frontend',
      script: 'npm',
      args: 'run preview',
      cwd: './frontend',
      instances: 1,
      max_memory_restart: '512M',
      merge_logs: true,
      out_file: './logs/frontend.log'
    }
  ]
};
```

### 4. Nginx 反向代理

```nginx
# /etc/nginx/sites-available/finance-dashboard
upstream backend {
  server localhost:8000;
}

upstream frontend {
  server localhost:5173;
}

server {
  listen 80;
  server_name yourdomain.com;

  # 重定向到 HTTPS
  return 301 https://$server_name$request_uri;
}

server {
  listen 443 ssl http2;
  server_name yourdomain.com;

  ssl_certificate /path/to/cert.pem;
  ssl_certificate_key /path/to/key.pem;

  # 前端靜態資源
  root /var/www/finance_dashboard/frontend/dist;

  # Admin API
  location /api/admin/ {
    proxy_pass http://backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 30s;
  }

  # 其他 API
  location /api/ {
    proxy_pass http://backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }

  # 前端應用
  location / {
    try_files $uri $uri/ /index.html;
  }

  # 日誌
  access_log /var/log/nginx/finance-access.log;
  error_log /var/log/nginx/finance-error.log;
}
```

### 5. 啟動服務

```bash
# 配置 Nginx
sudo ln -s /etc/nginx/sites-available/finance-dashboard \
           /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 啟動應用
cd /var/www/finance_dashboard
pm2 start ecosystem.config.js
pm2 save
pm2 startup

# 啟動 Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 驗證
curl https://yourdomain.com/api/health
```

---

## 環境配置

### 後端 .env 參數

```env
# 必需
ENVIRONMENT=production
SUPABASE_URL=https://...supabase.co
SUPABASE_KEY=eyJ...  # anon key
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SECRET_KEY=your-secret-key-32-chars-min

# 可選
DEBUG=0
CORS_ORIGINS=https://yourdomain.com
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
```

### 前端 .env.production

```env
VITE_API_BASE_URL=https://yourdomain.com
VITE_APP_ENV=production
VITE_ENABLE_ANALYTICS=true
```

### 環境變數驗證

```python
# backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    environment: str = "development"
    supabase_url: str
    supabase_key: str
    secret_key: str
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# 驗證
settings = Settings()
assert settings.supabase_url  # 必需
assert settings.secret_key    # 必需
```

---

## 驗證與測試

### 1. 後端驗證

```bash
# 健康檢查
curl https://yourdomain.com/api/health

# Admin API 認證測試
curl -H "Authorization: Bearer $JWT_TOKEN" \
     https://yourdomain.com/api/admin/users

# 統計端點
curl -H "Authorization: Bearer $JWT_TOKEN" \
     https://yourdomain.com/api/admin/stats/overview
```

### 2. 前端驗證

```bash
# 訪問 Admin Panel
https://yourdomain.com

# 檢查控制台
# 在瀏覽器 DevTools > Console 查看錯誤
```

### 3. 執行測試套件

```bash
# 後端單元測試
cd backend
pytest tests/unit/test_admin_api.py -v

# 後端集成測試
pytest tests/e2e/test_admin_api_integration.py -v

# 前端組件測試
cd ../frontend
npm run test:unit
```

### 4. 性能測試

```bash
# 負載測試
ab -n 1000 -c 10 https://yourdomain.com/api/health

# 查看 PM2 監控
pm2 monit
```

---

## 故障排除

### 問題 1：Admin API 返回 403 Forbidden

**症狀**：HTTP 403，權限被拒

**解決**：
```bash
# 檢查用戶是否為管理員
psql postgresql://... << EOF
SELECT id, email, is_admin FROM profiles WHERE email = 'user@example.com';
UPDATE profiles SET is_admin = true WHERE email = 'user@example.com';
EOF

# 重新登入獲取新 Token
```

### 問題 2：日誌無法載入

**症狀**：日誌頁面為空或報錯

**解決**：
```bash
# 檢查 PM2 日誌路徑
pm2 logs backend

# 確認日誌文件存在
ls -la logs/

# 檢查 system_logs 表
psql postgresql://... << EOF
SELECT COUNT(*) FROM system_logs;
SELECT * FROM system_logs ORDER BY created_at DESC LIMIT 5;
EOF
```

### 問題 3：CORS 錯誤

**症狀**：前端無法調用 API，瀏覽器顯示 CORS 錯誤

**解決**：
```bash
# 檢查後端 CORS 配置
cat backend/.env | grep CORS_ORIGINS

# 更新為正確的域名
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
```

### 問題 4：Redis 連接失敗

**症狀**：後端日誌："Redis connection error"

**解決**：
```bash
# 驗證 Redis 運行
redis-cli ping

# 檢查 Redis 連接字符串
echo $REDIS_URL  # 應為 redis://localhost:6379/0

# 重啟 Redis
sudo systemctl restart redis-server
```

### 問題 5：數據庫遷移失敗

**症狀**：部署時報告遷移失敗

**解決**：
```bash
# 手動應用遷移
psql postgresql://user:password@db:5432/dbname \
  -f /path/to/migrations.sql

# 驗證表存在
\dt system_logs
```

---

## 監控與維護

### 1. PM2 監控

```bash
# 查看進程狀態
pm2 list

# 實時監控
pm2 monit

# 查看日誌
pm2 logs backend     # 後端日誌
pm2 logs frontend    # 前端日誌

# 重啟應用
pm2 restart all
pm2 reload all       # 優雅重啟

# 停止應用
pm2 stop all
```

### 2. 日誌管理

```bash
# 查看後端日誌
tail -f logs/backend.log

# 查看 Nginx 日誌
tail -f /var/log/nginx/finance-access.log
tail -f /var/log/nginx/finance-error.log

# 清理過期日誌
find logs/ -name "*.log" -mtime +30 -delete
```

### 3. 性能監控

```bash
# 檢查系統資源
pm2 monit

# 監控 Redis
redis-cli info stats
redis-cli dbsize

# 監控數據庫
# 在 Supabase 儀表板檢查連接數和查詢性能
```

### 4. 定期備份

```bash
# 備份數據庫
pg_dump postgresql://user:password@db:5432/dbname > backup.sql

# 設置 Cron 自動備份
0 2 * * * pg_dump postgresql://... > /backups/db-$(date +\%Y\%m\%d).sql
```

### 5. 安全檢查

```bash
# 檢查 JWT Secret 強度（至少 32 字符）
echo -n "$SECRET_KEY" | wc -c

# 驗證 HTTPS 配置
curl -I https://yourdomain.com

# 檢查安全頭部
curl -I https://yourdomain.com | grep -E "X-Frame|X-Content|Strict"
```

---

## 升級與更新

### 1. 後端升級

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 測試
pytest tests/ -v

# 部署
pm2 restart finance-backend
```

### 2. 前端升級

```bash
cd frontend
npm install
npm run build

# PM2 自動熱加載
pm2 reload finance-frontend
```

### 3. 數據庫升級

```bash
# 應用遷移
psql postgresql://... -f migrations/new_migration.sql

# 驗證
psql postgresql://... -l  # 列出表
```

---

## 相關資源

| 資源 | 連結 |
|------|------|
| 技術文檔 | [後端](./backend/admin-panel.md) / [前端](./frontend/admin-panel.md) |
| 用戶指南 | [Admin Panel 用戶指南](./admin-panel-user-guide.md) |
| API 規範 | [Copilot 指引](./.github/copilot-instructions.md) |

---

**最後更新**：2026-04-01  
**作者**：DevOps Team  
**版本**：1.0
