#!/usr/bin/env python3
"""
匯入預設投資組合到指定用戶 (Plan A - 共享投資組合架構)

用法: python import_default_portfolios.py <user_id>

說明:
  使用方案 A 架構，創建共享投資組合
  - 三個模塊 (Backtest, Optimize, Monte Carlo) 可共享同一個 Portfolio
  - 各自的計算結果存在獨立的 JSONB 欄位中
  - 無 portfolio_type 判別器
"""

import sys
import os
import logging
import json
from pathlib import Path
from datetime import datetime

# 添加項目後端目錄到 Python 路徑
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.portfolio_template_service import init_user_default_portfolios
from app.database import get_supabase

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_portfolios_created(user_id: str, portfolio_ids: list) -> bool:
    """驗證投資組合已成功創建且符合新架構."""
    try:
        sb = get_supabase()
        
        print(f"\n{'='*60}")
        print("📊 驗證投資組合架構")
        print(f"{'='*60}\n")
        
        for portfolio_id in portfolio_ids:
            port_res = (
                sb.table("backtest_portfolios")
                .select("*")
                .eq("id", portfolio_id)
                .eq("user_id", user_id)
                .execute()
            )
            
            if not port_res.data:
                print(f"❌ Portfolio {portfolio_id} 未找到")
                return False
            
            portfolio = port_res.data[0]
            
            # 驗證新架構欄位
            has_backtest_json = "backtest_results_json" in portfolio
            has_optimize_json = "optimize_results_json" in portfolio
            has_monte_carlo_json = "monte_carlo_results_json" in portfolio
            
            print(f"✅ Portfolio: {portfolio.get('name')}")
            print(f"   ID: {portfolio_id}")
            print(f"   用戶: {portfolio.get('user_id')}")
            print(f"   初始金額: {portfolio.get('initial_amount', 'N/A')}")
            print(f"   建立時間: {portfolio.get('created_at', 'N/A')}")
            print(f"\n   架構欄位:")
            print(f"   ✓ backtest_results_json: {has_backtest_json}")
            print(f"   ✓ optimize_results_json: {has_optimize_json}")
            print(f"   ✓ monte_carlo_results_json: {has_monte_carlo_json}")
            
            # 查詢投資組合項目
            items_res = (
                sb.table("backtest_portfolio_items")
                .select("*")
                .eq("portfolio_id", portfolio_id)
                .execute()
            )
            
            if items_res.data:
                print(f"\n   持倉 ({len(items_res.data)} 個):")
                for item in items_res.data:
                    print(f"   • {item['symbol']:6s} ({item.get('name', 'N/A'):20s}) - {item['weight']*100:.1f}%")
            
            print()
        
        print(f"{'='*60}")
        print("✅ 所有投資組合已驗證成功！")
        print(f"{'='*60}\n")
        return True
        
    except Exception as e:
        logger.error(f"驗證失敗: {str(e)}", exc_info=True)
        print(f"❌ 驗證失敗: {str(e)}\n")
        return False


def main():
    """主函數"""
    if len(sys.argv) != 2:
        print("用法: python import_default_portfolios.py <user_id>")
        print("\n示例:")
        print("  python import_default_portfolios.py 821167ec-77fc-4094-bebe-b2231d0f35a9")
        print("\n說明:")
        print("  使用 Plan A 共享投資組合架構")
        print("  - 創建的投資組合可被 Backtest, Optimize, Monte Carlo 模塊共享")
        print("  - 各模塊的計算結果分別存儲在獨立的 JSONB 欄位中")
        sys.exit(1)
    
    user_id = sys.argv[1]
    
    print(f"\n{'='*60}")
    print(f"🚀 開始匯入預設投資組合 (Plan A 架構)")
    print(f"{'='*60}")
    print(f"用戶 ID: {user_id}")
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        logger.info(f"開始為用戶 {user_id} 初始化預設投資組合...")
        portfolio_ids = init_user_default_portfolios(user_id)
        
        if not portfolio_ids:
            print("❌ 未建立任何投資組合")
            sys.exit(1)
        
        print(f"✅ 成功建立 {len(portfolio_ids)} 個投資組合:\n")
        for i, portfolio_id in enumerate(portfolio_ids, 1):
            print(f"  {i}. {portfolio_id}")
        
        # 驗證投資組合
        if not verify_portfolios_created(user_id, portfolio_ids):
            print("⚠️  警告: 投資組合驗證失敗")
            sys.exit(1)
        
        print(f"{'='*60}")
        print("✅ 匯入並驗證完成！")
        print(f"{'='*60}")
        print("\n📝 後續步驟:")
        print("  1. 在前端加載投資組合")
        print("  2. 在 Backtest 模塊運行回測")
        print("  3. 在 Optimize 模塊運行優化")
        print("  4. 在 Monte Carlo 模塊運行模擬")
        print("  5. 驗證三個模塊都能看到相同的投資組合\n")
        
    except Exception as e:
        print(f"\n❌ 匯入失敗: {str(e)}")
        logger.error(f"匯入失敗: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
