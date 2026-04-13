"""Backtest calculation engine using pandas + numpy."""
import numpy as np
import pandas as pd
import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from app.services.market_data import get_historical_prices, get_symbol_currency
from app.utils import sanitize_data


RISK_FREE_RATE = 0.02  # 2% annual


def _annualized_return(cum_return: float, years: float) -> float:
    """Compound annual growth rate."""
    if years <= 0:
        return 0.0
    return (1 + cum_return) ** (1 / years) - 1


def _max_drawdown(price_series: pd.Series) -> float:
    """Maximum drawdown from peak."""
    roll_max = price_series.cummax()
    drawdown = (price_series - roll_max) / roll_max
    return float(drawdown.min())


def _sharpe_ratio(returns: pd.Series, risk_free: float = RISK_FREE_RATE) -> float:
    annual_ret = returns.mean() * 252
    annual_std = returns.std() * np.sqrt(252)
    if annual_std == 0:
        return 0.0
    return (annual_ret - risk_free) / annual_std


def _sortino_ratio(returns: pd.Series, risk_free: float = RISK_FREE_RATE) -> float:
    annual_ret = returns.mean() * 252
    downside = returns[returns < 0].std() * np.sqrt(252)
    if downside == 0:
        return 0.0
    return (annual_ret - risk_free) / downside


