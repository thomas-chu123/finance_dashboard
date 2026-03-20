-- SQL to add necessary columns to the profiles table for LINE integration

ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS line_binding_code TEXT,
ADD COLUMN IF NOT EXISTS line_binding_expires_at TIMESTAMPTZ;

-- Index for faster lookup during webhook handling
CREATE INDEX IF NOT EXISTS idx_profiles_line_binding_code ON profiles(line_binding_code);
