---
goal: Admin Management Interface Implementation Plan
version: 1.0
date_created: 2026-04-01
last_updated: 2026-04-01
owner: Tech Team
status: 'Planned'
tags: ['feature', 'admin', 'management', 'security']
---

# 管理者管理介面實施計劃

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

本計劃旨在為 Finance Dashboard 添加完整的管理者管理介面，包含用戶管理、Scheduler 任務控制、日誌查看等功能。

## 1. 需求與約束

### 核心需求
- **REQ-001**: 實現管理者專用菜單項目「管理者功能」，僅對 is_admin=true 的使用者可見
- **REQ-002**: 建立用戶管理模組，支援編輯、刪除、修改密碼、修改名稱等操作
- **REQ-003**: **使用者刪除後，級聯刪除該使用者的所有追蹤指數**（tracked_indices）
- **REQ-004**: 實現 Scheduler 任務管理，支援手動開啟、關閉、執行 task
- **REQ-005**: 實現前後端日誌查看功能
- **REQ-006**: 提供其他建議的管理者功能（系統統計、審計日誌等）

### 安全需求
- **SEC-001**: 所有管理員操作都須檢查用戶 is_admin 狀態
- **SEC-002**: 敏感操作（刪除用戶、修改密碼）需要確認機制
- **SEC-003**: 所有管理操作需記錄在審計日誌中
- **SEC-004**: 禁止管理員刪除自己的帳號或自己移除自己的管理者權限
- **SEC-005**: 使用者刪除時，需級聯刪除其所有投資組合相關數據（portfolios、portfolio_holdings）

### 約束條件
- **CON-001**: 前端使用 Vue 3 Composition API，遵循現有項目風格
- **CON-002**: 後端使用 FastAPI，API 遵循 RESTful 規範
- **CON-003**: 資料庫操作透過 Supabase，遵循 RLS 原則
- **CON-004**: 所有代碼註釋使用繁體中文
- **CON-005**: Git commit message 使用英文，遵循 Conventional Commits

### 技術指南
- **PAT-001**: 認證檢查使用 get_user_id() 和 JWT token
- **PAT-002**: Supabase 操作使用 get_supabase() 實例
- **PAT-003**: 前端路由需在 meta 中標記需要管理員權限
- **PAT-004**: 級聯刪除必須遵循資料庫表的依賴關係：users → profiles → tracked_indices, portfolios, backtest_results, optimization_results 等

## 2. 實施步驟

### 實施階段 1: 資料庫與安全層擴展

**GOAL-001**: 擴展資料庫結構，支援審計日誌、Scheduler 狀態追蹤、級聯刪除機制

| Task | 描述 | 完成 | 日期 |
|------|------|------|------|
| TASK-001 | 在 Supabase 中創建 `audit_logs` 表（id, user_id, action, target_user_id, changes, created_at, ip_address） | | |
| TASK-002 | 在 Supabase 中創建 `scheduler_jobs` 表（id, job_id, job_name, description, schedule_cron, is_enabled, last_run_at, next_run_at, status, created_at） | | |
| TASK-003 | 在 Supabase 中創建 `system_logs` 表（id, level, component, message, stack_trace, created_at） | | |
| TASK-004 | 配置 RLS 策略：只有 is_admin=true 的使用者能存取 audit_logs、scheduler_jobs 和 system_logs | | |
| TASK-005 | 在 Supabase 中配置級聯刪除：DELETE profiles → DELETE tracked_indices（user_id）、DELETE portfolios、DELETE backtest_results、DELETE optimization_results、DELETE alert_logs | | |
| TASK-006 | 建立 `backend/app/services/audit_service.py`，實現審計日誌記錄功能 | | |
| TASK-007 | 在 `backend/app/security.py` 中添加 `require_admin()` 依賴注入函數 | | |

---

### 實施階段 2: 後端 API 開發

**GOAL-002**: 開發管理者管理 API 端點

