-- Create portfolio_shares table for sharing backtest/optimize results
-- Supports snapshot-based sharing with short codes, 30-day TTL auto-expiry

BEGIN;

-- Main portfolio_shares table
CREATE TABLE IF NOT EXISTS portfolio_shares (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign keys
    portfolio_id UUID NOT NULL REFERENCES backtest_portfolios(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Share metadata
    share_key VARCHAR(20) UNIQUE NOT NULL, -- Format: abc-123-xyz
    share_type VARCHAR(20) DEFAULT 'snapshot', -- 'snapshot' or 'public'
    is_public BOOLEAN DEFAULT true,
    is_archived BOOLEAN DEFAULT false,
    
    -- Snapshot data (immutable once created)
    portfolio_snapshot JSONB NOT NULL, -- Complete portfolio configuration
    portfolio_items_snapshot JSONB[] NOT NULL, -- Holdings snapshot
    
    -- Statistics
    view_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0, -- Number of times shared to social
    
    -- Timestamps
    expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '30 days'),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_share_key CHECK (share_key ~ '^[a-z0-9\-]{10,20}$'),
    CONSTRAINT valid_share_type CHECK (share_type IN ('snapshot', 'public'))
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_portfolio_shares_share_key ON portfolio_shares(share_key);
CREATE INDEX IF NOT EXISTS idx_portfolio_shares_portfolio_id ON portfolio_shares(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_shares_user_id ON portfolio_shares(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_shares_is_public_created ON portfolio_shares(is_public, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_portfolio_shares_expires_at ON portfolio_shares(expires_at);
CREATE INDEX IF NOT EXISTS idx_portfolio_shares_user_created ON portfolio_shares(user_id, created_at DESC);

-- Enable RLS
ALTER TABLE portfolio_shares ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Anyone can view public shares
DROP POLICY IF EXISTS "Anyone can view public shares" ON portfolio_shares;
CREATE POLICY "Anyone can view public shares" ON portfolio_shares
    FOR SELECT USING (is_public = true);

-- RLS Policy: Users can manage their own shares
DROP POLICY IF EXISTS "Users can manage their own shares" ON portfolio_shares;
CREATE POLICY "Users can manage their own shares" ON portfolio_shares
    FOR ALL USING (auth.uid() = user_id);

-- RLS Policy: Users can only create shares for their own portfolios
DROP POLICY IF EXISTS "Users can only create shares for their portfolios" ON portfolio_shares;
CREATE POLICY "Users can only create shares for their portfolios" ON portfolio_shares
    FOR INSERT
    WITH CHECK (
        auth.uid() = user_id AND
        EXISTS(
            SELECT 1 FROM backtest_portfolios 
            WHERE id = portfolio_id AND user_id = auth.uid()
        )
    );

-- Add columns to backtest_portfolios for optional public visibility
ALTER TABLE backtest_portfolios 
    ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT false,
    ADD COLUMN IF NOT EXISTS public_created_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS share_description TEXT,
    ADD COLUMN IF NOT EXISTS share_tags VARCHAR(255)[];

-- Create indexes on new columns in backtest_portfolios
CREATE INDEX IF NOT EXISTS idx_backtest_portfolios_is_public ON backtest_portfolios(is_public)
    WHERE is_public = true;

-- Add comments for documentation
COMMENT ON TABLE portfolio_shares IS 'Immutable snapshots of backtest/optimize/monte_carlo results with short codes for sharing. Auto-expires after 30 days.';
COMMENT ON COLUMN portfolio_shares.share_key IS 'Short code (10-20 chars) for public sharing, e.g. abc-123-xyz';
COMMENT ON COLUMN portfolio_shares.share_type IS 'snapshot: immutable, public: real-time updates';
COMMENT ON COLUMN portfolio_shares.portfolio_snapshot IS 'Complete portfolio config snapshot at share time';
COMMENT ON COLUMN portfolio_shares.portfolio_items_snapshot IS 'Array of portfolio items snapshot';
COMMENT ON COLUMN portfolio_shares.expires_at IS 'Auto-delete after this timestamp (default: +30 days)';

COMMIT;
