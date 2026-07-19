"""Valuation Dashboard"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from models.dcf import AdvancedDCF
from models.graham import GrahamValuation
from models.epv import EarningsPowerValue
from models.residual_income import ResidualIncome
from theme import COLORS, style_fig, style_fig_3d, VALUE_COLORSCALE, animated_config

def create_valuation_dashboard(analyzer):
    st.markdown('<div class="section-header">💰 Advanced Valuation Models</div>', unsafe_allow_html=True)
    income = analyzer.financials.get('income')
    cashflow = analyzer.financials.get('cashflow')
    cp = analyzer.live_price_data.get('current_price')
    cur = analyzer.currency_symbol
    
    if not cp:
        st.warning("Current price not available.")
        return
    
    rev = analyzer._safe_get(income, ['Total Revenue', 'Revenue']) if income is not None else 0
    ni = analyzer._safe_get(income, ['Net Income', 'Net Income Common Stockholders']) if income is not None else 0
    fcf = analyzer._safe_get(cashflow, ['Free Cash Flow']) if cashflow is not None else None
    
    if not fcf:
        if ni and ni > 0:
            fcf = ni * 0.8
        elif rev and rev > 0:
            fcf = rev * 0.1
        else:
            fcf = cp * 1000000
    
    shares = None
    if income is not None:
        shares = analyzer._safe_get(income, ['Diluted Average Shares']) or analyzer._safe_get(income, ['Basic Average Shares'])
    
    if not shares:
        mcap = analyzer.live_price_data.get('market_cap')
        if mcap and mcap > 0 and cp > 0:
            shares = mcap / cp
        else:
            shares = 1e6
    
    if not shares or shares <= 0:
        shares = 1e6
    
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
    
    if result['intrinsic_value'] > cp * 1000 or result['intrinsic_value'] < cp * 0.001:
        st.warning("⚠️ DCF values seem extreme. This may be due to limited financial data. Adjust parameters or try a different ticker.")
        return
    
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
    fig.add_trace(go.Bar(x=years, y=fcf_vals, name='FCF', marker_color=COLORS['accent_1']))
    fig.update_layout(title=f'10-Year FCF Projection ({cur}{unit})', height=350)
    st.plotly_chart(style_fig(fig), use_container_width=True)

    eps = analyzer.ratios.get('EPS', ni/shares if ni and shares else 1)
    graham_val = GrahamValuation.calculate(eps, rg, rf) if eps and eps > 0 else 0
    epv = EarningsPowerValue.calculate(rev or 0, om, 0.25, result['wacc'], shares) if rev and rev > 0 else 0

    st.markdown("### 📊 Valuation Model Comparison")
    models = {'Advanced DCF': result['intrinsic_value'], 'Graham': graham_val, 'EPV': epv, 'Current Price': cp}
    fig = go.Figure()
    for model, val in models.items():
        if val and val > 0:
            color = COLORS['up'] if val > cp else COLORS['down'] if val < cp else COLORS['neutral']
            fig.add_trace(go.Bar(x=[model], y=[val], marker_color=color, text=[f"{cur}{val:.2f}"], textposition='outside'))
    fig.add_hline(y=cp, line_dash="dash", line_color=COLORS['text_3'])
    fig.update_layout(title='All Valuation Models', height=400, showlegend=False)
    st.plotly_chart(style_fig(fig), use_container_width=True)

    # ===== 3D DCF SENSITIVITY SURFACE =====
    st.markdown('<div class="section-header">🧊 3D Valuation Sensitivity</div>', unsafe_allow_html=True)
    st.caption("Intrinsic value across a grid of Growth × WACC assumptions — drag to rotate, scroll to zoom")

    growth_lo, growth_hi = max(0.01, dcf_growth - 0.15), min(0.40, dcf_growth + 0.15)
    beta_lo, beta_hi = max(0.3, dcf_beta - 0.9), min(2.6, dcf_beta + 0.9)
    growth_grid = np.linspace(growth_lo, growth_hi, 16)
    beta_grid = np.linspace(beta_lo, beta_hi, 16)

    z_surface = np.zeros((len(beta_grid), len(growth_grid)))
    wacc_axis = np.zeros(len(beta_grid))
    for i, b in enumerate(beta_grid):
        trial = None
        for j, g in enumerate(growth_grid):
            trial = AdvancedDCF(dcf_fcf, dcf_shares, cp, g, b, dcf_rf, dcf_mr)
            z_surface[i, j] = trial.calculate()['intrinsic_value']
        wacc_axis[i] = trial.wacc * 100  # WACC is independent of growth, only depends on beta

    # cap outlier spikes so the surface stays readable
    z_cap = np.nanpercentile(z_surface, 97)
    z_surface_display = np.clip(z_surface, None, z_cap)

    fig3d = go.Figure(data=[go.Surface(
        x=growth_grid * 100, y=wacc_axis, z=z_surface_display,
        colorscale=VALUE_COLORSCALE,
        colorbar=dict(title=f"{cur}/sh", tickfont=dict(color=COLORS['text_3']), len=0.65),
        contours={"z": {"show": True, "usecolormap": True, "highlightcolor": COLORS['accent_3'], "project_z": True}},
        hovertemplate="Growth: %{x:.1f}%<br>WACC: %{y:.1f}%<br>Value: " + cur + "%{z:.2f}<extra></extra>",
        opacity=0.94,
    )])
    fig3d.add_trace(go.Scatter3d(
        x=[dcf_growth * 100], y=[result['wacc'] * 100], z=[min(result['intrinsic_value'], z_cap)],
        mode='markers+text', text=['Current'], textposition='top center',
        marker=dict(size=6, color=COLORS['text_1'], symbol='diamond', line=dict(width=1.5, color=COLORS['accent_3'])),
        textfont=dict(color=COLORS['text_1'], size=11), showlegend=False,
        hovertemplate="Current assumptions<br>Value: " + cur + "%{z:.2f}<extra></extra>",
    ))
    fig3d = style_fig_3d(fig3d, x_title="Growth %", y_title="WACC %", z_title=f"Intrinsic Value ({cur})", height=520)
    st.plotly_chart(fig3d, use_container_width=True, config=animated_config())
    st.caption("Green ridge = assumption combinations that make the stock look cheap relative to today's price; red = expensive.")

    # ===== RESIDUAL INCOME VALUATION =====
    st.markdown("### 📊 Residual Income Valuation")
    ri = ResidualIncome.calculate(income, analyzer.financials.get('balance'), 
                                   analyzer.financials.get('info', {}), cp,
                                   risk_free_rate=0.072 if analyzer.currency == 'INR' else 0.045,
                                   market_return=0.12 if analyzer.currency == 'INR' else 0.10)
    if ri:
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Intrinsic Value", f"{cur}{ri['intrinsic_value']:.2f}")
        with col2: st.metric("Book Value/Share", f"{cur}{ri['book_value_ps']:.2f}")
        with col3: st.metric("Residual Income", f"{cur}{ri['residual_income']:.2f}")
        st.caption(f"Cost of Equity: {ri['cost_of_equity']}% | Growth: {ri['growth_rate']}% | {ri['recommendation']}")