#### Subphase 2A: 用戶管理 API
| Task | 描述 | 完成 | 日期 |
|------|------|------|------|
| TASK-008 | 擴展 `backend/app/models/__init__.py`，添加 UserManagementModel（user_id, email, display_name, is_admin, created_at, last_login） | | |
| TASK-009 | 擴展 `backend/app/models/__init__.py`，添加 PasswordChangeModel（old_password, new_password） | | |
| TASK-010 | 擴展 `backend/app/models/__init__.py`，添加 UserUpdateModel（display_name, is_admin） | | |
| TASK-011 | 在 `backend/app/routers/admin.py` 中實現 `GET /api/admin/users` — 列出所有使用者（分頁） | | |
| TASK-012 | 在 `backend/app/routers/admin.py` 中實現 `PUT /api/admin/users/{user_id}` — 編輯使用者資訊 | | |
| TASK-013 | 在 `backend/app/routers/admin.py` 中實現 `DELETE /api/admin/users/{user_id}` — 刪除使用者帳號及相關數據（級聯刪除） | | |
| TASK-014 | 在 `backend/app/routers/admin.py` 中實現 `POST /api/admin/users/{user_id}/password` — 重設使用者密碼 | | |
| TASK-015 | 在 `backend/app/routers/admin.py` 中實現 `PUT /api/admin/users/{user_id}/admin` — 升級/降級管理員權限 | | |
| TASK-016 | 在 `backend/app/routers/admin.py` 中實現 `GET /api/admin/users/{user_id}/activity` — 查看使用者活動日誌 | | |

#### Subphase 2B: Scheduler 管理 API
| Task | 描述 | 完成 | 日期 |
|------|------|------|------|
| TASK-017 | 在 `backend/app/services/scheduler_management.py` 中實現 `get_all_jobs()` — 列出所有 scheduler 任務 | | |
| TASK-018 | 在 `backend/app/services/scheduler_management.py` 中實現 `get_job(job_id)` — 獲取特定任務詳情 | | |
| TASK-019 | 在 `backend/app/services/scheduler_management.py` 中實現 `pause_job(job_id)` — 暫停任務 | | |
| TASK-020 | 在 `backend/app/services/scheduler_management.py` 中實現 `resume_job(job_id)` — 恢復任務 | | |
| TASK-021 | 在 `backend/app/services/scheduler_management.py` 中實現 `execute_job_now(job_id)` — 立即執行任務（異步） | | |
| TASK-022 | 在 `backend/app/routers/admin.py` 中實現 `GET /api/admin/scheduler/jobs` — 列出所有 scheduler 任務 | | |
| TASK-023 | 在 `backend/app/routers/admin.py` 中實現 `PUT /api/admin/scheduler/jobs/{job_id}/pause` — 暫停任務 | | |
| TASK-024 | 在 `backend/app/routers/admin.py` 中實現 `PUT /api/admin/scheduler/jobs/{job_id}/resume` — 恢復任務 | | |
| TASK-025 | 在 `backend/app/routers/admin.py` 中實現 `POST /api/admin/scheduler/jobs/{job_id}/execute` — 立即執行任務 | | |
| TASK-026 | 在 `backend/app/routers/admin.py` 中實現 `GET /api/admin/scheduler/jobs/{job_id}/history` — 查看任務執行歷史 | | |

#### Subphase 2C: 日誌管理 API
| Task | 描述 | 完成 | 日期 |
|------|------|------|------|
| TASK-027 | 在 `backend/app/routers/admin.py` 中實現 `GET /api/admin/logs/audit` — 查看審計日誌（分頁） | | |
| TASK-028 | 在 `backend/app/routers/admin.py` 中實現 `GET /api/admin/logs/system` — 查看系統日誌（實時） | | |
| TASK-029 | 在 `backend/app/routers/admin.py` 中實現 `GET /api/admin/logs/backend` — 讀取後端日誌檔案（tail -f）| | |
| TASK-030 | 在 `backend/app/routers/admin.py` 中實現 `GET /api/admin/logs/frontend` — 讀取前端日誌（從瀏覽器提交） | | |

