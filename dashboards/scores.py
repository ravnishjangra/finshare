"""Advanced Financial Scores Dashboard"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from models.piotroski import PiotroskiFScore
from models.altman import AltmanZScore
from theme import COLORS, style_fig

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
        score_color = f_score.get('color', COLORS['text_2'])
        rating = f_score.get('rating', 'N/A')
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            number={'font': {'color': score_color, 'size': 48, 'family': 'Inter, sans-serif'}},
            title={'text': "Piotroski F-Score", 'font': {'size': 14, 'color': COLORS['text_2'], 'family': 'Inter, sans-serif'}},
            gauge={
                'axis': {'range': [0, 9], 'tickwidth': 1, 'tickcolor': COLORS['text_3']},
                'bar': {'color': score_color, 'thickness': 0.2},
                'bgcolor': COLORS['bg_2'],
                'steps': [
                    {'range': [0, 3], 'color': "rgba(255,93,122,0.15)"},
                    {'range': [3, 6], 'color': "rgba(245,185,66,0.15)"},
                    {'range': [6, 9], 'color': "rgba(34,211,143,0.15)"}
                ],
                'threshold': {'line': {'color': score_color, 'width': 3}, 'thickness': 0.8, 'value': score}
            }
        ))
        fig.update_layout(height=220, margin=dict(t=40, b=10, l=30, r=30))
        st.plotly_chart(style_fig(fig), use_container_width=True)
        
        st.markdown(f"<h3 style='text-align:center; color:{score_color};'>{rating}</h3>", unsafe_allow_html=True)
        
        breakdown = f_score.get('breakdown', {})
        if breakdown and not f_score.get('error'):
            st.markdown("---")
            st.markdown(f"**Overall Score: {breakdown.get('total', 'N/A')}**")
            
            with st.expander("📋 Full Scorecard (9 Factors)", expanded=True):
                for category_name, category_key in [
                    ('💰 Profitability', 'profitability'),
                    ('🏦 Leverage & Liquidity', 'leverage'),
                    ('⚙️ Operating Efficiency', 'efficiency')
                ]:
                    cat = breakdown.get(category_key, {})
                    st.markdown(f"**{category_name}** {cat.get('stars', '')} ({cat.get('score', 'N/A')})")
                    
                    for item in cat.get('items', []):
                        status = item['status']
                        if status == 'pass':
                            icon = '✅'
                            color = COLORS['up']
                        elif status == 'fail':
                            icon = '❌'
                            color = COLORS['down']
                        else:
                            icon = '⬜'
                            color = COLORS['text_2']
                        
                        st.markdown(
                            f"<span style='color:{color};font-size:1.1rem;'>{icon}</span> "
                            f"<span style='color:{COLORS['text_1']};'>{item['name']}</span> "
                            f"<span style='color:{COLORS['text_3']};font-size:0.8rem;'>— {item['detail']}</span>",
                            unsafe_allow_html=True
                        )
                    st.markdown("")
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
                number={'font': {'color': z_color, 'size': 48, 'family': 'Inter, sans-serif'}},
                title={'text': "Altman Z-Score", 'font': {'size': 14, 'color': COLORS['text_2'], 'family': 'Inter, sans-serif'}},
                gauge={
                    'axis': {'range': [0, 6], 'tickwidth': 1, 'tickcolor': COLORS['text_3']},
                    'bar': {'color': z_color, 'thickness': 0.2},
                    'bgcolor': COLORS['bg_2'],
                    'steps': [
                        {'range': [0, 1.81], 'color': "rgba(255,93,122,0.15)"},
                        {'range': [1.81, 2.99], 'color': "rgba(245,185,66,0.15)"},
                        {'range': [2.99, 6], 'color': "rgba(34,211,143,0.15)"}
                    ],
                    'threshold': {'line': {'color': z_color, 'width': 3}, 'thickness': 0.8, 'value': z}
                }
            ))
            fig.update_layout(height=220, margin=dict(t=40, b=10, l=30, r=30))
            st.plotly_chart(style_fig(fig), use_container_width=True)
            
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
                        val_color = COLORS['up'] if val > 0 else COLORS['down']
                        st.markdown(f"**{comp_name}** = <span style='color:{val_color}'>{val:.3f}</span> × {weight} → *{signal}*", unsafe_allow_html=True)
        else:
            st.warning("Insufficient data for Z-Score calculation.")
            
            st.markdown("**Possible reasons:**")
            if not market_cap or market_cap <= 0:
                st.caption("❌ Market Cap not available")
            if balance is None or balance.empty:
                st.caption("❌ Balance Sheet not available")
            else:
                col = balance.columns[0] if not balance.empty else None
                if col:
                    ta = next((balance.loc[k, col] for k in ['Total Assets', 'Total Assets, Total'] if k in balance.index), 0)
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