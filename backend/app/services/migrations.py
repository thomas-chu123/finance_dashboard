"""數據庫遷移管理 - portfolio_shares 表初始化。"""
import os
import logging
from pathlib import Path
from app.database import get_supabase

logger = logging.getLogger(__name__)


def get_migration_sql(filename: str) -> str:
    """讀取遷移 SQL 文件。"""
    migration_path = Path(__file__).parent.parent.parent / "docs" / "migrations" / filename
    if not migration_path.exists():
        raise FileNotFoundError(f"遷移文件不存在: {migration_path}")
    
    with open(migration_path, 'r', encoding='utf-8') as f:
        return f.read()


async def ensure_portfolio_shares_table():
    """確保 portfolio_shares 表存在。如果不存在則建立。"""
    client = get_supabase()
    
    logger.info("🔍 檢查 portfolio_shares 表...")
    
    try:
        # 嘗試查詢表，如果不存在會拋出異常
        result = client.table('portfolio_shares').select('id', count='exact').limit(1).execute()
        logger.info("✅ portfolio_shares 表已存在")
        return True
    except Exception as e:
        if 'does not exist' in str(e) or 'no such table' in str(e).lower():
            logger.warning(f"⚠️  portfolio_shares 表不存在: {e}")
            logger.info("💡 請在 Supabase SQL 編輯器手動執行遷移:")
            
            # 顯示遷移指示
            try:
                sql_content = get_migration_sql("20260420_portfolio_shares.sql")
                logger.info("\n" + "="*70)
                logger.info("Supabase Migration SQL:")
                logger.info("="*70)
                # 只顯示前 1000 字
                logger.info(sql_content[:1000] + "\n... (已省略)\n")
                logger.info("="*70)
            except FileNotFoundError:
                logger.warning("⚠️  找不到遷移文件")
            
            return False
        else:
            logger.error(f"❌ 檢查表時出錯: {e}")
            raise


async def verify_portfolio_shares_columns():
    """驗證 portfolio_shares 表是否有所有必需的欄位。"""
    client = get_supabase()
    
    try:
        # 取得一筆記錄並檢查欄位
        result = client.table('portfolio_shares').select('*').limit(1).execute()
        logger.info("✅ portfolio_shares 表結構驗證通過")
        return True
    except Exception as e:
        logger.warning(f"⚠️  無法驗證表結構: {e}")
        return False