#### Subphase 2D: 系統監控 API
| Task | 描述 | 完成 | 日期 |
|------|------|------|------|
| TASK-031 | 在 `backend/app/routers/admin.py` 中實現 `GET /api/admin/stats/overview` — 系統概覽（用戶數、活躍用戶、任務狀態） | | |
| TASK-032 | 在 `backend/app/routers/admin.py` 中實現 `GET /api/admin/stats/users` — 用戶統計（按創建日期、登入統計） | | |
| TASK-033 | 在 `backend/app/routers/admin.py` 中實現 `GET /api/admin/stats/alerts` — 警報統計（已發送、失敗） | | |

---

### 實施階段 3: 前端菜單與頁面結構

**GOAL-003**: 構建前端管理介面框架

| Task | 描述 | 完成 | 日期 |
|------|------|------|------|
| TASK-034 | 在 `frontend/src/router/index.js` 中添加管理員路由組（meta: requiresAdmin: true） | | |
| TASK-035 | 在 `frontend/src/router/index.js` 中添加子路由：admin, admin-users, admin-scheduler, admin-logs, admin-stats | | |
| TASK-036 | 在 `frontend/src/views/LayoutView.vue` 中添加「管理者功能」菜單區塊（條件顯示 is_admin） | | |
| TASK-037 | 在 `frontend/src/views/LayoutView.vue` 中的「管理者功能」區塊添加 4 個菜單項（用戶管理、時程表、日誌查看、系統監控） | | |
| TASK-038 | 建立 `frontend/src/views/AdminPanelView.vue` — 管理者主頁面（導航、權限檢查） | | |
| TASK-039 | 建立 `frontend/src/views/AdminUsersView.vue` — 用戶管理頁面 | | |
| TASK-040 | 建立 `frontend/src/views/AdminSchedulerView.vue` — Scheduler 管理頁面 | | |
| TASK-041 | 建立 `frontend/src/views/AdminLogsView.vue` — 日誌查看頁面 | | |
| TASK-042 | 建立 `frontend/src/views/AdminStatsView.vue` — 系統監控頁面 | | |

---

### 實施階段 4: 前端組件開發

**GOAL-004**: 開發可複用的管理介面組件

| Task | 描述 | 完成 | 日期 |
|------|------|------|------|
| TASK-043 | 建立 `frontend/src/components/admin/UserList.vue` — 使用者列表（表格、搜尋、分頁） | | |
| TASK-044 | 建立 `frontend/src/components/admin/UserEditModal.vue` — 編輯用戶模態框 | | |
| TASK-045 | 建立 `frontend/src/components/admin/UserDeleteConfirm.vue` — 刪除確認對話框（警告級聯刪除） | | |
| TASK-046 | 建立 `frontend/src/components/admin/PasswordResetModal.vue` — 密碼重設模態框 | | |
| TASK-047 | 建立 `frontend/src/components/admin/SchedulerTable.vue` — Scheduler 任務表格 | | |
| TASK-048 | 建立 `frontend/src/components/admin/SchedulerJobDetail.vue` — 任務詳情卡片 | | |
| TASK-049 | 建立 `frontend/src/components/admin/LogViewer.vue` — 日誌查看器（支援日誌級別篩選） | | |
| TASK-050 | 建立 `frontend/src/components/admin/SystemStats.vue` — 系統統計卡片 | | |
| TASK-051 | 建立 `frontend/src/components/common/AdminOnly.vue` — 管理員權限檢查包裝組件 | | |

---

### 實施階段 5: 前端 API 客戶端與狀態管理

**GOAL-005**: 建立前端 API 通信層和狀態管理

