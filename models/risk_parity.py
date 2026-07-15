"""Risk Parity Portfolio"""
import numpy as np

class RiskParity:
    @staticmethod
    def calculate(cov_matrix, max_iter=500):
        tickers = list(cov_matrix.columns)
        n = len(tickers)
        w = np.ones(n) / n
        
        for it in range(max_iter):
            vol = np.sqrt(w.T @ cov_matrix.values @ w)
            if vol < 1e-10: break
            mrc = cov_matrix.values @ w / vol
            rc = w * mrc
            target = vol / n
            rc_safe = np.maximum(np.abs(rc), 1e-10)
            w = w * target / rc_safe
            w = np.maximum(w, 0)
            w = w / w.sum() if w.sum() > 0 else np.ones(n)/n
            if np.max(np.abs(rc - target)) < 1e-6: break
        
        vol = np.sqrt(w.T @ cov_matrix.values @ w)
        mrc = cov_matrix.values @ w / max(vol, 1e-10)
        rc = w * mrc
        rc_pct = rc / max(vol, 1e-10) * 100
        
        return {'weights': dict(zip(tickers, w.round(4))),
                'risk_contributions': dict(zip(tickers, rc_pct.round(1))),
                'port_volatility': vol, 'iterations': it + 1}