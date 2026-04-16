# 通知記錄增強 - 觸發原因與 RSI 資訊

## 問題分析

**當前狀態**：
通知記錄只顯示基本資訊（時間、代碼、觸發價、目前價、方式、狀態），**缺失**：
1. 觸發原因（何故觸發？）
2. RSI 指標資訊（特別是 RSI 触发时的 RSI 值）
3. 除權息通知的觸發詳情

**受影響頁面**：
- NotificationLogsView.vue - 前端顯示

**後端插入點**：
- backend/app/routers/market.py (line 390)
- backend/app/routers/tracking.py (get_alert_logs)
- backend/app/services/dividend_notify_service.py (line 319)
- backend/app/scheduler.py (RSI 監控)

---

## 需求分析

### 1. 觸發原因欄位

| 觸發類型 | 觸發原因示例 |
|---------|-----------|
| 價格警報 | `price_alert_above` / `price_alert_below` |
| RSI 指標 | `rsi_oversold` (RSI < 30) / `rsi_overbought` (RSI > 70) |
| 除權息 | `dividend_ex_date` / `dividend_payment_date` |
| 股息殖利率 | `high_dividend_yield` |

### 2. RSI 資訊

需要儲存：
- `rsi_value` (float) - 觸發時的 RSI 值
- `rsi_threshold` (float) - 觸發閾值（30 或 70）
- `rsi_period` (int) - RSI 計算週期（通常 14）

### 3. 額外的上下文資訊

需要儲存：
- `trigger_reason` (string) - 觸發原因編碼
- `trigger_details` (jsonb/text) - 觸發詳情 JSON
- `metadata` (jsonb) - 額外資訊

---

## 技術方案

### A. 資料庫擴展（推薦）

**新增欄位至 alert_logs 表**：

```sql
ALTER TABLE alert_logs ADD COLUMN IF NOT EXISTS trigger_reason VARCHAR(50);
ALTER TABLE alert_logs ADD COLUMN IF NOT EXISTS trigger_details JSONB;
ALTER TABLE alert_logs ADD COLUMN IF NOT EXISTS rsi_value FLOAT;
ALTER TABLE alert_logs ADD COLUMN IF NOT EXISTS rsi_threshold FLOAT;

-- 範例 trigger_details 結構
{
  "type": "rsi_oversold",
  "rsi_period": 14,
  "price_change": -5.5,
  "volume": 1000000,
  "dividend_yield": null
}
```

### B. 前端修改

**NotificationLogsView.vue**：
- 添加「觸發原因」欄位
- 添加「RSI 資訊」摺疊詳情
- 改進表格佈局顯示更多資訊

### C. 後端修改

**插入點修改**：

1. **scheduler.py** (RSI 監控):
```python
sb.table("alert_logs").insert({
    "user_id": item["user_id"],
    "tracked_index_id": tracking_id,
    "symbol": code,
    "trigger_price": current_rsi,
    "current_price": current_price,
    "channel": ",".join(channels),
    "status": "sent",
    "trigger_reason": "rsi_oversold",  # NEW
    "trigger_details": {  # NEW
        "type": "rsi_oversold",
        "rsi_value": 28.5,
        "rsi_threshold": 30,
        "rsi_period": 14
    },
    "rsi_value": 28.5,  # NEW
    "rsi_threshold": 30  # NEW
})
```

2. **dividend_notify_service.py**:
```python
sb.table("alert_logs").insert({
    "user_id": user_id,
    "tracked_index_id": tracking_id,
    "symbol": code,
    "channel": ",".join(channel_used),
    "status": "sent",
    "trigger_reason": "dividend_ex_date",  # NEW
    "trigger_details": {  # NEW
        "type": "dividend_ex_date",
        "dividend_amount": 2.5,
        "ex_date": "2026-04-20",
        "payment_date": "2026-05-10"
    }
})
```

---

## 實施步驟

### Phase 1: 資料庫遷移
- [ ] 建立新的 SQL migration 文件
- [ ] 添加 trigger_reason, trigger_details, rsi_value, rsi_threshold 欄位
- [ ] 設定適當的索引（trigger_reason, created_at）

### Phase 2: 後端修改
- [ ] 修改 scheduler.py 的 RSI 警報插入邏輯
- [ ] 修改 dividend_notify_service.py 的插入邏輯
- [ ] 修改 market.py 的插入邏輯
- [ ] 驗證所有路徑都包含觸發原因

### Phase 3: 前端修改
- [ ] 更新 NotificationLogsView.vue 顯示觸發原因
- [ ] 添加 RSI 詳情展開卡
- [ ] 改進表格佈局以適應新欄位
- [ ] 添加觸發原因的人類可讀標籤

### Phase 4: 測試與驗證
- [ ] 單元測試：確保所有插入路徑都正確填充欄位
- [ ] 集成測試：端到端測試 RSI 與除權息警報
- [ ] 手動測試：驗證前端顯示正確

---

## 風險與緩解

| 風險 | 等級 | 緩解 |
|------|------|------|
| 資料庫遷移 | 中 | 先在開發/測試環境驗證，再生產部署 |
| 向後兼容 | 低 | 新欄位可為 NULL，不影響既有記錄 |
| 性能 | 低 | 新欄位為可選，JSONB 索引按需添加 |

---

## 時間估算

- **資料庫設計**：30 分鐘
- **資料庫遷移文件**：15 分鐘
- **後端修改**：45 分鐘
- **前端修改**：60 分鐘
- **測試與驗證**：45 分鐘
- **總計**：約 3 小時

