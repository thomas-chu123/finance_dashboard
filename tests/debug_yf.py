
import yfinance as yf
import pandas as pd

symbols = ["0050.TW", "0056.TW", "SPY", "QQQ"]
start = "2023-01-01"
end = "2023-12-31"

for sym in symbols:
    print(f"Testing {sym}...")
    ticker = yf.Ticker(sym)
    hist = ticker.history(start=start, end=end, auto_adjust=True)
    if hist.empty:
        print(f"  FAILED: No data found for {sym}")
    else:
        print(f"  SUCCESS: Found {len(hist)} rows for {sym}")
        print(f"  First close: {hist['Close'].iloc[0]}")
        print(f"  Last close: {hist['Close'].iloc[-1]}")
