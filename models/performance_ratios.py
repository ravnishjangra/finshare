"""Performance Ratios - CAPM, Alpha, Treynor, Information Ratio, CVaR"""
import numpy as np
import pandas as pd

class PerformanceRatios:
    
    @staticmethod
    def calculate(prices_df, info, risk_free_rate=0.06, market_return=0.12):
        if prices_df is None or prices_df.empty or len(prices_df) < 252:
            return None
        
        close = prices_df['Close']
        returns = close.pct_change().dropna()
        
        if len(returns) < 60:
            return None
        
        # Annualized metrics
        ann_return = returns.mean() * 252
        ann_vol = returns.std() * np.sqrt(252)
        beta = info.get('beta', 1.0) or 1.0
        
        # CAPM Expected Return
        capm_return = risk_free_rate + beta * (market_return - risk_free_rate)
        
        # Jensen's Alpha
        jensens_alpha = ann_return - capm_return
        
        # Treynor Ratio
        treynor = (ann_return - risk_free_rate) / beta if beta > 0 else 0
        
        # Information Ratio (using market as benchmark)
        excess_returns = returns - (risk_free_rate / 252)
        tracking_error = returns.std() * np.sqrt(252)
        information_ratio = (ann_return - market_return) / tracking_error if tracking_error > 0 else 0
        
        # Sharpe Ratio
        sharpe = (ann_return - risk_free_rate) / ann_vol if ann_vol > 0 else 0
        
        # Sortino Ratio (downside deviation only)
        downside = returns[returns < 0].std() * np.sqrt(252) if len(returns[returns < 0]) > 0 else ann_vol
        sortino = (ann_return - risk_free_rate) / downside if downside > 0 else 0
        
        # Max Drawdown
        cum = (1 + returns).cumprod()
        running_max = cum.expanding().max()
        drawdown = (cum - running_max) / running_max
        max_dd = drawdown.min()
        
        # Calmar Ratio
        calmar = ann_return / abs(max_dd) if max_dd and max_dd != 0 else 0
        
        # Value at Risk (95% and 99%)
        var_95 = np.percentile(returns, 5) * np.sqrt(252)
        var_99 = np.percentile(returns, 1) * np.sqrt(252)
        
        # Conditional VaR (Expected Shortfall)
        cvar_95 = returns[returns <= np.percentile(returns, 5)].mean() * np.sqrt(252) if len(returns[returns <= np.percentile(returns, 5)]) > 0 else var_95
        
        # Win/Loss Ratio
        wins = len(returns[returns > 0])
        losses = len(returns[returns < 0])
        win_loss_ratio = wins / losses if losses > 0 else 999
        
        return {
            'annual_return': round(ann_return * 100, 1),
            'annual_volatility': round(ann_vol * 100, 1),
            'beta': round(beta, 2),
            'capm_expected_return': round(capm_return * 100, 1),
            'jensens_alpha': round(jensens_alpha * 100, 2),
            'sharpe_ratio': round(sharpe, 2),
            'sortino_ratio': round(sortino, 2),
            'treynor_ratio': round(treynor, 2),
            'information_ratio': round(information_ratio, 2),
            'calmar_ratio': round(calmar, 2),
            'max_drawdown': round(max_dd * 100, 1),
            'var_95': round(var_95 * 100, 1),
            'var_99': round(var_99 * 100, 1),
            'cvar_95': round(cvar_95 * 100, 1),
            'win_loss_ratio': round(win_loss_ratio, 1),
        }