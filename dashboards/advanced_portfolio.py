"""Portfolio Analytics - Efficient Frontier, Backtesting, Drawdown, Monte Carlo"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import yfinance as yf
from scipy.optimize import minimize


class AdvancedPortfolio:
    def __init__(self, tickers, period="5y", risk_free_rate=0.06):
        self.tickers = [t.strip().upper() for t in tickers]
        self.period = period
        self.risk_free_rate = risk_free_rate
        self.prices = None
        self.returns = None
        self.mean_returns = None
        self.cov_matrix = None
    
    def download_data(self):
        data = {}
        for t in self.tickers:
            try:
                stock = yf.Ticker(t)
                hist = stock.history(period=self.period)
                if not hist.empty and len(hist) > 60:
                    data[t] = hist['Close']
            except: pass
        if len(data) < 2: return False
        self.prices = pd.DataFrame(data).ffill().dropna()
        self.returns = self.prices.pct_change().dropna()
        self.mean_returns = self.returns.mean() * 252
        self.cov_matrix = self.returns.cov() * 252
        return True
    
    def port_stats(self, w):
        ret = np.sum(self.mean_returns.values * w)
        vol = np.sqrt(w.T @ self.cov_matrix.values @ w)
        sharpe = (ret - self.risk_free_rate) / vol if vol > 0 else 0
        return ret, vol, sharpe
    
    def efficient_frontier(self, points=50):
        n = len(self.tickers)
        bounds = tuple((0, 1) for _ in range(n))
        cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        
        res = minimize(lambda w: self.port_stats(w)[1], np.ones(n)/n, bounds=bounds, constraints=cons)
        min_vol_w = res.x
        min_vol_ret, _, _ = self.port_stats(min_vol_w)
        
        max_ret_w = np.zeros(n)
        max_ret_w[np.argmax(self.mean_returns.values)] = 1
        max_ret, _, _ = self.port_stats(max_ret_w)
        
        results = []
        targets = np.linspace(min_vol_ret, max_ret * 0.95, points)
        for target in targets:
            cons_target = (
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': lambda x, t=target: np.sum(self.mean_returns.values * x) - t}
            )
            res = minimize(lambda w: self.port_stats(w)[1], min_vol_w, bounds=bounds, constraints=cons_target)
            if res.success:
                ret, vol, sharpe = self.port_stats(res.x)
                results.append({'return': ret, 'volatility': vol, 'sharpe': sharpe, 'weights': res.x})
        return results
    
    def backtest(self, weights, test_period="2y"):
        n_days = 504 if test_period == "2y" else 252
        if len(self.prices) < n_days: n_days = len(self.prices)
        prices_test = self.prices.iloc[-n_days:]
        rets_test = prices_test.pct_change().dropna()
        port_rets = (rets_test.values * weights).sum(axis=1)
        cumulative = (1 + pd.Series(port_rets, index=rets_test.index)).cumprod() * 100
        return cumulative, port_rets
    
    def drawdown_analysis(self, weights):
        cumulative, _ = self.backtest(weights)
        cum_values = cumulative.values
        running_max = np.maximum.accumulate(cum_values)
        drawdown = (cum_values - running_max) / running_max * 100
        return pd.Series(drawdown, index=cumulative.index), cumulative
    
    def monte_carlo(self, weights, years=5, sims=5000):
        port_ret = np.sum(self.mean_returns.values * weights)
        port_vol = np.sqrt(weights.T @ self.cov_matrix.values @ weights)
        days = years * 252
        daily_ret = port_ret / 252
        daily_vol = port_vol / np.sqrt(252)
        
        np.random.seed(42)
        daily_returns = np.random.normal(daily_ret, daily_vol, (days, sims))
        simulations = np.zeros((days + 1, sims))
        simulations[0] = 100
        for i in range(days):
            simulations[i+1] = simulations[i] * (1 + daily_returns[i])
        return simulations


def create_advanced_portfolio_tab():
    st.markdown('<div class="section-header">📊 Portfolio Analytics</div>', unsafe_allow_html=True)
    st.caption("Efficient Frontier • Backtesting • Drawdown • Monte Carlo")
    
    presets = {
        "🌟 Magnificent 7": ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA"],
        "🇮🇳 Indian IT": ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
        "🏦 Indian Banks": ["HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","KOTAKBANK.NS","AXISBANK.NS"],
        "💻 US Tech": ["AAPL","MSFT","NVDA","GOOGL","AMD"],
        "🛡️ Defensive": ["WMT","JNJ","PG","KO","PEP"],
        "🏗️ Infrastructure": ["LT.NS","ADANIPORTS.NS","NTPC.NS","POWERGRID.NS","ULTRACEMCO.NS"],
        "🔧 Custom": [],
    }
    
    if 'adv_preset_name' not in st.session_state:
        st.session_state['adv_preset_name'] = "🌟 Magnificent 7"
    if 'adv_tickers_val' not in st.session_state:
        st.session_state['adv_tickers_val'] = "AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA"
    
    def on_preset_change():
        preset = presets[st.session_state.adv_preset_select]
        if preset:
            st.session_state['adv_tickers_val'] = ", ".join(preset)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.selectbox("Preset Portfolio", list(presets.keys()), key="adv_preset_select", on_change=on_preset_change)
    with col2:
        tickers_input = st.text_input("Tickers (comma-separated)", key="adv_tickers_val")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        risk_free = st.number_input("Risk-Free Rate (%)", value=6.0, step=0.5, key="adv_rf") / 100
    with col2:
        period = st.selectbox("Data Period", ["1y","2y","3y","5y"], index=3, key="adv_period")
    with col3:
        mc_years = st.selectbox("MC Years", [3, 5, 10], index=1, key="adv_mc_years")
    with col4:
        st.write("")
        run_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True, key="adv_run")
    
    if run_btn:
        tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
        if len(tickers) < 2:
            st.error("Need at least 2 tickers for portfolio analysis.")
            return
        
        with st.spinner("Running portfolio optimization..."):
            ap = AdvancedPortfolio(tickers, period=period, risk_free_rate=risk_free)
            if not ap.download_data():
                st.error("Could not fetch data. Check tickers or try a longer period.")
                return
        
        n = len(tickers)
        w_eq = np.ones(n) / n
        bounds = tuple((0, 1) for _ in range(n))
        cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        
        res = minimize(lambda w: -ap.port_stats(w)[2], w_eq, bounds=bounds, constraints=cons)
        w_ms = res.x
        
        res = minimize(lambda w: ap.port_stats(w)[1], w_eq, bounds=bounds, constraints=cons)
        w_mv = res.x
        
        # ===== 1. EFFICIENT FRONTIER =====
        st.markdown("### 📈 Efficient Frontier")
        
        with st.spinner("Generating efficient frontier..."):
            frontier = ap.efficient_frontier(50)
        
        if frontier:
            rets = [f['return']*100 for f in frontier]
            vols = [f['volatility']*100 for f in frontier]
            sharpes = [f['sharpe'] for f in frontier]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=vols, y=rets, mode='markers+lines',
                marker=dict(size=4, color=sharpes, colorscale='Viridis', showscale=True,
                           colorbar=dict(title='Sharpe')),
                line=dict(color='#667eea', width=2), name='Efficient Frontier'
            ))
            
            best_idx = np.argmax(sharpes)
            min_vol_idx = np.argmin(vols)
            
            fig.add_trace(go.Scatter(
                x=[vols[best_idx]], y=[rets[best_idx]], mode='markers+text',
                marker=dict(size=20, color='#10b981', symbol='star'),
                text=['Max Sharpe'], textposition='top center', name='Max Sharpe'
            ))
            fig.add_trace(go.Scatter(
                x=[vols[min_vol_idx]], y=[rets[min_vol_idx]], mode='markers+text',
                marker=dict(size=15, color='#f59e0b', symbol='diamond'),
                text=['Min Vol'], textposition='top center', name='Min Vol'
            ))
            
            fig.update_layout(xaxis_title='Risk (Volatility %)', yaxis_title='Return (%)',
                            template='plotly_white', height=450, hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"**Max Sharpe**: {rets[best_idx]:.1f}% return, {vols[best_idx]:.1f}% risk, Sharpe {sharpes[best_idx]:.2f}")
        
        # ===== 2. BACKTESTING =====
        st.markdown("### 🔄 Strategy Backtesting (Last 2 Years)")
        
        strategies_bt = {'Equal Weight': w_eq, 'Max Sharpe': w_ms, 'Min Volatility': w_mv}
        
        fig = go.Figure()
        for name, w in strategies_bt.items():
            cum, _ = ap.backtest(w)
            if not cum.empty:
                fig.add_trace(go.Scatter(x=cum.index, y=cum.values, name=name, line=dict(width=2)))
        
        bench_w = np.zeros(n)
        bench_w[0] = 1
        bench_cum, _ = ap.backtest(bench_w)
        if not bench_cum.empty:
            fig.add_trace(go.Scatter(
                x=bench_cum.index, y=bench_cum.values,
                name=f'{tickers[0]} (Benchmark)', line=dict(width=1, dash='dash', color='gray')
            ))
        
        fig.update_layout(title='Portfolio Performance Comparison', xaxis_title='Date',
                         yaxis_title='Growth of $100', template='plotly_white', height=400,
                         hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
        
        # ===== 3. DRAWDOWN =====
        st.markdown("### 📉 Drawdown Analysis (Max Sharpe)")
        
        dd_series, cum100 = ap.drawdown_analysis(w_ms)
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                           row_heights=[0.6, 0.4])
        
        fig.add_trace(go.Scatter(
            x=cum100.index, y=cum100.values, name='Portfolio Value',
            line=dict(color='#667eea', width=2)
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=dd_series.index, y=dd_series.values, name='Drawdown %',
            fill='tozeroy', line=dict(color='#ef4444', width=1),
            fillcolor='rgba(239,68,68,0.2)'
        ), row=2, col=1)
        
        fig.add_hline(y=0, line_color='gray', row=2, col=1)
        fig.update_layout(title='Max Sharpe Portfolio Drawdown', template='plotly_white',
                         height=450, showlegend=False)
        fig.update_yaxes(title_text='Portfolio Value', row=1, col=1)
        fig.update_yaxes(title_text='Drawdown %', row=2, col=1)
        st.plotly_chart(fig, use_container_width=True)
        
        max_dd = dd_series.min()
        current_dd = dd_series.iloc[-1]
        avg_dd = dd_series[dd_series < 0].mean() if len(dd_series[dd_series < 0]) > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Max Drawdown", f"{max_dd:.1f}%", delta_color="inverse")
        with col2: st.metric("Current Drawdown", f"{current_dd:.1f}%", delta_color="inverse")
        with col3: st.metric("Avg Drawdown", f"{avg_dd:.1f}%", delta_color="inverse")
        
        # ===== 4. MONTE CARLO =====
        st.markdown(f"### 🎲 Monte Carlo Simulation ({mc_years} Years)")
        
        with st.spinner(f"Running 5,000 simulations for {mc_years} years..."):
            sims = ap.monte_carlo(w_ms, years=mc_years, sims=5000)
        
        fig = go.Figure()
        for p, c in zip([5, 25, 50, 75, 95], ['#ef4444', '#f59e0b', '#10b981', '#34d399', '#667eea']):
            path = np.percentile(sims, p, axis=1)
            fig.add_trace(go.Scatter(
                y=path, mode='lines',
                line=dict(color=c, width=2 if p == 50 else 1),
                name=f'{p}th Percentile'
            ))
        
        fig.update_layout(title=f'5,000 Simulated Portfolio Paths', xaxis_title='Trading Days',
                         yaxis_title='Portfolio Value ($)', template='plotly_white', height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        final_values = sims[-1]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Worst (5th)", f"${np.percentile(final_values, 5):.0f}")
        with col2: st.metric("Median", f"${np.percentile(final_values, 50):.0f}")
        with col3: st.metric("Best (95th)", f"${np.percentile(final_values, 95):.0f}")
        with col4: st.metric("Mean", f"${final_values.mean():.0f}")
        
        prob_profit = (final_values > 100).mean() * 100
        prob_50 = (final_values > 150).mean() * 100
        prob_loss20 = (final_values < 80).mean() * 100
        
        st.success(f"""
        **Monte Carlo Summary ({mc_years} Years):**
        - **{prob_profit:.0f}%** probability of positive returns
        - **{prob_50:.0f}%** chance of 50%+ returns  
        - **{prob_loss20:.0f}%** risk of losing 20%+
        """)