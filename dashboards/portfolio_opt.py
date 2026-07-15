"""Portfolio Optimization Tab"""
import streamlit as st
import plotly.graph_objects as go
import time
from analytics.portfolio import PortfolioOptimizer

def create_portfolio_optimization_tab():
    st.markdown('<div class="section-header">🎯 Portfolio Optimization (MPT)</div>', unsafe_allow_html=True)
    
    presets = {
        "🔧 Custom": [], "🌟 Magnificent 7": ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA"],
        "🇮🇳 Indian IT": ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
        "🏦 Indian Banks": ["HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","KOTAKBANK.NS","AXISBANK.NS"],
    }
    
    col1, col2 = st.columns([1, 2])
    with col1: preset_name = st.selectbox("Preset", list(presets.keys()))
    with col2:
        default_tickers = ",".join(presets[preset_name]) if preset_name != "🔧 Custom" else "AAPL, MSFT, NVDA, AMZN, GOOGL"
        tickers_input = st.text_input("Tickers", value=default_tickers)
    
    risk_free = st.number_input("Risk-Free Rate (%)", value=6.0) / 100
    period = st.selectbox("Period", ["1y","2y","3y","5y"], index=3)
    
    if st.button("🚀 Optimize Portfolio", type="primary", use_container_width=True):
        tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
        if len(tickers) < 2: st.error("Need at least 2 tickers."); return
        
        opt = PortfolioOptimizer(tickers, period=period, risk_free_rate=risk_free)
        with st.spinner("Optimizing..."):
            if opt.download_data() and opt.calculate_returns():
                max_sharpe = opt.optimize_sharpe()
                min_vol = opt.optimize_min_volatility()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Max Sharpe", f"{max_sharpe['sharpe']:.2f}")
                    fig = go.Figure(data=[go.Pie(labels=list(max_sharpe['weights'].keys()), values=list(max_sharpe['weights'].values()), hole=0.4)])
                    fig.update_layout(height=300, template='plotly_white')
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    st.metric("Min Volatility", f"{min_vol['sharpe']:.2f}")
                    fig = go.Figure(data=[go.Pie(labels=list(min_vol['weights'].keys()), values=list(min_vol['weights'].values()), hole=0.4)])
                    fig.update_layout(height=300, template='plotly_white')
                    st.plotly_chart(fig, use_container_width=True)