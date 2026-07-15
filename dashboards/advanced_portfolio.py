"""Advanced Portfolio Construction"""
import streamlit as st
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd
import numpy as np
from models.black_litterman import BlackLitterman
from models.risk_parity import RiskParity
from analytics.portfolio import PortfolioOptimizer

def create_advanced_portfolio_tab():
    st.markdown('<div class="section-header">🏦 Advanced Portfolio Construction</div>', unsafe_allow_html=True)
    
    presets = {"🔧 Custom":[],"🌟 Magnificent 7":["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA"],"🇮🇳 Indian IT":["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"]}
    col1, col2 = st.columns([1,2])
    with col1: preset = st.selectbox("Preset", list(presets.keys()), key="adv_preset")
    with col2:
        default_tickers = ",".join(presets[preset]) if preset != "🔧 Custom" else "AAPL, MSFT, NVDA, AMZN, GOOGL"
        tickers_input = st.text_input("Tickers", value=default_tickers, key="adv_tickers")
    
    method = st.radio("Method:", ["🎯 Maximum Sharpe", "⚖️ Risk Parity", "🧠 Black-Litterman"], horizontal=True)
    
    if st.button("🚀 Construct", type="primary", use_container_width=True):
        tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
        if len(tickers) < 2: st.error("Need at least 2 tickers."); return
        
        prices_data = {}
        for t in tickers:
            try:
                hist = yf.Ticker(t).history(period="1y")
                if not hist.empty: prices_data[t] = hist['Close']
            except: pass
        
        prices_df = pd.DataFrame(prices_data).dropna()
        returns = prices_df.pct_change().dropna()
        cov_matrix = returns.cov() * 252
        
        if method == "🎯 Maximum Sharpe":
            opt = PortfolioOptimizer(tickers, period="1y")
            if opt.download_data() and opt.calculate_returns():
                ms = opt.optimize_sharpe()
                fig = go.Figure(data=[go.Pie(labels=list(ms['weights'].keys()), values=list(ms['weights'].values()), hole=0.4)])
                fig.update_layout(height=400, template='plotly_white')
                st.plotly_chart(fig, use_container_width=True)
                st.metric("Sharpe Ratio", f"{ms['sharpe']:.2f}")
        
        elif method == "⚖️ Risk Parity":
            rp = RiskParity.calculate(cov_matrix)
            fig = go.Figure(data=[go.Pie(labels=list(rp['weights'].keys()), values=list(rp['weights'].values()), hole=0.4)])
            fig.update_layout(height=400, template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)
            st.metric("Portfolio Volatility", f"{rp['port_volatility']*100:.1f}%")
        
        elif method == "🧠 Black-Litterman":
            market_caps = {t: yf.Ticker(t).info.get('marketCap', 1e9) or 1e9 for t in tickers}
            bl = BlackLitterman.calculate(market_caps, cov_matrix)
            if bl:
                fig = go.Figure(data=[go.Pie(labels=list(bl['weights'].keys()), values=list(bl['weights'].values()), hole=0.4)])
                fig.update_layout(height=400, template='plotly_white')
                st.plotly_chart(fig, use_container_width=True)