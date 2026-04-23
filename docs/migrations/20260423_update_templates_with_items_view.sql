-- Update portfolio_templates_with_items view to include category field
-- This view now provides a complete view of templates with all item details
-- including the newly added category field

CREATE OR REPLACE VIEW public.portfolio_templates_with_items AS
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
            'weight', ti.weight,
            'category', ti.category
        ) ORDER BY ti.display_order
    ) as items
FROM public.portfolio_templates t
LEFT JOIN public.portfolio_template_items ti ON t.id = ti.template_id
WHERE t.is_active = true
GROUP BY t.id, t.name, t.description, t.display_order;
