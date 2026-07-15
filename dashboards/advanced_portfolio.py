"""Advanced Analysis - Performance, Fraud Detection, DuPont, Monte Carlo"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import yfinance as yf
from scipy.optimize import minimize
from models.beneish import BeneishMScore
from models.dupont import DuPontAnalysis
from models.performance_ratios import PerformanceRatios
from models.composite_score import CompositeScore
from models.piotroski import PiotroskiFScore
from models.altman import AltmanZScore


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
    st.markdown('<div class="section-header">📊 Advanced Financial Analysis</div>', unsafe_allow_html=True)
    st.caption("Performance • Fraud Detection • DuPont • Portfolio • Monte Carlo")
    
    presets = {
        "🌟 Magnificent 7": ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA"],
        "🇮🇳 Indian IT": ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
        "🏦 Indian Banks": ["HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","KOTAKBANK.NS","AXISBANK.NS"],
        "💻 US Tech": ["AAPL","MSFT","NVDA","GOOGL","AMD"],
        "🛡️ Defensive": ["WMT","JNJ","PG","KO","PEP"],
        "🏗️ Infrastructure": ["LT.NS","ADANIPORTS.NS","NTPC.NS","POWERGRID.NS","ULTRACEMCO.NS"],
        "🔧 Custom": [],
    }
    
    # Session state for preset sync
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
    
    col1, col2, col3 = st.columns(3)
    with col1: risk_free = st.number_input("Risk-Free Rate (%)", value=6.0, step=0.5, key="adv_rf") / 100
    with col2: period = st.selectbox("Data Period", ["1y","2y","3y","5y"], index=3, key="adv_period")
    with col3: mc_years = st.selectbox("MC Years", [3, 5, 10], index=1, key="adv_mc_years")
    
    if st.button("🚀 Run Full Analysis", type="primary", use_container_width=True):
        tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
        if len(tickers) < 1: st.error("Need at least 1 ticker."); return
        
        # ===== FETCH DATA FOR FIRST TICKER =====
        main_ticker = tickers[0]
        with st.spinner(f"Fetching data for {main_ticker}..."):
            try:
                stock = yf.Ticker(main_ticker)
                info = stock.info
                income = stock.financials
                balance = stock.balance_sheet
                cashflow = stock.cashflow
                prices = stock.history(period=period)
            except:
                st.error(f"Could not fetch data for {main_ticker}")
                return
        
        if not info or len(info) < 3:
            st.error("Insufficient data.")
            return
        
        # ===== SECTION 1: PERFORMANCE METRICS =====
        st.markdown("### 📈 Performance Metrics")
        
        perf = PerformanceRatios.calculate(prices, info, risk_free_rate=risk_free)
        
        if perf:
            cols = st.columns(5)
            metrics_display = [
                ('Return', f"{perf['annual_return']}%"),
                ('Volatility', f"{perf['annual_volatility']}%"),
                ('Sharpe', f"{perf['sharpe_ratio']}"),
                ('Sortino', f"{perf['sortino_ratio']}"),
                ('Max DD', f"{perf['max_drawdown']}%"),
                ('Alpha', f"{perf['jensens_alpha']}%"),
                ('Beta', f"{perf['beta']}"),
                ('Treynor', f"{perf['treynor_ratio']}"),
                ('Info Ratio', f"{perf['information_ratio']}"),
                ('Calmar', f"{perf['calmar_ratio']}"),
            ]
            for col, (label, val) in zip(cols, metrics_display[:5]):
                with col:
                    st.metric(label, val)
            
            cols = st.columns(5)
            for col, (label, val) in zip(cols, metrics_display[5:]):
                with col:
                    st.metric(label, val)
            
            # Risk metrics
            with st.expander("🔍 Risk Metrics"):
                col1, col2, col3, col4 = st.columns(4)
                with col1: st.metric("VaR 95%", f"{perf['var_95']}%", delta_color="inverse")
                with col2: st.metric("VaR 99%", f"{perf['var_99']}%", delta_color="inverse")
                with col3: st.metric("CVaR 95%", f"{perf['cvar_95']}%", delta_color="inverse")
                with col4: st.metric("Win/Loss", f"{perf['win_loss_ratio']}")
                st.caption("VaR = Value at Risk | CVaR = Expected loss in worst 5% of cases")
        
        # ===== SECTION 2: FRAUD DETECTION =====
        st.markdown("### 🔍 Earnings Quality & Fraud Detection")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Beneish M-Score**")
            st.caption("Detects earnings manipulation (> -1.78 = high risk)")
            m_score = BeneishMScore.calculate(income, balance, cashflow)
            if m_score:
                st.markdown(f"<h2 style='color:{m_score['color']};'>{m_score['m_score']}</h2>", unsafe_allow_html=True)
                st.markdown(f"**{m_score['risk']}**")
                st.caption(m_score['interpretation'])
                with st.expander("Components"):
                    for k, v in m_score['components'].items():
                        st.caption(f"{k}: {v}")
            else:
                st.warning("Insufficient data")
        
        with col2:
            st.markdown("**Piotroski F-Score**")
            f_score = PiotroskiFScore.calculate(income, balance, cashflow)
            if f_score:
                st.markdown(f"<h2 style='color:{f_score.get('color','#94a3b8')};'>{f_score['score']}/9</h2>", unsafe_allow_html=True)
                st.markdown(f"**{f_score['rating']}**")
            else:
                st.warning("Insufficient data")
            
            st.markdown("---")
            st.markdown("**Altman Z-Score**")
            mcap = info.get('marketCap', 0)
            z_score = AltmanZScore.calculate(balance, income, mcap)
            if z_score and z_score.get('z_score'):
                st.markdown(f"<h2 style='color:{z_score.get('color','#94a3b8')};'>{z_score['z_score']:.2f}</h2>", unsafe_allow_html=True)
                st.markdown(f"**{z_score['zone']}** - {z_score['risk_level']}")
            else:
                st.warning("Insufficient data")
        
        # ===== SECTION 3: DUPONT ANALYSIS =====
        st.markdown("### 🧩 DuPont ROE Decomposition")
        
        # Calculate ratios first for composite score
        ratios = {}
        if isinstance(info, dict):
            for key, ratio_key, mult in [
                ('returnOnEquity', 'ROE', 100), ('returnOnAssets', 'ROA', 100),
                ('profitMargins', 'Net Profit Margin', 100), ('debtToEquity', 'Debt to Equity', 1),
                ('trailingPE', 'P/E Ratio', 1), ('priceToBook', 'P/B Ratio', 1),
                ('currentRatio', 'Current Ratio', 1),
            ]:
                val = info.get(key)
                if val is not None:
                    try: ratios[ratio_key] = float(val) * mult
                    except: pass
        
        dupont = DuPontAnalysis.calculate(income, balance, ratios)
        
        if dupont:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**3-Step DuPont: ROE = {dupont['three_step']['roe']}%**")
                st.caption(f"Net Margin: {dupont['three_step']['net_margin']}%")
                st.caption(f"Asset Turnover: {dupont['three_step']['asset_turnover']}")
                st.caption(f"Equity Multiplier: {dupont['three_step']['equity_multiplier']}")
                
                fig = go.Figure(go.Waterfall(
                    name="3-Step", orientation="v",
                    measure=["relative", "relative", "relative", "total"],
                    x=["Net Margin", "× Asset Turnover", "× Equity Multiplier", "= ROE"],
                    y=[dupont['three_step']['net_margin'], 
                       dupont['three_step']['asset_turnover'] * 100,
                       dupont['three_step']['equity_multiplier'] * 10,
                       dupont['three_step']['roe']],
                    connector={"line": {"color": "#94a3b8"}},
                ))
                fig.update_layout(height=300, template='plotly_white')
                st.plotly_chart(fig, use_container_width=True)
            
            if dupont.get('five_step'):
                with col2:
                    st.markdown(f"**5-Step DuPont: ROE = {dupont['five_step']['roe']}%**")
                    for label, key in [('Tax Burden', 'tax_burden'), ('Interest Burden', 'interest_burden'),
                                       ('Op Margin', 'operating_margin'), ('Asset Turnover', 'asset_turnover'),
                                       ('Equity Multiplier', 'equity_multiplier')]:
                        val = dupont['five_step'][key]
                        if val: st.caption(f"{label}: {val}")
        else:
            st.warning("Insufficient data for DuPont analysis")
        
        # ===== SECTION 4: COMPOSITE HEALTH SCORE =====
        st.markdown("### 🏆 Composite Financial Health Score")
        
        composite = CompositeScore.calculate(ratios, f_score, z_score)
        
        col1, col2 = st.columns([1, 2])
        with col1:
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=composite['score'],
                number={'font': {'color': composite['color'], 'size': 48}},
                title={'text': "Health Score"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': composite['color']},
                    'steps': [
                        {'range': [0, 40], 'color': "rgba(239,68,68,0.2)"},
                        {'range': [40, 60], 'color': "rgba(245,158,11,0.2)"},
                        {'range': [60, 80], 'color': "rgba(16,185,129,0.2)"},
                        {'range': [80, 100], 'color': "rgba(16,185,129,0.4)"},
                    ]
                }
            ))
            fig.update_layout(height=250, margin=dict(t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(f"<h3 style='text-align:center;color:{composite['color']};'>{composite['rating']}</h3>", unsafe_allow_html=True)
        
        with col2:
            for category, score in composite['breakdown'].items():
                st.markdown(f"**{category}**: {'█' * (score//10)}{'░' * (10-score//10)} {score}%")
        
        # ===== SECTION 5: PORTFOLIO ANALYSIS (if multiple tickers) =====
        if len(tickers) >= 2:
            st.markdown("---")
            st.markdown("### 📈 Portfolio Analysis")
            
            with st.spinner("Running portfolio optimization..."):
                ap = AdvancedPortfolio(tickers, period=period, risk_free_rate=risk_free)
                if ap.download_data():
                    n = len(tickers)
                    w_eq = np.ones(n) / n
                    bounds = tuple((0, 1) for _ in range(n))
                    cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
                    
                    res = minimize(lambda w: -ap.port_stats(w)[2], w_eq, bounds=bounds, constraints=cons)
                    w_ms = res.x
                    
                    # Efficient Frontier
                    st.markdown("#### Efficient Frontier")
                    frontier = ap.efficient_frontier(50)
                    if frontier:
                        rets = [f['return']*100 for f in frontier]
                        vols = [f['volatility']*100 for f in frontier]
                        sharpes = [f['sharpe'] for f in frontier]
                        
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=vols, y=rets, mode='markers+lines',
                            marker=dict(size=4, color=sharpes, colorscale='Viridis', showscale=True,
                                       colorbar=dict(title='Sharpe')),
                            line=dict(color='#667eea', width=2)))
                        best_idx = np.argmax(sharpes)
                        fig.add_trace(go.Scatter(x=[vols[best_idx]], y=[rets[best_idx]], mode='markers+text',
                            marker=dict(size=20, color='#10b981', symbol='star'),
                            text=['Max Sharpe'], textposition='top center'))
                        fig.update_layout(xaxis_title='Risk (%)', yaxis_title='Return (%)',
                                        template='plotly_white', height=350)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Backtesting
                    st.markdown("#### Strategy Backtesting")
                    strategies_bt = {'Equal Weight': w_eq, 'Max Sharpe': w_ms}
                    
                    fig = go.Figure()
                    for name, w in strategies_bt.items():
                        cum, _ = ap.backtest(w)
                        if not cum.empty:
                            fig.add_trace(go.Scatter(x=cum.index, y=cum.values, name=name, line=dict(width=2)))
                    
                    bench_w = np.zeros(n); bench_w[0] = 1
                    bench_cum, _ = ap.backtest(bench_w)
                    if not bench_cum.empty:
                        fig.add_trace(go.Scatter(x=bench_cum.index, y=bench_cum.values,
                            name=f'{tickers[0]}', line=dict(width=1, dash='dash', color='gray')))
                    fig.update_layout(title='Portfolio Performance', xaxis_title='Date',
                                    yaxis_title='Growth of $100', template='plotly_white', height=350)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Monte Carlo
                    st.markdown(f"#### 🎲 Monte Carlo Simulation ({mc_years} Years)")
                    
                    with st.spinner(f"Running 5,000 simulations..."):
                        sims = ap.monte_carlo(w_ms, years=mc_years, sims=5000)
                    
                    fig = go.Figure()
                    for p, c in zip([5, 25, 50, 75, 95], ['#ef4444', '#f59e0b', '#10b981', '#34d399', '#667eea']):
                        path = np.percentile(sims, p, axis=1)
                        fig.add_trace(go.Scatter(y=path, mode='lines',
                            line=dict(color=c, width=2 if p == 50 else 1), name=f'{p}th'))
                    fig.update_layout(title=f'5,000 Simulated Paths', xaxis_title='Days',
                                    yaxis_title='Value ($)', template='plotly_white', height=350)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    final_vals = sims[-1]
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Worst (5th)", f"${np.percentile(final_vals, 5):.0f}")
                    c2.metric("Median", f"${np.percentile(final_vals, 50):.0f}")
                    c3.metric("Best (95th)", f"${np.percentile(final_vals, 95):.0f}")
                    c4.metric("Mean", f"${final_vals.mean():.0f}")
                    
                    prob_profit = (final_vals > 100).mean() * 100
                    st.success(f"**{prob_profit:.0f}%** probability of profit | **{(final_vals > 150).mean()*100:.0f}%** chance of 50%+ returns | **{(final_vals < 80).mean()*100:.0f}%** risk of 20%+ loss")