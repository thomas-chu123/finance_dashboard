"""手動執行除權息日曆同步（一次性工具腳本）."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', '.env'))

from app.services.dividend_sync import sync_dividend_calendar


async def main():
    print('[Sync] Starting dividend calendar sync...')
    count = await sync_dividend_calendar()
    print(f'[Sync] Done: {count} records upserted.')


if __name__ == '__main__':
    asyncio.run(main())
