"""Index Comparison Dashboard"""
import streamlit as st
import plotly.graph_objects as go
from analytics.index_compare import IndexComparison
from theme import COLORS, style_fig

def create_index_comparison_dashboard(analyzer):
    st.markdown('<div class="section-header">📊 Index & Sector Comparison</div>', unsafe_allow_html=True)
    ticker = analyzer.ticker
    currency = analyzer.currency
    benchmark_name = 'NIFTY 50' if currency == 'INR' else 'S&P 500'
    
    periods = {"1 Month": "1mo", "3 Months": "3mo", "6 Months": "6mo", "1 Year": "1y", "2 Years": "2y"}
    selected = st.select_slider("Comparison Period", options=list(periods.keys()), value="1 Year")
    period = periods[selected]
    
    if st.button(f"📊 Compare vs {benchmark_name}", type="primary", use_container_width=True):
        with st.spinner("Fetching comparison data..."):
            comp = IndexComparison.fetch_comparison_data(ticker, currency, period)
        if comp is None:
            st.error("Could not fetch comparison data.")
            return
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(analyzer.company_name[:15], f"{comp['stock_annual_return']*100:.1f}%")
        col2.metric(benchmark_name, f"{comp['benchmark_annual_return']*100:.1f}%")
        col3.metric("Alpha", f"{comp['alpha']*100:.2f}%")
        col4.metric("Beta", f"{comp['beta']:.2f}")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=comp['stock_cumulative'].index, y=comp['stock_cumulative'].values, name=analyzer.company_name[:20], line=dict(color=COLORS['accent_1'], width=3)))
        fig.add_trace(go.Scatter(x=comp['benchmark_cumulative'].index, y=comp['benchmark_cumulative'].values, name=benchmark_name, line=dict(color=COLORS['text_3'], width=2, dash='dash')))
        fig.update_layout(title=f'Total Return Comparison • {selected}', height=500)
        st.plotly_chart(style_fig(fig), use_container_width=True)