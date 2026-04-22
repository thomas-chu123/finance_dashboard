#!/usr/bin/env python3
"""
匯入預設投資組合到指定用戶
用法: python import_default_portfolios.py <user_id>
"""

import sys
import os
import logging
from pathlib import Path

# 添加項目後端目錄到 Python 路徑
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.portfolio_template_service import init_user_default_portfolios

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函數"""
    if len(sys.argv) != 2:
        print("用法: python import_default_portfolios.py <user_id>")
        print("\n示例:")
        print("  python import_default_portfolios.py 821167ec-77fc-4094-bebe-b2231d0f35a9")
        sys.exit(1)
    
    user_id = sys.argv[1]
    
    print(f"\n{'='*60}")
    print(f"🚀 開始匯入預設投資組合")
    print(f"{'='*60}")
    print(f"用戶 ID: {user_id}\n")
    
    try:
        logger.info(f"開始為用戶 {user_id} 初始化預設投資組合...")
        portfolio_ids = init_user_default_portfolios(user_id)
        
        if not portfolio_ids:
            print("❌ 未建立任何投資組合")
            sys.exit(1)
        
        print(f"\n✅ 成功建立 {len(portfolio_ids)} 個投資組合:\n")
        for i, portfolio_id in enumerate(portfolio_ids, 1):
            print(f"  {i}. {portfolio_id}")
        
        print(f"\n{'='*60}")
        print("✅ 匯入完成！")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n❌ 匯入失敗: {str(e)}")
        logger.error(f"匯入失敗: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
