-- Migration: Add category column to tracked_indices table
-- Purpose: Support filtering tracking items by category (us_etf, tw_etf, index, vix, oil, crypto, exchange, etc.)
-- Date: 2026-03-24

-- Add category column if it doesn't exist
ALTER TABLE tracked_indices
ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'us_etf' CHECK (category IN ('vix', 'oil', 'us_etf', 'tw_etf', 'index', 'crypto', 'exchange'));

-- Create index for faster category filtering
CREATE INDEX IF NOT EXISTS idx_tracked_indices_category ON tracked_indices(category);
CREATE INDEX IF NOT EXISTS idx_tracked_indices_user_category ON tracked_indices(user_id, category);

-- Update NULL values to default category (infer from symbol if possible)
-- This is a safe operation that won't affect existing non-NULL values
UPDATE tracked_indices
SET category = 'us_etf'
WHERE category IS NULL;

-- Add constraints if needed
COMMENT ON COLUMN tracked_indices.category IS 'Category of tracked index: vix, oil, us_etf, tw_etf, index, crypto, exchange';

-- Note: To rollback this migration, run:
-- ALTER TABLE tracked_indices
-- DROP COLUMN IF EXISTS category;
--
-- DROP INDEX IF EXISTS idx_tracked_indices_category;
-- DROP INDEX IF EXISTS idx_tracked_indices_user_category;
