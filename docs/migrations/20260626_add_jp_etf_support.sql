-- Add Japan ETF asset category and JPX ETF list table.

ALTER TYPE public.index_category ADD VALUE IF NOT EXISTS 'jp_etf' AFTER 'tw_etf';

CREATE TABLE IF NOT EXISTS public.jp_etf_list (
    symbol TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    index_name TEXT,
    management_company TEXT,
    trading_unit TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jp_etf_list_name ON public.jp_etf_list(name);
CREATE INDEX IF NOT EXISTS idx_jp_etf_list_updated_at ON public.jp_etf_list(updated_at);

COMMENT ON TABLE public.jp_etf_list IS 'Japan ETF list synced from JPX ETF issues page.';
COMMENT ON COLUMN public.jp_etf_list.symbol IS 'JPX security code without Yahoo Finance .T suffix.';
