-- 管理者管理系統資料庫遷移
-- 建立日期: 2026-04-01

-- ===================================================================
-- 1. 審計日誌表 (audit_logs)
-- ===================================================================
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    action TEXT NOT NULL,
    target_user_id UUID,
    changes JSONB,
    ip_address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 審計日誌索引以加速查詢
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON public.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON public.audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON public.audit_logs(action);

-- 說明: user_id 不再受外鍵約束，允許記錄已刪除用戶的操作以保持完整的審計日誌
COMMENT ON COLUMN public.audit_logs.user_id IS 
'執行操作的用戶 ID。移除外鍵約束以允許記錄已刪除用戶的審計操作。';

-- ===================================================================
-- 2. 系統日誌表 (system_logs)
-- ===================================================================
CREATE TABLE IF NOT EXISTS public.system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level TEXT NOT NULL,
    component TEXT NOT NULL,
    message TEXT NOT NULL,
    stack_trace TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 系統日誌索引
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON public.system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_component ON public.system_logs(component);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON public.system_logs(created_at DESC);

-- ===================================================================
-- 3. Scheduler 任務追蹤表 (scheduler_jobs)
-- ===================================================================
CREATE TABLE IF NOT EXISTS public.scheduler_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id TEXT UNIQUE NOT NULL,
    job_name TEXT NOT NULL,
    description TEXT,
    schedule_cron TEXT,
    is_enabled BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    status TEXT DEFAULT 'idle',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Scheduler 任務索引
CREATE INDEX IF NOT EXISTS idx_scheduler_jobs_job_id ON public.scheduler_jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_scheduler_jobs_is_enabled ON public.scheduler_jobs(is_enabled);

