"""Factor Investing Dashboard"""
import streamlit as st
import plotly.graph_objects as go
from models.factor import FactorInvesting
from theme import COLORS, style_fig, metric_card

def create_factor_investing_dashboard(analyzer):
    prices = analyzer.financials.get('prices')
    info = analyzer.financials.get('info', {})
    ratios = analyzer.ratios
    
    exposures = FactorInvesting.analyze_factor_exposure(prices, info, ratios)
    if not exposures:
        return
    
    st.markdown('<div class="section-header">🎯 Quantitative Factor Investing</div>', unsafe_allow_html=True)
    st.caption("Fama-French style factor analysis using 5-year returns and fundamentals")
    
    st.markdown("### 📊 Factor Exposure Scores")
    cols = st.columns(5)
    
    for col, (factor, data) in zip(cols, exposures.items()):
        with col:
            score = data.get('score', 'N/A')
            classification = data.get('classification', 'N/A')
            color = data.get('color', COLORS['text_2'])

            st.markdown(
                metric_card(
                    label=factor, value=str(score), value_color=color, accent=color,
                    sublabel=classification, footer=data.get('detail', '')[:60], center=True,
                    min_height='160px',
                ),
                unsafe_allow_html=True,
            )
    
    # Factor descriptions
    with st.expander("📖 What do these factors mean?"):
        for factor, desc in FactorInvesting.FACTOR_DESCRIPTIONS.items():
            st.markdown(f"**{factor}**: {desc}")
    
    # Radar chart
    categories = list(exposures.keys())
    scores = [exposures[cat].get('score', 50) for cat in categories]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        name='Factor Exposure',
        line=dict(color=COLORS['accent_1'], width=2),
        fillcolor='rgba(109,94,248,0.28)',
        hovertemplate='%{theta}: %{r:.1f}<extra></extra>',
    ))
    fig.update_layout(
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(visible=True, range=[0, 100], gridcolor=COLORS['border'], linecolor=COLORS['border']),
            angularaxis=dict(gridcolor=COLORS['border'], linecolor=COLORS['border'])
        ),
        showlegend=False,
        height=400,
    )
    st.plotly_chart(style_fig(fig), use_container_width=True)