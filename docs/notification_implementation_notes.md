# 通知記錄增強 - 實施筆記

## 概要

已完成 **Phase 1 - MVP：RSI 通知觸發原因與資訊追蹤**

### 變更內容

#### 1. 資料庫遷移 (SQL)
**文件**：`docs/migrations/20260416_alert_logs_trigger_info.sql`

需要執行的變更：
```sql
ALTER TABLE alert_logs ADD COLUMN IF NOT EXISTS trigger_reason VARCHAR(50);
ALTER TABLE alert_logs ADD COLUMN IF NOT EXISTS trigger_details JSONB;
ALTER TABLE alert_logs ADD COLUMN IF NOT EXISTS rsi_value FLOAT;
ALTER TABLE alert_logs ADD COLUMN IF NOT EXISTS rsi_threshold FLOAT;

CREATE INDEX idx_alert_logs_trigger_reason ON alert_logs(trigger_reason, created_at DESC);
CREATE INDEX idx_alert_logs_user_trigger ON alert_logs(user_id, trigger_reason, created_at DESC);
```

**應用方式**：
1. 在 Supabase SQL Editor 中執行上述 SQL
2. 或使用遷移工具執行 `docs/migrations/20260416_alert_logs_trigger_info.sql`
3. 新欄位均可為 NULL，不影響現有記錄

#### 2. 後端修改
**檔案**：`backend/app/scheduler.py` (第 285-339 行)

改進內容：
- RSI 超賣 (RSI < 30) → `trigger_reason: "rsi_oversold"`
- RSI 超買 (RSI > 70) → `trigger_reason: "rsi_overbought"`
- 價格上方 → `trigger_reason: "price_alert_above"`
- 價格下方 → `trigger_reason: "price_alert_below"`
- 複合條件 → `trigger_reason: "price_and_rsi"`

新增欄位示例：
```python
"trigger_reason": "rsi_oversold",
"trigger_details": {
    "type": "rsi_oversold",
    "rsi_value": 28.5,
    "rsi_threshold": 30,
    "rsi_period": 14
},
"rsi_value": 28.5,
"rsi_threshold": 30
```

#### 3. 前端改進
**檔案**：`frontend/src/views/NotificationLogsView.vue`

新功能：
- 添加「觸發原因」欄位，顯示 RSI 狀態、價格條件等
- 可點擊展開詳情，顯示 RSI 值、閾值、計算週期
- 8 種觸發類型的色彩編碼（綠色=超賣、紅色=超買、藍色=價格等）
- JSON 詳情展示用於技術調試

### 向後兼容性

✅ **完全向後兼容**
- 新欄位均為 NULL 友好型
- 既有的 alert_logs 記錄不需遷移
- 現有查詢不受影響（SELECT * 仍可正常運作）
- 舊通知記錄將顯示「未知」觸發原因

### 測試驗證

✅ **已通過**
- 後端語法驗證 (scheduler.py)
- 前端構建成功 (npm run build)
- 現有單元測試全部通過 (34/34 tests pass)
- 邏輯測試覆蓋所有觸發模式（price, rsi, both, either）

### 部署清單

- [ ] 在 Supabase 中執行 SQL 遷移
- [ ] 部署後端代碼（scheduler.py）
- [ ] 部署前端代碼（NotificationLogsView.vue）
- [ ] 驗證 RSI 警報觸發並正確記錄新欄位
- [ ] 檢查通知記錄頁面顯示觸發原因

### 後續改進方向

**Phase 2：除權息通知**
- 修改 `dividend_notify_service.py` 以記錄觸發原因
- 添加配息金額、除權日期、配息日期等詳情

**Phase 3：價格警報詳情**
- 增強價格警報的 trigger_details
- 記錄價格變動幅度、成交量等

**Phase 4：進階分析**
- 添加警報統計儀表板
- 按觸發原因統計警報頻率
- 追蹤警報的轉化率（警報後是否實現交易）

### 故障排除

**Q: 新通知記錄顯示「未知」觸發原因**
A: 確保已部署最新的 scheduler.py，新警報才會記錄 trigger_reason

**Q: 前端顯示詳情為空**
A: trigger_details 欄位可能為 NULL，這是正常的。檢查 trigger_reason 是否有值。

**Q: 資料庫索引未建立**
A: 手動執行遷移文件中的 CREATE INDEX 語句

---

**提交 Hash**：c89af56
**分支**：feature/notification-trigger-reasons
**最後更新**：2026-04-16 09:42 UTC
