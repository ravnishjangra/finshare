"""Advanced Financial Scores Dashboard"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from models.piotroski import PiotroskiFScore
from models.altman import AltmanZScore

def create_advanced_scores_dashboard(analyzer):
    st.markdown('<div class="section-header">🔬 Financial Strength Scores</div>', unsafe_allow_html=True)
    income = analyzer.financials.get('income')
    balance = analyzer.financials.get('balance')
    cashflow = analyzer.financials.get('cashflow')
    market_cap = analyzer.live_price_data.get('market_cap', 0)
    
    if income is None or income.empty:
        st.warning("Financial statements not available.")
        return
    
    col1, col2 = st.columns(2)
    
    # ===== PIOTROSKI F-SCORE =====
    with col1:
        st.markdown("### 📊 Piotroski F-Score")
        st.caption("Financial strength indicator (0-9)")
        f_score = PiotroskiFScore.calculate(income, balance, cashflow)
        
        score = f_score.get('score', 0)
        score_color = f_score.get('color', '#94a3b8')
        rating = f_score.get('rating', 'N/A')
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            number={'font': {'color': score_color, 'size': 48}},
            title={'text': "Piotroski F-Score", 'font': {'size': 14}},
            gauge={
                'axis': {'range': [0, 9], 'tickwidth': 1},
                'bar': {'color': score_color, 'thickness': 0.2},
                'steps': [
                    {'range': [0, 3], 'color': "rgba(239,68,68,0.15)"},
                    {'range': [3, 6], 'color': "rgba(245,158,11,0.15)"},
                    {'range': [6, 9], 'color': "rgba(16,185,129,0.15)"}
                ],
                'threshold': {'line': {'color': score_color, 'width': 3}, 'thickness': 0.8, 'value': score}
            }
        ))
        fig.update_layout(height=220, margin=dict(t=30, b=0, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown(f"<h3 style='text-align:center; color:{score_color};'>{rating}</h3>", unsafe_allow_html=True)
        
        breakdown = f_score.get('breakdown', {})
        if breakdown and not f_score.get('error'):
            st.markdown("---")
            st.markdown(f"**Overall: {breakdown.get('total', 'N/A')}**")
            
            prof = breakdown.get('profitability', {})
            st.markdown(f"**Profitability** {prof.get('stars', '')} ({prof.get('score', 'N/A')})")
            for item in prof.get('items', []):
                icon = '✅' if item['status'] == 'pass' else '❌' if item['status'] == 'fail' else '⬜'
                st.caption(f"{icon} {item['name']}: {item['detail']}")
            
            lev = breakdown.get('leverage', {})
            st.markdown(f"**Leverage & Liquidity** {lev.get('stars', '')} ({lev.get('score', 'N/A')})")
            for item in lev.get('items', []):
                icon = '✅' if item['status'] == 'pass' else '❌' if item['status'] == 'fail' else '⬜'
                st.caption(f"{icon} {item['name']}: {item['detail']}")
            
            eff = breakdown.get('efficiency', {})
            st.markdown(f"**Operating Efficiency** {eff.get('stars', '')} ({eff.get('score', 'N/A')})")
            for item in eff.get('items', []):
                icon = '✅' if item['status'] == 'pass' else '❌' if item['status'] == 'fail' else '⬜'
                st.caption(f"{icon} {item['name']}: {item['detail']}")
        else:
            with st.expander("📋 Details"):
                for d in f_score.get('details', []):
                    st.write(d)
    
    # ===== ALTMAN Z-SCORE =====
    with col2:
        st.markdown("### 🏦 Altman Z-Score")
        st.caption("Bankruptcy prediction model")
        z_result = AltmanZScore.calculate(balance, income, market_cap)
        
        if z_result and z_result.get('z_score') and not pd.isna(z_result['z_score']):
            z = z_result['z_score']
            z_color = z_result.get('color', '#94a3b8')
            zone = z_result.get('zone', 'N/A')
            risk = z_result.get('risk_level', 'N/A')
            prob = z_result.get('probability', 'N/A')
            interpretation = z_result.get('interpretation', '')
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=z,
                number={'font': {'color': z_color, 'size': 48}},
                title={'text': "Altman Z-Score", 'font': {'size': 14}},
                gauge={
                    'axis': {'range': [0, 6], 'tickwidth': 1},
                    'bar': {'color': z_color, 'thickness': 0.2},
                    'steps': [
                        {'range': [0, 1.81], 'color': "rgba(239,68,68,0.15)"},
                        {'range': [1.81, 2.99], 'color': "rgba(245,158,11,0.15)"},
                        {'range': [2.99, 6], 'color': "rgba(16,185,129,0.15)"}
                    ],
                    'threshold': {'line': {'color': z_color, 'width': 3}, 'thickness': 0.8, 'value': z}
                }
            ))
            fig.update_layout(height=220, margin=dict(t=30, b=0, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown(f"<h3 style='text-align:center; color:{z_color};'>{zone}</h3>", unsafe_allow_html=True)
            
            st.markdown("---")
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Z-Score", f"{z:.2f}")
                st.metric("Probability of Distress", prob)
            with col_b:
                st.metric("Risk Level", risk)
            
            st.markdown(f"**Interpretation:** {interpretation}")
            
            components = z_result.get('components', {})
            if components:
                with st.expander("🔍 Component Breakdown"):
                    for comp_name, comp_data in components.items():
                        val = comp_data['value']
                        weight = comp_data['weight']
                        signal = comp_data['signal']
                        val_color = '#10b981' if val > 0 else '#ef4444'
                        st.markdown(f"**{comp_name}** = <span style='color:{val_color}'>{val:.3f}</span> × {weight} → *{signal}*", unsafe_allow_html=True)
        else:
            st.warning("Insufficient data for Z-Score calculation.")
            
            # Show what's missing
            st.markdown("**Possible reasons:**")
            if not market_cap or market_cap <= 0:
                st.caption("❌ Market Cap not available")
            if balance is None or balance.empty:
                st.caption("❌ Balance Sheet not available")
            else:
                col = balance.columns[0] if not balance.empty else None
                if col:
                    ta = next((balance.loc[k, col] for k in ['Total Assets'] if k in balance.index), 0)
                    if not ta or ta <= 0 or pd.isna(ta):
                        st.caption("❌ Total Assets = 0 or missing")
            if income is None or income.empty:
                st.caption("❌ Income Statement not available")
            else:
                inc_col = income.columns[0] if not income.empty else None
                if inc_col:
                    ebit = next((income.loc[k, inc_col] for k in ['EBIT', 'Operating Income'] if k in income.index), 0)
                    sales = next((income.loc[k, inc_col] for k in ['Total Revenue', 'Revenue'] if k in income.index), 0)
                    if not ebit or ebit == 0 or pd.isna(ebit):
                        st.caption("⚠️ EBIT/Operating Income = 0 (X3 component)")
                    if not sales or sales == 0 or pd.isna(sales):
                        st.caption("⚠️ Revenue = 0 (X5 component)")