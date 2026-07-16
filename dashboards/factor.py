"""Factor Investing Dashboard"""
import streamlit as st
import plotly.graph_objects as go
from models.factor import FactorInvesting
from theme import COLORS, style_fig

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
            
            st.markdown(f"""
            <div style="background: linear-gradient(160deg, {COLORS['surface']}, {COLORS['bg_2']}); border: 1px solid {color}55; border-top: 2px solid {color};
                        padding: 1rem; border-radius: 14px; text-align: center; min-height: 160px; box-shadow: 0 8px 20px rgba(0,0,0,0.25);">
                <div style="font-size: 0.75rem; color: {COLORS['text_3']}; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem;">{factor}</div>
                <div style="font-size: 2rem; font-weight: 900; color: {color};">{score}</div>
                <div style="font-size: 0.85rem; font-weight: 600; color: {color};">{classification}</div>
                <div style="font-size: 0.65rem; color: {COLORS['text_3']}; margin-top: 0.5rem;">{data.get('detail', '')[:60]}</div>
            </div>
            """, unsafe_allow_html=True)
    
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
        fillcolor='rgba(109,94,248,0.28)'
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