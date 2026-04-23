-- Add category column to portfolio_template_items
-- This allows templates to pre-define the category of each item, eliminating
-- the need for symbol-based inference during portfolio copying.

ALTER TABLE public.portfolio_template_items 
ADD COLUMN IF NOT EXISTS category index_category NOT NULL DEFAULT 'index';

-- Update category for Taiwan ETFs (by symbol pattern or known codes)
UPDATE public.portfolio_template_items 
SET category = 'tw_etf' 
WHERE symbol LIKE '%.TW' 
   OR symbol LIKE '%.TWO'
   OR symbol IN (
       '0050', '0056', '00878', '006208', '0070', '0051', '00752', '00713',
       '00919', '00900', '00929', '00940', '00950', '0071', '00880', '00881',
       '006204', '006205', '006206', '006207'
   );

-- Update category for US ETFs
UPDATE public.portfolio_template_items 
SET category = 'us_etf' 
WHERE symbol LIKE '%.US'
   OR symbol IN (
       'SPY', 'QQQ', 'IVV', 'VOO', 'VTI', 'BND', 'AGG', 'VWO', 'VEA', 'VXUS'
   );

-- Verify the update
SELECT symbol, category, COUNT(*) as cnt 
FROM public.portfolio_template_items 
GROUP BY symbol, category 
ORDER BY symbol;
