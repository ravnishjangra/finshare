"""AI Investment Thesis Dashboard - BULLETPROOF"""
import streamlit as st
from models.dcf import AdvancedDCF
from theme import COLORS, status_pill, card_html

# Maps the same semantic levels the thesis previously encoded via raw
# 🟢🟡🟠🔴 emoji onto the shared design-system colors, rendered as a
# status_pill() dot instead (see status_pill in theme.py).
_STATUS_COLOR = {
    'good': COLORS['up'],
    'ok': COLORS['neutral'],
    'warn': '#f97316',
    'bad': COLORS['down'],
}

def safe_float(val, default=0):
    """Safely convert to float"""
    if val is None:
        return default
    try:
        return float(val)
    except:
        return default

def generate_investment_thesis(analyzer, dcf_result=None):
    ratios = analyzer.ratios if hasattr(analyzer, 'ratios') else {}
    cur = analyzer.currency_symbol if hasattr(analyzer, 'currency_symbol') else '$'
    cp = (analyzer.live_price_data or {}).get('current_price')
    thesis_parts = []
    score = 0
    max_score = 0
    
    rev_growth = ratios.get('Revenue Growth (YoY)')
    if rev_growth is not None:
        max_score += 1
        if rev_growth > 20: thesis_parts.append(('good', f"**Strong Revenue Growth:** {rev_growth:.1f}% YoY")); score += 1
        elif rev_growth > 10: thesis_parts.append(('ok', f"**Moderate Revenue Growth:** {rev_growth:.1f}% YoY")); score += 0.5
        elif rev_growth > 0: thesis_parts.append(('warn', f"**Slow Revenue Growth:** {rev_growth:.1f}% YoY"))
        else: thesis_parts.append(('bad', f"**Revenue Decline:** {abs(rev_growth):.1f}% YoY"))
    
    net_margin = ratios.get('Net Profit Margin')
    if net_margin is not None:
        max_score += 1
        if net_margin > 20: thesis_parts.append(('good', f"**Excellent Profitability:** {net_margin:.1f}% net margin")); score += 1
        elif net_margin > 10: thesis_parts.append(('ok', f"**Healthy Profitability:** {net_margin:.1f}% net margin")); score += 0.5
        else: thesis_parts.append(('warn', f"**Thin Margins:** {net_margin:.1f}%"))
    
    roe = ratios.get('ROE')
    if roe is not None:
        max_score += 1
        if roe > 20: thesis_parts.append(('good', f"**Efficient Capital Allocation:** ROE {roe:.1f}%")); score += 1
        elif roe > 10: thesis_parts.append(('ok', f"**Adequate Returns:** ROE {roe:.1f}%")); score += 0.5
        else: thesis_parts.append(('bad', f"**Poor Returns:** ROE {roe:.1f}%"))
    
    de = ratios.get('Debt to Equity')
    if de is not None:
        max_score += 1
        if de < 0.5: thesis_parts.append(('good', f"**Conservative Capital Structure:** D/E {de:.2f}")); score += 1
        elif de < 1.5: thesis_parts.append(('ok', f"**Moderate Leverage:** D/E {de:.2f}")); score += 0.5
        else: thesis_parts.append(('bad', f"**High Leverage:** D/E {de:.2f}"))
    
    cr = ratios.get('Current Ratio')
    if cr is not None:
        max_score += 1
        if cr > 1.5: thesis_parts.append(('good', f"**Healthy Liquidity:** Current Ratio {cr:.2f}")); score += 1
        elif cr > 1.0: thesis_parts.append(('ok', f"**Adequate Liquidity:** {cr:.2f}")); score += 0.5
        else: thesis_parts.append(('bad', f"**Liquidity Concern:** {cr:.2f}"))
    
    if dcf_result:
        upside = dcf_result.get('upside')
        if upside is not None:
            max_score += 1
            # Cap extreme values from data quality issues
            if abs(upside) > 500:
                thesis_parts.append(('warn', f"**DCF Unreliable:** Data quality prevents accurate valuation")); score += 0.5
            elif upside > 20: thesis_parts.append(('good', f"**Significantly Undervalued:** DCF {upside:.0f}% upside")); score += 1
            elif upside > 0: thesis_parts.append(('ok', f"**Modestly Undervalued:** DCF {upside:.0f}% upside")); score += 0.5
            else: thesis_parts.append(('bad', f"**Overvalued:** DCF {abs(upside):.0f}% downside"))
    
    eps = ratios.get('EPS')
    ni_growth = ratios.get('Net Income Growth (YoY)')
    if eps is not None and ni_growth is not None:
        max_score += 1
        if ni_growth > 15 and eps > 0: thesis_parts.append(('good', f"**Strong Earnings:** EPS {cur}{eps:.2f}, growth {ni_growth:.1f}%")); score += 1
        elif eps > 0: thesis_parts.append(('ok', f"**Stable Earnings:** EPS {cur}{eps:.2f}")); score += 0.5
    
    # SAFEST market cap check
    market_cap = None
    try:
        if hasattr(analyzer, 'live_price_data') and analyzer.live_price_data:
            market_cap = analyzer.live_price_data.get('market_cap')
    except:
        pass
    
    sector = "Unknown"
    try:
        if hasattr(analyzer, 'financials') and analyzer.financials:
            sector = analyzer.financials.get('sector', 'Unknown') or 'Unknown'
    except:
        pass
    
    if market_cap is not None and safe_float(market_cap) > 0:
        thesis_parts.append(f"📊 **Market Position:** {analyzer.company_name} in **{sector}** with market cap **{analyzer._format_amount(market_cap)}**")
    else:
        thesis_parts.append(f"📊 **Market Position:** {analyzer.company_name} operates in **{sector}** sector")
    
    if max_score > 0:
        final_score = (score/max_score)*100
        if final_score >= 75: overall = ('good', "OVERALL: STRONG FUNDAMENTALS")
        elif final_score >= 50: overall = ('ok', "OVERALL: MIXED SIGNALS")
        elif final_score >= 25: overall = ('warn', "OVERALL: BELOW AVERAGE")
        else: overall = ('bad', "OVERALL: HIGH RISK")
    else: overall = ('warn', "⚠️ INSUFFICIENT DATA")
    
    return {'thesis_parts': thesis_parts, 'overall': overall, 'score': f"{score}/{max_score}" if max_score > 0 else "N/A", 'score_pct': (score/max_score*100) if max_score > 0 else 0}


