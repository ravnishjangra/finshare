"""Advanced Financial Scores Dashboard"""
import streamlit as st
import plotly.graph_objects as go
from models.piotroski import PiotroskiFScore
from models.altman import AltmanZScore

def create_advanced_scores_dashboard(analyzer):
    st.markdown('<div class="section-header">🔬 Advanced Financial Scores</div>', unsafe_allow_html=True)
    income = analyzer.financials.get('income')
    balance = analyzer.financials.get('balance')
    cashflow = analyzer.financials.get('cashflow')
    market_cap = analyzer.live_price_data.get('market_cap', 0)
    
    if income is None or income.empty:
        st.warning("Financial statements not available.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Piotroski F-Score")
        f_score = PiotroskiFScore.calculate(income, balance, cashflow)
        score_color = "#10b981" if f_score['score'] >= 7 else "#f59e0b" if f_score['score'] >= 4 else "#ef4444"
        
        fig = go.Figure(go.Indicator(mode="gauge+number", value=f_score['score'], title={'text':"F-Score"},
                        gauge={'axis':{'range':[0,9]},'bar':{'color':score_color},
                               'steps':[{'range':[0,3],'color':"rgba(239,68,68,0.2)"},
                                        {'range':[3,6],'color':"rgba(245,158,11,0.2)"},
                                        {'range':[6,9],'color':"rgba(16,185,129,0.2)"}]}))
        fig.update_layout(height=250, margin=dict(t=30,b=0))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f"**{f_score['rating']}**")
        with st.expander(f"Details ({f_score['score']}/9)"):
            for d in f_score['details']: st.write(d)
    
    with col2:
        st.markdown("### 🏦 Altman Z-Score")
        z_result = AltmanZScore.calculate(balance, income, market_cap)
        if z_result:
            z = z_result['z_score']
            z_color = "#10b981" if z > 2.99 else "#f59e0b" if z > 1.81 else "#ef4444"
            fig = go.Figure(go.Indicator(mode="gauge+number", value=z, title={'text':"Z-Score"},
                            gauge={'axis':{'range':[0,6]},'bar':{'color':z_color},
                                   'steps':[{'range':[0,1.81],'color':"rgba(239,68,68,0.2)"},
                                            {'range':[1.81,2.99],'color':"rgba(245,158,11,0.2)"},
                                            {'range':[2.99,6],'color':"rgba(16,185,129,0.2)"}]}))
            fig.update_layout(height=250, margin=dict(t=30,b=0))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(f"**{z_result['zone']}** - {z_result['risk']}")
        else:
            st.warning("Insufficient data for Z-Score")