"""Technical Analysis Dashboard"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

def create_technical_dashboard(analyzer):
    st.markdown('<div class="section-header">📈 Technical Analysis</div>', unsafe_allow_html=True)
    prices = analyzer.financials.get('prices')
    if prices is None or prices.empty:
        st.warning("No price data.")
        return
    
    close = prices['Close']
    cur = analyzer.currency_symbol
    
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain/loss))
    
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    hist = macd - signal
    
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    upper = sma20 + 2*std20
    lower = sma20 - 2*std20
    
    rsi_now = rsi.iloc[-1]
    macd_sig = "Bullish 🟢" if macd.iloc[-1] > signal.iloc[-1] else "Bearish 🔴"
    sma50 = close.rolling(50).mean().iloc[-1]
    sma200 = close.rolling(200).mean().iloc[-1]
    trend = "Golden Cross ✨" if sma50 > sma200 else "Death Cross 💀"
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("RSI (14)", f"{rsi_now:.1f}")
    col2.metric("MACD", f"{macd.iloc[-1]:.2f}", delta=macd_sig)
    col3.metric("Trend", trend.split(' ')[0])
    col4.metric("Close", f"{cur}{close.iloc[-1]:.2f}")
    
    idx = slice(-120, None)
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.5,0.25,0.25])
    
    fig.add_trace(go.Scatter(x=close.index[idx], y=upper.iloc[idx], line=dict(color='gray',width=1,dash='dash'), name='Upper BB'), row=1, col=1)
    fig.add_trace(go.Scatter(x=close.index[idx], y=sma20.iloc[idx], line=dict(color='orange',width=1.5), name='20 MA'), row=1, col=1)
    fig.add_trace(go.Scatter(x=close.index[idx], y=lower.iloc[idx], line=dict(color='gray',width=1,dash='dash'), fill='tonexty', name='Lower BB'), row=1, col=1)
    fig.add_trace(go.Scatter(x=close.index[idx], y=close.iloc[idx], line=dict(color='#667eea',width=2), name='Price'), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=rsi.index[idx], y=rsi.iloc[idx], line=dict(color='#667eea',width=2), name='RSI'), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    fig.add_trace(go.Scatter(x=macd.index[idx], y=macd.iloc[idx], line=dict(color='#667eea',width=2), name='MACD'), row=3, col=1)
    fig.add_trace(go.Scatter(x=signal.index[idx], y=signal.iloc[idx], line=dict(color='#f59e0b',width=1.5), name='Signal'), row=3, col=1)
    colors = ['#10b981' if h >= 0 else '#ef4444' for h in hist.iloc[idx]]
    fig.add_trace(go.Bar(x=hist.index[idx], y=hist.iloc[idx], marker_color=colors, name='Histogram'), row=3, col=1)
    
    fig.update_layout(height=750, template='plotly_white', hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)