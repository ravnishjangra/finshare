"""Index & Sector Comparison"""
import yfinance as yf
import numpy as np

class IndexComparison:
    BENCHMARKS = {'INR': '^NSEI', 'USD': '^GSPC'}

    @staticmethod
    def fetch_comparison_data(ticker, currency, period="1y"):
        benchmark = IndexComparison.BENCHMARKS.get(currency, '^GSPC')
        try:
            data = yf.download([ticker, benchmark], period=period, progress=False)
            if data.empty: return None
            close = data['Close']
            sp = close[ticker]; bp = close[benchmark]
            sr = sp.pct_change().dropna(); br = bp.pct_change().dropna()
            common = sr.index.intersection(br.index)
            sr = sr[common]; br = br[common]
            sc = (1+sr).cumprod()*100; bc = (1+br).cumprod()*100
            cov = sr.cov(br); var = br.var()
            beta = cov/var if var > 0 else 1.0
            sa = sr.mean()*252; ba = br.mean()*252
            alpha = sa - beta*ba
            return {'stock_cumulative': sc, 'benchmark_cumulative': bc, 'beta': beta, 'alpha': alpha,
                    'stock_annual_return': sa, 'benchmark_annual_return': ba,
                    'benchmark_name': 'NIFTY 50' if currency=='INR' else 'S&P 500'}
        except: return None