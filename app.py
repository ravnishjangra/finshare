"""Finshare Pro - Enterprise Financial Analysis Platform"""
from dashboards.financial_models import create_financial_models_dashboard
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

st.markdown("""
<style>
    /* ===== GLOBAL ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* ===== HEADERS ===== */
    .main-header { 
        font-size: 3rem; font-weight: 900; text-align: center; margin-bottom: 0.3rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 40%, #f093fb 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
    }
    .sub-header { 
        font-size: 0.95rem; color: #94a3b8; text-align: center; margin-bottom: 2.5rem; 
        letter-spacing: 0.5px;
    }
    
    /* ===== CARDS ===== */
    .card { 
        background: linear-gradient(145deg, #1e293b, #0f172a); 
        border: 1px solid rgba(102,126,234,0.12); 
        padding: 1.3rem; border-radius: 14px; 
        transition: all 0.25s ease;
        position: relative; overflow: hidden;
    }
    .card::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, rgba(102,126,234,0.3), transparent);
        opacity: 0; transition: opacity 0.25s;
    }
    .card:hover { 
        transform: translateY(-2px); 
        box-shadow: 0 12px 30px rgba(0,0,0,0.3), 0 0 0 1px rgba(102,126,234,0.2);
    }
    .card:hover::before { opacity: 1; }
    .metric-value { font-size: 1.7rem; font-weight: 700; color: #f1f5f9; line-height: 1.2; }
    .metric-label { font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1.2px; margin-top: 0.3rem; }
    
    /* ===== LIVE PRICE ===== */
    .live-price-box { 
        background: linear-gradient(135deg, #0f172a 0%, #1a1f3a 50%, #0f172a 100%); 
        border: 2px solid rgba(102,126,234,0.25); 
        padding: 2rem; border-radius: 20px; 
        color: white; text-align: center; 
        box-shadow: 0 20px 50px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.03);
    }
    .price-up { color: #10b981; font-size: 3rem; font-weight: 900; text-shadow: 0 0 40px rgba(16,185,129,0.2); }
    .price-down { color: #ef4444; font-size: 3rem; font-weight: 900; text-shadow: 0 0 40px rgba(239,68,68,0.2); }
    .company-name { font-size: 1.3rem; font-weight: 600; color: #e2e8f0; margin-bottom: 0.5rem; }
    .price-change { font-size: 1.1rem; font-weight: 500; margin-top: 0.3rem; }
    
    /* ===== SECTION HEADERS ===== */
    .section-header { 
        font-size: 1.25rem; font-weight: 700; color: #f1f5f9; 
        margin: 2.5rem 0 1rem 0; padding-bottom: 0.6rem;
        border-bottom: 2px solid rgba(102,126,234,0.2);
        display: flex; align-items: center; gap: 0.6rem;
    }
    
    /* ===== BUTTONS ===== */
    .stButton button { 
        width: 100%; border-radius: 10px; padding: 0.5rem 1.2rem; 
        font-weight: 600; font-size: 0.9rem; letter-spacing: 0.3px;
        background: linear-gradient(135deg, #667eea, #764ba2); 
        color: white; border: none; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative; overflow: hidden;
    }
    .stButton button::after {
        content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        transition: left 0.5s;
    }
    .stButton button:hover { 
        transform: translateY(-1px); 
        box-shadow: 0 8px 25px rgba(102,126,234,0.35); 
    }
    .stButton button:hover::after { left: 100%; }
    
    /* ===== INPUTS ===== */
    .stTextInput input, .stSelectbox select {
        border-radius: 10px !important; border: 1px solid rgba(102,126,234,0.2) !important;
        background: #1e293b !important; color: #e2e8f0 !important;
        transition: border-color 0.3s !important;
    }
    .stTextInput input:focus, .stSelectbox select:focus {
        border-color: #667eea !important; box-shadow: 0 0 0 2px rgba(102,126,234,0.15) !important;
    }
    
    /* ===== INFO BOX ===== */
    .info-box { 
        background: linear-gradient(135deg, #1e293b, #162032); 
        padding: 0.9rem 1.3rem; border-radius: 12px; 
        color: #e2e8f0; margin: 0.8rem 0; 
        border-left: 3px solid #667eea;
        font-size: 0.9rem; font-weight: 500;
    }
    
    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem; background: #0f172a; 
        padding: 0.5rem; border-radius: 14px;
        border: 1px solid rgba(102,126,234,0.1);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px; padding: 0.6rem 1.2rem;
        font-weight: 500; color: #94a3b8; font-size: 0.9rem;
        transition: all 0.3s;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important; font-weight: 600;
        box-shadow: 0 4px 12px rgba(102,126,234,0.3);
    }
    
    /* ===== METRICS ===== */
    [data-testid="stMetricValue"] { font-weight: 700; color: #f1f5f9; }
    [data-testid="stMetricDelta"] { font-weight: 600; }
    
    /* ===== EXPANDERS ===== */
    .streamlit-expanderHeader {
        background: #1e293b; border-radius: 10px !important;
        font-weight: 600; font-size: 0.9rem; color: #e2e8f0 !important;
        border: 1px solid rgba(102,126,234,0.15) !important;
    }
    .streamlit-expanderHeader:hover { border-color: #667eea !important; }
    
    /* ===== DATAFRAMES ===== */
    [data-testid="stDataFrame"] { 
        border-radius: 12px; overflow: hidden; 
        border: 1px solid rgba(102,126,234,0.1);
    }
    
    /* ===== SUGGESTIONS ===== */
    .suggestion-grid {
        display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem;
    }
    
    /* ===== ANIMATIONS ===== */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-in { animation: fadeInUp 0.4s ease-out; }
    
    @keyframes shimmer {
        0% { background-position: -200px 0; }
        100% { background-position: 200px 0; }
    }
    
    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0f172a; border-radius: 3px; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #475569; }
    
    /* ===== DIVIDER ===== */
    hr { border-color: rgba(102,126,234,0.1) !important; margin: 2rem 0 !important; }
    
    /* ===== WARNINGS/ERRORS ===== */
    .stAlert { border-radius: 10px !important; border: none !important; }
    
    /* ===== EMPTY STATE ===== */
    .empty-state { 
        text-align: center; padding: 4rem 2rem; 
        background: linear-gradient(135deg, #1e293b, #0f172a);
        border-radius: 20px; border: 1px dashed rgba(102,126,234,0.2);
    }
    .empty-state h2 { color: #e2e8f0; margin-bottom: 0.5rem; }
    .empty-state p { color: #94a3b8; font-size: 1rem; }
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
    st.markdown('<p class="sub-header">DCF Valuation • Factor Investing • Risk Models • Portfolio Analytics • Monte Carlo</p>', unsafe_allow_html=True)

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
                value=st.session_state['current_ticker'],
                key="main_ticker_widget",
                placeholder="Type any ticker (e.g., AAPL, RELIANCE, VEDL)...",
            )
        
        with c2:
            ticker_upper = ticker_input.upper().strip() if ticker_input else ''
            if ticker_upper in ALL_STOCKS:
                default_exchange = ALL_STOCKS[ticker_upper][0]
            elif ticker_upper.endswith('.NS'):
                default_exchange = "NSE India (.NS)"
            elif ticker_upper.endswith('.BO'):
                default_exchange = "BSE India (.BO)"
            else:
                default_exchange = st.session_state.get('current_exchange', 'Auto-detect')
            
            exchange_options = ["Auto-detect","NSE India (.NS)","BSE India (.BO)","US Market"]
            default_idx = exchange_options.index(default_exchange) if default_exchange in exchange_options else 0
            
            exchange = st.selectbox("Exchange", exchange_options, index=default_idx, key="main_exchange_widget")
        
        with c3:
            st.write("")
            analyze_btn = st.button("🔍 Analyze", type="primary", use_container_width=True)

        if ticker_input:
            st.session_state['current_ticker'] = ticker_input.upper().strip()
        if exchange:
            st.session_state['current_exchange'] = exchange

        if analyze_btn:
            st.session_state['analyze_clicked'] = True

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
                st.caption(f"'{ticker_input}' not in quick list but will be searched on Yahoo Finance.")

        if st.session_state['analyze_clicked'] and st.session_state['current_ticker']:
            ticker_to_analyze = st.session_state['current_ticker']
            exchange_to_use = st.session_state['current_exchange']
            
            with st.spinner(f"🔍 Fetching data for {ticker_to_analyze}..."):
                try:
                    em = {"NSE India (.NS)":"NSE","BSE India (.BO)":"BSE","US Market":"US","Auto-detect":"Auto"}
                    analyzer = ProFinancialAnalyzer(ticker_to_analyze, exchange=em.get(exchange_to_use, "Auto"))
                    analyzer.get_live_price()
                    analyzer.fetch_financial_data()
                    analyzer.calculate_all_ratios()
                    
                    if not analyzer.live_price_data.get('current_price'):
                        st.error(f"❌ Could not fetch data for **{ticker_to_analyze}**. Try again in a moment.")
                    else:
                        pd_d = analyzer.live_price_data
                        cur = analyzer.currency_symbol
                        cp = pd_d.get('current_price')
                        pc = pd_d.get('previous_close')
                        
                        if cp and pc:
                            ch = cp - pc
                            ch_pct = (ch/pc)*100
                            color = "price-up" if ch >= 0 else "price-down"
                            arrow = "▲" if ch >= 0 else "▼"
                            st.markdown(f'<div class="live-price-box"><div class="company-name">{analyzer.company_name}</div><div class="{color}">{cur}{cp:.2f} <span style="font-size:1.5rem;">{arrow}</span></div><div class="price-change" style="color:{"#10b981" if ch>=0 else "#ef4444"}">{cur}{abs(ch):.2f} ({ch_pct:+.2f}%)</div><p style="color:#64748b;font-size:0.75rem;margin-top:0.5rem;">Source: {analyzer.data_source}</p></div>', unsafe_allow_html=True)
                        elif cp:
                            st.markdown(f'<div class="live-price-box"><div class="company-name">{analyzer.company_name}</div><div style="font-size:3rem;font-weight:900;">{cur}{cp:.2f}</div><p style="color:#64748b;font-size:0.75rem;margin-top:0.5rem;">Source: {analyzer.data_source}</p></div>', unsafe_allow_html=True)

                        st.markdown(f'<div class="info-box">📊 <b>{analyzer.company_name}</b> • {analyzer.financials.get("sector","N/A")} • {analyzer.currency} • MCap: {analyzer._format_amount(pd_d.get("market_cap",0))}</div>', unsafe_allow_html=True)

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
                                        st.markdown(f'<div class="card animate-in"><div class="metric-value">{d}</div><div class="metric-label">{l}</div></div>', unsafe_allow_html=True)

                        create_valuation_dashboard(analyzer)
                        create_advanced_scores_dashboard(analyzer)
                        create_index_comparison_dashboard(analyzer)
                        create_investment_thesis_dashboard(analyzer)
                        create_factor_investing_dashboard(analyzer)
                        create_financial_models_dashboard(analyzer)

                        group_name, peer_list = detect_peer_group(analyzer.ticker)
                        if peer_list:
                            with st.spinner("Fetching peers..."):
                                all_peers = [analyzer.ticker] + [p for p in peer_list if p != analyzer.ticker][:5]
                                pdf = get_peer_comparison(analyzer.ticker, all_peers)
                                if pdf is not None and not pdf.empty:
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
                except Exception as e:
                    st.error(f"❌ Error: {str(e)[:100]}. Please try again.")
        elif not st.session_state.get('analyze_clicked'):
            st.markdown('''<div class="empty-state">
                <h2>🏦 Welcome to Finshare Pro</h2>
                <p>Type any ticker above, select exchange, and click Analyze</p>
                <p style="color:#64748b;font-size:0.9rem;">Works for ALL Indian stocks (.NS) and US stocks</p>
            </div>''', unsafe_allow_html=True)

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
                with st.spinner("Running stress tests..."):
                    try:
                        em2 = {"NSE India (.NS)":"NSE","BSE India (.BO)":"BSE","US Market":"US","Auto-detect":"Auto"}
                        a2 = ProFinancialAnalyzer(st2_t.strip().upper(), exchange=em2.get(st2_e, "Auto"))
                        if a2.get_live_price():
                            a2.fetch_financial_data()
                            create_stress_test_dashboard(a2)
                        else:
                            st.error("Could not fetch data. Try again.")
                    except:
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
                with st.spinner("Calculating..."):
                    try:
                        em3 = {"NSE India (.NS)":"NSE","BSE India (.BO)":"BSE","US Market":"US","Auto-detect":"Auto"}
                        a3 = ProFinancialAnalyzer(ta_t.strip().upper(), exchange=em3.get(ta_e, "Auto"))
                        if a3.get_live_price():
                            a3.fetch_financial_data()
                            create_technical_dashboard(a3)
                        else:
                            st.error("Could not fetch data. Try again.")
                    except:
                        st.error("Could not fetch data. Try again.")

    with tab4:
        create_portfolio_optimization_tab()

    with tab5:
        create_advanced_portfolio_tab()

    st.divider()
    st.caption(f"Finshare Pro | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

if __name__ == "__main__":
    main()