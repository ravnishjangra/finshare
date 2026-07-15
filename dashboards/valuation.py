"""Valuation Dashboard"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from models.dcf import AdvancedDCF
from models.graham import GrahamValuation
from models.epv import EarningsPowerValue

def create_valuation_dashboard(analyzer):
    st.markdown('<div class="section-header">💰 Advanced Valuation Models</div>', unsafe_allow_html=True)
    income = analyzer.financials.get('income')
    cashflow = analyzer.financials.get('cashflow')
    cp = analyzer.live_price_data.get('current_price')
    cur = analyzer.currency_symbol
    
    if not cp:
        st.warning("Current price not available.")
        return
    
    rev = analyzer._safe_get(income, ['Total Revenue', 'Revenue']) or 0
    ni = analyzer._safe_get(income, ['Net Income', 'Net Income Common Stockholders']) or 0
    fcf = analyzer._safe_get(cashflow, ['Free Cash Flow']) or (ni * 0.8 if ni else (rev * 0.1 if rev else 1e6))
    shares = analyzer._safe_get(income, ['Diluted Average Shares']) or analyzer._safe_get(income, ['Basic Average Shares']) or (analyzer.live_price_data.get('market_cap', 1e9) / cp if cp > 0 else 1e6)
    beta = analyzer.live_price_data.get('beta', 1.0) or 1.0
    rg = max(0.02, min((analyzer.ratios.get('Revenue Growth (YoY)', 10) or 10) / 100, 0.35))
    om = (analyzer.ratios.get('Operating Margin', 15) or 15) / 100
    rf = 0.072 if analyzer.currency == 'INR' else 0.045
    mr = 0.12 if analyzer.currency == 'INR' else 0.10

    with st.expander("⚙️ DCF Parameters", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            dcf_growth = st.slider("Growth %", 1, 35, int(rg*100)) / 100
            dcf_fcf = st.number_input("FCF (M)", value=float(fcf)/1e6, format="%.1f") * 1e6
        with c2:
            dcf_shares = st.number_input("Shares (M)", value=float(shares)/1e6, format="%.1f") * 1e6
            dcf_beta = st.number_input("Beta", value=float(beta), min_value=0.1, max_value=3.0, step=0.1)
        with c3:
            dcf_rf = st.slider("Risk-Free %", 1.0, 12.0, rf*100, 0.1) / 100
            dcf_mr = st.slider("Market Return %", 5.0, 18.0, mr*100, 0.1) / 100

    dcf = AdvancedDCF(dcf_fcf, dcf_shares, cp, dcf_growth, dcf_beta, dcf_rf, dcf_mr)
    result = dcf.calculate()
    
    st.markdown(f'<div style="background-color:{result["rec_color"]};padding:1.5rem;border-radius:16px;color:white;text-align:center;margin:1rem 0;"><h2>{result["recommendation"]}</h2><p>Intrinsic Value: {cur}{result["intrinsic_value"]:.2f} | Upside: {result["upside"]:+.1f}%</p></div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Intrinsic Value", f"{cur}{result['intrinsic_value']:.2f}")
    col2.metric("Current Price", f"{cur}{cp:.2f}", delta=f"{result['upside']:+.1f}%")
    col3.metric("WACC", f"{result['wacc']*100:.1f}%")
    col4.metric("Bear/Bull", f"{cur}{result['bear_case']:.0f} - {cur}{result['bull_case']:.0f}")

    unit = 'Cr' if analyzer.currency == 'INR' else 'B'
    div = 1e7 if analyzer.currency == 'INR' else 1e9
    years = [p['year'] for p in result['projections']]
    fcf_vals = [p['fcf']/div for p in result['projections']]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=years, y=fcf_vals, name='FCF', marker_color='#667eea'))
    fig.update_layout(title=f'10-Year FCF Projection ({cur}{unit})', template='plotly_white', height=350)
    st.plotly_chart(fig, use_container_width=True)

    eps = analyzer.ratios.get('EPS', ni/shares if ni and shares else 1)
    graham_val = GrahamValuation.calculate(eps, rg, rf)
    epv = EarningsPowerValue.calculate(rev or 0, om, 0.25, result['wacc'], shares)

    st.markdown("### 📊 Valuation Model Comparison")
    models = {'Advanced DCF': result['intrinsic_value'], 'Graham': graham_val, 'EPV': epv, 'Current Price': cp}
    fig = go.Figure()
    for model, val in models.items():
        color = '#10b981' if val > cp else '#ef4444' if val < cp else '#f59e0b'
        fig.add_trace(go.Bar(x=[model], y=[val], marker_color=color, text=[f"{cur}{val:.2f}"], textposition='outside'))
    fig.add_hline(y=cp, line_dash="dash", line_color="#94a3b8")
    fig.update_layout(title='All Valuation Models', template='plotly_white', height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)