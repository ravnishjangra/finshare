"""Black-Litterman Portfolio Model"""
import numpy as np

class BlackLitterman:
    @staticmethod
    def calculate(market_caps, cov_matrix, risk_aversion=2.5, views=None, view_confidences=None):
        tickers = list(market_caps.keys())
        n = len(tickers)
        total_mcap = sum(market_caps.values())
        if total_mcap == 0: return None
        
        market_weights = np.array([market_caps[t]/total_mcap for t in tickers])
        pi = risk_aversion * cov_matrix.values @ market_weights
        
        if views is None or len(views) == 0:
            return {'weights': dict(zip(tickers, market_weights.round(4))), 
                    'expected_returns': dict(zip(tickers, pi.round(4))), 
                    'method': 'Market Equilibrium'}
        
        k = len(views)
        P = np.zeros((k, n))
        Q = np.zeros(k)
        for i, view in enumerate(views):
            for t in view.get('tickers', []):
                if t in tickers: P[i, tickers.index(t)] = 1.0/len(view['tickers'])
            Q[i] = view.get('return', 0)
        
        tau = 0.05
        conf = view_confidences or [0.5]*k
        Omega = np.diag([max(tau*(1/c-1)*(P[i]@cov_matrix.values@P[i].T), 1e-8) for i, c in enumerate(conf)])
        
        try:
            tau_Sigma = tau * cov_matrix.values
            M = np.linalg.inv(np.linalg.inv(tau_Sigma) + P.T @ np.linalg.inv(Omega) @ P)
            bl_returns = M @ (np.linalg.inv(tau_Sigma) @ pi + P.T @ np.linalg.inv(Omega) @ Q)
            w = np.linalg.inv(cov_matrix.values) @ bl_returns
            w = np.maximum(w, 0)
            w = w / w.sum() if w.sum() > 0 else np.ones(n)/n
            return {'weights': dict(zip(tickers, w.round(4))),
                    'expected_returns': dict(zip(tickers, bl_returns.round(4))),
                    'method': f'Black-Litterman ({k} views)'}
        except np.linalg.LinAlgError:
            return {'weights': dict(zip(tickers, market_weights.round(4))), 
                    'method': 'Market Equilibrium (singular)'}