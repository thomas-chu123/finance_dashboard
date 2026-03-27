---
goal: 將前端 Vue 3 + Vite 專案轉換為 Progressive Web App (PWA)
version: 1.0
date_created: 2026-03-27
last_updated: 2026-03-27
owner: 前端團隊
status: 'Planned'
tags: ['feature', 'pwa', 'frontend', 'ux']
---

# Introduction

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

本計畫詳細列出將現有 Vue 3 + Vite 前端專案轉換為完整的 Progressive Web App (PWA) 所需的所有變更。轉換完成後，應用將支持離線訪問、安裝到主屏幕、後台同步等現代 Web 應用功能。

## 1. Requirements & Constraints

### 功能需求
- **REQ-001**: 應用必須可離線訪問，至少支持基礎功能（Dashboard、Tracking 視圖）
- **REQ-002**: 用戶可將應用安裝到設備主屏幕
- **REQ-003**: Service Worker 必須緩存關鍵資源，支持快速加載
- **REQ-004**: 應用必須在弱網環境下正常運行（3G 連接）
- **REQ-005**: 後台數據同步功能，當網絡恢復時自動上傳待同步數據

### 技術約束
- **CON-001**: 仍使用 Vite 作為構建工具，不引入額外的框架
- **CON-002**: 避免破壞現有的 Vue Router 路由邏輯
- **CON-003**: 保持 Tailwind CSS 和現有的樣式配置
- **CON-004**: 必須兼容現有的 Pinia 狀態管理
- **CON-005**: Service Worker 緩存策略必須可配置（開發/生產環境區分）

### 安全約束
- **SEC-001**: JWT token 必須安全存儲，不得存儲在 localStorage 中（改用內存 + cookies）
- **SEC-002**: Service Worker 不得緩存敏感 API 響應
- **SEC-003**: 離線時禁用所有涉及用戶認證的操作

### 指南
- **GUD-001**: 遵循 Google PWA Checklist 標準
- **GUD-002**: 使用 Cache-first 策略緩存靜態資源，Network-first 策略用於 API 請求
- **GUD-003**: 提供清晰的離線狀態 UI 反饋

## 2. Implementation Steps

### Implementation Phase 1：依賴安裝與配置

- GOAL-001: 安裝 PWA 必要的 npm 依賴

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | 安裝 `vite-plugin-pwa` 作為主要 PWA 構建工具 | | |
| TASK-002 | 安裝 `workbox-window` 用於 Service Worker 交互 | | |
| TASK-003 | 安裝 `idb` 用於本地儲存敏感數據（替代 localStorage） | | |
| TASK-004 | 驗證依賴兼容性，無版本衝突 | | |

**詳細實施**：
```
npm install vite-plugin-pwa@^0.20 workbox-window@^7 idb@^8
```

---

### Implementation Phase 2：Vite 配置更新

- GOAL-002: 配置 Vite 以支持 PWA

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-005 | 修改 `vite.config.js`，引入 `VitePWA` 插件 | | |
| TASK-006 | 配置 PWA 選項（manifest、icon、colors） | | |
| TASK-007 | 設置 Service Worker 策略（Workbox 配置） | | |
| TASK-008 | 配置開發環境禁用 PWA，生產環境啟用 | | |

**修改 `frontend/vite.config.js`**：
- 導入 `{ VitePWA } from 'vite-plugin-pwa'`
- 在 `plugins` 陣列中添加 `VitePWA(options)` 配置
- 配置 PWA 選項包括 manifest、icons、colors、workbox 等

---

### Implementation Phase 3：Manifest 和靜態資源

- GOAL-003: 創建 PWA manifest 和相關圖標資源

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-009 | 在 `public/` 目錄創建 `manifest.json` | | |
| TASK-010 | 生成不同尺寸的應用圖標（192x192, 512x512 等） | | |
| TASK-011 | 創建應用範圍內的截圖資源（可選） | | |
| TASK-012 | 更新 `index.html`，添加 manifest 和 meta tags | | |

