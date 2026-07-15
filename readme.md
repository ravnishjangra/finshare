# 📊 Finshare Pro

**Enterprise Financial Analysis Platform** — Modular, multi-source, production-ready.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ravnishjangra-finshare.streamlit.app)

---

## 🚀 Features

| Category | Features |
|----------|----------|
| **Live Data** | Multi-source price fetching (yfinance → yahooquery → Twelve Data → Alpha Vantage → Google Finance) |
| **Valuation** | Advanced DCF (10-year), Benjamin Graham, Earnings Power Value |
| **Financial Scores** | Piotroski F-Score (0-9), Altman Z-Score (bankruptcy prediction) |
| **Risk Analysis** | 30 Stress Tests (market crash, rate shocks, sector collapse, war scenarios) |
| **Portfolio** | Markowitz MPT, Black-Litterman, Risk Parity, Efficient Frontier |
| **Technical** | RSI, MACD, Bollinger Bands, Golden/Death Cross detection |
| **Factor Investing** | Fama-French 5-factor exposure (Value, Size, Momentum, Quality, Low Vol) |
| **AI Thesis** | Auto-generated investment thesis from financial metrics |
| **Comparison** | Index comparison (NIFTY 50 / S&P 500), Peer comparison |
| **Multi-Currency** | ₹ (INR), $ (USD), € (EUR), £ (GBP), ¥ (JPY) |
| **Indian Stocks** | 40+ NSE/BSE stocks with auto-detection |

---

## 🏗️ Architecture

finshare/
├── app.py # Main entry point
├── config.py # Constants & configuration
├── core/ # Data fetching & analysis
│ ├── analyzer.py # ProFinancialAnalyzer
│ └── fallback.py # 5-source price fallback
├── models/ # Financial models
│ ├── dcf.py, graham.py, epv.py
│ ├── piotroski.py, altman.py
│ ├── black_litterman.py, risk_parity.py
│ └── factor.py
├── analytics/ # Analytics engines
│ ├── stress.py # 30 stress scenarios
│ ├── portfolio.py # MPT optimizer
│ └── index_compare.py # Benchmark comparison
├── dashboards/ # UI dashboards
│ ├── valuation.py, stress_test.py, technical.py
│ ├── scores.py, thesis.py, factor.py
│ ├── index_compare.py, portfolio_opt.py
│ └── advanced_portfolio.py
└── utils/ # Helpers
├── formatting.py
└── helpers.py

---

## 📦 Installation

```bash
# Clone
git clone https://github.com/ravnishjangra/finshare.git
cd finshare

# Install dependencies
pip install -r requirements.txt
