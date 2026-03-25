# UI 設定與實際 RSI 週期不一致問題分析

## 📋 問題概述

**症狀：** 00878 的 RSI 顯示為 57.33，對應 **11 天週期**，但系統預設應該是 **14 天**

---

## 🔍 根本原因分析

### 1️⃣ **代碼中的預設值設定**

#### 後端 (`backend/app/routers/tracking.py`)
```python
# 新增追蹤項目時的預設值（行 395）
"rsi_period": 14,  # 預設 14 天

# 查詢時的 fallback（行 286, 329）
rsi_period = item.get("rsi_period", 14)  # 若無值則用 14
```

#### 前端 (`frontend/src/views/TrackingView.vue`)
```javascript
// 新增追蹤項目的預設值（行 406, 598）
rsi_period: 14,  // 預設 14 天

// 編輯表單的預設值（行 580）
rsi_period: item.rsi_period || 14,  // 讀取數據庫，若無則用 14
```

#### 資料庫 (`docs/rsi_columns_migration.sql`)
```sql
ADD COLUMN IF NOT EXISTS rsi_period INTEGER DEFAULT 14 
CHECK (rsi_period >= 7 AND rsi_period <= 50),
```

### 2️⃣ **UI 顯示的值**

```javascript
// RSIMonitoringDashboard.vue (行 145)
<div class="font-bold text-[var(--text-primary)] font-mono">{{ item.rsi_period ?? 14 }} 天</div>
```

✅ 正確顯示數據庫中儲存的 `rsi_period` 值

---

## 🎯 為什麼 00878 是 11 天？

### **根本原因：配置不一致**

00878 的 `rsi_period` 被設定為 **11 天**， 而不是預設的 **14 天**。

### **可能的原因：**

1. **✅ 最有可能：** 使用者在 UI 上手動編輯了該追蹤項目，將 RSI 週期從 14 天改為 11 天
   - 在追蹤管理面板上點擊編輯
   - 在 RSI 參數表單中修改週期為 11 天
   - 點擊「更新」保存

2. **⭕ 測試過程中：** 可能在開發/測試時硬編碼設定了特定項目的週期

### **驗證方式：**

檢查 Supabase 數據庫：
```sql
SELECT id, symbol, rsi_period, rsi_below, rsi_above, created_at, updated_at 
FROM tracked_indices 
WHERE symbol = '00878';
```

預期結果：
```
id      | symbol | rsi_period | rsi_below | rsi_above | created_at | updated_at
--------|--------|-----------|-----------|-----------|-----------|----------
<uuid>  | 00878  | 11        | 30        | 70        | ...       | ...
```

---

## ⚠️ 這是否需要修正？

### **評估：✅ 根據使用情況決定**

| 情況 | 建議 |
|------|------|
| **用戶故意設定 11 天** | ❌ 不需修正（這是有效的配置） |
| **無意中被修改** | ✅ 需要修正為 14 天 |
| **測試數據遺留** | ✅ 需要清理 |

---

## 🛠️ 如何修正（如果需要）

### **方案 1：通過 UI 修改（推薦）**

1. 進入「指數追蹤管理」
2. 找到 00878，點擊編輯
3. 修改「RSI 週期」為 14 天
4. 點擊「更新」

### **方案 2：直接修改資料庫**

```python
# 使用 Supabase Python 客戶端
from supabase import create_client

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

# 恢復為 14 天
response = (
    sb.table("tracked_indices")
    .update({"rsi_period": 14})
    .eq("symbol", "00878")
    .execute()
)

print(f"✅ 已更新 {len(response.data)} 筆記錄")
```

### **方案 3：一鍵重置所有非預期的設定（謹慎操作）**

```python
# 只重置不是 14 天的 RSI 週期
response = (
    sb.table("tracked_indices")
    .update({"rsi_period": 14})
    .neq("rsi_period", 14)
    .execute()
)

print(f"✅ 已恢復 {len(response.data)} 筆記錄到預設值")
```

---

## 📊 代碼層面的改進建議

### **1️⃣ 在 UI 中添加「重置為預設」選項**

```vue
<button @click="resetRSIPeriodToDefault" class="text-xs text-zinc-500">
  🔄 重置為預設 (14 天)
</button>
```

### **2️⃣ 添加驗證警告**

當用戶設定非標準週期時，顯示提示：
```vue
<div v-if="form.rsi_period !== 14" class="text-amber-600 text-sm">
  ⚠️ 注意：您正在使用 {{ form.rsi_period }} 天的自定義週期
</div>
```

### **3️⃣ 添加配置審計日誌**

```python
# 在 update_tracking 時記錄變更
if updated_data.get("rsi_period") != existing_data.get("rsi_period"):
    logger.info(
        f"📊 RSI 週期已變更: {existing_data['symbol']} "
        f"{existing_data['rsi_period']} → {updated_data['rsi_period']} 天"
    )
```

---

## 🎓 結論

### **是否已修正？**
**❌ 否 - 這不是自動修正的問題。 00878 確實被設定為 11 天。**

### **根本原因：**
配置不一致 - 該項目的 `rsi_period` 欄位值為 11，而不是系統預設的 14。

### **是否需要修正？**
取決於是否為有意設定或無意遺留。

### **建議行動：**
1. ✅ 確認 00878 設定 11 天是否為故意
2. ✅ 如果無意，可通過上述三種方案之一修正
3. ✅ 建議添加前述的代碼改進，防止未來混淆

---

## 📎 相關文件

- 後端路由：`backend/app/routers/tracking.py`
- 前端視圖：`frontend/src/views/TrackingView.vue`
- 監控組件：`frontend/src/components/RSIMonitoringDashboard.vue`
- 參數表單：`frontend/src/components/RSIParametersForm.vue`
- 數據庫遷移：`docs/rsi_columns_migration.sql`
