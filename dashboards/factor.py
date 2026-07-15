"""Factor Investing Dashboard"""
import streamlit as st
import plotly.graph_objects as go
from models.factor import FactorInvesting

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
            color = data.get('color', '#94a3b8')
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1e293b, #0f172a); border: 2px solid {color}; 
                        padding: 1rem; border-radius: 12px; text-align: center; min-height: 160px;">
                <div style="font-size: 0.75rem; color: #94a3b8; margin-bottom: 0.5rem;">{factor}</div>
                <div style="font-size: 2rem; font-weight: 900; color: {color};">{score}</div>
                <div style="font-size: 0.85rem; font-weight: 600; color: {color};">{classification}</div>
                <div style="font-size: 0.65rem; color: #94a3b8; margin-top: 0.5rem;">{data.get('detail', '')[:60]}</div>
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
        line=dict(color='#667eea', width=2),
        fillcolor='rgba(102,126,234,0.3)'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        height=400,
        template='plotly_white'
    )
    st.plotly_chart(fig, use_container_width=True)