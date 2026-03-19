
import asyncio
import sys
import os
import time

# Add backend to path
sys.path.append(os.path.abspath("backend"))

from app.services.backtest_engine import run_backtest

async def main():
    items = [
        {"symbol": "0050", "name": "元大台灣50", "weight": 25, "category": "tw_etf"},
        {"symbol": "0056", "name": "元大高股息", "weight": 25, "category": "tw_etf"},
        {"symbol": "SPY", "name": "SPDR S&P 500 ETF", "weight": 25, "category": "us_etf"},
        {"symbol": "QQQ", "name": "Invesco QQQ", "weight": 25, "category": "us_etf"},
    ]
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    
    print(f"Starting test backtest with {len(items)} symbols...")
    start_time = time.time()
    result = await run_backtest(items, start_date, end_date)
    duration = time.time() - start_time
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Success! Backtest completed in {duration:.2f} seconds.")
        print(f"Metrics: CAGR={result['metrics']['cagr']}%, Sharpe={result['metrics']['sharpe_ratio']}")
        print(f"Symbols processed: {result.get('available_symbols')}")
        print(f"Date range: {result.get('date_range')}")

if __name__ == "__main__":
    import os
    # Mocking some env vars if needed
    os.environ["SUPABASE_URL"] = "https://nwfbdgiodeubppydadkn.supabase.co" # real one is better if possible
    os.environ["SUPABASE_KEY"] = "mock"
    asyncio.run(main())
