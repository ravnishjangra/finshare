"""Performance Ratios - CAPM, Alpha, Treynor, Information Ratio, CVaR"""
import numpy as np
import pandas as pd

class PerformanceRatios:

    @staticmethod
    def calculate(prices_df, info, risk_free_rate=0.06, market_return=0.12, benchmark_prices_df=None):
        """
        benchmark_prices_df: optional DataFrame with a 'Close' column for an
        actual index (e.g. Nifty50/S&P500) covering the same dates as
        prices_df. When supplied, Information Ratio is computed correctly
        against realized benchmark returns. When not supplied (the current
        caller in financial_models.py doesn't have an index series wired up),
        we fall back to an approximation and label it as such in the output
        rather than silently mislabeling it as a true Information Ratio.
        """
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
        
        # Information Ratio: excess return over the benchmark, divided by
        # TRACKING ERROR (volatility of the *difference* between stock and
        # benchmark returns) - not the stock's own volatility. Requires an
        # actual benchmark return series to compute correctly.
        information_ratio = None
        ir_is_approx = True
        if benchmark_prices_df is not None and not benchmark_prices_df.empty and 'Close' in benchmark_prices_df.columns:
            bench_returns = benchmark_prices_df['Close'].pct_change().dropna()
            aligned = pd.concat([returns, bench_returns], axis=1, join='inner')
            aligned.columns = ['stock', 'bench']
            if len(aligned) >= 60:
                active_returns = aligned['stock'] - aligned['bench']
                tracking_error = active_returns.std() * np.sqrt(252)
                if tracking_error > 0:
                    information_ratio = (active_returns.mean() * 252) / tracking_error
                    ir_is_approx = False

        if information_ratio is None:
            # Approximation only: uses the stock's own volatility in place of
            # true tracking error, since no benchmark series was supplied.
            # This is NOT a real Information Ratio - treat it as a rough
            # excess-return-to-volatility gauge, closer in spirit to a
            # benchmark-adjusted Sharpe ratio.
            tracking_error_proxy = ann_vol
            information_ratio = (ann_return - market_return) / tracking_error_proxy if tracking_error_proxy > 0 else 0
        
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
        
        # Value at Risk (95% and 99%) - daily percentile scaled to annual
        # under the standard iid-normal assumption (VaR_annual ~= VaR_daily * sqrt(252))
        var_95 = np.percentile(returns, 5) * np.sqrt(252)
        var_99 = np.percentile(returns, 1) * np.sqrt(252)
        
        # Conditional VaR (Expected Shortfall) - same scaling assumption as VaR above
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
            'information_ratio_is_approx': ir_is_approx,
            'calmar_ratio': round(calmar, 2),
            'max_drawdown': round(max_dd * 100, 1),
            'var_95': round(var_95 * 100, 1),
            'var_99': round(var_99 * 100, 1),
            'cvar_95': round(cvar_95 * 100, 1),
            'win_loss_ratio': round(win_loss_ratio, 1),
        }