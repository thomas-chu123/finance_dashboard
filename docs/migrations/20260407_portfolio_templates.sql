-- ============================================================
-- Migration: Portfolio Templates System
-- Date: 2026-04-07
-- Purpose: Create default portfolio templates for new users
-- ============================================================

-- 1. 建立 portfolio_templates 表
CREATE TABLE IF NOT EXISTS public.portfolio_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_template_name UNIQUE(name)
);

-- 2. 建立 portfolio_template_items 表
CREATE TABLE IF NOT EXISTS public.portfolio_template_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES public.portfolio_templates(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(255),
    weight DECIMAL(5,2) NOT NULL CHECK (weight > 0 AND weight <= 100),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_template_item UNIQUE(template_id, symbol)
);

-- 3. 建立索引
CREATE INDEX IF NOT EXISTS idx_portfolio_templates_active ON public.portfolio_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_portfolio_templates_order ON public.portfolio_templates(display_order);
CREATE INDEX IF NOT EXISTS idx_portfolio_template_items_template ON public.portfolio_template_items(template_id);

-- 4. 啟用 Row Level Security
ALTER TABLE public.portfolio_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portfolio_template_items ENABLE ROW LEVEL SECURITY;

-- 5. RLS 政策：已認證使用者可讀取所有模板
CREATE POLICY "templates_read_all"
    ON public.portfolio_templates
    FOR SELECT
    TO authenticated
    USING (is_active = true);

CREATE POLICY "template_items_read_all"
    ON public.portfolio_template_items
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.portfolio_templates
            WHERE portfolio_templates.id = portfolio_template_items.template_id
            AND portfolio_templates.is_active = true
        )
    );

-- 6. 插入預設模板資料
INSERT INTO public.portfolio_templates (name, description, display_order, is_active) VALUES
    ('元大穩健核心型', '50% 0050 + 50% 0056 的穩健組合', 1, true),
    ('富邦國泰穩健核心型', '50% 006208 + 50% 00878 的穩健組合', 2, true),
    ('台股etf月月配型', '40% 0056 + 30% 00878 + 30% 00919 的配息組合', 3, true),
    ('台股etf防禦槓鈴型', '50% 00878 + 50% 00713 的防禦組合', 4, true),
    ('Vanguard全世界(股票)', '60% VTI + 40% VXUS 的全球股票組合', 5, true),
    ('Vanguard全世界(股債)', '60% VT + 40% BND 的股債平衡組合', 6, true),
    ('美國科技成長型', '50% VOO + 50% QQQ 的科技成長組合', 7, true)
ON CONFLICT (name) DO NOTHING;

-- 7. 插入模板項目資料
DO $$
DECLARE
    t1_id UUID;
    t2_id UUID;
    t3_id UUID;
    t4_id UUID;
    t5_id UUID;
    t6_id UUID;
    t7_id UUID;
BEGIN
    -- 取得各個模板的 ID
    SELECT id INTO t1_id FROM public.portfolio_templates WHERE name = '元大穩健核心型';
    SELECT id INTO t2_id FROM public.portfolio_templates WHERE name = '富邦國泰穩健核心型';
    SELECT id INTO t3_id FROM public.portfolio_templates WHERE name = '台股etf月月配型';
    SELECT id INTO t4_id FROM public.portfolio_templates WHERE name = '台股etf防禦槓鈴型';
    SELECT id INTO t5_id FROM public.portfolio_templates WHERE name = 'Vanguard全世界(股票)';
    SELECT id INTO t6_id FROM public.portfolio_templates WHERE name = 'Vanguard全世界(股債)';
    SELECT id INTO t7_id FROM public.portfolio_templates WHERE name = '美國科技成長型';
    
    -- 模板 1: 元大穩健核心型
    INSERT INTO public.portfolio_template_items (template_id, symbol, name, weight, display_order) VALUES
        (t1_id, '0050', '元大台灣50', 50.00, 1),
        (t1_id, '0056', '元大高股息', 50.00, 2)
    ON CONFLICT (template_id, symbol) DO NOTHING;
    
    -- 模板 2: 富邦國泰穩健核心型
    INSERT INTO public.portfolio_template_items (template_id, symbol, name, weight, display_order) VALUES
        (t2_id, '006208', '富邦台灣優質高息', 50.00, 1),
        (t2_id, '00878', '國泰永續高股息', 50.00, 2)
    ON CONFLICT (template_id, symbol) DO NOTHING;
    
    -- 模板 3: 台股etf月月配型
    INSERT INTO public.portfolio_template_items (template_id, symbol, name, weight, display_order) VALUES
        (t3_id, '0056', '元大高股息', 40.00, 1),
        (t3_id, '00878', '國泰永續高股息', 30.00, 2),
        (t3_id, '00919', '群益台灣精選高息', 30.00, 3)
    ON CONFLICT (template_id, symbol) DO NOTHING;
    
    -- 模板 4: 台股etf防禦槓鈴型
    INSERT INTO public.portfolio_template_items (template_id, symbol, name, weight, display_order) VALUES
        (t4_id, '00878', '國泰永續高股息', 50.00, 1),
        (t4_id, '00713', '元大台灣公司治理', 50.00, 2)
    ON CONFLICT (template_id, symbol) DO NOTHING;
    
    -- 模板 5: Vanguard全世界(股票)
    INSERT INTO public.portfolio_template_items (template_id, symbol, name, weight, display_order) VALUES
        (t5_id, 'VTI', 'Vanguard Total Stock Market', 60.00, 1),
        (t5_id, 'VXUS', 'Vanguard Total International Stock', 40.00, 2)
    ON CONFLICT (template_id, symbol) DO NOTHING;
    
    -- 模板 6: Vanguard全世界(股債)
    INSERT INTO public.portfolio_template_items (template_id, symbol, name, weight, display_order) VALUES
        (t6_id, 'VT', 'Vanguard Total World Stock', 60.00, 1),
        (t6_id, 'BND', 'Vanguard Total Bond Market', 40.00, 2)
    ON CONFLICT (template_id, symbol) DO NOTHING;
    
    -- 模板 7: 美國科技成長型
    INSERT INTO public.portfolio_template_items (template_id, symbol, name, weight, display_order) VALUES
        (t7_id, 'VOO', 'Vanguard S&P 500', 50.00, 1),
        (t7_id, 'QQQ', 'Invesco QQQ Trust', 50.00, 2)
    ON CONFLICT (template_id, symbol) DO NOTHING;
END $$;

-- 8. 建立檢視 (視圖)，方便查詢模板及其項目
CREATE OR REPLACE VIEW portfolio_templates_with_items AS
SELECT 
    t.id as template_id,
    t.name as template_name,
    t.description,
    t.display_order,
    json_agg(
        json_build_object(
            'id', ti.id,
            'symbol', ti.symbol,
            'name', ti.name,
            'weight', ti.weight
        ) ORDER BY ti.display_order
    ) as items
FROM public.portfolio_templates t
LEFT JOIN public.portfolio_template_items ti ON t.id = ti.template_id
WHERE t.is_active = true
GROUP BY t.id, t.name, t.description, t.display_order;

