"""Portfolio Optimization Tab - 6 Strategy Comparison"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import yfinance as yf
from scipy.optimize import minimize
from analytics.portfolio import PortfolioOptimizer
from models.max_diversification import MaxDiversification

def create_portfolio_optimization_tab():
    st.markdown('<div class="section-header">🎯 Portfolio Strategy Comparison</div>', unsafe_allow_html=True)
    st.caption("Compare 6 portfolio construction strategies side-by-side")
    
    presets = {
        "🔧 Custom": [],
        "🌟 Magnificent 7": ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA"],
        "🇮🇳 Indian IT": ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
        "🏦 Indian Banks": ["HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","KOTAKBANK.NS","AXISBANK.NS"],
        "💻 US Tech": ["AAPL","MSFT","NVDA","GOOGL","AMD"],
        "🛡️ Defensive": ["WMT","JNJ","PG","KO","PEP"],
    }
    
    col1, col2 = st.columns([1, 2])
    with col1: 
        preset_name = st.selectbox("Preset", list(presets.keys()))
    with col2:
        default_tickers = ",".join(presets[preset_name]) if preset_name != "🔧 Custom" else "AAPL, MSFT, NVDA, AMZN, GOOGL"
        tickers_input = st.text_input("Tickers (comma-separated)", value=default_tickers)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        risk_free = st.number_input("Risk-Free Rate (%)", value=6.0, step=0.5) / 100
    with col2:
        period = st.selectbox("Period", ["1y","2y","3y","5y"], index=3)
    with col3:
        st.write("")
        run_btn = st.button("🚀 Compare Strategies", type="primary", use_container_width=True)
    
    if run_btn:
        tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
        if len(tickers) < 2: 
            st.error("Need at least 2 tickers."); return
        
        opt = PortfolioOptimizer(tickers, period=period, risk_free_rate=risk_free)
        with st.spinner(f"Optimizing {len(tickers)} assets across 6 strategies..."):
            if not opt.download_data() or not opt.calculate_returns():
                st.error("Could not fetch data. Check tickers."); return
            
            n = len(tickers)
            cov = opt.cov_matrix.values
            mean_ret = opt.mean_returns.values
            
            def port_return(w): return np.sum(mean_ret * w)
            def port_vol(w): return np.sqrt(w.T @ cov @ w)
            def port_sharpe(w): 
                r, v = port_return(w), port_vol(w)
                return (r - risk_free) / v if v > 0 else -np.inf
            
            # ===== 1. EQUAL WEIGHT =====
            w1 = np.ones(n) / n
            
            # ===== 2. MAX SHARPE (MARKOWITZ) =====
            constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
            bounds = tuple((0, 1) for _ in range(n))
            res = minimize(lambda x: -port_sharpe(x), w1, method='SLSQP', bounds=bounds, constraints=constraints)
            w2 = res.x
            
            # ===== 3. MIN VOLATILITY =====
            res = minimize(port_vol, w1, method='SLSQP', bounds=bounds, constraints=constraints)
            w3 = res.x
            
            # ===== 4. RISK PARITY =====
            w4 = w1.copy()
            for _ in range(100):
                pv = port_vol(w4)
                mrc = cov @ w4 / pv
                rc = w4 * mrc
                target = pv / n
                w4 = w4 * target / (rc + 1e-10)
                w4 = w4 / w4.sum()
            
            # ===== 5. BLACK-LITTERMAN =====
            market_caps = {}
            for t in tickers:
                try: market_caps[t] = yf.Ticker(t).info.get('marketCap', 1e9) or 1e9
                except: market_caps[t] = 1e9
            total_mcap = sum(market_caps.values())
            mkt_w = np.array([market_caps[t]/total_mcap for t in tickers])
            pi = 2.5 * cov @ mkt_w
            w5 = np.linalg.inv(cov) @ pi
            w5 = np.maximum(w5, 0)
            w5 = w5 / w5.sum()
            
            # ===== 6. MAX DIVERSIFICATION =====
            md = MaxDiversification.calculate(opt.mean_returns, opt.cov_matrix)
            w6 = md['weights']
            
            strategies = [
                {'name': 'Equal Weight', 'weights': dict(zip(tickers, w1)), 'return': port_return(w1), 'volatility': port_vol(w1), 'sharpe': port_sharpe(w1), 'color': '#94a3b8'},
                {'name': 'Max Sharpe', 'weights': dict(zip(tickers, w2)), 'return': port_return(w2), 'volatility': port_vol(w2), 'sharpe': port_sharpe(w2), 'color': '#667eea'},
                {'name': 'Min Volatility', 'weights': dict(zip(tickers, w3)), 'return': port_return(w3), 'volatility': port_vol(w3), 'sharpe': port_sharpe(w3), 'color': '#f59e0b'},
                {'name': 'Risk Parity', 'weights': dict(zip(tickers, w4)), 'return': port_return(w4), 'volatility': port_vol(w4), 'sharpe': port_sharpe(w4), 'color': '#10b981'},
                {'name': 'Black-Litterman', 'weights': dict(zip(tickers, w5)), 'return': port_return(w5), 'volatility': port_vol(w5), 'sharpe': port_sharpe(w5), 'color': '#f093fb'},
                {'name': 'Max Diversification', 'weights': dict(zip(tickers, w6.round(4))), 'return': port_return(w6), 'volatility': port_vol(w6), 'sharpe': port_sharpe(w6), 'color': '#8b5cf6'},
            ]
        
        # ===== PIE CHARTS =====
        st.markdown("### 📊 Portfolio Weights by Strategy")
        cols = st.columns(6)
        for col, strat in zip(cols, strategies):
            with col:
                st.markdown(f"**{strat['name']}**")
                fig = go.Figure(data=[go.Pie(
                    labels=list(strat['weights'].keys()), values=list(strat['weights'].values()),
                    hole=0.5, textinfo='label+percent',
                    marker=dict(colors=[strat['color']] + ['#334155']*10)
                )])
                fig.update_layout(height=250, margin=dict(t=0,b=0,l=10,r=10), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        
        # ===== COMPARISON TABLE =====
        st.markdown("### 📈 Performance Comparison")
        df = pd.DataFrame([{
            'Strategy': s['name'],
            'Return': f"{s['return']*100:.1f}%",
            'Risk (Vol)': f"{s['volatility']*100:.1f}%",
            'Sharpe': f"{s['sharpe']:.2f}",
        } for s in strategies])
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # ===== RISK vs RETURN SCATTER =====
        st.markdown("### 📊 Risk vs Return")
        fig = go.Figure()
        for s in strategies:
            fig.add_trace(go.Scatter(
                x=[s['volatility']*100], y=[s['return']*100],
                mode='markers+text', name=s['name'], text=[s['name']],
                textposition='top center',
                marker=dict(size=22, color=s['color'], line=dict(width=2, color='white')),
                textfont=dict(size=10)
            ))
        fig.update_layout(xaxis_title='Risk (Volatility %)', yaxis_title='Return (%)',
                          template='plotly_white', height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # ===== HEATMAP =====
        st.markdown("### 🔥 Weight Allocation Heatmap")
        hm_data = {}
        for s in strategies:
            hm_data[s['name']] = [s['weights'].get(t, 0)*100 for t in tickers]
        hm_df = pd.DataFrame(hm_data, index=[t.replace('.NS','').replace('.BO','') for t in tickers])
        
        fig = go.Figure(data=go.Heatmap(
            z=hm_df.values, x=hm_df.columns, y=hm_df.index,
            colorscale='Blues', text=np.round(hm_df.values, 1),
            texttemplate='%{text:.1f}%', textfont={"size":11},
            showscale=True, colorbar=dict(title='Weight %')
        ))
        fig.update_layout(height=300, template='plotly_white')
        st.plotly_chart(fig, use_container_width=True)
        
        # ===== KEY TAKEAWAY =====
        best = max(strategies, key=lambda x: x['sharpe'])
        lowest = min(strategies, key=lambda x: x['volatility'])
        highest = max(strategies, key=lambda x: x['return'])
        st.success(f"""
        **Key Takeaways:**
        - 🎯 **Best Risk-Adjusted**: {best['name']} (Sharpe: {best['sharpe']:.2f})
        - 🛡️ **Lowest Risk**: {lowest['name']} (Vol: {lowest['volatility']*100:.1f}%)
        - 📈 **Highest Return**: {highest['name']} (Return: {highest['return']*100:.1f}%)
        """)