-- ===================================================================
-- 4. Scheduler 執行歷史表 (scheduler_job_runs)
-- ===================================================================
CREATE TABLE IF NOT EXISTS public.scheduler_job_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES public.scheduler_jobs(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    status TEXT,
    duration_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Scheduler 執行歷史索引
CREATE INDEX IF NOT EXISTS idx_scheduler_job_runs_job_id ON public.scheduler_job_runs(job_id);
CREATE INDEX IF NOT EXISTS idx_scheduler_job_runs_created_at ON public.scheduler_job_runs(created_at DESC);

-- ===================================================================
-- 5. RLS 策略 - audit_logs
-- ===================================================================
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- 只有管理員可以查看所有審計日誌
CREATE POLICY "只有管理員可以查看審計日誌" 
    ON public.audit_logs 
    FOR SELECT 
    USING (
        auth.uid() IS NOT NULL 
        AND EXISTS (
            SELECT 1 FROM profiles 
            WHERE profiles.id = auth.uid() 
            AND profiles.is_admin = true
        )
    );

-- 只有系統可以寫入審計日誌（透過 service_role）
-- 此策略允許認證用戶透過後端 API 寫入
CREATE POLICY "允許寫入審計日誌"
    ON public.audit_logs 
    FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

-- ===================================================================
-- 6. RLS 策略 - system_logs
-- ===================================================================
ALTER TABLE public.system_logs ENABLE ROW LEVEL SECURITY;

-- 只有管理員可以查看系統日誌
CREATE POLICY "只有管理員可以查看系統日誌" 
    ON public.system_logs 
    FOR SELECT 
    USING (
        auth.uid() IS NOT NULL 
        AND EXISTS (
            SELECT 1 FROM profiles 
            WHERE profiles.id = auth.uid() 
            AND profiles.is_admin = true
        )
    );

-- ===================================================================
-- 7. RLS 策略 - scheduler_jobs
-- ===================================================================
ALTER TABLE public.scheduler_jobs ENABLE ROW LEVEL SECURITY;

-- 只有管理員可以查看和管理 scheduler 任務
CREATE POLICY "只有管理員可以查看 scheduler 任務" 
    ON public.scheduler_jobs 
    FOR SELECT 
    USING (
        auth.uid() IS NOT NULL 
        AND EXISTS (
            SELECT 1 FROM profiles 
            WHERE profiles.id = auth.uid() 
            AND profiles.is_admin = true
        )
    );

CREATE POLICY "只有管理員可以更新 scheduler 任務"
    ON public.scheduler_jobs 
    FOR UPDATE 
    USING (
        auth.uid() IS NOT NULL 
        AND EXISTS (
            SELECT 1 FROM profiles 
            WHERE profiles.id = auth.uid() 
            AND profiles.is_admin = true
        )
    );

-- ===================================================================
-- 8. RLS 策略 - scheduler_job_runs
-- ===================================================================
ALTER TABLE public.scheduler_job_runs ENABLE ROW LEVEL SECURITY;

-- 只有管理員可以查看任務執行歷史
CREATE POLICY "只有管理員可以查看任務執行歷史" 
    ON public.scheduler_job_runs 
    FOR SELECT 
    USING (
        auth.uid() IS NOT NULL 
        AND EXISTS (
            SELECT 1 FROM profiles 
            WHERE profiles.id = auth.uid() 
            AND profiles.is_admin = true
        )
    );

-- ===================================================================
-- 9. 級聯刪除設定
-- ===================================================================
-- 當使用者被刪除時，級聯刪除相關表中的記錄
-- 注意：依賴順序很重要，必須先刪除有外鍵的表

-- alert_logs 已有 ON DELETE CASCADE
-- notification_logs 已有 ON DELETE CASCADE 
-- backtest_results 更新以支援級聯刪除
-- optimization_results 更新以支援級聯刪除
-- portfolio_holdings 已有 ON DELETE CASCADE
-- portfolios 已有 ON DELETE CASCADE
-- tracked_indices 已有 ON DELETE CASCADE
-- user_preferences 已有 ON DELETE CASCADE

-- 檢查並更新 tracked_indices 表（確保有 ON DELETE CASCADE）
-- 如果不存在，可透過後端應用層實現級聯刪除

-- ===================================================================
-- 10. 觸發函數 - 自動更新 scheduler_jobs.updated_at
-- ===================================================================
CREATE OR REPLACE FUNCTION update_scheduler_jobs_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 建立觸發器
DROP TRIGGER IF EXISTS update_scheduler_jobs_timestamp_trigger ON public.scheduler_jobs;
CREATE TRIGGER update_scheduler_jobs_timestamp_trigger
    BEFORE UPDATE ON public.scheduler_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_scheduler_jobs_timestamp();

-- ===================================================================
-- 11. 初始化 Scheduler 任務資料（參考現有任務）
-- ===================================================================
INSERT INTO public.scheduler_jobs (job_id, job_name, description, schedule_cron, is_enabled)
VALUES 
    ('price_check', '價格檢查', '每 30 分鐘檢查追蹤指數價格並送出警報', 'interval:30m', TRUE),
    ('tw_etf_sync', '台灣 ETF 同步', '每日 01:00 同步台灣 ETF 清單', '0 1 * * *', TRUE),
    ('us_etf_sync', '美股 ETF 同步', '每日 02:00 同步美股 ETF 清單', '0 2 * * *', TRUE),
    ('briefing_0800', '市場早報 08:00', '每日 08:00 生成市場早報', '0 8 * * *', TRUE),
    ('briefing_1300', '市場早報 13:00', '每日 13:00 生成市場早報', '0 13 * * *', TRUE),
    ('briefing_1800', '市場早報 18:00', '每日 18:00 生成市場早報', '0 18 * * *', TRUE),
    ('dividend_sync', '除權息同步', '每日 06:00 同步除權息日曆', '0 6 * * *', TRUE),
    ('dividend_notify', '除權息通知', '每日 06:30 檢查除權息通知', '30 6 * * *', TRUE)
ON CONFLICT (job_id) DO NOTHING;
