import numpy as np
import pandas as pd
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from app.services.market_data import get_historical_prices

logger = logging.getLogger(__name__)

async def run_monte_carlo_simulation(
    assets: List[Dict[str, Any]], # [{"symbol": "SPY", "weight": 0.6}, ...]
    initial_amount: float,
    years: int = 30,
    simulations: int = 10000,
    annual_contribution: float = 0,
    annual_withdrawal: float = 0,
    inflation_mean: float = 0.03,
    inflation_std: float = 0.01,
    adjust_for_inflation: bool = True
) -> Dict[str, Any]:
    """
    Perform a Monte Carlo simulation using the Single Year Bootstrap method.
    """
    if not assets:
        return {"error": "No assets provided"}

    symbols = [a["symbol"] for a in assets]
    weights = np.array([a["weight"] for a in assets])
    
    if abs(np.sum(weights) - 1.0) > 0.001:
        # Normalize weights if they don't sum to 1
        weights = weights / np.sum(weights)

    # 1. Fetch historical data
    # We want as much history as possible to have a diverse set of annual returns
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = "2000-01-01" # Default to 2000 to get a good sample size
    
    price_tasks = [get_historical_prices(s, start_date, end_date, adjusted=True) for s in symbols]
    price_series_list = await asyncio.gather(*price_tasks)
    
    # Merge into a single DataFrame
    df_prices = pd.DataFrame()
    for s, series in zip(symbols, price_series_list):
        if not series.empty:
            df_prices[s] = series
            
    if df_prices.empty:
        return {"error": "Could not fetch historical data for any of the provided assets"}

    # Calculate annual returns
    # Resample to year-end and calculate pct_change
    annual_prices = df_prices.resample('YE').last()
    annual_returns = annual_prices.pct_change().dropna()
    
    if len(annual_returns) < 2:
        return {"error": "Insufficient historical data (less than 2 years of annual returns) to perform simulation"}

    num_historical_years = len(annual_returns)
    historical_returns_matrix = annual_returns.values # Shape: (historical_years, num_assets)
    
    # 2. Simulation Logic
    # We'll pre-generate random indices for the bootstrap
    # Shape: (simulations, simulation_years)
    random_indices = np.random.randint(0, num_historical_years, size=(simulations, years))
    
    # Pre-generate inflation rates if needed
    # Shape: (simulations, simulation_years)
    if inflation_std > 0:
        sim_inflation = np.random.normal(inflation_mean, inflation_std, size=(simulations, years))
    else:
        sim_inflation = np.full((simulations, years), inflation_mean)

    # Initialize results
    # Shape: (simulations, years + 1)
    paths = np.zeros((simulations, years + 1))
    paths[:, 0] = initial_amount
    
    # Keep track of success (balance > 0)
    # We'll check this at each step
    
    for t in range(1, years + 1):
        # Get returns for this year across all simulations
        # sampled_returns shape: (simulations, num_assets)
        indices_at_t = random_indices[:, t-1]
        sampled_returns = historical_returns_matrix[indices_at_t]
        
        # Portfolio return for each simulation at year t
        # portfolio_returns shape: (simulations,)
        portfolio_returns = np.dot(sampled_returns, weights)
        
        # Current balances
        prev_balances = paths[:, t-1]
        
        # Update balances with returns
        new_balances = prev_balances * (1 + portfolio_returns)
        
        # Calculate inflation factor for this year (for adjusting contributions/withdrawals)
        current_year_inflation = 1.0
        if adjust_for_inflation and inflation_std > 0:
            current_year_inflation = 1 + sim_inflation[:, t-1]
        elif adjust_for_inflation:
            current_year_inflation = 1 + inflation_mean
        
        # Add contribution (grew by inflation)
        contribution = annual_contribution * current_year_inflation
        new_balances += contribution
        
        # Subtract withdrawal (as percentage of current balance, adjusted for inflation)
        # withdrawal_rate should be in percentage (0-100), convert to decimal
        withdrawal_rate = annual_withdrawal / 100.0  # Convert percentage to decimal
        withdrawal = new_balances * withdrawal_rate
        new_balances -= withdrawal
        
        # Floor at zero (bankrupt condition)
        new_balances = np.maximum(new_balances, 0)
        
        paths[:, t] = new_balances

    # 3. Calculate Metrics
    # Success Rate: % of paths that achieved the capital preservation goal
    # Success is defined as: Ending Balance >= Initial Amount
    # This represents achieving the fundamental investment objective (保本)
    success_mask = paths[:, -1] >= initial_amount
    success_rate = np.mean(success_mask)
    
    # Percentiles
    percentiles = [10, 25, 50, 75, 90]
    percentile_results = {}
    for p in percentiles:
        percentile_results[f"p{p}"] = np.percentile(paths, p, axis=0).tolist()
    
    # Distribution of end values
    end_values = paths[:, -1]
    
    # Basic summary stats
    summary = {
        "initial_amount": initial_amount,
        "years": years,
        "simulations": simulations,
        "success_rate": float(success_rate),
        "median_end_balance": float(np.median(end_values)),
        "mean_end_balance": float(np.mean(end_values)),
        "p10_end_balance": float(np.percentile(end_values, 10)),
        "p90_end_balance": float(np.percentile(end_values, 90)),
    }

    return {
        "summary": summary,
        "percentile_paths": percentile_results,
        "history_years": num_historical_years,
        "assets_used": symbols
    }