| Task | 描述 | 完成 | 日期 |
|------|------|------|------|
| TASK-052 | 建立 `frontend/src/api/admin-api.js` — 後端 admin API 客戶端 | | |
| TASK-053 | 建立 `frontend/src/stores/admin.js` — Pinia admin store（用戶、任務、日誌、統計） | | |
| TASK-054 | 在 `frontend/src/stores/auth.js` 中添加 is_admin 檢查函數 | | |
| TASK-055 | 建立 `frontend/src/composables/useAdmin.js` — 複用管理功能 | | |
| TASK-056 | 建立 `frontend/src/composables/useAdminAuth.js` — 管理員權限檢查 composable | | |

---

### 實施階段 6: 整合、測試與文檔

**GOAL-006**: 測試、優化與文檔編寫

| Task | 描述 | 完成 | 日期 |
|------|------|------|------|
| TASK-057 | 編寫後端單元測試：`tests/unit/test_admin_users.py`（含級聯刪除測試） | | |
| TASK-058 | 編寫後端單元測試：`tests/unit/test_admin_scheduler.py` | | |
| TASK-059 | 編寫後端單元測試：`tests/unit/test_audit_service.py` | | |
| TASK-060 | 編寫前端單元測試：`tests/unit/test_admin_store.js` | | |
| TASK-061 | 編寫端到端測試：`tests/e2e/test_admin_api.py`（含級聯刪除驗證） | | |
| TASK-062 | 編寫前端 E2E 測試：`tests/e2e/test_admin_ui.js` | | |
| TASK-063 | 更新 `/docs/admin-panel.md` — 管理者功能文檔 | | |
| TASK-064 | 更新 `/docs/backend/backend.md` — 新增 admin API 端點說明 | | |
| TASK-065 | 更新 `/docs/frontend/frontend.md` — 新增 admin UI 說明 | | |
| TASK-066 | 代碼優化與效能調整 | | |

---

## 3. 級聯刪除詳細說明

當管理員刪除使用者帳號時，系統應自動執行以下級聯刪除：

### 刪除順序（依賴關係）
1. **alert_logs** — 該使用者的所有警報日誌
2. **notification_logs** — 該使用者的所有通知日誌
3. **backtest_results** — 該使用者的所有回測結果
4. **optimization_results** — 該使用者的所有優化結果
5. **portfolio_holdings** — 該使用者投資組合的所有持倉
6. **portfolios** — 該使用者的所有投資組合
7. **tracked_indices** — 該使用者追蹤的所有指數
8. **user_preferences** — 該使用者的偏好設置
9. **profiles** — 該使用者的個人檔案
10. **auth** / **users** 表 — 最後刪除用戶認證記錄

### 實施細節
- 使用 Supabase 的 RLS + ON DELETE CASCADE 政策，或在後端應用程式端手動執行刪除
- 所有刪除操作需在單一事務中完成，確保資料一致性
- 紀錄詳細的審計日誌：刪除操作者、被刪除用戶、時間戳、刪除的記錄數

---

## 4. 替代方案

- **ALT-001**: 使用現有的「使用者管理」頁面擴展為管理者功能，而非新增單獨菜單
  - **評估**: 不採用。現有 UsersView 是給個人用戶調整偏好設置，管理者功能需要獨立、完整的界面。

- **ALT-002**: Scheduler 管理透過 SSH 直接執行命令，而非 API
  - **評估**: 不採用。API 方式更安全、更易於審計、支援多用戶並行操作。

- **ALT-003**: 使用第三方日誌管理工具（ELK、Splunk），而非自建日誌系統
  - **評估**: 可滾動實施。初期自建簡單日誌系統，後期可升級至專業日誌系統。

- **ALT-004**: 使用軟刪除（soft delete）而非硬刪除
  - **評估**: 可選。軟刪除便於數據恢復，但增加查詢複雜性。建議初期採用硬刪除 + 備份策略。

---

## 5. 依賴關係

