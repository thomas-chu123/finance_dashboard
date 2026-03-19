import asyncio
import os
import pandas as pd
from dotenv import load_dotenv
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

import app.services.market_data as md

async def test_tw_adjusted():
    print("--- Testing Taiwan Adjusted Price (FinMind) ---")
    symbol = "0056.TW"
    start_date = "2024-01-01"
    end_date = "2024-03-01"
    
    if not md.FINMIND_API_TOKEN:
        print("FinMind Token not found! Skipping FinMind test.")
        return

    prices = await md.get_historical_prices(symbol, start_date, end_date)
    if not prices.empty:
        print(f"Successfully fetched {len(prices)} days for {symbol}")
        print("First 5 rows:")
        print(prices.head())
    else:
        print(f"Failed to fetch data for {symbol}")

async def test_us_adjusted():
    print("\n--- Testing US Adjusted Price (yfinance) ---")
    symbol = "TLT"
    start_date = "2024-01-01"
    end_date = "2024-03-01"
    
    prices = await md.get_historical_prices(symbol, start_date, end_date)
    if not prices.empty:
        print(f"Successfully fetched {len(prices)} days for {symbol}")
        print("First 5 rows:")
        print(prices.head())
    else:
        print(f"Failed to fetch data for {symbol}")

async def main():
    # Load .env from root
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    load_dotenv(env_path)
    
    # Set the token in the module directly
    md.FINMIND_API_TOKEN = os.getenv("FinMind_API")
    print(f"Token loaded: {md.FINMIND_API_TOKEN[:10]}...")
    
    await test_tw_adjusted()
    await test_us_adjusted()

if __name__ == "__main__":
    asyncio.run(main())
