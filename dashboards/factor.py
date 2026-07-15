"""Factor Investing Dashboard"""
import streamlit as st
from models.factor import FactorInvesting

def create_factor_investing_dashboard(analyzer):
    exposures = FactorInvesting.analyze_factor_exposure(analyzer)
    if not exposures: return
    st.markdown('<div class="section-header">🎯 Factor Profile (Fama-French)</div>', unsafe_allow_html=True)
    cols = st.columns(len(exposures))
    for col, (factor, data) in zip(cols, exposures.items()):
        with col:
            st.markdown(f'<div style="background:#1e293b;border:2px solid {data["color"]};padding:1rem;border-radius:12px;text-align:center;"><div style="font-size:0.75rem;color:#94a3b8;">{factor}</div><div style="font-size:1.1rem;font-weight:700;color:{data["color"]};">{data["score"]}</div><div style="font-size:0.7rem;color:#64748b;">{data["detail"]}</div></div>', unsafe_allow_html=True)