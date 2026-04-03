-- Portfolio Results Consolidation Migration
-- Created: 2026-04-02
-- Purpose: Consolidate optimization_results, optimization_items, monte_carlo_results, monte_carlo_items into backtest_portfolios with portfolio_type discriminator

-- 1. Drop old result tables (in reverse dependency order)
DROP TABLE IF EXISTS optimization_items CASCADE;
DROP TABLE IF EXISTS optimization_results CASCADE;
DROP TABLE IF EXISTS monte_carlo_items CASCADE;
DROP TABLE IF EXISTS monte_carlo_results CASCADE;

-- 2. Add portfolio_type column to backtest_portfolios
ALTER TABLE backtest_portfolios ADD COLUMN IF NOT EXISTS portfolio_type VARCHAR(50) DEFAULT 'backtest';

-- 3. Make start_date and end_date nullable (for optimize and monte_carlo which don't use them)
ALTER TABLE backtest_portfolios 
  ALTER COLUMN start_date DROP NOT NULL,
  ALTER COLUMN end_date DROP NOT NULL;

-- 4. Create index on portfolio_type for faster filtering
CREATE INDEX IF NOT EXISTS idx_backtest_portfolios_user_id_type ON backtest_portfolios(user_id, portfolio_type);

-- portfolio_type values:
-- 'backtest' - Results from BacktestView (requires start_date, end_date)
-- 'optimize' - Results from OptimizeView (start_date/end_date are optional)
-- 'monte_carlo' - Results from MonteCarloView (start_date/end_date are optional)
