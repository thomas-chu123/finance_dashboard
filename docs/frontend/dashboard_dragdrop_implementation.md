---
title: Dashboard 卡片拖放排列功能實現
version: 1.0
status: Completed
date_implemented: 2026-03-22
---

# Dashboard 卡片拖放排列功能實現文檔

本文檔說明了 Finance Dashboard 的卡片拖放排列功能的完整實現。

## 功能概述

用戶現在可以通過拖放操作重新排列 Dashboard 上的卡片（追蹤指數表格、通知記錄表格、系統狀態側邊欄），並且排列偏好會自動保存到後端資料庫，跨設備和會話保留。

### 支持的卡片

1. **市場行情卡片** (`market-ticker`) - 頁面頂部固定的行情報價
2. **追蹤指數卡片** (`tracking-table`) - 追蹤中的指數表格
3. **通知記錄卡片** (`alert-logs`) - 最近的警報通知記錄
4. **系統狀態卡片** (`status-sidebar`) - 系統運作狀態側邊欄

## 實現清單

### 前端實現 ✅

#### 1. **Pinia Store** (`frontend/src/stores/dashboard.js`)
- `cardOrder`: 卡片 ID 陣列，管理乾坤布局順序
- `moveCard(fromIndex, toIndex)`: 移動卡片邏輯
- `swapCards(index1, index2)`: 交換兩個卡片
- `loadCardOrder(token)`: 從後端加載保存的順序
- `saveCardOrder(token)`: 向後端保存卡片順序
- `loadFromLocalStorage()`: 從瀏覽器本地存儲加載
- `saveToLocalStorage()`: 保存到瀏覽器本地存儲
- `resetToDefault()`: 恢復默認順序

#### 2. **拖放 Composable** (`frontend/src/composables/useDragDrop.js`)
提供 HTML5 Drag & Drop API 封裝：
- `handleDragStart()`: 開始拖動
- `handleDragEnd()`: 結束拖動
- `handleDragEnter()`: 進入放置目標
- `handleDragLeave()`: 離開放置目標
- `handleDragOver()`: 在放置目標上方拖動
- `handleDrop()`: 執行放置操作
- `resetDragState()`: 重置拖放狀態

視覺狀態：
- `isDragging`: 是否正在拖動
- `draggedIndex`: 被拖動的卡片索引
- `dragOverIndex`: 懸停的目標卡片索引

#### 3. **API 客戶端** (`frontend/src/api/preferences.js`)
- `getPreferences(token)`: 獲取用戶偏好設置
- `updatePreferences(token, preferences)`: 更新偏好設置
- `updateCardOrder(token, cardOrder)`: 更新卡片順序
- `resetPreferences(token)`: 重置為默認值

#### 4. **DashboardView 組件修改** (`frontend/src/views/DashboardView.vue`)
- 導入 `useDashboardStore`, `useDragDrop`, `preferencesAPI`
- 添加 `draggable="true"` 屬性到卡片元素
- 綁定拖放事件監聽器
- 在 `onMounted` 中加載卡片順序
- 拖放完成後自動保存到後端

#### 5. **視覺反饋 CSS** (`frontend/src/assets/main.css`)
- `.drag-over`: 懸停時的視覺效果（綠色虛線邊框、背景淡化）
- `[draggable="true"]`: 拖動時的光標改變和陰影效果

### 後端實現 ✅

#### 1. **用戶偏好設置服務** (`backend/app/services/user_preferences.py`)
- `UserPreferencesService` 類提供以下方法：
  - `get_default_card_order()`: 取得默認卡片順序
  - `get_user_preferences(user_id)`: 查詢用戶偏好設置
  - `update_user_preferences(user_id, preferences)`: 更新偏好設置
  - `update_card_order(user_id, card_order)`: 更新卡片順序
  - `reset_user_preferences(user_id)`: 重置為默認值

#### 2. **API 端點** (`backend/app/routers/users.py`)
添加以下三個新端點：

```
GET /api/users/preferences
```
獲取用戶的偏好設置（包括卡片順序）

**響應範例：**
```json
{
  "user_id": "uuid",
  "card_order": ["market-ticker", "tracking-table", "alert-logs", "status-sidebar"],
  "created_at": "2026-03-22T10:00:00Z",
  "updated_at": "2026-03-22T10:00:00Z"
}
```

---

```
PUT /api/users/preferences
```
更新用戶的偏好設置

**請求體範例：**
```json
{
  "card_order": ["alert-logs", "tracking-table", "market-ticker", "status-sidebar"]
}
```

---

```
POST /api/users/preferences/reset
```
將用戶偏好設置重置為系統默認值

### 資料庫設置 ✅

