BEGIN;

ALTER TABLE portfolio_shares 
    ALTER COLUMN portfolio_id DROP NOT NULL;

ALTER TABLE portfolio_shares 
    ALTER COLUMN portfolio_snapshot DROP NOT NULL;

ALTER TABLE portfolio_shares 
    ALTER COLUMN portfolio_items_snapshot DROP NOT NULL;

ALTER TABLE portfolio_shares 
    ADD COLUMN IF NOT EXISTS image_hash VARCHAR(64);

ALTER TABLE portfolio_shares 
    ADD COLUMN IF NOT EXISTS result_type VARCHAR(20);

ALTER TABLE portfolio_shares
    ADD CONSTRAINT valid_result_type 
    CHECK (result_type IS NULL OR result_type IN ('backtest', 'optimize', 'monte_carlo'));

CREATE INDEX IF NOT EXISTS idx_portfolio_shares_image_hash ON portfolio_shares(image_hash)
    WHERE image_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_portfolio_shares_result_type ON portfolio_shares(result_type)
    WHERE result_type IS NOT NULL;

DROP POLICY IF EXISTS "Users can only create shares for their portfolios" ON portfolio_shares;

CREATE POLICY "Users can only create shares for their portfolios" ON portfolio_shares
    FOR INSERT
    WITH CHECK (
        auth.uid() = user_id AND (
            portfolio_id IS NULL OR
            EXISTS(
                SELECT 1 FROM backtest_portfolios 
                WHERE id = portfolio_id AND user_id = auth.uid()
            )
        )
    );

DROP POLICY IF EXISTS "Service role can manage image shares" ON portfolio_shares;
CREATE POLICY "Service role can manage image shares" ON portfolio_shares
    FOR ALL USING (auth.role() = 'service_role');

COMMENT ON COLUMN portfolio_shares.image_hash IS 'SHA-256 hash of PNG file for image-based sharing. NULL for snapshot shares.';
COMMENT ON COLUMN portfolio_shares.result_type IS 'Type of result: backtest, optimize, or monte_carlo. Used for PNG image shares.';
COMMENT ON COLUMN portfolio_shares.portfolio_id IS 'FK to backtest_portfolios. NULL for image-only shares that do not require a saved portfolio.';

COMMIT;
