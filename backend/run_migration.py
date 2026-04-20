#!/usr/bin/env python3
"""Run database migration for portfolio_shares table."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import get_supabase

def run_migration():
    """Execute portfolio_shares migration."""
    client = get_supabase()
    
    # Read migration SQL
    migration_path = os.path.join(
        os.path.dirname(__file__), 
        '../docs/migrations/20260420_portfolio_shares.sql'
    )
    
    with open(migration_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print("🚀 執行數據庫遷移...")
    print(f"📄 遷移文件: {migration_path}")
    
    try:
        # Execute migration
        result = client.rpc('execute_sql', {'sql': sql}).execute()
        print("✅ 遷移執行成功!")
        print(f"📊 結果: {result}")
        return True
    except Exception as e:
        print(f"❌ 遷移執行失敗: {e}")
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