- **DEP-001**: Supabase 資料庫須支援 RLS 策略
- **DEP-002**: FastAPI 後端框架
- **DEP-003**: Vue 3 前端框架  
- **DEP-004**: APScheduler（已整合）
- **DEP-005**: python-jose 用於 JWT 簽署（已整合）
- **DEP-006**: logging 標準庫用於日誌記錄
- **DEP-007**: 前端需要 TailwindCSS v4 用於樣式

---

## 6. 受影響的檔案

### 後端檔案
- **FILE-001**: `backend/app/models/__init__.py` — 新增 Pydantic 模型
- **FILE-002**: `backend/app/security.py` — 新增 require_admin() 檢查
- **FILE-003**: `backend/app/routers/admin.py` （新建）— 管理者 API 路由
- **FILE-004**: `backend/app/routers/__init__.py` — 導入 admin 路由
- **FILE-005**: `backend/app/services/audit_service.py` （新建）— 審計日誌服務
- **FILE-006**: `backend/app/services/scheduler_management.py` （新建）— Scheduler 管理服務
- **FILE-007**: `backend/app/main.py` — 註冊 admin 路由

### 前端檔案
- **FILE-008**: `frontend/src/router/index.js` — 新增管理路由
- **FILE-009**: `frontend/src/views/LayoutView.vue` — 添加管理菜單
- **FILE-010**: `frontend/src/views/AdminPanelView.vue` （新建）
- **FILE-011**: `frontend/src/views/AdminUsersView.vue` （新建）
- **FILE-012**: `frontend/src/views/AdminSchedulerView.vue` （新建）
- **FILE-013**: `frontend/src/views/AdminLogsView.vue` （新建）
- **FILE-014**: `frontend/src/views/AdminStatsView.vue` （新建）
- **FILE-015**: `frontend/src/api/admin-api.js` （新建）
- **FILE-016**: `frontend/src/stores/admin.js` （新建）
- **FILE-017**: `frontend/src/composables/useAdmin.js` （新建）
- **FILE-018**: `frontend/src/composables/useAdminAuth.js` （新建）
- **FILE-019**: `frontend/src/components/admin/*` （多個新建檔案）

### 資料庫檔案
- **FILE-020**: `docs/migrations/[timestamp]_admin_system.sql` — 新增表和 RLS 策略
- **FILE-021**: `docs/migrations/[timestamp]_cascade_delete.sql` — 級聯刪除設定

### 文檔檔案
- **FILE-022**: `docs/admin-panel.md` （新建）
- **FILE-023**: `docs/backend/backend.md` — 更新 API 說明
- **FILE-024**: `docs/frontend/frontend.md` — 更新組件說明

### 測試檔案
- **FILE-025**: `tests/unit/test_admin_*.py` （多個新建）
- **FILE-026**: `tests/e2e/test_admin_*.py` （多個新建）

---

## 7. 測試策略

### 後端測試
- **TEST-001**: 單元測試 - 用戶管理 API（建立、讀取、更新、刪除、密碼重設）
- **TEST-002**: 單元測試 - 使用者刪除時級聯刪除追蹤指數和投資組合
- **TEST-003**: 單元測試 - 驗證刪除後相關表無孤立記錄
- **TEST-004**: 單元測試 - Scheduler 管理 API（暫停、恢復、執行、履歷）
- **TEST-005**: 單元測試 - 審計日誌服務（記錄、查詢、篩選）
- **TEST-006**: 單元測試 - 安全檢查（is_admin 驗證、自刪除防護）
- **TEST-007**: 整合測試 - 用戶刪除級聯清理驗證
- **TEST-008**: 整合測試 - 密碼重設流程（驗證舊密碼、新密碼安全性）

