# 🛡️ 管理者管理介面 (Admin Management Interface)

**建立日期**：2026年4月1日  
**狀態**：📝 待實作  
**優先度**：高  

---

## 📋 功能需求概覽

新增一套後端 + 前端的管理者 (Admin) 專用介面，讓具備管理員身份的使用者可以進行系統層級的操作與監控。

---

## 🔐 1. 管理員認證與權限

### 需求說明
- 在 `users` 資料表中新增 `is_admin` 欄位（Boolean，預設 `false`）
- 管理員 JWT 中須包含 `is_admin: true` 的 Claim
- 後端所有管理員 API 須透過 `require_admin` 依賴注入進行身份驗證

### 資料庫變更
```sql
ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT false;
```

### 後端實作
- 新增 `app/security/admin_guard.py`：實作 `require_admin()` 依賴函數
- 在 `app/routers/auth.py` 的 `/api/auth/login` 中，將 `is_admin` 欄位納入 JWT payload

---

## 👤 2. 使用者管理 (User Management)

### 功能列表
| 功能 | HTTP 方法 | 端點 |
|------|-----------|------|
| 列出所有使用者 | GET | `/api/admin/users` |
| 取得單一使用者詳情 | GET | `/api/admin/users/{user_id}` |
| 封鎖 / 解封使用者 | PATCH | `/api/admin/users/{user_id}/status` |
| 刪除使用者 | DELETE | `/api/admin/users/{user_id}` |
| 賦予 / 撤銷管理員權限 | PATCH | `/api/admin/users/{user_id}/role` |

### 刪除使用者 — 連動刪除規則
**⚠️ 重要**：刪除使用者時，須連動移除其所有相關資料：
1. `tracked_indices`（追蹤指數）→ 對應 `user_id` 的所有記錄
2. `portfolios`（投資組合）→ 對應 `user_id` 的所有組合
3. `portfolio_holdings`（持倉明細）→ 透過 `portfolio_id` 串聯刪除
4. `backtest_results`（回測結果）→ 對應 `user_id` 的所有結果
5. `optimization_results`（優化結果）→ 對應 `user_id` 的所有結果
6. `user_preferences`（使用者偏好）→ 對應 `user_id` 的設定
7. `market_briefings`（AI 早報）→ 對應 `user_id` 的所有記錄

**建議使用 Supabase 的 `CASCADE` 外鍵約束**，確保資料完整性自動由資料庫層級保障。

詳見 → [`user_deletion_cascade.md`](./user_deletion_cascade.md)

### 前端元件
- 頁面：`frontend/src/views/admin/UserManagement.vue`
- 功能：使用者列表（分頁）、搜尋、篩選（狀態/角色）、操作按鈕（封鎖/刪除/升權）

---

## ⏰ 3. 排程任務管理 (Task Scheduling)

### 功能列表
| 功能 | HTTP 方法 | 端點 |
|------|-----------|------|
| 列出所有排程任務 | GET | `/api/admin/scheduler/jobs` |
| 立即觸發某任務 | POST | `/api/admin/scheduler/jobs/{job_id}/trigger` |
| 暫停某任務 | PATCH | `/api/admin/scheduler/jobs/{job_id}/pause` |
| 恢復某任務 | PATCH | `/api/admin/scheduler/jobs/{job_id}/resume` |

### 現有排程任務（APScheduler）
- `sync_tw_etf` — 台灣 ETF 每日資料同步
- `sync_us_etf` — 美股 ETF 每日資料同步
- `check_price_alerts` — 價格警報檢測
- `check_rsi_alerts` — RSI 警報檢測
- `generate_ai_briefing` — AI 市場早報生成（08:00/13:00/18:00）

### 後端實作
- 新增 `app/routers/admin.py` 中的 scheduler 管理端點
- 透過 APScheduler 的 `scheduler.get_jobs()` 取得任務清單
- 使用 `scheduler.pause_job(job_id)` / `scheduler.resume_job(job_id)` 控制任務

### 前端元件
- 頁面：`frontend/src/views/admin/SchedulerManagement.vue`
- 功能：任務列表（名稱、狀態、下次執行時間、上次執行時間）、手動觸發按鈕、暫停/恢復切換

---

## 📄 4. 日誌讀取 (Log Reading)

### 功能列表
| 功能 | HTTP 方法 | 端點 |
|------|-----------|------|
| 取得最新日誌（N 行） | GET | `/api/admin/logs?lines=100` |
| 取得特定等級日誌 | GET | `/api/admin/logs?level=ERROR` |
| 即時日誌串流（SSE） | GET | `/api/admin/logs/stream` |

