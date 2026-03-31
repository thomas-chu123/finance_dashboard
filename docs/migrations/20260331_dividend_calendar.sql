-- Dividend Calendar -- public ex-dividend/ex-right data
-- Source: TWSE https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL
-- Synced daily at 06:00 Asia/Taipei

CREATE TABLE IF NOT EXISTS dividend_calendar (
    id                   UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    code                 VARCHAR(20)   NOT NULL,
    name                 TEXT          NOT NULL,
    ex_date              DATE          NOT NULL,
    ex_type              VARCHAR(10)   NOT NULL,
    cash_dividend        NUMERIC(12,6),
    stock_dividend_ratio TEXT          DEFAULT '',
    subscription_ratio   TEXT          DEFAULT '',
    subscription_price   NUMERIC(12,4),
    raw_data             JSONB         DEFAULT '{}',
    updated_at           TIMESTAMPTZ   DEFAULT NOW(),
    CONSTRAINT uq_dividend_code_exdate UNIQUE (code, ex_date, ex_type)
);

CREATE INDEX IF NOT EXISTS idx_dc_ex_date ON dividend_calendar(ex_date DESC);
CREATE INDEX IF NOT EXISTS idx_dc_code    ON dividend_calendar(code);

ALTER TABLE dividend_calendar ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS dc_read ON dividend_calendar;
CREATE POLICY dc_read ON dividend_calendar
    FOR SELECT TO authenticated USING (true);