def create_investment_thesis_dashboard(analyzer):
    st.markdown('<div class="section-header">📝 AI-Generated Investment Thesis</div>', unsafe_allow_html=True)
    
    try:
        income = analyzer.financials.get('income') if hasattr(analyzer, 'financials') else None
        cashflow = analyzer.financials.get('cashflow') if hasattr(analyzer, 'financials') else None
    except:
        income = None
        cashflow = None
    
    cp = (analyzer.live_price_data or {}).get('current_price')
    
    dcf_result = None
    if cp and cp > 0 and income is not None and not income.empty:
        try:
            fcf = analyzer._safe_get(cashflow, ['Free Cash Flow']) if cashflow is not None else 0
            if not fcf:
                ni = analyzer._safe_get(income, ['Net Income']) or 0
                fcf = ni * 0.8 if ni else 0
            if fcf and fcf > 0:
                shares = analyzer._safe_get(income, ['Diluted Average Shares']) or 1e6
                if not shares or shares <= 0:
                    mcap = (analyzer.live_price_data or {}).get('market_cap', 0) or 0
                    shares = mcap / cp if cp > 0 and mcap > 0 else 1e6
                beta = (analyzer.live_price_data or {}).get('beta', 1.0) or 1.0
                rg = (analyzer.ratios or {}).get('Revenue Growth (YoY)', 10) or 10
                rf = 0.072 if (getattr(analyzer, 'currency', 'USD') == 'INR') else 0.045
                mr = 0.12 if (getattr(analyzer, 'currency', 'USD') == 'INR') else 0.10
                balance = analyzer.financials.get('balance') if hasattr(analyzer, 'financials') else None
                mcap_for_dcf = (analyzer.live_price_data or {}).get('market_cap')
                pretax = analyzer._safe_get(income, ['Pretax Income'])
                tax_paid = analyzer._safe_get(income, ['Tax Provision'])
                if pretax and tax_paid and pretax > 0:
                    eff_tax_rate = min(max(tax_paid / pretax, 0.0), 0.45)
                else:
                    eff_tax_rate = 0.25 if getattr(analyzer, 'currency', 'USD') == 'INR' else 0.21
                dcf = AdvancedDCF(fcf, shares, cp, max(0.02, min(rg/100, 0.35)), beta, rf, mr,
                                   tax_rate=eff_tax_rate, market_cap=mcap_for_dcf,
                                   balance_df=balance, income_df=income)
                dcf_result = dcf.calculate()
        except:
            pass
    
    thesis = generate_investment_thesis(analyzer, dcf_result)
    score_pct = thesis.get('score_pct', 0) or 0
    score_color = COLORS['up'] if score_pct >= 75 else COLORS['neutral'] if score_pct >= 50 else COLORS['down']
    
    header_inner = (
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<h3 style="color:{COLORS["text_1"]};margin:0;">📝 {analyzer.company_name}</h3>'
        f'<span style="font-size:1.5rem;font-weight:900;color:{score_color};">{thesis.get("score", "N/A")}</span>'
        f'</div>'
    )
    st.markdown(card_html(header_inner, accent=score_color), unsafe_allow_html=True)

    for status, part in thesis.get('thesis_parts', []):
        color = _STATUS_COLOR.get(status, COLORS['text_2'])
        st.markdown(f"- <span style='color:{color};font-weight:700;'>●</span> {part}", unsafe_allow_html=True)

    st.markdown("---")
    overall_status, overall_text = thesis.get('overall', ('warn', 'No data'))
    overall_color = _STATUS_COLOR.get(overall_status, COLORS['text_2'])
    st.markdown(f'<h3 style="color:{overall_color};">{overall_text}</h3>', unsafe_allow_html=True)
    st.caption("💡 Auto-generated from reported financial data.")