"""Maximum Diversification Portfolio"""
import numpy as np
from scipy.optimize import minimize

class MaxDiversification:
    """
    Maximizes the Diversification Ratio = (weighted avg vol) / portfolio vol
    Most diversified portfolio - reduces concentration risk
    """
    
    @staticmethod
    def calculate(mean_returns, cov_matrix):
        n = len(mean_returns)
        vols = np.sqrt(np.diag(cov_matrix.values))
        
        def diversification_ratio(w):
            port_vol = np.sqrt(w.T @ cov_matrix.values @ w)
            weighted_vol = np.sum(w * vols)
            return -weighted_vol / port_vol if port_vol > 0 else -1  # Negative for minimization
        
        bounds = tuple((0, 1) for _ in range(n))
        cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        
        res = minimize(diversification_ratio, np.ones(n)/n, method='SLSQP', bounds=bounds, constraints=cons)
        
        w = res.x
        port_ret = np.sum(mean_returns.values * w)
        port_vol = np.sqrt(w.T @ cov_matrix.values @ w)
        div_ratio = np.sum(w * vols) / port_vol if port_vol > 0 else 0
        
        return {
            'weights': w,
            'return': port_ret,
            'volatility': port_vol,
            'diversification_ratio': div_ratio,
        }