def _beta(port_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Beta relative to benchmark (SPY)."""
    if len(port_returns) < 10:
        return 1.0
    cov = np.cov(port_returns, benchmark_returns)
    if cov[1][1] == 0:
        return 1.0
    return cov[0][1] / cov[1][1]


def _var_historical(returns: pd.Series, confidence: float = 0.95) -> float:
    """Historical Value at Risk at given confidence level."""
    return float(np.percentile(returns, (1 - confidence) * 100))


def _cvar(returns: pd.Series, confidence: float = 0.95) -> float:
    """Conditional VaR (Expected Shortfall)."""
    var = _var_historical(returns, confidence)
    return float(returns[returns <= var].mean())


async def run_backtest(
    items: List[Dict],  # [{symbol, weight, name, category}]
    start_date: str,
    end_date: str,
    initial_amount: float = 100000,
) -> Dict[str, Any]:
    """
    Run portfolio backtest.
    Returns performance metrics and time series data.
    """
    symbols = [it["symbol"] for it in items]
    weights = np.array([it["weight"] / 100 for it in items])

    # Normalize weights
    weights = weights / weights.sum()

    # Fetch price data in parallel
    logger = logging.getLogger(__name__)
    overall_start = time.time()
    
    tasks = [get_historical_prices(sym, start_date, end_date) for sym in symbols]
    results = await asyncio.gather(*tasks)
    
    price_data = {}
    for sym, series in zip(symbols, results):
        if not series.empty:
            price_data[sym] = series
            logger.info(f"[Backtest] Fetched {len(series)} rows for {sym}")
        else:
            logger.warning(f"[Backtest] NO data found for {sym}")

    # Currency conversion (TWD -> USD)
    # NOTE: Disabled for consistency with debug_backtest.py tool
    # When TWD symbols are mixed with USD symbols, we use local returns
    # without FX adjustment to ensure consistent results across all tools.
    # This avoids data loss from FX alignment and keeps results stable.
    #
    # If FX adjustment is needed in the future, ensure:
    # 1. Use ffill().bfill() without dropna() to preserve all trading days
    # 2. Coordinate with debug_backtest.py to apply same transformation
    # twd_fx = pd.Series()
    # if any(get_symbol_currency(s) == "TWD" for s in symbols):
    #     twd_fx = await get_historical_prices("TWD=X", start_date, end_date)
    #     if twd_fx.empty:
    #         logger.warning("[Backtest] Could not fetch TWD=X exchange rate.")
    #     else:
    #         logger.info(f"[Backtest] Fetched {len(twd_fx)} days of USD/TWD exchange rate.")
    # 
    # if not twd_fx.empty:
    #     for sym in list(price_data.keys()):
    #         if get_symbol_currency(sym) == "TWD":
    #             combined = pd.DataFrame({"price": price_data[sym], "fx": twd_fx}).ffill().bfill()
    #             combined = combined.dropna(how='all')
    #             if not combined.empty:
    #                 price_data[sym] = combined["price"] / combined["fx"]
    #                 logger.info(f"[Backtest] Adjusted {sym} to USD (aligned rows: {len(combined)})")

    logger.info("[Backtest] Using local prices without FX adjustment for consistency across tools.")

    if not price_data:
        logger.error("[Backtest] No data fetched for ANY symbol.")
        return {"error": "No data available for the selected symbols and date range."}

    # Align dates: use ffill + bfill to handle holidays across different markets (e.g. TW vs US)
    # Do NOT use dropna() as it removes symbols with any missing data at row level
    df = pd.DataFrame(price_data).ffill().bfill()
    
    # Remove rows where all values are NaN (shouldn't happen, but safe)
    df = df.dropna(how='all')
    
    logger.info(f"[Backtest] After alignment (ffill+bfill): {len(df)} rows, columns: {list(df.columns)}")
    if not df.empty:
        logger.info(f"[Backtest] Date range: {df.index[0]} to {df.index[-1]}")
    
    if df.empty or len(df) < 10:
        logger.error(f"[Backtest] Insufficient data after alignment. Rows found: {len(df)}")
        return {"error": f"Insufficient data for the selected period ({len(df)} overlapping days found)."}

    available_symbols = list(df.columns)
    # Recalculate weights for available symbols only
    item_map = {it["symbol"]: it["weight"] / 100 for it in items}
    avail_weights = np.array([item_map.get(s, 0) for s in available_symbols])
    avail_weights = avail_weights / avail_weights.sum()

    # Daily returns
    returns = df.pct_change().dropna()

    # Portfolio daily returns (weighted)
    port_returns = (returns * avail_weights).sum(axis=1)

    # Portfolio value curve
    port_value = (1 + port_returns).cumprod() * initial_amount
    port_value.index = port_value.index.strftime("%Y-%m-%d")

    # Drawdown series — daily drawdown from peak in %
    cumulative = (1 + port_returns).cumprod()
    rolling_max = cumulative.cummax()
    drawdown_series_raw = ((cumulative - rolling_max) / rolling_max) * 100
    drawdown_series_raw.index = drawdown_series_raw.index.strftime("%Y-%m-%d")
    # Downsample to ~250 points max (every n-th day) to keep payload small
    step = max(1, len(drawdown_series_raw) // 250)
    drawdown_series = drawdown_series_raw.iloc[::step].round(4).to_dict()

    # Metrics
    years = len(returns) / 252
    total_return = float(port_value.iloc[-1] / initial_amount - 1)
    cagr = _annualized_return(total_return, years)
    ann_std = float(port_returns.std() * np.sqrt(252))
    max_dd = _max_drawdown(pd.Series((1 + port_returns).cumprod()))
    sharpe = _sharpe_ratio(port_returns)
    sortino = _sortino_ratio(port_returns)
    var_95 = _var_historical(port_returns)
    cvar_95 = _cvar(port_returns)

    # Annual returns
    annual_returns = {}
    for year, grp in returns.groupby(returns.index.year):
        yr_port = (grp * avail_weights).sum(axis=1)
        annual_returns[str(year)] = float((1 + yr_port).prod() - 1)

    # Monthly returns (for heatmap)
    # Monthly returns (for heatmap)
    years_list = sorted(list(returns.index.year.unique()))
    months_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    # Initialize 2D array with None (null in JSON)
    heatmap_data = [[None for _ in range(12)] for _ in range(len(years_list))]
    year_to_idx = {y: i for i, y in enumerate(years_list)}
    
    for (year, month), grp in returns.groupby([returns.index.year, returns.index.month]):
        mo_port = (grp * avail_weights).sum(axis=1)
        mo_ret = float((1 + mo_port).prod() - 1)
        heatmap_data[year_to_idx[year]][month-1] = round(mo_ret, 4)
        
    monthly_returns = {
        "years": years_list,
        "months": months_labels,
        "data": heatmap_data
    }

    # Beta vs SPY
    beta_val = 1.0
    try:
        if "SPY" in price_data:
            spy_series = price_data["SPY"]
        else:
            spy_series = await get_historical_prices("SPY", start_date, end_date)
            
        if not spy_series.empty:
            spy_returns = spy_series.pct_change().dropna()
            aligned = port_returns.align(spy_returns, join="inner")
            if len(aligned[0]) > 10:
                beta_val = _beta(aligned[0], aligned[1])
    except Exception as e:
        logger.warning(f"[Backtest] Beta calculation problem: {e}")

    # Per-asset contribution
    asset_contributions = {}
    for i, sym in enumerate(available_symbols):
        asset_ret = (returns[sym] * avail_weights[i])
        contrib = float((1 + asset_ret).prod() - 1) * initial_amount
        asset_contributions[sym] = {
            "weight": round(float(avail_weights[i]) * 100, 2),
            "return_contribution": round(contrib, 2),
            "name": next((it["name"] for it in items if it["symbol"] == sym), sym),
        }

    # Correlation matrix
    corr_matrix = returns.corr().round(4).to_dict()

    # Benchmark fetching and comparison
    benchmark_symbol = "SPY"  # Default benchmark
    benchmark_prices = pd.Series()
    try:
        # Determine benchmark based on symbols or category
        has_taiwan = any(
            it.get("category") == "tw_etf" or 
            it["symbol"].endswith(".TW") or 
            it["symbol"].endswith(".TWO") 
            for it in items
        )
        if has_taiwan:
            benchmark_symbol = "0050.TW"
        
        if benchmark_symbol in price_data:
            benchmark_prices = price_data[benchmark_symbol]
        else:
            benchmark_prices = await get_historical_prices(benchmark_symbol, start_date, end_date)
            
        if not benchmark_prices.empty and get_symbol_currency(benchmark_symbol) == "TWD" and not twd_fx.empty:
            combined_bm = pd.DataFrame({"price": benchmark_prices, "fx": twd_fx}).ffill().dropna()
            if not combined_bm.empty:
                benchmark_prices = combined_bm["price"] / combined_bm["fx"]
                logger.info(f"[Backtest] Converted benchmark {benchmark_symbol} to USD")
    except Exception as e:
        logger.warning(f"[Backtest] Benchmark fetch problem: {e}")

    benchmark_metrics = {}
    benchmark_series_data = []
    if not benchmark_prices.empty:
        benchmark_returns = benchmark_prices.pct_change().dropna()
        if not benchmark_returns.empty:
            benchmark_cumulative_returns = (1 + benchmark_returns).cumprod()
            benchmark_cumulative_returns.index = benchmark_cumulative_returns.index.strftime("%Y-%m-%d")

            bm_years = len(benchmark_returns) / 252
            bm_total_return = float(benchmark_cumulative_returns.iloc[-1] - 1)
            bm_cagr = _annualized_return(bm_total_return, bm_years)
            bm_ann_std = float(benchmark_returns.std() * np.sqrt(252))
            bm_max_dd = _max_drawdown(benchmark_cumulative_returns)
            bm_sharpe = _sharpe_ratio(benchmark_returns)

            benchmark_metrics = {
                "symbol": benchmark_symbol,
                "total_return": round(bm_total_return * 100, 2),
                "cagr": round(bm_cagr * 100, 2),
                "annual_std": round(bm_ann_std * 100, 2),
                "max_drawdown": round(bm_max_dd * 100, 2),
                "sharpe_ratio": round(bm_sharpe, 4),
            }
            benchmark_series_data = benchmark_cumulative_returns.to_dict()


    logger.info(f"[Backtest] Completed backtest for {len(symbols)} symbols in {time.time() - overall_start:.2f}s")
    result = {
        "metrics": {
            "initial_amount": round(initial_amount, 2),
            "final_amount": round(float(port_value.iloc[-1]), 2),
            "total_return": round(total_return * 100, 2),
            "cagr": round(cagr * 100, 2),
            "annual_std": round(ann_std * 100, 2),
            "max_drawdown": round(max_dd * 100, 2),
            "sharpe_ratio": round(sharpe, 4),
            "sortino_ratio": round(sortino, 4),
            "beta": round(beta_val, 4),
            "var_95": round(var_95 * 100, 2),
            "cvar_95": round(cvar_95 * 100, 2),
            "best_year": max(annual_returns, key=annual_returns.get) if annual_returns else None,
            "worst_year": min(annual_returns, key=annual_returns.get) if annual_returns else None,
            "benchmark_symbol": benchmark_symbol,
            "benchmark_total_return": benchmark_metrics.get("total_return"),
            "benchmark_cagr": benchmark_metrics.get("cagr"),
            "benchmark_annual_std": benchmark_metrics.get("annual_std"),
            "benchmark_max_drawdown": benchmark_metrics.get("max_drawdown"),
            "benchmark_sharpe_ratio": benchmark_metrics.get("sharpe_ratio"),
        },
        "portfolio_value_series": port_value.to_dict(),
        "benchmark_value_series": benchmark_series_data,
        "drawdown_series": drawdown_series,
        "annual_returns": annual_returns,
        "monthly_returns": monthly_returns,
        "asset_contributions": asset_contributions,
        "correlation_matrix": corr_matrix,
        "available_symbols": available_symbols,
        "date_range": {
            "start": str(df.index[0].date()),
            "end": str(df.index[-1].date()),
        },
    }
    return sanitize_data(result)
