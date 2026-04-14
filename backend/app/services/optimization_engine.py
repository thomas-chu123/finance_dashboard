import numpy as np
import pandas as pd
import scipy.optimize as sco
from typing import Dict, Any
from app.utils import sanitize_data

RISK_FREE_RATE = 0.02
TRADING_DAYS = 252

def _portfolio_performance(weights: np.ndarray, mean_returns: pd.Series, cov_matrix: pd.DataFrame) -> tuple[float, float, float]:
    returns = np.sum(mean_returns * weights)
    std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    sharpe = (returns - RISK_FREE_RATE) / std if std > 0 else 0
    return returns, std, sharpe

def _negative_sharpe(weights: np.ndarray, mean_returns: pd.Series, cov_matrix: pd.DataFrame) -> float:
    p_ret, p_std, p_sharpe = _portfolio_performance(weights, mean_returns, cov_matrix)
    return -p_sharpe

def _portfolio_volatility(weights: np.ndarray, mean_returns: pd.Series, cov_matrix: pd.DataFrame) -> float:
    p_ret, p_std, p_sharpe = _portfolio_performance(weights, mean_returns, cov_matrix)
    return p_std

def _efficient_return(mean_returns: pd.Series, cov_matrix: pd.DataFrame, target_return: float) -> dict:
    num_assets = len(mean_returns)
    args = (mean_returns, cov_matrix)
    
    constraints = (
        {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
        {'type': 'eq', 'fun': lambda x, mean_returns=mean_returns, cov_matrix=cov_matrix: _portfolio_performance(x, mean_returns, cov_matrix)[0] - target_return}
    )
    bounds = tuple((0.0, 1.0) for _ in range(num_assets))
    
    result = sco.minimize(_portfolio_volatility, num_assets * [1./num_assets,], args=args,
                          method='SLSQP', bounds=bounds, constraints=constraints)
    return result

def run_optimization(prices_df: pd.DataFrame, display_currency: str = "TWD") -> Dict[str, Any]:
    """
    Run Markowitz portfolio optimization on a DataFrame of historical daily prices.
    Returns optimal weights for Max Sharpe and Min Volatility, plus points for the Efficient Frontier.
    """
    if prices_df.empty or len(prices_df.columns) < 2:
        return {"error": "Need at least 2 assets for optimization."}

    # Calculate daily returns
    returns = prices_df.pct_change().dropna()
    mean_returns = returns.mean() * TRADING_DAYS
    cov_matrix = returns.cov() * TRADING_DAYS
    num_assets = len(mean_returns)
    symbols = prices_df.columns.tolist()

    # Constraints and bounds (no short selling)
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0.0, 1.0) for _ in range(num_assets))
    init_guess = np.array(num_assets * [1. / num_assets,])
    args = (mean_returns, cov_matrix)

    # 1. Maximum Sharpe Ratio
    opt_sharpe = sco.minimize(_negative_sharpe, init_guess, args=args,
                              method='SLSQP', bounds=bounds, constraints=constraints)
    ms_weights = opt_sharpe.x
    ms_ret, ms_std, ms_sharpe = _portfolio_performance(ms_weights, mean_returns, cov_matrix)

    # 2. Minimum Volatility
    opt_vol = sco.minimize(_portfolio_volatility, init_guess, args=args,
                           method='SLSQP', bounds=bounds, constraints=constraints)
    mv_weights = opt_vol.x
    mv_ret, mv_std, mv_sharpe = _portfolio_performance(mv_weights, mean_returns, cov_matrix)

    # 3. Efficient Frontier Curve (calculate 20 points between min_ret and max_ret)
    min_ret = returns.mean().min() * TRADING_DAYS
    max_ret = returns.mean().max() * TRADING_DAYS
    # Generate target returns for the frontier curve
    target_returns = np.linspace(min_ret, max_ret, 20)
    frontier_volatility = []
    frontier_returns = []
    
    for tr in target_returns:
        res = _efficient_return(mean_returns, cov_matrix, tr)
        if res.success:
            frontier_volatility.append(res.fun)
            frontier_returns.append(tr)

    # Format output
    def format_weights(w):
        return {symbols[i]: round(w[i] * 100, 2) for i in range(len(w))}

    # Individual asset coordinates (for scatter plot overlay)
    asset_points = []
    for sym in symbols:
        asset_points.append({
            "symbol": sym,
            "return": round(mean_returns[sym], 4),
            "volatility": round(np.sqrt(cov_matrix.loc[sym, sym]), 4)
        })

    return {
        "max_sharpe": {
            "weights": format_weights(ms_weights),
            "return": round(ms_ret, 4),
            "volatility": round(ms_std, 4),
            "sharpe": round(ms_sharpe, 4)
        },
        "min_volatility": {
            "weights": format_weights(mv_weights),
            "return": round(mv_ret, 4),
            "volatility": round(mv_std, 4),
            "sharpe": round(mv_sharpe, 4)
        },
        "efficient_frontier": {
            "returns": [round(r, 4) for r in frontier_returns],
            "volatilities": [round(v, 4) for v in frontier_volatility]
        },
        "asset_points": asset_points,
        "currency": display_currency  # 新增：顯示幣值
    }
    return sanitize_data(result)
