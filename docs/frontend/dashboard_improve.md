---
goal: 實現 Dashboard 卡片拖放排列功能
version: 1.0
date_created: 2026-03-22
status: Planned
tags: [feature, frontend, UX]
---

# Dashboard 卡片拖放排列功能實現計畫

此計畫旨在為 Finance Dashboard 的卡片添加可拖放重新排列的功能。

## 1. 需求 & 約束

### 功能需求
- REQ-001: 用戶可通過拖放改變卡片位置
- REQ-002: 卡片排列偏好保存到後端資料庫
- REQ-003: 用戶下次登錄時恢復上次保存的排列
- REQ-004: 支持響應式布局
- REQ-005: 提供視覺反饋

### 技術約束
- CON-001: 使用 Vue 3 Composition API
- CON-002: 保持 Tailwind CSS 樣式系統
- CON-003: 不破壞響應式 grid 布局
- CON-004: 與 Pinia store 集成
- CON-005: 符合 FastAPI + Supabase 架構

## 2. 實現步驟

### 階段 1: 前端基礎設施 (5 tasks)
- TASK-001: 建立 frontend/src/stores/dashboard.js
- TASK-002: 定義 cardOrder 狀態 (卡片 ID 數組)
- TASK-003: 實作 moveCard(fromIndex, toIndex) 方法
- TASK-004: 實作 loadCardOrder() 和 saveCardOrder() 方法
- TASK-005: 建立 frontend/src/composables/useDragDrop.js

### 階段 2: DashboardView 組件修改 (5 tasks)
- TASK-006: 將"追蹤中的指數"卡片改為可拖放元素
- TASK-007: 將"最近通知記錄"卡片改為可拖放元素
- TASK-008: 將"系統運作狀態"側邊欄卡片改為可拖放元素
- TASK-009: 添加拖放視覺反饋 (cursor-grab, ring, opacity)
- TASK-010: 在 layout div 中實現動畫效果 (transitions)

### 階段 3: 後端 API 實現 (5 tasks)
- TASK-011: Supabase 創建 user_preferences 表 (JSON card_order)
- TASK-012: 添加 GET /api/users/preferences 端點
- TASK-013: 添加 PUT /api/users/preferences 端點
- TASK-014: 建立 backend/app/services/user_preferences.py
- TASK-015: 配置 RLS 策略確保數據隔離

### 階段 4: 前端 API 集成 (5 tasks)
- TASK-016: 建立 frontend/src/api/preferences.js
- TASK-017: dashboard store 中整合 loadCardOrder() API 呼叫
- TASK-018: dashboard store 中整合 saveCardOrder() API 呼叫
- TASK-019: 在 DashboardView onMounted 中調用 loadCardOrder()
- TASK-020: 拖放 drop 事件後調用 saveCardOrder()

### 階段 5: 響應式設計 & 觸摸支援 (4 tasks)
- TASK-021: 桌面設備 (lg+) 拖放功能測試
- TASK-022: 行動設備 (sm) 響應式行為測試
- TASK-023: 行動設備替代排列方式 (可選上下移動按鈕)
- TASK-024: 優化拖放 zone 大小，防止誤觸發

### 階段 6: 測試與優化 (5 tasks)
- TASK-025: 前端單元測試 (dashboard store)
- TASK-026: 後端單元測試 (preferences API)
- TASK-027: 集成測試 (拖放 → 保存 → 刷新 → 驗證)
- TASK-028: 性能測試 (拖放流暢度)
- TASK-029: 用戶體驗測試

## 3. 備選方案

- **ALT-001**: 使用 SortableJS 庫
  - 優點：功能豐富，開箱即用
  - 缺點：額外依賴，打包體積增加
  - 決定：選擇原生 HTML5 Drag & Drop API 保持輕量化

- **ALT-002**: localStorage 本地存儲
  - 優點：無需後端改動
  - 缺點：跨設備同步困難，數據不安全
  - 決定：選擇 Supabase 後端存儲

- **ALT-003**: 只允許相鄰卡片交換
  - 優點：實現簡單
  - 缺點：用戶體驗受限
  - 決定：實現完整的自由拖放

## 4. 依賴關係

**無新 npm 依賴** - 使用原生 HTML5 Drag & Drop API

所有依賴均已存在：
- Pinia 3.0.4 (狀態管理)
- Vue 3.5.30 (框架)
- Axios 1.13.6 (HTTP 客戶端)
- Supabase (後端服務)
- FastAPI (後端框架)

## 5. 受影響的文件

### 前端 (4 個新建 + 1 個修改)
- `frontend/src/stores/dashboard.js` (新建)
- `frontend/src/composables/useDragDrop.js` (新建)
- `frontend/src/api/preferences.js` (新建)
- `frontend/src/views/DashboardView.vue` (修改)

### 後端 (1 個新建 + 1 個修改)
- `backend/app/services/user_preferences.py` (新建)
- `backend/app/routers/users.py` (修改 - 添加端點)

## 6. 卡片 ID 定義

- `market-ticker` - 行情報價卡片 
- `tracking-table` - 追蹤中的指數表格
- `alert-logs` - 最近通知記錄表格
- `status-sidebar` - 系統運作狀態側邊欄

## 7. 風險 & 假設

### 風險
- **RISK-001**: 舊版瀏覽器不支援 HTML5 Drag & Drop API
  - 緩解：添加功能檢測，不支援時隱藏拖放或提供替代方案

- **RISK-002**: 快速交互可能產生競態條件
  - 緩解：保存期間禁用拖放，顯示加載狀態

- **RISK-003**: 行動設備上拖放可能困難
  - 緩解：提供替代的排列方式

### 假設
- **ASSUMPTION-001**: 用戶對拖放行為的期望符合標準 Web 應用
- **ASSUMPTION-002**: Supabase RLS 已正確配置
- **ASSUMPTION-003**: 不需要卡片隱藏/顯示功能
- **ASSUMPTION-004**: 所有新用戶使用相同的初始卡片順序

## 8. 相關文檔

- [HTML Drag and Drop API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API)
- [Vue 3 Composition API](https://vuejs.org/guide/extras/composition-api-faq.html)
- [Pinia 狀態管理](https://pinia.vuejs.org/)
- [Supabase RLS](https://supabase.com/docs/guides/auth/row-level-security)
- [Finance Dashboard 前端架構](./frontend.md)
- [Finance Dashboard 後端架構](../backend/backend.md)
