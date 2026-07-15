"""Stress Test Dashboard"""
import streamlit as st
import plotly.graph_objects as go
from analytics.stress import StressTestEngine

def create_stress_test_dashboard(analyzer):
    st.markdown('<div class="section-header">🛡️ Comprehensive Stress Tests</div>', unsafe_allow_html=True)
    cp = analyzer.live_price_data.get('current_price')
    cur = analyzer.currency_symbol
    
    if not cp:
        st.warning("Current price not available.")
        return
    
    sector = analyzer.financials.get('sector', 'Unknown')
    industry = analyzer.financials.get('industry', 'Unknown')
    beta = analyzer.live_price_data.get('beta', 1.0) or 1.0
    market_cap = analyzer.live_price_data.get('market_cap', 0) or 0
    
    engine = StressTestEngine(cp, sector, industry, beta, analyzer.currency, market_cap)
    
    with st.spinner("Running stress tests..."):
        results_df = engine.run_all_tests()
    
    st.success(f"✅ {len(results_df)} scenarios completed!")
    
    col1, col2, col3, col4 = st.columns(4)
    worst = results_df.loc[results_df['Loss %'].idxmin()]
    best = results_df.loc[results_df['Loss %'].idxmax()]
    critical_count = len(results_df[results_df['Severity'].str.contains('CRITICAL|EXTREME|MAXIMUM')])
    
    col1.metric("Current Price", f"{cur}{cp:.2f}")
    col2.metric("Worst Case", f"{cur}{worst['Impact Price']:.2f}", delta=f"{worst['Loss %']:.1f}%", delta_color="inverse")
    col3.metric("Best Case", f"{cur}{best['Impact Price']:.2f}", delta=f"{best['Loss %']:.1f}%")
    col4.metric("Critical", f"{critical_count}/{len(results_df)}")

    def color_severity(val):
        if 'CRITICAL' in str(val) or 'EXTREME' in str(val) or 'MAXIMUM' in str(val):
            return 'background-color: rgba(239,68,68,0.3); color: #ef4444; font-weight: bold'
        elif 'HIGH' in str(val):
            return 'background-color: rgba(245,158,11,0.2); color: #f59e0b; font-weight: bold'
        elif 'POSITIVE' in str(val) or 'WINNER' in str(val):
            return 'background-color: rgba(16,185,129,0.2); color: #10b981; font-weight: bold'
        return ''
    
    try:
        styled_df = results_df.style.applymap(color_severity, subset=['Severity'])
        st.dataframe(styled_df, use_container_width=True, height=500)
    except:
        st.dataframe(results_df, use_container_width=True, height=500)

    severity_counts = results_df['Severity'].str.extract(r'(🔴|🟠|🟡|🟢|💀)')[0].value_counts()
    fig = go.Figure(data=[go.Pie(labels=severity_counts.index, values=severity_counts.values, hole=0.4)])
    fig.update_layout(title='Severity Distribution', template='plotly_white', height=350)
    st.plotly_chart(fig, use_container_width=True)