### 日誌來源
- 後端應用程式日誌（`uvicorn` / `FastAPI logger`）
- PM2 process 日誌（`pm2 logs backend --nostream --lines N`）
- APScheduler 任務執行日誌

### 後端實作
- 在 `app/routers/admin.py` 中新增 `/api/admin/logs` 端點
- 讀取 `logs/` 目錄下的日誌文件（或執行 `pm2 logs` 子進程）
- 可選：使用 Server-Sent Events (SSE) 實作即時日誌串流

### 前端元件
- 頁面：`frontend/src/views/admin/LogViewer.vue`
- 功能：日誌等級篩選（INFO/WARNING/ERROR）、關鍵字搜尋、自動捲動、即時更新切換

---

## 📊 5. 系統概覽儀表板 (System Overview Dashboard)

> 選配功能，提升管理介面完整度

| 指標 | 說明 |
|------|------|
| 總使用者數 | 含活躍 / 封鎖使用者分布 |
| 今日新增使用者 | 24hr 內註冊數 |
| 追蹤指數總數 | 所有使用者的追蹤項目合計 |
| Redis 快取狀態 | Hit rate、記憶體使用量 |
| 今日 API 請求數 | 各端點請求統計 |
| 排程任務狀態 | 各任務最後執行結果 |

### 後端端點
- `GET /api/admin/stats` — 返回上述所有統計數據

### 前端元件
- 頁面：`frontend/src/views/admin/AdminDashboard.vue`

---

## 🗂️ 6. 前端路由與導航

### 新增路由（`frontend/src/router/index.js`）
```javascript
{
  path: '/admin',
  component: AdminLayout,
  meta: { requiresAdmin: true },
  children: [
    { path: '', redirect: '/admin/dashboard' },
    { path: 'dashboard', component: AdminDashboard },
    { path: 'users', component: UserManagement },
    { path: 'scheduler', component: SchedulerManagement },
    { path: 'logs', component: LogViewer }
  ]
}
```

### 導航守衛
- 在 `router/index.js` 中新增管理員路由守衛
- 若使用者 JWT 無 `is_admin: true` Claim，則重導向至 `403 Forbidden` 頁面

---

## 🗂️ 7. 後端檔案結構

```
backend/app/
├── routers/
│   └── admin.py          # 新增：所有管理員 API 路由
├── security/
│   └── admin_guard.py    # 新增：require_admin 依賴注入
└── services/
    └── admin_service.py  # 新增：管理員業務邏輯（統計、日誌讀取等）
```

---

## 🗂️ 8. 前端檔案結構

```
frontend/src/
├── views/
│   └── admin/
│       ├── AdminLayout.vue          # 新增：管理介面主佈局
│       ├── AdminDashboard.vue       # 新增：系統概覽
│       ├── UserManagement.vue       # 新增：使用者管理
│       ├── SchedulerManagement.vue  # 新增：排程任務管理
│       └── LogViewer.vue            # 新增：日誌讀取器
├── stores/
│   └── admin.js                     # 新增：Pinia admin store
└── api/
    └── admin.js                     # 新增：管理員 API 客戶端
```

---

## ✅ 實作檢查清單

### 後端
- [ ] `users` 資料表新增 `is_admin` 欄位（資料庫 migration）
- [ ] 更新 JWT 登入邏輯，納入 `is_admin` Claim
- [ ] 實作 `admin_guard.py` — `require_admin()` 依賴
- [ ] 實作 `app/routers/admin.py`：使用者管理、排程、日誌端點
- [ ] 使用者刪除時連動清除相關資料（詳見 `user_deletion_cascade.md`）
- [ ] 在 `app/main.py` 中註冊 admin router

### 前端
- [ ] 新增管理員路由守衛
- [ ] 實作 `AdminLayout.vue`（側邊欄導航）
- [ ] 實作 `AdminDashboard.vue`
- [ ] 實作 `UserManagement.vue`
- [ ] 實作 `SchedulerManagement.vue`
- [ ] 實作 `LogViewer.vue`
- [ ] 新增 `stores/admin.js` Pinia store
- [ ] 新增 `api/admin.js` API 客戶端

---

## 🔗 相關文件

- [`user_deletion_cascade.md`](./user_deletion_cascade.md) — 使用者刪除連動邏輯詳細設計
- [`future_plan.md`](./future_plan.md) — 整體功能藍圖
