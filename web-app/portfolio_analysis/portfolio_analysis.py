import pandas as pd
import numpy as np
from scipy.optimize import minimize

def ret_vol_cal(price_df):
    # Annulize return data
    ret_df =  price_df.pct_change()
    ex_ret = ret_df.mean()
    vol = ret_df.std()
    anl_vol = vol * np.sqrt(252)
    anl_ex_ret = (1 + ex_ret) ** 252 - 1
    
    return anl_ex_ret, anl_vol

def opt_vol_given_ret(rets, vols, target_ret):
    """
    计算给定收益率下的最小波动率。
    """
    n_assets = len(rets)
    def objective(weights):
        weighted_returns = weights * rets
        portfolio_return = np.sum(weighted_returns)
        weighted_volatility = weights * vols
        portfolio_volatility = np.sqrt(np.dot(weighted_volatility, weighted_volatility.T))
        return portfolio_volatility
    
    constraints = ({'type': 'eq', 'fun': lambda weights: np.sum(weights * rets) - target_ret},
                   {'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1})  # 权重和为1
    
    bounds = tuple((0, 1) for asset in range(n_assets))
    initial_guess = np.array(n_assets * [1. / n_assets])
    result = minimize(objective, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints)
    
    if result.success:
        return result.fun, result.x
    else:
        return None, None

def portfolio_performance_cal(price_df, shares):
    latest_price = price_df.iloc[-1]
    stock_val = shares * latest_price
    port_val = np.sum(stock_val)
    
    account_weights = stock_val/port_val
    anl_ex_ret_df, anl_vol_df = ret_vol_cal(price_df)
    
    weighted_volatility = account_weights * anl_vol_df
    portfolio_return = np.sum(account_weights * anl_ex_ret_df)
    portfolio_volatility = np.sqrt(np.dot(weighted_volatility, weighted_volatility.T))
    
    return portfolio_return, portfolio_volatility

def sharpe_cal(price_df, shares, rf = 0.02):
    portfolio_return, portfolio_volatility = portfolio_performance_cal(price_df, shares)
    
    sharpe_ratio = (portfolio_return - rf) / portfolio_volatility
    
    return sharpe_ratio