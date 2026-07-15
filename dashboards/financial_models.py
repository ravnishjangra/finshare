"""Financial Models Dashboard - Performance, Beneish, DuPont, Composite, Ohlson, Fear & Greed"""
import streamlit as st
import plotly.graph_objects as go
from models.beneish import BeneishMScore
from models.dupont import DuPontAnalysis
from models.performance_ratios import PerformanceRatios
from models.composite_score import CompositeScore
from models.piotroski import PiotroskiFScore
from models.altman import AltmanZScore
from models.ohlson import OhlsonOScore
from models.fear_greed import FearGreedIndex

def create_financial_models_dashboard(analyzer):
    st.markdown('<div class="section-header">📊 Advanced Financial Models</div>', unsafe_allow_html=True)
    
    income = analyzer.financials.get('income')
    balance = analyzer.financials.get('balance')
    cashflow = analyzer.financials.get('cashflow')
    prices = analyzer.financials.get('prices')
    info = analyzer.financials.get('info', {})
    ratios = analyzer.ratios
    market_cap = analyzer.live_price_data.get('market_cap', 0)
    
    if income is None or income.empty:
        st.warning("Financial statements not available for advanced models.")
        return
    
    # ===== SECTION 1: FEAR & GREED INDEX =====
    st.markdown("### 😱 Fear & Greed Index")
    
    fg = FearGreedIndex.calculate(prices, info)
    if fg:
        col1, col2 = st.columns([1, 2])
        with col1:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=fg['score'],
                number={'font': {'color': fg['color'], 'size': 48}},
                title={'text': "Fear & Greed"},
                gauge={
                    'axis': {'range': [0, 100], 'tickcolor': '#94a3b8'},
                    'bar': {'color': fg['color']},
                    'steps': [
                        {'range': [0, 25], 'color': "rgba(239,68,68,0.3)"},
                        {'range': [25, 45], 'color': "rgba(245,158,11,0.3)"},
                        {'range': [45, 55], 'color': "rgba(148,163,184,0.3)"},
                        {'range': [55, 75], 'color': "rgba(52,211,153,0.3)"},
                        {'range': [75, 100], 'color': "rgba(16,185,129,0.3)"},
                    ],
                    'threshold': {'line': {'color': 'white', 'width': 3}, 'value': fg['score']}
                }
            ))
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(f"<h3 style='text-align:center;color:{fg['color']};'>{fg['sentiment']}</h3>", unsafe_allow_html=True)
            st.caption(f"💡 {fg['advice']}")
        
        with col2:
            for factor, score in fg['factors'].items():
                bar = '█' * int(score) + '░' * (25 - int(score))
                factor_color = '#10b981' if score > 15 else '#f59e0b' if score > 8 else '#ef4444'
                st.markdown(f"**{factor}**: <span style='color:{factor_color}'>{bar}</span> {score}/25", unsafe_allow_html=True)
    
    # ===== SECTION 2: PERFORMANCE METRICS =====
    st.markdown("### 📈 Performance Metrics")
    
    risk_free = 0.06 if analyzer.currency == 'USD' else 0.07
    perf = PerformanceRatios.calculate(prices, info, risk_free_rate=risk_free)
    
    if perf:
        cols = st.columns(5)
        for col, (label, val) in zip(cols, [
            ('Annual Return', f"{perf['annual_return']}%"),
            ('Volatility', f"{perf['annual_volatility']}%"),
            ('Sharpe Ratio', f"{perf['sharpe_ratio']}"),
            ('Sortino Ratio', f"{perf['sortino_ratio']}"),
            ('Max Drawdown', f"{perf['max_drawdown']}%"),
        ]):
            with col: st.metric(label, val)
        
        cols = st.columns(5)
        for col, (label, val) in zip(cols, [
            ("Jensen's Alpha", f"{perf['jensens_alpha']}%"),
            ('Beta', f"{perf['beta']}"),
            ('Treynor Ratio', f"{perf['treynor_ratio']}"),
            ('Info Ratio', f"{perf['information_ratio']}"),
            ('Calmar Ratio', f"{perf['calmar_ratio']}"),
        ]):
            with col: st.metric(label, val)
        
        with st.expander("🔍 Risk Metrics (VaR & CVaR)"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("VaR 95%", f"{perf['var_95']}%", delta_color="inverse")
            c2.metric("VaR 99%", f"{perf['var_99']}%", delta_color="inverse")
            c3.metric("CVaR 95%", f"{perf['cvar_95']}%", delta_color="inverse")
            c4.metric("Win/Loss Ratio", f"{perf['win_loss_ratio']}")
    
    # ===== SECTION 3: EARNINGS QUALITY =====
    st.markdown("### 🔍 Earnings Quality & Fraud Detection")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**Beneish M-Score**")
        st.caption("Earnings manipulation detection")
        m_score = BeneishMScore.calculate(income, balance, cashflow)
        if m_score:
            st.markdown(f"<h2 style='color:{m_score['color']};text-align:center;'>{m_score['m_score']}</h2>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center;color:{m_score['color']};'><b>{m_score['risk']}</b></p>", unsafe_allow_html=True)
            with st.expander("📋 Components"):
                st.caption(m_score['interpretation'])
                for k, v in m_score['components'].items():
                    st.caption(f"• {k}: {v}")
        else:
            st.warning("Insufficient data")
    
    with col2:
        st.markdown("**Piotroski F-Score**")
        st.caption("Financial strength (0-9)")
        f_score = PiotroskiFScore.calculate(income, balance, cashflow)
        st.markdown(f"<h2 style='color:{f_score.get('color','#94a3b8')};text-align:center;'>{f_score['score']}/9</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;color:{f_score.get('color','#94a3b8')};'><b>{f_score['rating']}</b></p>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("**Altman Z-Score**")
        st.caption("Bankruptcy prediction")
        z_score = AltmanZScore.calculate(balance, income, market_cap)
        if z_score and z_score.get('z_score'):
            st.markdown(f"<h2 style='color:{z_score.get('color','#94a3b8')};text-align:center;'>{z_score['z_score']:.2f}</h2>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center;color:{z_score.get('color','#94a3b8')};'><b>{z_score['zone']}</b></p>", unsafe_allow_html=True)
            st.caption(f"Probability: {z_score.get('probability','N/A')}")
        else:
            st.warning("Insufficient data")
    
    with col4:
        st.markdown("**Ohlson O-Score**")
        st.caption("Bankruptcy probability (1980)")
        o_score = OhlsonOScore.calculate(income, balance, info)
        if o_score:
            st.markdown(f"<h2 style='color:{o_score['color']};text-align:center;'>{o_score['probability']}</h2>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center;color:{o_score['color']};'><b>{o_score['risk']}</b></p>", unsafe_allow_html=True)
            st.caption(o_score['interpretation'])
            with st.expander("📋 Components"):
                for k, v in o_score['components'].items():
                    st.caption(f"• {k}: {v}")
        else:
            st.warning("Insufficient data")
    
    # ===== SECTION 4: DUPONT ANALYSIS =====
    st.markdown("### 🧩 DuPont ROE Decomposition")
    
    dupont = DuPontAnalysis.calculate(income, balance, ratios)
    
    if dupont:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**3-Step DuPont: ROE = {dupont['three_step']['roe']}%**")
            st.caption(f"Net Profit Margin: {dupont['three_step']['net_margin']}%")
            st.caption(f"× Asset Turnover: {dupont['three_step']['asset_turnover']}")
            st.caption(f"× Equity Multiplier: {dupont['three_step']['equity_multiplier']}")
            st.caption(f"= **ROE: {dupont['three_step']['roe']}%**")
            
            fig = go.Figure(go.Waterfall(
                name="3-Step DuPont", orientation="v",
                measure=["relative", "relative", "relative", "total"],
                x=["Net Margin", "× Asset Turnover", "× Equity Multiplier", "= ROE"],
                y=[dupont['three_step']['net_margin'],
                   dupont['three_step']['asset_turnover'] * 100,
                   dupont['three_step']['equity_multiplier'] * 10,
                   dupont['three_step']['roe']],
                connector={"line": {"color": "#94a3b8"}},
            ))
            fig.update_layout(height=280, template='plotly_white', margin=dict(t=10))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if dupont.get('five_step'):
                st.markdown(f"**5-Step DuPont: ROE = {dupont['five_step']['roe']}%**")
                st.caption(f"Tax Burden: {dupont['five_step']['tax_burden']}")
                st.caption(f"× Interest Burden: {dupont['five_step']['interest_burden']}")
                st.caption(f"× Operating Margin: {dupont['five_step']['operating_margin']}%")
                st.caption(f"× Asset Turnover: {dupont['five_step']['asset_turnover']}")
                st.caption(f"× Equity Multiplier: {dupont['five_step']['equity_multiplier']}")
                st.caption(f"= **ROE: {dupont['five_step']['roe']}%**")
                
                fig = go.Figure(go.Waterfall(
                    name="5-Step DuPont", orientation="v",
                    measure=["relative", "relative", "relative", "relative", "relative", "total"],
                    x=["Tax", "Interest", "Op Margin", "Asset TO", "Equity Mult", "= ROE"],
                    y=[dupont['five_step']['tax_burden']*100,
                       dupont['five_step']['interest_burden']*100,
                       dupont['five_step']['operating_margin'],
                       dupont['five_step']['asset_turnover']*100,
                       dupont['five_step']['equity_multiplier']*10,
                       dupont['five_step']['roe']],
                    connector={"line": {"color": "#94a3b8"}},
                ))
                fig.update_layout(height=280, template='plotly_white', margin=dict(t=10))
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Insufficient data for DuPont analysis")
    
    # ===== SECTION 5: COMPOSITE HEALTH SCORE =====
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
            bar = '█' * (score // 10) + '░' * (10 - score // 10)
            st.markdown(f"**{category}**: {bar} {score}%")