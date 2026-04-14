-- Add 'funds' to index_category ENUM type
ALTER TYPE public.index_category ADD VALUE 'funds' AFTER 'tw_etf';

-- Verify the migration
-- SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid 
-- WHERE pg_type.typname = 'index_category' ORDER BY enumsortorder;
