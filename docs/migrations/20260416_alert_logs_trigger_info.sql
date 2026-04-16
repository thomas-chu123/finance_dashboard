-- Add trigger reason and RSI information columns to alert_logs table
-- This enables tracking why alerts were triggered and capturing RSI metrics

BEGIN;

-- Add new columns to alert_logs table
ALTER TABLE alert_logs ADD COLUMN IF NOT EXISTS trigger_reason VARCHAR(50);
ALTER TABLE alert_logs ADD COLUMN IF NOT EXISTS trigger_details JSONB;
ALTER TABLE alert_logs ADD COLUMN IF NOT EXISTS rsi_value FLOAT;
ALTER TABLE alert_logs ADD COLUMN IF NOT EXISTS rsi_threshold FLOAT;

-- Create index on trigger_reason for efficient filtering
CREATE INDEX IF NOT EXISTS idx_alert_logs_trigger_reason 
ON alert_logs(trigger_reason, created_at DESC);

-- Create index on user_id + trigger_reason for common queries
CREATE INDEX IF NOT EXISTS idx_alert_logs_user_trigger 
ON alert_logs(user_id, trigger_reason, created_at DESC);

-- Add comment for documentation
COMMENT ON COLUMN alert_logs.trigger_reason IS 'Alert trigger type: rsi_oversold, rsi_overbought, dividend_ex_date, price_alert_above, price_alert_below';
COMMENT ON COLUMN alert_logs.trigger_details IS 'JSON object containing detailed trigger information (e.g., rsi_value, dividend_amount)';
COMMENT ON COLUMN alert_logs.rsi_value IS 'RSI value at time of alert trigger';
COMMENT ON COLUMN alert_logs.rsi_threshold IS 'RSI threshold that triggered the alert (e.g., 30 or 70)';

COMMIT;
