"""Stress Test Dashboard"""
import streamlit as st
import plotly.graph_objects as go
from analytics.stress import StressTestEngine
from theme import COLORS, style_fig

SEVERITY_COLOR = {
    '💀 EXTREME': '#7f1d1d',
    '🔴 CRITICAL': COLORS['down'],
    '🟠 HIGH': '#f97316',
    '🟡 MODERATE': COLORS['neutral'],
    '🟢 LOW/NEUTRAL': COLORS['text_3'],
    '🟢 POSITIVE': COLORS['up'],
}


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

    st.success(f"✅ {len(results_df)} distinct scenarios completed — each models a different real-world event, not the same shock at different magnitudes.")

    col1, col2, col3, col4 = st.columns(4)
    worst = results_df.loc[results_df['Loss %'].idxmin()]
    best = results_df.loc[results_df['Loss %'].idxmax()]
    critical_count = len(results_df[results_df['Severity'].str.contains('CRITICAL|EXTREME')])

    col1.metric("Current Price", f"{cur}{cp:.2f}")
    col2.metric("Worst Case", f"{worst['Test']}", delta=f"{worst['Loss %']:.1f}%", delta_color="inverse")
    col3.metric("Best Case", f"{best['Test']}", delta=f"{best['Loss %']:.1f}%")
    col4.metric("Critical/Extreme", f"{critical_count}/{len(results_df)}")

    # ── Category filter ──
    categories = ['All'] + sorted(results_df['Category'].unique().tolist())
    selected_cat = st.selectbox("Filter by scenario category", categories)
    view_df = results_df if selected_cat == 'All' else results_df[results_df['Category'] == selected_cat]

    # ── Sorted horizontal bar chart of impact across scenarios ──
    sorted_df = view_df.sort_values('Loss %')
    bar_colors = [SEVERITY_COLOR.get(s, COLORS['text_3']) for s in sorted_df['Severity']]

    fig = go.Figure(go.Bar(
        x=sorted_df['Loss %'], y=sorted_df['Test'], orientation='h',
        marker=dict(color=bar_colors, line=dict(color=COLORS['border_strong'], width=0.5)),
        customdata=sorted_df[['Category', 'Description']],
        hovertemplate="<b>%{y}</b><br>Impact: %{x:.1f}%<br>Category: %{customdata[0]}<br>%{customdata[1]}<extra></extra>",
        text=[f"{v:+.1f}%" for v in sorted_df['Loss %']], textposition='outside',
        textfont=dict(size=10, color=COLORS['text_1']),
    ))
    fig.add_vline(x=0, line_color=COLORS['border_strong'], line_width=1)
    fig.update_layout(
        title="Price Impact by Scenario",
        height=max(500, 26 * len(sorted_df)),
        margin=dict(l=10, r=60, t=45, b=20),
        xaxis=dict(title="Price Impact %", ticksuffix="%"),
        showlegend=False,
    )
    st.plotly_chart(style_fig(fig), use_container_width=True)

    def color_severity(val):
        if 'EXTREME' in str(val):
            return f'background-color: rgba(127,29,29,0.35); color: #fca5a5; font-weight: bold'
        if 'CRITICAL' in str(val):
            return f'background-color: rgba(255,93,122,0.22); color: {COLORS["down"]}; font-weight: bold'
        elif 'HIGH' in str(val):
            return f'background-color: rgba(249,115,22,0.18); color: #f97316; font-weight: bold'
        elif 'MODERATE' in str(val):
            return f'background-color: rgba(245,185,66,0.14); color: {COLORS["neutral"]}; font-weight: bold'
        elif 'POSITIVE' in str(val):
            return f'background-color: rgba(34,211,143,0.18); color: {COLORS["up"]}; font-weight: bold'
        return ''

    st.markdown("#### 📋 Scenario Detail")
    display_cols = ['Test', 'Category', 'Impact Price', 'Loss %', 'Severity', 'Description']
    try:
        styled_df = view_df[display_cols].style.applymap(color_severity, subset=['Severity'])
        st.dataframe(styled_df, use_container_width=True, height=460)
    except Exception:
        st.dataframe(view_df[display_cols], use_container_width=True, height=460)

    # ── Severity distribution + category breakdown side by side ──
    c1, c2 = st.columns(2)
    with c1:
        severity_counts = results_df['Severity'].value_counts()
        pie_colors = [SEVERITY_COLOR.get(s, COLORS['text_3']) for s in severity_counts.index]
        fig = go.Figure(data=[go.Pie(
            labels=severity_counts.index, values=severity_counts.values, hole=0.5,
            marker=dict(colors=pie_colors, line=dict(color=COLORS['bg_1'], width=2)),
            textinfo='label+value', textfont=dict(size=11, color=COLORS['text_1']),
        )])
        fig.update_layout(title='Severity Distribution (All Scenarios)', height=380,
                           legend=dict(orientation='h', y=-0.1))
        st.plotly_chart(style_fig(fig), use_container_width=True)

    with c2:
        cat_avg = results_df.groupby('Category')['Loss %'].mean().sort_values()
        cat_colors = [COLORS['down'] if v < 0 else COLORS['up'] for v in cat_avg.values]
        fig = go.Figure(go.Bar(
            x=cat_avg.values, y=cat_avg.index, orientation='h',
            marker=dict(color=cat_colors, line=dict(color=COLORS['border_strong'], width=1)),
            text=[f"{v:+.1f}%" for v in cat_avg.values], textposition='outside',
            textfont=dict(size=11, color=COLORS['text_1']),
        ))
        fig.add_vline(x=0, line_color=COLORS['border_strong'], line_width=1)
        fig.update_layout(title='Average Impact by Category', height=380,
                           margin=dict(l=10, r=40, t=45, b=20),
                           xaxis=dict(title="Avg Loss %", ticksuffix="%"), showlegend=False)
        st.plotly_chart(style_fig(fig), use_container_width=True)

    st.caption(
        f"Scenarios are calibrated using this stock's beta ({beta:.2f}), sector ({sector}), and market cap; "
        "each scenario has its own base severity and sensitivity profile rather than being a rescaled copy of another test."
    )