### 前端測試
- **TEST-009**: 單元測試 - Admin Store（狀態管理）
- **TEST-010**: 單元測試 - Admin Composables（權限檢查、數據操作）
- **TEST-011**: 組件測試 - UserList、UserEditModal、SchedulerTable
- **TEST-012**: 組件測試 - UserDeleteConfirm（驗證級聯刪除警告）
- **TEST-013**: E2E 測試 - 用戶編輯流程（完整端到端）
- **TEST-014**: E2E 測試 - 用戶刪除流程（完整端到端，含級聯驗證）
- **TEST-015**: E2E 測試 - Scheduler 執行流程（完整端到端）
- **TEST-016**: E2E 測試 - 權限檢查（非管理員無法訪問）

### 安全測試
- **TEST-017**: 驗證非管理員無法訪問管理 API
- **TEST-018**: 驗證管理員無法刪除自己的帳號
- **TEST-019**: 驗證所有敏感操作都被記錄在審計日誌
- **TEST-020**: 驗證級聯刪除完整性（無孤立數據）

---

## 8. 風險與假設

### 風險
- **RISK-001**: 級聯刪除可能誤刪數據
  - **缓解**: 實現備份機制、軟刪除選項、詳細審計日誌、刪除前確認對話框
  
- **RISK-002**: 管理員操作可能造成數據不一致
  - **缓解**: 實現數據驗證、事務支持、審計日誌
  
- **RISK-003**: Scheduler 任務管理可能影響系統穩定性
  - **缓解**: 添加手動確認機制、任務隔離、錯誤處理
  
- **RISK-004**: 日誌快速增長可能消耗大量存儲空間
  - **缓解**: 實現日誌輪換、歸檔策略、保留期限設置

- **RISK-005**: 管理員帳號被盜可能導致系統被惡意操縱
  - **缓解**: 強制強密碼、IP 白名單（可選）、操作審計

### 假設
- **ASSUMPTION-001**: 不超過 10% 的用戶是管理員
- **ASSUMPTION-002**: 日誌存儲容量不受限制（或有清理策略）
- **ASSUMPTION-003**: 網絡連接穩定，支援實時日誌推送
- **ASSUMPTION-004**: Scheduler 任務總數不超過 50 個
- **ASSUMPTION-005**: 管理員可信任，設備安全
- **ASSUMPTION-006**: 單一使用者帳號的相關數據不超過 100 萬筆記錄

---

## 9. 相關說明與進階說明

### Scheduler 任務詳情
當前系統已有以下 scheduler 任務（參考 `/backend/app/scheduler.py`）：
- `price_check`（每 30 分鐘）— 檢查追蹤指數價格並送出警報
- `tw_etf_sync`（每日 01:00）— 同步台灣 ETF 清單
- `us_etf_sync`（每日 02:00）— 同步美股 ETF 清單
- `briefing_0800/1300/1800`（三次日報）— 生成市場早報
- `dividend_sync`（每日 06:00）— 同步除權息日曆
- `dividend_notify`（每日 06:30）— 檢查除權息通知

### 日誌來源
1. **系統應用日誌**（Python logging）→ 儲存至 Supabase `system_logs` 表
2. **審計日誌**（管理操作）→ 儲存至 Supabase `audit_logs` 表
3. **後端日誌檔案**（stdout/stderr）→ 透過 API tail 讀取（/var/log/finance-dashboard/ 或 pm2 logs）
4. **前端日誌**（瀏覽器控制台）→ 透過 API 提交、儲存至 Supabase

### 建議的額外管理功能
1. **系統配置管理** — 編輯應用設定（如郵件服務、Redis 連接）
2. **備份與恢復** — 資料庫備份管理、復原點列表
3. **系統健康檢查** — Supabase 連接、Redis 狀態、第三方 API 可用性
4. **用戶活動熱力圖** — 登入時間分佈、功能使用統計
5. **告警規則管理** — 自訂告警閾值
6. **郵件/通知測試** — 發送測試郵件驗證設定
7. **系統維護模式** — 臨時關閉應用供維護
8. **資料庫清理工具** — 清理過期的追蹤指數、舊日誌記錄

---
