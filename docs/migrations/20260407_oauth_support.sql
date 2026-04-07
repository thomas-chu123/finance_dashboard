-- OAuth Support Migration
-- Migration Date: 2026-04-07
-- Description: Add OAuth support fields to profiles table
-- Changes: Add google_id, oauth_provider, picture_url, oauth_created_at

-- Add OAuth support columns to profiles table
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS google_id TEXT UNIQUE;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS oauth_provider TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS picture_url TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS oauth_created_at TIMESTAMP WITH TIME ZONE;

-- Create indexes for OAuth columns
CREATE INDEX IF NOT EXISTS idx_profiles_google_id ON profiles(google_id);
CREATE INDEX IF NOT EXISTS idx_profiles_oauth_provider ON profiles(oauth_provider);
CREATE INDEX IF NOT EXISTS idx_profiles_oauth_created_at ON profiles(oauth_created_at);

-- Add column comments for documentation
COMMENT ON COLUMN profiles.google_id IS 'Google OAuth ID for user identification';
COMMENT ON COLUMN profiles.oauth_provider IS 'OAuth provider identifier (e.g., google, github)';
COMMENT ON COLUMN profiles.picture_url IS 'User profile picture URL from OAuth provider';
COMMENT ON COLUMN profiles.oauth_created_at IS 'Timestamp when OAuth account was linked';

-- Verification queries
-- Run these to verify the migration was successful:
-- SELECT column_name, data_type, is_nullable FROM information_schema.columns
--   WHERE table_name = 'profiles' AND column_name IN ('google_id', 'oauth_provider', 'picture_url', 'oauth_created_at');
-- SELECT indexname FROM pg_indexes WHERE tablename = 'profiles' AND indexname LIKE 'idx_profiles_oauth%';

