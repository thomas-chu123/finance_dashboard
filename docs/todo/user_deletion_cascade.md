# 🗑️ 使用者刪除連動機制 (User Deletion Cascade)

**建立日期**：2026年4月1日  
**狀態**：📝 待實作  
**優先度**：高  
**相關功能**：管理者管理介面 → 使用者管理  

---

## 📋 問題描述

目前當管理員或使用者刪除帳號時，只有 `users` 資料表的記錄被移除，但以下相關資料表中對應 `user_id` 的資料**並未自動清除**，造成孤立資料 (Orphan Data) 的問題：

- `tracked_indices`（使用者追蹤的指數與警報）
- `portfolios`（使用者的投資組合）
- `portfolio_holdings`（投資組合的持倉明細）
- `backtest_results`（回測結果）
- `optimization_results`（優化結果）
- `user_preferences`（使用者偏好設定）
- `market_briefings`（AI 市場早報）

---

## 🔧 解決方案

### 方案一：資料庫外鍵 CASCADE（推薦）

在 Supabase PostgreSQL 中，對所有包含 `user_id` 欄位的資料表設定 `ON DELETE CASCADE` 外鍵約束，讓資料庫自動處理串聯刪除。

#### 資料庫 Migration SQL

```sql
-- ============================================================
-- 使用者刪除連動清除 Migration
-- 日期：2026-04-01
-- ============================================================

-- 1. tracked_indices：追蹤指數
ALTER TABLE tracked_indices
  DROP CONSTRAINT IF EXISTS tracked_indices_user_id_fkey,
  ADD CONSTRAINT tracked_indices_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- 2. portfolios：投資組合
ALTER TABLE portfolios
  DROP CONSTRAINT IF EXISTS portfolios_user_id_fkey,
  ADD CONSTRAINT portfolios_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- 3. portfolio_holdings：持倉明細（透過 portfolio_id 串聯）
--    注意：若 portfolios 已設定 CASCADE，此處可透過二階段自動觸發
ALTER TABLE portfolio_holdings
  DROP CONSTRAINT IF EXISTS portfolio_holdings_portfolio_id_fkey,
  ADD CONSTRAINT portfolio_holdings_portfolio_id_fkey
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE;

-- 4. backtest_results：回測結果
ALTER TABLE backtest_results
  DROP CONSTRAINT IF EXISTS backtest_results_user_id_fkey,
  ADD CONSTRAINT backtest_results_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- 5. optimization_results：優化結果
ALTER TABLE optimization_results
  DROP CONSTRAINT IF EXISTS optimization_results_user_id_fkey,
  ADD CONSTRAINT optimization_results_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- 6. user_preferences：使用者偏好
ALTER TABLE user_preferences
  DROP CONSTRAINT IF EXISTS user_preferences_user_id_fkey,
  ADD CONSTRAINT user_preferences_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- 7. market_briefings：AI 市場早報（若存在）
ALTER TABLE market_briefings
  DROP CONSTRAINT IF EXISTS market_briefings_user_id_fkey,
  ADD CONSTRAINT market_briefings_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

> **執行位置**：在 Supabase Dashboard → SQL Editor 中執行，或新增至 `docs/migrations/` 目錄作為版本控制的 migration 文件。

---

### 方案二：後端應用層程式控制（備用）

若資料庫 CASCADE 約束無法設定（例如部分資料表尚未建立外鍵），可在後端 `admin_service.py` 中手動依序刪除：

```python
async def delete_user_with_cascade(user_id: str) -> dict:
    """
    刪除使用者及其所有相關資料.
    
    依照依賴順序刪除，確保不違反現有外鍵約束。
    
    Args:
        user_id: 要刪除的使用者 UUID
        
    Returns:
        dict: 各資料表刪除的記錄數統計
    """
    supabase = get_supabase()
    stats = {}

    # Step 1: 刪除追蹤指數
    result = supabase.table("tracked_indices") \
        .delete() \
        .eq("user_id", user_id) \
        .execute()
    stats["tracked_indices"] = len(result.data)

    # Step 2: 取得所有 portfolio_id 後刪除持倉明細
    portfolios = supabase.table("portfolios") \
        .select("id") \
        .eq("user_id", user_id) \
        .execute()
    portfolio_ids = [p["id"] for p in portfolios.data]
    
    if portfolio_ids:
        result = supabase.table("portfolio_holdings") \
            .delete() \
            .in_("portfolio_id", portfolio_ids) \
            .execute()
        stats["portfolio_holdings"] = len(result.data)

    # Step 3: 刪除投資組合
    result = supabase.table("portfolios") \
        .delete() \
        .eq("user_id", user_id) \
        .execute()
    stats["portfolios"] = len(result.data)

    # Step 4: 刪除回測結果
    result = supabase.table("backtest_results") \
        .delete() \
        .eq("user_id", user_id) \
        .execute()
    stats["backtest_results"] = len(result.data)

    # Step 5: 刪除優化結果
    result = supabase.table("optimization_results") \
        .delete() \
        .eq("user_id", user_id) \
        .execute()
    stats["optimization_results"] = len(result.data)

    # Step 6: 刪除使用者偏好
    result = supabase.table("user_preferences") \
        .delete() \
        .eq("user_id", user_id) \
        .execute()
    stats["user_preferences"] = len(result.data)

    # Step 7: 刪除 AI 早報（若存在）
    try:
        result = supabase.table("market_briefings") \
            .delete() \
            .eq("user_id", user_id) \
            .execute()
        stats["market_briefings"] = len(result.data)
    except Exception:
        stats["market_briefings"] = 0  # 資料表可能尚未建立

    # Step 8: 最後刪除使用者本身
    result = supabase.table("users") \
        .delete() \
        .eq("id", user_id) \
        .execute()
    stats["users"] = len(result.data)

    return stats