**必要欄位（manifest.json）**：
- `name`: "NEXUS Finance Dashboard"
- `short_name`: "NEXUS"
- `display`: "standalone"
- `theme_color`: "#1f2937"（深灰色）
- `background_color`: "#ffffff"
- `icons`: 圖標陣列（192x192、512x512）

**index.html 更新**：
- `<link rel="manifest" href="/manifest.json">`
- `<meta name="theme-color" content="#1f2937">`
- `<meta name="mobile-web-app-capable" content="yes">`
- `<meta name="apple-mobile-web-app-capable" content="yes">`

---

### Implementation Phase 4：Service Worker 註冊與初始化

- GOAL-004: 在應用中正確註冊和初始化 Service Worker

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-013 | 在 `src/main.js` 中註冊 Service Worker | | |
| TASK-014 | 創建 PWA 註冊和更新邏輯模組 | | |
| TASK-015 | 實現 Service Worker 更新檢測和通知機制 | | |
| TASK-016 | 處理 Service Worker 錯誤和超時情況 | | |

**詳細實施**：
- 創建新文件：`src/services/pwa-service.js`
- 在 `src/main.js` 中導入並執行 PWA 初始化
- 實現 Service Worker 更新檢測和使用者提示

---

### Implementation Phase 5：離線支持和緩存策略

- GOAL-005: 實現離線功能和智能緩存策略

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-017 | 實現 Cache-first 策略（靜態資源） | | |
| TASK-018 | 實現 Network-first 策略（API 請求） | | |
| TASK-019 | 創建離線狀態檢測機制 | | |
| TASK-020 | 實現離線時的降級 UI | | |

**緩存策略配置**：
- 靜態資源（JS、CSS、圖片）：Cache-first，60 天過期
- HTML 文件：Network-first，24 小時網絡超時
- API 請求（`/api/*`）：Network-first，帶降級緩存
- 字體資源：Cache-first，無期限過期

---

### Implementation Phase 6：認證和安全存儲更新

- GOAL-006: 實現安全的 token 存儲和認證管理

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-021 | 將 JWT token 從 localStorage 遷移至內存存儲 | | |
| TASK-022 | 使用 HTTP-only cookies 存儲敏感 token | | |
| TASK-023 | 使用 IndexedDB（via idb）存儲用戶偏好 | | |
| TASK-024 | 實現 Service Worker 中的認證驗證邏輯 | | |

---

### Implementation Phase 7：後台同步功能（可選）

- GOAL-007: 實現後台數據同步

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-025 | 實現 Background Sync API（如果支持） | | |
| TASK-026 | 創建待同步任務隊列存儲 | | |
| TASK-027 | 實現同步重試邏輯和錯誤處理 | | |
| TASK-028 | 提供同步狀態 UI 反饋 | | |

---

### Implementation Phase 8：測試和驗證

- GOAL-008: 測試 PWA 功能和兼容性

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-029 | 使用 Lighthouse 測試 PWA 評分 | | |
| TASK-030 | 在 Chrome DevTools 中測試 Service Worker | | |
| TASK-031 | 測試離線功能（模擬網絡中斷） | | |
| TASK-032 | 測試應用安裝和啟動屏幕 | | |
| TASK-033 | 在實際移動設備上測試（iOS/Android） | | |
| TASK-034 | 驗證緩存有效期和更新機制 | | |

---

### Implementation Phase 9：文件變更總結和優化

- GOAL-009: 匯總所有文件變更並進行性能優化

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-035 | 檢查並優化 Service Worker 大小 | | |
| TASK-036 | 實現代碼分割優化（lazy loading） | | |
| TASK-037 | 壓縮圖標和靜態資源 | | |
| TASK-038 | 更新 CI/CD 構建配置 | | |
| TASK-039 | 編寫 PWA 使用文檔 | | |

