-- Store the Japanese JPX fund name alongside the English name.
ALTER TABLE public.jp_etf_list
    ADD COLUMN IF NOT EXISTS name_ja TEXT;

COMMENT ON COLUMN public.jp_etf_list.name_ja IS 'Japanese fund name from the Japanese JPX ETF issues page.';