```

---

## 📡 API 端點設計

### DELETE `/api/admin/users/{user_id}`

**請求**：
```
DELETE /api/admin/users/abc-123-def
Authorization: Bearer <admin_jwt_token>
```

**成功回應** (`200 OK`)：
```json
{
  "message": "使用者及所有相關資料已成功刪除",
  "deleted_user_id": "abc-123-def",
  "deleted_counts": {
    "tracked_indices": 12,
    "portfolio_holdings": 45,
    "portfolios": 3,
    "backtest_results": 8,
    "optimization_results": 5,
    "user_preferences": 1,
    "market_briefings": 30,
    "users": 1
  }
}
```

**錯誤回應** (`404 Not Found`)：
```json
{
  "detail": "使用者不存在"
}
```

**錯誤回應** (`403 Forbidden`)：
```json
{
  "detail": "需要管理員權限"
}
```

---

## ⚠️ 注意事項

1. **軟刪除考量**：若未來需要審計記錄或資料恢復功能，可考慮改為軟刪除（在 `users` 資料表新增 `deleted_at` 欄位），而非直接硬刪除。
2. **Redis 快取清除**：刪除使用者後，需同時清除 Redis 中該使用者相關的快取 key（例如 `user:{user_id}:*`）。
3. **操作確認機制**：前端刪除使用者時，應顯示二次確認對話框，列出將被刪除的資料統計，防止誤操作。
4. **不可刪除自己**：管理員不得透過此 API 刪除自己的帳號，後端需進行檢查。
5. **不可刪除最後一個管理員**：後端需確保系統中至少保留一個管理員帳號。

---

## ✅ 實作檢查清單

- [ ] 執行資料庫 Migration SQL，設定所有相關資料表的 `ON DELETE CASCADE` 外鍵約束
- [ ] 在 `app/services/admin_service.py` 中實作 `delete_user_with_cascade()` 函數
- [ ] 在 `app/routers/admin.py` 中實作 `DELETE /api/admin/users/{user_id}` 端點
- [ ] 刪除後清除 Redis 中該使用者相關快取
- [ ] 前端 `UserManagement.vue` 實作刪除確認對話框（顯示將被刪除的資料數量）
- [ ] 後端測試：新增 `tests/test_admin_user_deletion.py` 單元測試

---

## 🔗 相關文件

- [`admin_management_interface.md`](./admin_management_interface.md) — 管理者介面完整設計
- [`future_plan.md`](./future_plan.md) — 整體功能藍圖
