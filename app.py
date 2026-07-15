"""Finshare Pro - Enterprise Financial Analysis Platform"""
import streamlit as st
from datetime import datetime
from config import *
from core.analyzer import ProFinancialAnalyzer
from utils.helpers import detect_peer_group, get_peer_comparison
from utils.formatting import format_financial_df
from dashboards.valuation import create_valuation_dashboard
from dashboards.stress_test import create_stress_test_dashboard
from dashboards.technical import create_technical_dashboard
from dashboards.scores import create_advanced_scores_dashboard
from dashboards.thesis import create_investment_thesis_dashboard
from dashboards.factor import create_factor_investing_dashboard
from dashboards.index_compare import create_index_comparison_dashboard
from dashboards.portfolio_opt import create_portfolio_optimization_tab
from dashboards.advanced_portfolio import create_advanced_portfolio_tab

st.set_page_config(page_title="Finshare Pro", page_icon="📊", layout="wide")

if 'app_initialized' not in st.session_state:
    st.session_state.clear()
    st.cache_data.clear()
    st.session_state['app_initialized'] = True

st.markdown("""
<style>
    .main-header { font-size: 2.8rem; font-weight: 900; text-align: center; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1rem; color: #94a3b8; text-align: center; margin-bottom: 2rem; }
    .card { background: #1e293b; border: 1px solid rgba(102,126,234,0.2); padding: 1.5rem; border-radius: 16px; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #e2e8f0; }
    .metric-label { font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; }
    .live-price-box { background: linear-gradient(135deg, #0f172a, #1e293b); border: 2px solid rgba(102,126,234,0.4); padding: 2rem; border-radius: 20px; color: white; text-align: center; }
    .price-up { color: #10b981; font-size: 3rem; font-weight: 900; }
    .price-down { color: #ef4444; font-size: 3rem; font-weight: 900; }
    .section-header { font-size: 1.4rem; font-weight: 700; color: #e2e8f0; margin: 1.5rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 2px solid rgba(102,126,234,0.3); }
    .stButton button { width: 100%; border-radius: 12px; padding: 0.6rem; font-weight: 600; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; }
    .info-box { background: #1e293b; padding: 1rem; border-radius: 12px; color: #e2e8f0; margin: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)

def get_all_stocks():
    all_stocks = {}
    for s in ["AAPL","MSFT","GOOGL","AMZN","META","NVDA","TSLA","JPM","V","WMT",
              "NFLX","ADBE","CRM","AMD","INTC","DIS","BA","NKE","PYPL","UBER",
              "COIN","SNAP","RIVN","LCID","PLTR","SNOW","ZM","DOCU","SQ","BABA"]:
        all_stocks[s] = ("US Market", s)
    for tick in INDIAN_STOCKS_DB:
        all_stocks[tick] = ("NSE India (.NS)", tick)
    return all_stocks

ALL_STOCKS = get_all_stocks()

def main():
    st.markdown('<h1 class="main-header">📊 Finshare Pro</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Advanced DCF • Stress Tests • Portfolio Optimizer • Technical Analysis</p>', unsafe_allow_html=True)

    if 'current_ticker' not in st.session_state:
        st.session_state['current_ticker'] = "AAPL"
    if 'current_exchange' not in st.session_state:
        st.session_state['current_exchange'] = "Auto-detect"
    if 'analyze_clicked' not in st.session_state:
        st.session_state['analyze_clicked'] = False

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Stock Analysis", "🛡️ Stress Tests", "📈 Technical", 
        "🎯 Portfolio", "🏦 Advanced"
    ])

    with tab1:
        st.markdown("### 🔍 Search Stock")
        
        c1, c2, c3 = st.columns([3, 1.5, 1])
        with c1:
            ticker_input = st.text_input(
                "Stock Ticker",
                value=st.session_state.get('current_ticker', ''),
                key="main_ticker",
                placeholder="Type any ticker (e.g., AAPL, RELIANCE, ITC)...",
            )
            ticker = ticker_input.upper().strip() if ticker_input else ''
        
        with c2:
            if ticker in ALL_STOCKS:
                auto_exchange = ALL_STOCKS[ticker][0]
            elif ticker.endswith('.NS'):
                auto_exchange = "NSE India (.NS)"
            elif ticker.endswith('.BO'):
                auto_exchange = "BSE India (.BO)"
            else:
                auto_exchange = st.session_state.get('current_exchange', 'Auto-detect')
            
            exchange = st.selectbox(
                "Exchange",
                ["Auto-detect","NSE India (.NS)","BSE India (.BO)","US Market"],
                index=["Auto-detect","NSE India (.NS)","BSE India (.BO)","US Market"].index(auto_exchange) if auto_exchange in ["Auto-detect","NSE India (.NS)","BSE India (.BO)","US Market"] else 0,
                key="main_exchange"
            )
        
        with c3:
            st.write("")
            analyze_btn = st.button("🔍 Analyze", type="primary", use_container_width=True, key="main_analyze_btn")

        if ticker_input and len(ticker_input) >= 1:
            search_term = ticker_input.upper().strip()
            suggestions = [s for s in ALL_STOCKS if search_term in s][:8]
            
            if suggestions:
                st.markdown("#### 💡 Suggestions")
                cols = st.columns(min(len(suggestions), 4))
                for i, stock in enumerate(suggestions):
                    with cols[i % 4]:
                        if st.button(f"📈 {stock}", key=f"suggest_{stock}", use_container_width=True):
                            st.session_state['current_ticker'] = stock
                            st.session_state['current_exchange'] = ALL_STOCKS[stock][0]
                            st.session_state['analyze_clicked'] = True
                            st.rerun()
            else:
                st.caption(f"'{ticker_input}' not in quick list. Select 'NSE India (.NS)' and click Analyze to search entire Indian market.")

        if ticker:
            st.session_state['current_ticker'] = ticker
        if exchange:
            st.session_state['current_exchange'] = exchange

        if analyze_btn:
            st.session_state['analyze_clicked'] = True
            st.cache_data.clear()

        if st.session_state.get('analyze_clicked', False) and ticker:
            em = {"NSE India (.NS)":"NSE","BSE India (.BO)":"BSE","US Market":"US","Auto-detect":"Auto"}
            
            with st.spinner(f"🔍 Fetching data for {ticker}... This may take a few seconds."):
                analyzer = ProFinancialAnalyzer(ticker, exchange=em.get(exchange, "Auto"))
                
                if not analyzer.get_live_price():
                    st.error(f"❌ Could not fetch data for **{ticker}**. Try:\n- Check the ticker spelling\n- Select the correct exchange\n- Wait a moment and retry (rate limits)")
                else:
                    analyzer.fetch_financial_data()
                    analyzer.calculate_all_ratios()

                    pd_d = analyzer.live_price_data
                    cur = analyzer.currency_symbol
                    cp = pd_d.get('current_price')
                    pc = pd_d.get('previous_close')
                    
                    if cp and pc:
                        ch = cp - pc
                        ch_pct = (ch/pc)*100
                        color = "price-up" if ch >= 0 else "price-down"
                        arrow = "▲" if ch >= 0 else "▼"
                        st.markdown(f'<div class="live-price-box"><h2>{analyzer.company_name}</h2><div class="{color}">{cur}{cp:.2f} {arrow}</div><div>{cur}{abs(ch):.2f} ({ch_pct:+.2f}%)</div><p style="color:#94a3b8;font-size:0.8rem;">Source: {analyzer.data_source}</p></div>', unsafe_allow_html=True)
                    elif cp:
                        st.markdown(f'<div class="live-price-box"><h2>{analyzer.company_name}</h2><div style="font-size:3rem;font-weight:900;">{cur}{cp:.2f}</div><p style="color:#94a3b8;font-size:0.8rem;">Source: {analyzer.data_source}</p></div>', unsafe_allow_html=True)

                    st.markdown(f'<div class="info-box">📊 {analyzer.company_name} | {analyzer.financials.get("sector","N/A")} | {analyzer.currency} | MCap: {analyzer._format_amount(pd_d.get("market_cap",0))}</div>', unsafe_allow_html=True)

                    ratios = analyzer.ratios
                    if ratios:
                        st.markdown('<div class="section-header">📊 Key Ratios</div>', unsafe_allow_html=True)
                        cols = st.columns(5)
                        for col, (l, v) in zip(cols, [
                            ('P/E', ratios.get('P/E Ratio')), ('ROE %', ratios.get('ROE')),
                            ('P/B', ratios.get('P/B Ratio')), ('D/E', ratios.get('Debt to Equity')),
                            ('Div Yld', ratios.get('Dividend Yield'))
                        ]):
                            with col:
                                if isinstance(v, (int, float)):
                                    d = f"{v:.1f}%" if l in ['ROE %', 'Div Yld'] else f"{v:.2f}"
                                    st.markdown(f'<div class="card"><div class="metric-value">{d}</div><div class="metric-label">{l}</div></div>', unsafe_allow_html=True)

                    create_valuation_dashboard(analyzer)
                    create_advanced_scores_dashboard(analyzer)
                    create_index_comparison_dashboard(analyzer)
                    create_investment_thesis_dashboard(analyzer)
                    create_factor_investing_dashboard(analyzer)

                    group_name, peer_list = detect_peer_group(analyzer.ticker)
                    if peer_list:
                        with st.spinner("Fetching peers..."):
                            all_peers = [analyzer.ticker] + [p for p in peer_list if p != analyzer.ticker][:5]
                            pdf = get_peer_comparison(analyzer.ticker, all_peers)
                            if not pdf.empty:
                                st.markdown('<div class="section-header">🏢 Peer Comparison</div>', unsafe_allow_html=True)
                                st.dataframe(pdf, use_container_width=True, hide_index=True)

                    st.markdown('<div class="section-header">📋 Financial Statements</div>', unsafe_allow_html=True)
                    t1, t2, t3 = st.tabs(["Income", "Balance", "Cash Flow"])
                    for tab, key in [(t1, 'income'), (t2, 'balance'), (t3, 'cashflow')]:
                        with tab:
                            df = analyzer.financials.get(key)
                            if df is not None and not df.empty:
                                formatted = format_financial_df(df, analyzer.currency_symbol, analyzer.currency)
                                if formatted is not None:
                                    st.dataframe(formatted, use_container_width=True)
                            else:
                                st.info("Not available.")
        elif not ticker:
            st.markdown('<div style="text-align:center;padding:4rem;"><h2>🏦 Finshare Pro</h2><p>Type any ticker above, select exchange, and click Analyze</p><p style="color:#94a3b8;">Works for ALL Indian stocks (.NS) and US stocks</p></div>', unsafe_allow_html=True)

    with tab2:
        st.markdown("### 🛡️ Stress Tests")
        col1, col2 = st.columns([2, 1])
        with col1:
            st2_t = st.text_input("Ticker", value=st.session_state.get('current_ticker', 'AAPL'), key="stress_ticker")
        with col2:
            st2_e = st.selectbox("Exchange", ["Auto-detect","NSE India (.NS)","BSE India (.BO)","US Market"], key="stress_exchange")
        if st.button("🛡️ Run Stress Tests", type="primary", key="stress_btn"):
            if not st2_t:
                st.warning("Please enter a ticker.")
            else:
                em2 = {"NSE India (.NS)":"NSE","BSE India (.BO)":"BSE","US Market":"US","Auto-detect":"Auto"}
                with st.spinner("Running stress tests..."):
                    a2 = ProFinancialAnalyzer(st2_t.strip().upper(), exchange=em2.get(st2_e, "Auto"))
                    if a2.get_live_price():
                        a2.fetch_financial_data()
                        create_stress_test_dashboard(a2)
                    else:
                        st.error("Could not fetch data. Try again.")

    with tab3:
        st.markdown("### 📈 Technical Analysis")
        col1, col2 = st.columns([2, 1])
        with col1:
            ta_t = st.text_input("Ticker", value=st.session_state.get('current_ticker', 'AAPL'), key="ta_ticker")
        with col2:
            ta_e = st.selectbox("Exchange", ["Auto-detect","NSE India (.NS)","BSE India (.BO)","US Market"], key="ta_exchange")
        if st.button("📈 Run Technical Analysis", type="primary", key="ta_btn"):
            if not ta_t:
                st.warning("Please enter a ticker.")
            else:
                em3 = {"NSE India (.NS)":"NSE","BSE India (.BO)":"BSE","US Market":"US","Auto-detect":"Auto"}
                with st.spinner("Calculating..."):
                    a3 = ProFinancialAnalyzer(ta_t.strip().upper(), exchange=em3.get(ta_e, "Auto"))
                    if a3.get_live_price():
                        a3.fetch_financial_data()
                        create_technical_dashboard(a3)
                    else:
                        st.error("Could not fetch data. Try again.")

    with tab4:
        create_portfolio_optimization_tab()

    with tab5:
        create_advanced_portfolio_tab()

    st.divider()
    st.caption(f"Finshare Pro | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

if __name__ == "__main__":
    main()