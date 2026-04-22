BEGIN;

-- 修改 valid_result_type CHECK 約束以支持 'compare' 類型
ALTER TABLE portfolio_shares
    DROP CONSTRAINT valid_result_type;

ALTER TABLE portfolio_shares
    ADD CONSTRAINT valid_result_type 
    CHECK (result_type IS NULL OR result_type IN ('backtest', 'optimize', 'monte_carlo', 'compare'));

COMMENT ON COLUMN portfolio_shares.result_type IS 'Type of result: backtest, optimize, monte_carlo, or compare. Used for PNG image shares.';

COMMIT;
