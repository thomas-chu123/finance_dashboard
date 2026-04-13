# Admin Panel - 後端技術文檔

## 目錄

- [概述](#概述)
- [架構設計](#架構設計)
- [API 端點](#api-端點)
- [數據模型](#數據模型)
- [認證與授權](#認證與授權)
- [日誌系統](#日誌系統)
- [環境配置](#環境配置)
- [部署指南](#部署指南)

---

## 概述

Admin Panel 後端提供完整的管理員管理功能，包括：

- **用戶管理** - 列表、編輯、刪除、密碼重設
- **統計監控** - 系統統計、用戶統計、警報統計
- **日誌查看** - 操作日誌、系統日誌、應用日誌
- **時程表管理** - Scheduler 任務監控和控制

---

## 架構設計

### 目錄結構

```
backend/app/
├── routers/
│   ├── admin.py              # Admin API 路由（700+ 行）
│   ├── auth.py
│   ├── market.py
│   ├── tracking.py
│   └── ...
├── services/
│   ├── audit_service.py      # 審計日誌服務
│   ├── scheduler_management.py  # Scheduler 管理服務
│   └── ...
├── models/
│   └── __init__.py           # Pydantic 數據模型
├── security.py               # 認證與授權
├── config.py                 # 配置管理
└── database.py               # Supabase 連接
```

### 分層架構

```
┌─────────────────────┐
│   FastAPI Router    │  (/api/admin/*)
├─────────────────────┤
│  Authentication     │  require_admin()
├─────────────────────┤
│     Services        │  AuditService, SchedulerManagementService
├─────────────────────┤
│    Supabase ORM     │  表查詢、資料操作
├─────────────────────┤
│   PostgreSQL        │  profiles, audit_logs, system_logs
└─────────────────────┘
```

---

## API 端點

### 認證

所有 Admin API 端點都需要：
1. **有效的 JWT Token**（Authorization header）
2. **管理員身份**（is_admin = true）

```bash
Authorization: Bearer <JWT_TOKEN>
```

### 用戶管理 API

#### 獲取用戶列表
```http
GET /api/admin/users?skip=0&limit=20
```

**返回**：
```json
[
  {
    "id": "user-id",
    "email": "user@example.com",
    "display_name": "User Name",
    "is_admin": false,
    "created_at": "2026-04-01T10:00:00+00:00"
  }
]
```

#### 獲取單個用戶
```http
GET /api/admin/users/{user_id}
```

#### 更新用戶
```http
PUT /api/admin/users/{user_id}

Body:
{
  "display_name": "New Name",
  "is_admin": false
}
```

#### 刪除用戶
```http
DELETE /api/admin/users/{user_id}
```

#### 重設密碼
```http
POST /api/admin/users/{user_id}/password

Body:
{
  "new_password": "new_secure_password"
}
```

#### 切換管理員狀態
```http
PUT /api/admin/users/{user_id}/admin
```

### 統計 API

#### 系統統計概覽
```http
GET /api/admin/stats/overview
```

**返回**：
```json
{
  "total_users_count": 50,
  "active_users_count": 25,
  "tracked_indices_count": 15,
  "alerts_sent_count": 120
}
```

#### 用戶統計
```http
GET /api/admin/stats/users
```

**返回**：
```json
{
  "today": 2,
  "week": 8,
  "month": 25
}
```

#### 警報統計
```http
GET /api/admin/stats/alerts
```

**返回**：
```json
{
  "sent_count": 150,
  "failed_count": 5
}
```

### 日誌 API

#### 審計日誌
```http
GET /api/admin/logs/audit?skip=0&limit=50&action=UPDATE
```

#### 系統日誌
```http
GET /api/admin/logs/system?skip=0&limit=100&level=ERROR&environment=development
```

#### 後端日誌
```http
GET /api/admin/logs/backend?lines=100
```

#### 提交前端日誌
```http
POST /api/admin/logs/frontend

Body:
{
  "level": "error",
  "component": "Dashboard",
  "message": "Failed to fetch data",
  "timestamp": "2026-04-01T10:00:00Z"
}
```

---

## 數據模型

### AdminUserResponse
```python
class AdminUserResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str]
    is_admin: bool
    created_at: str
```

### SystemStatsOverviewResponse
```python
class SystemStatsOverviewResponse(BaseModel):
    total_users_count: int
    active_users_count: int
    tracked_indices_count: int
    alerts_sent_count: int
```

### AuditLogResponse
```python
class AuditLogResponse(BaseModel):
    id: str
    user_id: str
    action: str  # CREATE, UPDATE, DELETE
    resource_type: str  # user, portfolio, etc.
    resource_id: str
    changes: dict
    created_at: str
```

---

## 認證與授權

### 認證流程

1. **用戶登入** → `/api/auth/login`
2. **獲得 JWT Token**
3. **請求 Admin API** → `Authorization: Bearer <token>`
4. **中間件驗證** → `require_admin()` 依賴注入

### require_admin() 函數

```python
async def require_admin(authorization: str = Header(None)) -> str:
    """驗證 Admin 身份"""
    if not authorization:
        raise HTTPException(status_code=401)
    
    token = authorization.replace("Bearer ", "")
    payload = verify_jwt_token(token)
    admin_id = payload.get("sub")
    
    # 檢查 is_admin 標誌
    is_admin = check_user_is_admin(admin_id)
    if not is_admin:
        raise HTTPException(status_code=403)
    
    return admin_id
```

### RLS (Row Level Security) 策略

所有表都配置了 RLS 策略：

```sql
-- audit_logs 表 RLS
CREATE POLICY "Admin only" ON audit_logs
  USING (EXISTS(
    SELECT 1 FROM profiles
    WHERE profiles.id = auth.uid()
    AND profiles.is_admin = true
  ))
```

---

## 日誌系統

### 環境追蹤

所有日誌自動記錄環境信息：

```json
{
  "message": "User login",
  "level": "INFO",
  "component": "auth",
  "environment": "development",  // development|production
  "hostname": "local-machine",
  "created_at": "2026-04-01T10:00:00+00:00"
}
```

### 日誌查詢過濾

```http
GET /api/admin/logs/system?environment=production&level=ERROR
```

支持過濾：
- `environment` - 開發/生產環境
- `level` - DEBUG, INFO, WARNING, ERROR
- `component` - frontend, backend, scheduler
- `skip` / `limit` - 分頁

### ANSI 顏色碼處理

後端保留原始 ANSI 顏色碼，前端負責轉換為 HTML：

```
原始：\x1b[31mERROR\x1b[0m: Something failed
HTML：<span style="color: #ff4444">ERROR</span>: Something failed
```

---

## 環境配置

### .env 設置

```env
# 環境識別
ENVIRONMENT=development  # development | production

# Supabase
SUPABASE_URL=https://...
SUPABASE_SERVICE_ROLE_KEY=...

# 應用設置
DEBUG=0
SECRET_KEY=your-secret-key
```

### 配置讀取

```python
from app.config import get_settings

settings = get_settings()
print(settings.environment)  # 'development'
```

---

## 部署指南

### 開發環境

```bash
cd backend
pip install -r requirements.txt

# 設置 .env
ENVIRONMENT=development

# 運行
uvicorn app.main:app --reload --port 8000
```

### 生產環境

```bash
# 服務器 .env
ENVIRONMENT=production
SUPABASE_URL=<production-url>
SECRET_KEY=<strong-key>

# PM2 部署
pm2 start ecosystem.config.js --only finance-backend
pm2 save
```

### 數據庫遷移

```bash
# 應用遷移到 Supabase
psql postgresql://... -f /path/to/20260401_admin_system.sql
```

---

## 故障排除

### 403 Forbidden

**原因**：用戶不是管理員
**解決**：
```sql
UPDATE profiles SET is_admin = true WHERE id = 'user-id';
```

### 500 系統統計失敗

**原因**：未來自動創建 `last_login_at` 欄位
**解決**：使用警報記錄計算活躍用戶

### 日誌為空

**原因**：PM2 日誌路徑不存在
**解決**：使用 Supabase `system_logs` 表

---

## 測試

### 執行單元測試

```bash
pytest tests/unit/test_admin_api.py -v
```

### 執行集成測試

```bash
pytest tests/e2e/test_admin_api_integration.py -v
```

### 測試覆蓋率

```bash
pytest tests/ --cov=app --cov-report=html
```

---

## 相關資源

- [前端文檔](../frontend/frontend.md)
- [部署指南](./deploy.md)
- [API 規範](../../.github/copilot-instructions.md)
