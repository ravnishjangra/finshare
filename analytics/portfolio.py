"""Portfolio Optimizer - MPT"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import yfinance as yf
import streamlit as st

class PortfolioOptimizer:
    def __init__(self, tickers, period="5y", risk_free_rate=0.06):
        self.tickers = [t.strip().upper() for t in tickers]
        self.period = period
        self.risk_free_rate = risk_free_rate
        self.prices = None
        self.daily_returns = None
        self.mean_returns = None
        self.cov_matrix = None

    def download_data(self):
        data = {}
        failed = []
        for ticker in self.tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period=self.period)
                if not hist.empty: data[ticker] = hist['Close']
                else: failed.append(ticker)
            except: failed.append(ticker)
        if failed: st.warning(f"Could not fetch: {', '.join(failed)}")
        if len(data) < 2: return False
        self.prices = pd.DataFrame(data).ffill().dropna()
        return True

    def calculate_returns(self):
        if self.prices is None: return False
        self.daily_returns = self.prices.pct_change().dropna()
        self.mean_returns = self.daily_returns.mean() * 252
        self.cov_matrix = self.daily_returns.cov() * 252
        return True

    def portfolio_return(self, weights): return np.sum(self.mean_returns * weights)
    def portfolio_volatility(self, weights): return np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
    def portfolio_sharpe(self, weights):
        ret = self.portfolio_return(weights); vol = self.portfolio_volatility(weights)
        return (ret - self.risk_free_rate) / vol if vol > 0 else -np.inf

    def optimize_sharpe(self):
        n = len(self.tickers)
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0, 1) for _ in range(n))
        result = minimize(lambda x: -self.portfolio_sharpe(x), np.array([1/n]*n), method='SLSQP', bounds=bounds, constraints=constraints)
        w = result.x
        return {'weights': dict(zip(self.tickers, w.round(4))), 'return': self.portfolio_return(w), 'volatility': self.portfolio_volatility(w), 'sharpe': self.portfolio_sharpe(w)}

    def optimize_min_volatility(self):
        n = len(self.tickers)
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0, 1) for _ in range(n))
        result = minimize(self.portfolio_volatility, np.array([1/n]*n), method='SLSQP', bounds=bounds, constraints=constraints)
        w = result.x
        return {'weights': dict(zip(self.tickers, w.round(4))), 'return': self.portfolio_return(w), 'volatility': self.portfolio_volatility(w), 'sharpe': self.portfolio_sharpe(w)}

    def generate_efficient_frontier(self, num_portfolios=20000):
        n = len(self.tickers)
        results = np.zeros((3, num_portfolios))
        np.random.seed(42)
        for i in range(num_portfolios):
            w = np.random.random(n); w /= np.sum(w)
            results[0,i] = self.portfolio_return(w)
            results[1,i] = self.portfolio_volatility(w)
            results[2,i] = self.portfolio_sharpe(w)
        return {'returns': results[0], 'volatilities': results[1], 'sharpes': results[2]}