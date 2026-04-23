-- Shared Portfolio Architecture Migration
-- Created: 2026-04-23
-- Purpose: Allow backtest, optimize, and monte_carlo modules to share the same portfolio
--          by storing their results in separate JSONB columns

-- 1. Add new result columns for each module
ALTER TABLE backtest_portfolios 
  ADD COLUMN IF NOT EXISTS backtest_results_json JSONB DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS optimize_results_json JSONB DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS monte_carlo_results_json JSONB DEFAULT NULL;

-- 2. Create indexes on the new columns for faster queries
CREATE INDEX IF NOT EXISTS idx_backtest_results_json ON backtest_portfolios 
  USING gin (backtest_results_json);
CREATE INDEX IF NOT EXISTS idx_optimize_results_json ON backtest_portfolios 
  USING gin (optimize_results_json);
CREATE INDEX IF NOT EXISTS idx_monte_carlo_results_json ON backtest_portfolios 
  USING gin (monte_carlo_results_json);

-- 3. Migrate existing results_json data based on portfolio_type
-- This preserves existing data while preparing for the new architecture
UPDATE backtest_portfolios
SET backtest_results_json = results_json
WHERE portfolio_type = 'backtest' AND backtest_results_json IS NULL;

UPDATE backtest_portfolios
SET optimize_results_json = results_json
WHERE portfolio_type = 'optimize' AND optimize_results_json IS NULL;

UPDATE backtest_portfolios
SET monte_carlo_results_json = results_json
WHERE portfolio_type = 'monte_carlo' AND monte_carlo_results_json IS NULL;

-- 4. Optional: Keep portfolio_type for now for backward compatibility
--    Will be removed in a future migration after full rollout
-- Note: portfolio_type will no longer be used for filtering in the backend
--       but keeping it for reference/debugging purposes

-- 5. Drop the old index that filters by portfolio_type
-- (no longer needed once all backends are updated)
-- DROP INDEX IF EXISTS idx_backtest_portfolios_user_id_type;