#### 1. **user_preferences 表** (`docs/user_preferences_setup.sql`)
```sql
CREATE TABLE user_preferences (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL UNIQUE REFERENCES auth.users ON DELETE CASCADE,
  card_order TEXT[] DEFAULT ARRAY['market-ticker', 'tracking-table', 'alert-logs', 'status-sidebar'],
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 2. **RLS 策略**
- 用戶只能查看自己的偏好設置
- 用戶只能修改自己的偏好設置
- 用戶只能插入自己的偏好設置

#### 3. **自動時間戳更新**
當記錄更新時，`updated_at` 欄位自動更新為當前時間

## 使用說明

### 用戶指南

1. **拖放卡片**
   - 在桌面上，將滑鼠懸停在卡片標題上方
   - 卡片會變為可拖動狀態（光標改變為 `grab`）
   - 拖動卡片到另一個卡片位置
   - 放開滑鼠完成操作
   - 新的排列順序會自動保存

2. **視覺反饋**
   - 可拖動卡片在滑鼠懸停時會產生光暈效果
   - 拖動過程中卡片透明度降至 50%
   - 放置目標以綠色虛線邊框突出顯示

3. **恢復默認順序**
   - 可通過後端 API 的 `/api/users/preferences/reset` 端點重置

### 開發部署指南

#### 前置準備

1. **運行 SQL 初始化腳本**
   ```bash
   # 在 Supabase SQL Editor 中執行：
   # /docs/user_preferences_setup.sql
   ```

2. **驗證資料庫設置**
   - 確認 `user_preferences` 表已創建
   - 確認 RLS 策略已應用
   - 確認索引已創建

#### 本地開發

1. **後端**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. **前端**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **測試功能**
   - 打開 Dashboard 頁面
   - 嘗試拖放卡片
   - 刷新頁面，驗證順序是否保留
   - 檢查瀏覽器控制台是否有錯誤

#### 生產部署

1. 更新 Docker 容器中的 SQL 初始化腳本
2. 重新構建前端（`npm run build`）
3. 重新啟動後端服務
4. 驗證拖放功能正常運作

## 技術詳節

### 狀態管理流程

```
用戶拖放卡片
    ↓
DashboardView 的 @drop 事件處理
    ↓
handleCardDrop() 調用 dashboard.moveCard()
    ↓
store 中的 cardOrder 更新
    ↓
saveCardOrder() 發送 PUT 請求到後端
    ↓
後端保存到 Supabase
    ↓
返回成功響應
    ↓
同時保存到瀏覽器 localStorage
```

### 本地優先策略

- 應用啟動時先從 localStorage 加載卡片順序
- 然後嘗試從後端同步最新順序
- 如後端同步失敗，保持 localStorage 中的順序
- 用戶進行拖放操作時，同時保存到 localStorage 和後端

### 響應式設計考慮

- **桌面** (lg+)：完整拖放支援
- **平板** (md-lg)：拖放支援（經過優化以適應較小屏幕）
- **行動裝置** (sm)：由於觸摸交互限制，拖放體驗有限（可在未來版本添加替代方案，如上下移動按鈕）

## 錯誤處理

### 前端

- 網絡請求失敗時回退到本地存儲
- 提供視覺反饋（加載動畫、錯誤提示）
- 自動重試機制（通過前端框架）

### 後端

- 用戶認證失敗返回 401
- 數據驗證失敗返回 400
- 資料庫操作失敗返回 500
- 提供清晰的錯誤訊息

## 性能考慮

- 拖放操作不會阻塞主線程
- 保存操作在背景進行（非模態）
- 使用本地存儲減少網絡請求
- 卡片排序不涉及大數據量（最多 4-5 個卡片）

## 未來改進

1. **觸摸設備支援**
   - 長按激活拖動
   - 上下移動按鈕替代方案

2. **更多自訂選項**
   - 隱藏/顯示卡片功能
   - 主題偏好設置
   - 字體大小調整

3. **協作功能**
   - 保存多個預設布局
   - 與團隊成員共享布局

4. **動畫增強**
   - 平滑的過度動畫
   - 拖放反彈效果

## 測試檢查清單

- [x] 拖放卡片在桌面上正常運作
- [x] 刷新頁面後卡片順序保留
- [x] 多標籤頁打開時順序同步
- [x] 登出後重新登入順序保留
- [x] 後端 API 返回正確的偏好設置
- [x] RLS 策略防止未授權訪問
- [x] 默認順序恢復功能正常
- [x] 視覺反饋清晰可見
- [x] 無 JavaScript 控制台錯誤

## 相關文檔

- [Dashboard 改進計畫](./dashboard_improve.md) - 原始計畫文檔
- [後端架構](./backend/backend.md) - FastAPI 架構
- [前端架構](./frontend/frontend.md) - Vue 3 架構
- [部署指南](./deploy/deploy.md) - 生產部署

## 支持

如有問題或建議，請提交 Issue 或聯繫開發團隊。
