-- Migration: Add RSI trigger columns to tracked_indices table
-- Purpose: Support RSI-based and composite trigger conditions for alerts
-- Date: 2026-03-24

-- Add RSI-related columns to tracked_indices
ALTER TABLE tracked_indices
ADD COLUMN IF NOT EXISTS trigger_mode TEXT DEFAULT 'price' CHECK (trigger_mode IN ('price', 'rsi', 'both')),
ADD COLUMN IF NOT EXISTS rsi_period INTEGER DEFAULT 14 CHECK (rsi_period >= 7 AND rsi_period <= 50),
ADD COLUMN IF NOT EXISTS rsi_below NUMERIC(5,2),
ADD COLUMN IF NOT EXISTS rsi_above NUMERIC(5,2),
ADD COLUMN IF NOT EXISTS current_rsi NUMERIC(5,2),
ADD COLUMN IF NOT EXISTS rsi_updated_at TIMESTAMPTZ;

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_tracked_indices_trigger_mode ON tracked_indices(trigger_mode);
CREATE INDEX IF NOT EXISTS idx_tracked_indices_is_active_trigger_mode ON tracked_indices(is_active, trigger_mode);
CREATE INDEX IF NOT EXISTS idx_tracked_indices_rsi ON tracked_indices(current_rsi);

-- Add comment for documentation
COMMENT ON COLUMN tracked_indices.trigger_mode IS 'Alert trigger mode: price, rsi, or both';
COMMENT ON COLUMN tracked_indices.rsi_period IS 'RSI calculation period (7-50 days)';
COMMENT ON COLUMN tracked_indices.rsi_below IS 'RSI oversold threshold (alert if RSI < this value)';
COMMENT ON COLUMN tracked_indices.rsi_above IS 'RSI overbought threshold (alert if RSI > this value)';
COMMENT ON COLUMN tracked_indices.current_rsi IS 'Current RSI value (0-100)';
COMMENT ON COLUMN tracked_indices.rsi_updated_at IS 'Timestamp when RSI was last calculated';

-- Note: To rollback this migration, run:
-- ALTER TABLE tracked_indices
-- DROP COLUMN IF EXISTS trigger_mode,
-- DROP COLUMN IF EXISTS rsi_period,
-- DROP COLUMN IF EXISTS rsi_below,
-- DROP COLUMN IF EXISTS rsi_above,
-- DROP COLUMN IF EXISTS current_rsi,
-- DROP COLUMN IF EXISTS rsi_updated_at;
--
-- DROP INDEX IF EXISTS idx_tracked_indices_trigger_mode;
-- DROP INDEX IF EXISTS idx_tracked_indices_is_active_trigger_mode;
-- DROP INDEX IF EXISTS idx_tracked_indices_rsi;
