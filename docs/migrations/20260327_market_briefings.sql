-- ============================================================
-- Migration: Create market_briefings table
-- Date: 2026-03-27
-- Purpose: AI Daily Market Briefing feature
-- ============================================================

-- 1. 建立 market_briefings 表
CREATE TABLE IF NOT EXISTS market_briefings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_time    TIMESTAMPTZ NOT NULL,
    symbol          VARCHAR(20) NOT NULL,
    symbol_name     TEXT,
    news_json       JSONB NOT NULL DEFAULT '[]',
    summary_text    TEXT,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'completed', 'failed')),
    error_message   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),

    -- 確保同一排程批次內每個 symbol 只有一筆記錄（支援 upsert）
    CONSTRAINT uq_mb_session_symbol UNIQUE (session_time, symbol)
);

-- 2. 索引
CREATE INDEX IF NOT EXISTS idx_mb_session_time ON market_briefings (session_time DESC);
CREATE INDEX IF NOT EXISTS idx_mb_symbol       ON market_briefings (symbol);

-- 3. 啟用 Row Level Security
ALTER TABLE market_briefings ENABLE ROW LEVEL SECURITY;

-- 4. RLS 政策：已認證使用者可讀取所有早報記錄
CREATE POLICY briefings_read
    ON market_briefings
    FOR SELECT
    TO authenticated
    USING (true);

-- （可選）只允許 service_role 寫入，避免前端直接寫入
-- CREATE POLICY briefings_insert_service
--     ON market_briefings
--     FOR INSERT
--     TO service_role
--     WITH CHECK (true);
