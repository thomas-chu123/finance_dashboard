# Dashboard 拖放功能 - 快速部署指南

## 📋 部署步驟

### 步驟 1: 設置 Supabase 資料庫

1. 登入 [Supabase Dashboard](https://app.supabase.com)
2. 選擇你的專案
3. 打開 **SQL Editor**
4. 建立新的查詢
5. 複製並執行 [`docs/user_preferences_setup.sql`](./user_preferences_setup.sql) 中的 SQL 腳本

**驗證結果：**
```sql
-- 執行此查詢驗證表已建立
SELECT * FROM public.user_preferences LIMIT 1;
```

### 步驟 2: 更新後端代碼

後端代碼已實現，無需額外修改。確保以下檔案存在：

- ✅ `backend/app/services/user_preferences.py` - 業務邏輯
- ✅ `backend/app/routers/users.py` - API 端點（已更新）

### 步驟 3: 更新前端代碼

前端代碼已實現，無需額外修改。確保以下檔案存在：

- ✅ `frontend/src/stores/dashboard.js` - Pinia store
- ✅ `frontend/src/composables/useDragDrop.js` - 拖放邏輯
- ✅ `frontend/src/api/preferences.js` - API 客戶端
- ✅ `frontend/src/views/DashboardView.vue` - 已更新組件
- ✅ `frontend/src/assets/main.css` - 已添加 CSS

### 步驟 4: 本地測試（開發環境）

```bash
# 終端 1 - 後端
cd backend
uvicorn app.main:app --reload

# 終端 2 - 前端
cd frontend
npm run dev

# 瀏覽器打開
open http://localhost:5173
```

**測試流程：**
1. 登入 Dashboard
2. 在 Dashboard 頁面上拖放卡片
3. 刷新頁面 - 卡片順序應保留 ✓
4. 打開瀏覽器開發者工具 (F12) 檢查 Network 標籤
5. 應看到 `PUT /api/users/preferences` 請求 ✓

### 步驟 5: 生產部署

#### Docker 部署

1. **更新 backend Dockerfile（如需要）**
   ```dockerfile
   # 無需變更，依賴已在 requirements.txt 中
   ```

2. **構建 Docker 映像**
   ```bash
   docker-compose build
   ```

3. **啟動容器**
   ```bash
   docker-compose up -d
   ```

#### PM2 部署

```bash
# 編輯 ecosystem.config.js（如需要）
# 無需變更，已有配置

# 重啟應用
pm2 restart ecosystem.config.js

# 驗證狀態
pm2 status
```

### 步驟 6: 驗證部署

部署後執行以下驗證：

```bash
# 檢查後端健康狀態
curl http://your-api-url/api/auth/health

# 測試偏好設置 API（需登入令牌）
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://your-api-url/api/users/preferences

# 前端應該能正常加載
open http://your-frontend-url
```

## 🔧 故障排除

### 問題 1: 資料庫連接失敗

**症狀：** 後端啟動時出錯，涉及 Supabase 連接

**解決方案：**
1. 檢查 `backend/.env` 中的環境變數
2. 確認 `SUPABASE_URL` 和 `SUPABASE_KEY` 正確
3. 驗證 API 密鑰在 Supabase 中有效

### 問題 2: SQL 執行失敗

**症狀：** 執行 `user_preferences_setup.sql` 時出錯

**解決方案：**
1. 確認使用具有管理員權限的帳戶
2. 檢查 SQL 語法是否正確（複製粘貼時注意格式）
3. 如表已存在，嘗試先執行 `DROP TABLE IF EXISTS user_preferences;`

### 問題 3: 前端無法保存拖放順序

**症狀：** 拖放卡片後刷新頁面，順序恢復原樣

**解決方案：**
1. 打開瀏覽器開發者工具 (F12)
2. 檢查 Console 標籤是否有錯誤訊息
3. 檢查 Network 標籤中的 `PUT /api/users/preferences` 請求
   - 如果返回 401，用戶認證失敗
   - 如果返回 500，檢查後端日誌
4. 確認使用者已登入
5. 檢查 localStorage 是否已保存（DevTools → Application → Local Storage）

### 問題 4: CORS 錯誤

**症狀：** 瀏覽器控制台出現 CORS 錯誤

**解決方案：**
1. 檢查 `backend/app/config.py` 中的 `CORS_ORIGINS` 設置
2. 確認包含前端 URL（例如：`http://localhost:5173`）
3. 重啟後端服務

## 📊 監控和日誌

### 查看後端日誌

```bash
# PM2 環境
pm2 logs backend

# Docker 環境
docker logs finance_dashboard-backend-1

# 開發環境
# 直接在終端查看 uvicorn 輸出
```

### 查看前端錯誤

1. 打開瀏覽器開發者工具 (F12)
2. 查看 **Console** 標籤
3. 查看 **Network** 標籤檢查 API 請求

## 🔐 安全檢查清單

- [ ] SUPABASE_SERVICE_KEY 已設置為環境變數（不在代碼中）
- [ ] RLS 策略已應用於 `user_preferences` 表
- [ ] API 端點需要有效的 JWT 令牌
- [ ] 用戶只能修改自己的偏好設置
- [ ] CORS 設置正確，不暴露不必要的源

## 📈 性能考慮

- 拖放操作不會阻塞 UI（非同步保存）
- 每次拖放最多發一個 HTTP 請求
- 使用 localStorage 作為備份，減少不必要的網絡請求
- 卡片順序資料量小，不會影響性能

## 🚀 後續優化

1. **添加確認提示**
   ```javascript
   // 在保存前確認用戶操作
   if (confirm("確定要改變卡片順序嗎？")) {
     await saveCardOrder()
   }
   ```

2. **添加撤銷/重做功能**
   ```javascript
   // 使用 UndoManager 管理歷史記錄
   ```

3. **版本化偏好設置**
   - 存儲多個預設布局
   - 允許快速切換

## 📞 支持資源

- 📖 [完整實現文檔](./dashboard_dragdrop_implementation.md)
- 📋 [原始計畫文檔](./dashboard_improve.md)
- 🔧 [後端架構](./backend/backend.md)
- 🎨 [前端架構](./frontend/frontend.md)

---

**部署完成後，用戶應該能夠：**
✅ 拖放 Dashboard 卡片  
✅ 自動保存順序偏好  
✅ 跨會話保留排列  
✅ 依需要重置為默認值
