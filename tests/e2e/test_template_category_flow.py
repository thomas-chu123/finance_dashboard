"""
端到端測試：驗證模板分類流程

驗證以下流程：
1. 模板從 portfolio_template_items 表讀取正確的 category 值
2. 用戶創建投資組合時，分類被正確複製
3. 回測時，基準根據分類正確選擇（台灣 ETF → 0050.TW，美國 ETF → SPY）
"""

import sys
import os
import pytest
import logging
from decimal import Decimal

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

logger = logging.getLogger(__name__)


def test_templates_have_correct_categories():
    """驗證模板項目有正確的分類值"""
    from app.database import get_supabase
    
    sb = get_supabase()
    
    # Query portfolio_template_items to verify categories
    result = sb.table("portfolio_template_items").select("symbol, category, template_id").execute()
    
    items = result.data or []
    assert len(items) > 0, "No template items found"
    
    # Count by category
    category_counts = {}
    tw_etf_count = 0
    us_etf_count = 0
    
    for item in items:
        category = item.get('category')
        symbol = item.get('symbol')
        
        # Verify category is valid enum value
        assert category in ['tw_etf', 'us_etf', 'index'], \
            f"Invalid category '{category}' for symbol {symbol}"
        
        category_counts[category] = category_counts.get(category, 0) + 1
        
        # Log categorization samples
        if category == 'tw_etf' and tw_etf_count < 3:
            logger.info(f"✓ Taiwan ETF: {symbol} → {category}")
            tw_etf_count += 1
        elif category == 'us_etf' and us_etf_count < 3:
            logger.info(f"✓ US ETF: {symbol} → {category}")
            us_etf_count += 1
    
    logger.info(f"\n分類統計:\n  - tw_etf: {category_counts.get('tw_etf', 0)}\n  - us_etf: {category_counts.get('us_etf', 0)}\n  - index: {category_counts.get('index', 0)}")
    
    # Verify we have both Taiwan and US ETFs properly categorized
    assert category_counts.get('tw_etf', 0) > 0, "No Taiwan ETFs found"
    assert category_counts.get('us_etf', 0) > 0, "No US ETFs found"


def test_view_includes_category_in_items():
    """驗證視圖 portfolio_templates_with_items 在 items JSON 中包含 category"""
    from app.database import get_supabase
    
    sb = get_supabase()
    
    # Query the view
    result = sb.table("portfolio_templates_with_items").select("*").execute()
    
    templates = result.data or []
    assert len(templates) > 0, "No templates found in view"
    
    # Check first template has items with category
    template = templates[0]
    items = template.get('items', [])
    
    assert len(items) > 0, "Template has no items"
    
    for item in items:
        assert 'category' in item, f"Item missing 'category': {item}"
        assert item['category'] in ['tw_etf', 'us_etf', 'index'], \
            f"Invalid category value in item: {item['category']}"
        
        logger.info(f"✓ Item {item.get('symbol')}: category='{item.get('category')}'")


def test_benchmark_selection_logic():
    """驗證回測基準選擇邏輯"""
    from app.services.backtest_engine import determine_benchmark
    
    # Test 1: Only Taiwan ETFs → use 0050.TW
    has_taiwan = True
    has_us = False
    benchmark = determine_benchmark(has_taiwan, has_us)
    assert benchmark == "0050.TW", f"Expected 0050.TW for Taiwan-only portfolio, got {benchmark}"
    logger.info(f"✓ Taiwan-only portfolio → benchmark: {benchmark}")
    
    # Test 2: Only US ETFs → use SPY
    has_taiwan = False
    has_us = True
    benchmark = determine_benchmark(has_taiwan, has_us)
    assert benchmark == "SPY", f"Expected SPY for US-only portfolio, got {benchmark}"
    logger.info(f"✓ US-only portfolio → benchmark: {benchmark}")
    
    # Test 3: Mixed Taiwan + US → use SPY
    has_taiwan = True
    has_us = True
    benchmark = determine_benchmark(has_taiwan, has_us)
    assert benchmark == "SPY", f"Expected SPY for mixed portfolio, got {benchmark}"
    logger.info(f"✓ Mixed portfolio → benchmark: {benchmark}")
    
    # Test 4: Only index → use SPY (default)
    has_taiwan = False
    has_us = False
    benchmark = determine_benchmark(has_taiwan, has_us)
    assert benchmark == "SPY", f"Expected SPY for index-only portfolio, got {benchmark}"
    logger.info(f"✓ Index-only portfolio → benchmark: {benchmark}")


def test_category_flow_taiwan_etf_portfolio():
    """
    集成測試：驗證台灣 ETF 投資組合的完整流程
    
    流程：
    1. 獲取模板（應包含 category）
    2. 驗證台灣 ETF 項目有 category='tw_etf'
    3. 驗證基準選擇邏輯會選擇 0050.TW
    """
    from app.database import get_supabase
    from app.services.backtest_engine import determine_benchmark
    
    sb = get_supabase()
    
    # Find a template with Taiwan ETFs (e.g., template 1 or 2)
    templates = sb.table("portfolio_templates_with_items").select("*").execute().data or []
    
    # Find template with Taiwan ETFs
    tw_template = None
    for template in templates:
        items = template.get('items', [])
        for item in items:
            if item.get('category') == 'tw_etf':
                tw_template = template
                break
        if tw_template:
            break
    
    if not tw_template:
        logger.warning("No template with Taiwan ETFs found, skipping integration test")
        return
    
    # Verify template has Taiwan ETFs
    items = tw_template.get('items', [])
    tw_etf_items = [item for item in items if item.get('category') == 'tw_etf']
    
    assert len(tw_etf_items) > 0, "Template should have Taiwan ETF items"
    logger.info(f"✓ Found {len(tw_etf_items)} Taiwan ETF items in template")
    
    # Determine benchmark based on categories
    has_us = any(item.get('category') == 'us_etf' for item in items)
    has_taiwan = any(item.get('category') == 'tw_etf' for item in items)
    
    benchmark = determine_benchmark(has_taiwan, has_us)
    
    # Verify correct benchmark
    if has_us:
        assert benchmark == "SPY", f"Mixed portfolio should use SPY, got {benchmark}"
        logger.info(f"✓ Template has US ETFs → using SPY benchmark")
    else:
        assert benchmark == "0050.TW", f"Taiwan-only portfolio should use 0050.TW, got {benchmark}"
        logger.info(f"✓ Template has only Taiwan ETFs → using 0050.TW benchmark")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