---

## 3. 涉及的主要文件變更

| 文件路徑 | 變更類型 | 說明 |
|---------|---------|------|
| `frontend/package.json` | 修改 | 添加 3 個依賴 |
| `frontend/vite.config.js` | 修改 | 導入 VitePWA，配置 PWA 選項 |
| `frontend/index.html` | 修改 | 添加 manifest 鏈接和 meta tags |
| `frontend/public/manifest.json` | 新建 | PWA 應用清單 |
| `frontend/public/icons/` | 新建 | 應用圖標資源 |
| `frontend/src/main.js` | 修改 | 導入 PWA 初始化 |
| `frontend/src/services/pwa-service.js` | 新建 | PWA 管理服務 |
| `frontend/src/services/secure-storage.js` | 新建 | 安全存儲服務 |
| `frontend/src/composables/useOfflineDetection.js` | 新建 | 離線檢測組合 API |
| `frontend/src/stores/auth.js` | 修改 | 更新 token 存儲邏輯 |
| `frontend/src/components/OfflineWarning.vue` | 新建 | 離線警告組件 |

---

## 4. Alternative Approaches

- **ALT-001**: 使用 `workbox-webpack-plugin` 而不是 `vite-plugin-pwa`
  - **不選原因**：Vite 已棄用 Webpack，vite-plugin-pwa 更符合現代構建流程

- **ALT-002**: 手動編寫 Service Worker 而不依賴自動生成
  - **不選原因**：增加維護複雜度，vite-plugin-pwa 的自動生成足以滿足需求

- **ALT-003**: 使用 localStorage 存儲 token
  - **不選原因**：安全性風險（XSS 攻擊），推薦使用 HttpOnly cookies 或內存存儲

---

## 5. Dependencies

- **DEP-001**: `vite-plugin-pwa: ^0.20` - PWA 構建和生成工具
- **DEP-002**: `workbox-window: ^7` - Service Worker 通信和控制
- **DEP-003**: `idb: ^8` - IndexedDB 簡化操作庫
- **DEP-004**: Vue 3、Vue Router、Pinia（已有）
- **DEP-005**: Vite 8.x（已有）

---

## 6. Risks & Assumptions

### 風險
- **RISK-001**: Service Worker 緩存策略不當可能導致陳舊內容展示
  - **緩解**：實現版本化資源名稱，使用 Workbox 的智能緩存清理

- **RISK-002**: 某些舊設備或瀏覽器不支持 PWA
  - **緩解**：提供 Progressive enhancement，應用在非 PWA 環境中仍可用

- **RISK-003**: IndexedDB 儲存容量限制（通常 50MB）
  - **緩解**：只存儲必要的用戶偏好和非敏感數據，定期清理

- **RISK-004**: Background Sync API 支持率不完全（iOS 不支持）
  - **緩解**：實現 fallback 機制，使用定期網絡檢查

- **RISK-005**: 離線時，用戶無法執行涉及實時數據的操作
  - **緩解**：清晰的 UI 提示和禁用相關按鈕

### 假設
- **ASSUMPTION-001**: 後端已配置 CORS 和 HttpOnly cookie 支持
- **ASSUMPTION-002**: 用戶願意授予應用"安裝到主屏幕"的權限
- **ASSUMPTION-003**: 應用主要在 Android 和新版 iOS Safari 上運行
- **ASSUMPTION-004**: 緩存數據超過 30 天可安全清除

---

## 7. Related Reading

- [Google PWA Checklist](https://web.dev/pwa-checklist/)
- [Web App Manifest Specification](https://www.w3.org/TR/appmanifest/)
- [Service Worker API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [vite-plugin-pwa 官方文檔](https://vite-plugin-pwa.netlify.app/)
- [Workbox 緩存策略指南](https://developers.google.com/web/tools/workbox/modules/workbox-strategies)