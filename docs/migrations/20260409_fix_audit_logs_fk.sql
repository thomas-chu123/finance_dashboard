-- 修復 audit_logs 外鍵約束
-- 目的: 移除 audit_logs.user_id 對 auth.users 的外鍵約束
-- 原因: 刪除用戶時無法記錄審計日誌，因為執行管理員的 user_id 檢查失敗
-- 日期: 2026-04-09

-- ===================================================================
-- 移除外鍵約束
-- ===================================================================
ALTER TABLE public.audit_logs 
DROP CONSTRAINT IF EXISTS audit_logs_user_id_fkey;

-- 確保 user_id 和 target_user_id 欄位允許 NULL（以防未來有需要）
ALTER TABLE public.audit_logs 
ALTER COLUMN user_id DROP NOT NULL;

-- 添加備註以解釋為什麼移除了外鍵約束
COMMENT ON COLUMN public.audit_logs.user_id IS 
'執行操作的用戶 ID。不再受外鍵約束，允許記錄已刪除用戶的操作以保持完整的審計日誌。';

-- ===================================================================
-- 驗證
-- ===================================================================
-- 檢查約束是否已移除
-- SELECT constraint_name FROM information_schema.table_constraints 
-- WHERE table_name='audit_logs' AND constraint_type='FOREIGN KEY';
