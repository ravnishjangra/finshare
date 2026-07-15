"""AI Investment Thesis Dashboard"""
import streamlit as st
from models.dcf import AdvancedDCF

def generate_investment_thesis(analyzer, dcf_result=None):
    ratios = analyzer.ratios
    cur = analyzer.currency_symbol
    cp = analyzer.live_price_data.get('current_price')
    thesis_parts = []
    score = 0
    max_score = 0
    
    rev_growth = ratios.get('Revenue Growth (YoY)')
    if rev_growth is not None:
        max_score += 1
        if rev_growth > 20: thesis_parts.append(f"🟢 **Strong Revenue Growth:** {rev_growth:.1f}% YoY"); score += 1
        elif rev_growth > 10: thesis_parts.append(f"🟡 **Moderate Revenue Growth:** {rev_growth:.1f}% YoY"); score += 0.5
        elif rev_growth > 0: thesis_parts.append(f"🟠 **Slow Revenue Growth:** {rev_growth:.1f}% YoY")
        else: thesis_parts.append(f"🔴 **Revenue Decline:** {abs(rev_growth):.1f}% YoY")
    
    net_margin = ratios.get('Net Profit Margin')
    if net_margin is not None:
        max_score += 1
        if net_margin > 20: thesis_parts.append(f"🟢 **Excellent Profitability:** {net_margin:.1f}% net margin"); score += 1
        elif net_margin > 10: thesis_parts.append(f"🟡 **Healthy Profitability:** {net_margin:.1f}% net margin"); score += 0.5
        else: thesis_parts.append(f"🟠 **Thin Margins:** {net_margin:.1f}%")
    
    roe = ratios.get('ROE')
    if roe is not None:
        max_score += 1
        if roe > 20: thesis_parts.append(f"🟢 **Efficient Capital Allocation:** ROE {roe:.1f}%"); score += 1
        elif roe > 10: thesis_parts.append(f"🟡 **Adequate Returns:** ROE {roe:.1f}%"); score += 0.5
        else: thesis_parts.append(f"🔴 **Poor Returns:** ROE {roe:.1f}%")
    
    de = ratios.get('Debt to Equity')
    if de is not None:
        max_score += 1
        if de < 0.5: thesis_parts.append(f"🟢 **Conservative Capital Structure:** D/E {de:.2f}"); score += 1
        elif de < 1.5: thesis_parts.append(f"🟡 **Moderate Leverage:** D/E {de:.2f}"); score += 0.5
        else: thesis_parts.append(f"🔴 **High Leverage:** D/E {de:.2f}")
    
    cr = ratios.get('Current Ratio')
    if cr is not None:
        max_score += 1
        if cr > 1.5: thesis_parts.append(f"🟢 **Healthy Liquidity:** Current Ratio {cr:.2f}"); score += 1
        elif cr > 1.0: thesis_parts.append(f"🟡 **Adequate Liquidity:** {cr:.2f}"); score += 0.5
        else: thesis_parts.append(f"🔴 **Liquidity Concern:** {cr:.2f}")
    
    if dcf_result:
        upside = dcf_result.get('upside', 0); max_score += 1
        if upside > 20: thesis_parts.append(f"🟢 **Significantly Undervalued:** DCF {upside:.0f}% upside"); score += 1
        elif upside > 0: thesis_parts.append(f"🟡 **Modestly Undervalued:** DCF {upside:.0f}% upside"); score += 0.5
        else: thesis_parts.append(f"🔴 **Overvalued:** DCF {abs(upside):.0f}% downside")
    
    eps = ratios.get('EPS')
    ni_growth = ratios.get('Net Income Growth (YoY)')
    if eps is not None and ni_growth is not None:
        max_score += 1
        if ni_growth > 15 and eps > 0: thesis_parts.append(f"🟢 **Strong Earnings:** EPS {cur}{eps:.2f}, growth {ni_growth:.1f}%"); score += 1
        elif eps > 0: thesis_parts.append(f"🟡 **Stable Earnings:** EPS {cur}{eps:.2f}"); score += 0.5
    
    market_cap = analyzer.live_price_data.get('market_cap', 0)
    sector = analyzer.financials.get('sector', 'Unknown')
    if market_cap > 0: thesis_parts.append(f"📊 **Market Position:** {analyzer.company_name} in **{sector}** with market cap **{analyzer._format_amount(market_cap)}**")
    
    if max_score > 0:
        final_score = (score/max_score)*100
        if final_score >= 75: overall = "🟢 **OVERALL: STRONG FUNDAMENTALS**"
        elif final_score >= 50: overall = "🟡 **OVERALL: MIXED SIGNALS**"
        elif final_score >= 25: overall = "🟠 **OVERALL: BELOW AVERAGE**"
        else: overall = "🔴 **OVERALL: HIGH RISK**"
    else: overall = "⚠️ **INSUFFICIENT DATA**"
    
    return {'thesis_parts': thesis_parts, 'overall': overall, 'score': f"{score}/{max_score}" if max_score > 0 else "N/A", 'score_pct': (score/max_score*100) if max_score > 0 else 0}


def create_investment_thesis_dashboard(analyzer):
    st.markdown('<div class="section-header">📝 AI-Generated Investment Thesis</div>', unsafe_allow_html=True)
    income = analyzer.financials.get('income')
    cashflow = analyzer.financials.get('cashflow')
    cp = analyzer.live_price_data.get('current_price')
    
    dcf_result = None
    if cp and income is not None and not income.empty:
        fcf = analyzer._safe_get(cashflow, ['Free Cash Flow']) or 0
        if not fcf: fcf = (analyzer._safe_get(income, ['Net Income']) or 0) * 0.8
        if fcf and fcf > 0:
            shares = analyzer._safe_get(income, ['Diluted Average Shares']) or 1e6
            beta = analyzer.live_price_data.get('beta', 1.0) or 1.0
            rg = analyzer.ratios.get('Revenue Growth (YoY)', 10) or 10
            rf = 0.072 if analyzer.currency == 'INR' else 0.045
            mr = 0.12 if analyzer.currency == 'INR' else 0.10
            dcf = AdvancedDCF(fcf, shares, cp, max(0.02, min(rg/100, 0.35)), beta, rf, mr)
            dcf_result = dcf.calculate()
    
    thesis = generate_investment_thesis(analyzer, dcf_result)
    score_pct = thesis['score_pct']
    score_color = "#10b981" if score_pct >= 75 else "#f59e0b" if score_pct >= 50 else "#ef4444"
    
    st.markdown(f'<div style="background:#1e293b;border:2px solid {score_color};padding:1.5rem;border-radius:16px;margin-bottom:1rem;"><div style="display:flex;justify-content:space-between;"><h3>📝 {analyzer.company_name}</h3><span style="font-size:1.5rem;font-weight:900;color:{score_color};">{thesis["score"]}</span></div></div>', unsafe_allow_html=True)
    for part in thesis['thesis_parts']: st.markdown(f"- {part}")
    st.markdown("---"); st.markdown(f"### {thesis['overall']}")
    st.caption("💡 Auto-generated from reported financial data.")