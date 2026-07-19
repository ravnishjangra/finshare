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
from dashboards.news import create_news_dashboard

st.set_page_config(page_title="Finshare Pro", page_icon="📊", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@500;700;800;900&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
    :root {
        --bg-0: #05070d; --bg-1: #0a0e17; --bg-2: #10141f;
        --surface: #131826; --surface-hover: #171d2e;
        --border: rgba(148, 163, 253, 0.10); --border-strong: rgba(148, 163, 253, 0.22);
        --accent-1: #6d5ef8; --accent-2: #9b6bf5; --accent-3: #4fd1ff;
        --accent-grad: linear-gradient(135deg, #6d5ef8 0%, #9b6bf5 45%, #4fd1ff 100%);
        --accent-grad-soft: linear-gradient(135deg, rgba(109,94,248,0.14), rgba(79,209,255,0.10));
        --up: #22d38f; --up-glow: rgba(34, 211, 143, 0.25);
        --down: #ff5d7a; --down-glow: rgba(255, 93, 122, 0.25);
        --text-1: #f4f6fb; --text-2: #aab1c5; --text-3: #6b7488;
        --radius-lg: 18px; --radius-md: 12px; --radius-sm: 8px;
        --shadow-lift: 0 18px 40px rgba(3, 5, 12, 0.55);
        --font-display: 'Manrope', 'Inter', sans-serif;
        --font-body: 'Inter', sans-serif;
        --font-mono: 'JetBrains Mono', monospace;
    }
    html, body, [class*="css"] { font-family: var(--font-body); }
    .stApp { background: radial-gradient(ellipse 120% 80% at 50% -10%, #131a30 0%, var(--bg-0) 55%) fixed; }
    .app-header { text-align: center; margin-bottom: 0.25rem; padding-top: 0.5rem; }
    .app-badge { display: inline-flex; align-items: center; gap: 0.4rem; background: rgba(109, 94, 248, 0.10); border: 1px solid var(--border-strong); color: var(--accent-3); font-size: 0.72rem; font-weight: 700; letter-spacing: 1.4px; text-transform: uppercase; padding: 0.3rem 0.9rem; border-radius: 999px; margin-bottom: 1rem; animation: badgePulse 2.8s ease-in-out infinite; }
    .main-header { font-family: var(--font-display); font-size: 3.2rem; font-weight: 900; text-align: center; margin-bottom: 0.4rem; background: var(--accent-grad); background-size: 200% 200%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -1.3px; line-height: 1.05; animation: gradientDrift 8s ease-in-out infinite; }
    .sub-header { font-size: 0.97rem; color: var(--text-2); text-align: center; margin-bottom: 2.75rem; letter-spacing: 0.3px; font-weight: 500; }
    .sub-header .dot { color: var(--accent-3); margin: 0 0.5rem; }
    .card { background: linear-gradient(160deg, var(--surface) 0%, var(--bg-2) 100%); border: 1px solid var(--border); padding: 1.35rem 1.3rem; border-radius: var(--radius-lg); transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden; }
    .card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: var(--accent-grad); opacity: 0; transition: opacity 0.25s; }
    .card:hover { transform: translateY(-3px); border-color: var(--border-strong); box-shadow: var(--shadow-lift), 0 0 0 1px rgba(109, 94, 248, 0.15); }
    .card:hover::before { opacity: 1; }
    .metric-value { font-family: var(--font-display); font-size: 1.75rem; font-weight: 800; color: var(--text-1); line-height: 1.2; font-variant-numeric: tabular-nums; }
    .metric-label { font-size: 0.68rem; color: var(--text-3); text-transform: uppercase; letter-spacing: 1.3px; margin-top: 0.35rem; font-weight: 600; }
    .live-price-box { background: linear-gradient(160deg, #10121e 0%, #171a30 55%, #0e1120 100%); border: 1px solid var(--border-strong); padding: 2.2rem 2rem; border-radius: 22px; color: white; text-align: center; box-shadow: var(--shadow-lift), inset 0 1px 0 rgba(255,255,255,0.04); position: relative; overflow: hidden; }
    .live-price-box::after { content: ''; position: absolute; inset: 0; pointer-events: none; background: radial-gradient(circle at 50% 0%, rgba(109,94,248,0.16), transparent 60%); animation: livePulse 3.6s ease-in-out infinite; }
    .price-up { font-family: var(--font-mono); color: var(--up); font-size: 3.1rem; font-weight: 900; text-shadow: 0 0 50px var(--up-glow); letter-spacing: -1px; }
    .price-down { font-family: var(--font-mono); color: var(--down); font-size: 3.1rem; font-weight: 900; text-shadow: 0 0 50px var(--down-glow); letter-spacing: -1px; }
    .company-name { font-family: var(--font-display); font-size: 1.35rem; font-weight: 700; color: var(--text-1); margin-bottom: 0.6rem; letter-spacing: -0.2px; }
    .price-change { font-family: var(--font-mono); font-size: 1.02rem; font-weight: 700; margin-top: 0.5rem; display: inline-flex; padding: 0.25rem 0.8rem; border-radius: 999px; }
    .source-tag { color: var(--text-3); font-size: 0.72rem; margin-top: 0.9rem; letter-spacing: 0.3px; }
    .section-header { font-family: var(--font-display); font-size: 1.28rem; font-weight: 800; color: var(--text-1); margin: 2.75rem 0 1.1rem 0; padding-bottom: 0.7rem; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 0.65rem; letter-spacing: -0.3px; }
    .section-header::after { content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, var(--border-strong), transparent); }
    .info-box { background: linear-gradient(135deg, var(--surface), #101426); padding: 1rem 1.4rem; border-radius: var(--radius-md); color: var(--text-1); margin: 0.9rem 0; border-left: 3px solid var(--accent-1); font-size: 0.92rem; font-weight: 500; box-shadow: 0 4px 16px rgba(0,0,0,0.2); }
    .stButton button { width: 100%; border-radius: var(--radius-sm); padding: 0.55rem 1.2rem; font-weight: 700; font-size: 0.9rem; letter-spacing: 0.2px; background: var(--accent-grad); background-size: 200% 200%; color: white; border: none; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden; box-shadow: 0 4px 14px rgba(109, 94, 248, 0.25); }
    .stButton button::after { content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent); transition: left 0.5s; }
    .stButton button:hover { transform: translateY(-1px); box-shadow: 0 10px 28px rgba(109, 94, 248, 0.4); background-position: 100% 50%; }
    .stButton button:hover::after { left: 100%; }
    .stTextInput input, .stSelectbox > div > div { border-radius: var(--radius-sm) !important; border: 1px solid var(--border) !important; background: var(--surface) !important; color: var(--text-1) !important; transition: border-color 0.25s, box-shadow 0.25s !important; }
    .stTextInput input:focus { border-color: var(--accent-1) !important; box-shadow: 0 0 0 3px rgba(109,94,248,0.15) !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 0.4rem; background: var(--bg-1); padding: 0.45rem; border-radius: 16px; border: 1px solid var(--border); }
    .stTabs [data-baseweb="tab"] { border-radius: var(--radius-sm); padding: 0.65rem 1.3rem; font-weight: 600; color: var(--text-2); font-size: 0.9rem; transition: all 0.25s; }
    .stTabs [data-baseweb="tab"]:hover { color: var(--text-1); background: var(--surface-hover); }
    .stTabs [aria-selected="true"] { background: var(--accent-grad) !important; color: white !important; font-weight: 700; box-shadow: 0 6px 18px rgba(109,94,248,0.35); }
    [data-testid="stMetricValue"] { font-family: var(--font-display); font-weight: 800; color: var(--text-1); font-variant-numeric: tabular-nums; }
    [data-testid="stMetricDelta"] { font-weight: 700; }
    [data-testid="stMetricLabel"] { color: var(--text-3); font-weight: 600; text-transform: uppercase; font-size: 0.72rem; letter-spacing: 1px; }
    .streamlit-expanderHeader { background: var(--surface); border-radius: var(--radius-sm) !important; font-weight: 700; font-size: 0.9rem; color: var(--text-1) !important; border: 1px solid var(--border) !important; }
    .streamlit-expanderHeader:hover { border-color: var(--border-strong) !important; }
    [data-testid="stDataFrame"] { border-radius: var(--radius-md); overflow: hidden; border: 1px solid var(--border); }

    /* News feed cards */
    .news-card { background: linear-gradient(160deg, var(--surface) 0%, var(--bg-2) 100%); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 0.9rem 1.1rem; margin-bottom: 0.6rem; transition: all 0.22s cubic-bezier(0.4,0,0.2,1); }
    .news-card:hover { transform: translateX(3px); border-color: var(--border-strong); box-shadow: var(--shadow-lift); background: linear-gradient(160deg, var(--surface-hover) 0%, var(--bg-2) 100%); }
    .news-card-title { font-family: var(--font-display); color: var(--text-1); font-size: 0.98rem; font-weight: 700; line-height: 1.4; margin-bottom: 0.5rem; letter-spacing: -0.1px; }
    .news-card-meta { display: flex; align-items: center; gap: 0.4rem; font-size: 0.76rem; color: var(--text-3); font-weight: 600; }
    .news-card-source { color: var(--accent-3); }
    .news-card-dot { color: var(--text-3); }

    @keyframes fadeInUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    .animate-in { animation: fadeInUp 0.45s cubic-bezier(0.4, 0, 0.2, 1) backwards; }
    .animate-in:nth-child(1) { animation-delay: 0.02s; } .animate-in:nth-child(2) { animation-delay: 0.06s; }
    .animate-in:nth-child(3) { animation-delay: 0.10s; } .animate-in:nth-child(4) { animation-delay: 0.14s; }
    .animate-in:nth-child(5) { animation-delay: 0.18s; }
    @keyframes gradientDrift { 0%,100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
    @keyframes badgePulse { 0%,100% { box-shadow: 0 0 0 0 rgba(79,209,255,0.0); } 50% { box-shadow: 0 0 0 5px rgba(79,209,255,0.08); } }
    @keyframes livePulse { 0%,100% { opacity: 0.7; } 50% { opacity: 1; } }
    @keyframes growWidth { from { width: 0; } }
    .grow-bar { animation: growWidth 0.9s cubic-bezier(0.4,0,0.2,1) backwards; }
    ::-webkit-scrollbar { width: 7px; height: 7px; }
    ::-webkit-scrollbar-track { background: var(--bg-1); }
    ::-webkit-scrollbar-thumb { background: #2a3145; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #3a4258; }
    hr { border-color: var(--border) !important; margin: 2.25rem 0 !important; }
    .stAlert { border-radius: var(--radius-sm) !important; border: 1px solid var(--border) !important; }
    .empty-state { text-align: center; padding: 4.5rem 2rem; background: linear-gradient(160deg, var(--surface) 0%, var(--bg-1) 100%); border-radius: 24px; border: 1px dashed var(--border-strong); margin-top: 1rem; }
    .empty-state .icon { font-size: 2.6rem; margin-bottom: 0.75rem; }
    .empty-state h2 { font-family: var(--font-display); color: var(--text-1); margin-bottom: 0.5rem; font-weight: 800; }
    .empty-state p { color: var(--text-2); font-size: 1rem; margin: 0.2rem 0; }
    .empty-state .muted { color: var(--text-3); font-size: 0.85rem; }
    .app-footer { text-align: center; color: var(--text-3); font-size: 0.78rem; letter-spacing: 0.3px; padding-bottom: 1rem; }
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

@st.cache_resource(ttl=120)
def get_cached_analyzer(ticker, exchange):
    """Cache analyzer results for 2 minutes - reduces API calls, refreshes quickly"""
    em = {"NSE India (.NS)":"NSE","BSE India (.BO)":"BSE","US Market":"US"}
    analyzer = ProFinancialAnalyzer(ticker, exchange=em.get(exchange, "NSE"))
    if analyzer.get_live_price():
        analyzer.fetch_financial_data()
        analyzer.calculate_all_ratios()
    return analyzer

def main():
    st.markdown('''
        <div class="app-header">
            <div class="app-badge">⚡ Live Market Intelligence</div>
            <h1 class="main-header">📊 Finshare Pro</h1>
            <p class="sub-header">DCF Valuation <span class="dot">•</span> Factor Investing <span class="dot">•</span> Risk Models <span class="dot">•</span> News & Sentiment <span class="dot">•</span> Portfolio Analytics <span class="dot">•</span> Monte Carlo</p>
        </div>
    ''', unsafe_allow_html=True)

    if 'current_ticker' not in st.session_state:
        st.session_state['current_ticker'] = "AAPL"
    if 'current_exchange' not in st.session_state:
        st.session_state['current_exchange'] = "NSE India (.NS)"
    if 'analyze_clicked' not in st.session_state:
        st.session_state['analyze_clicked'] = False

    tab1, tab_news, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Stock Analysis", "📰 News", "🛡️ Stress Tests", "📈 Technical",
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
            exchange = st.selectbox(
                "Exchange",
                ["NSE India (.NS)","BSE India (.BO)","US Market"],
                index=0,
                key="main_exchange_widget"
            )
        
        with c3:
            st.write("")
            analyze_btn = st.button("🔍 Analyze", type="primary", use_container_width=True)

        if analyze_btn:
            st.session_state['analyze_clicked'] = True
            st.session_state['current_ticker'] = ticker_input.upper().strip() if ticker_input else ''
            st.session_state['current_exchange'] = exchange

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
            else:
                st.caption(f"'{ticker_input}' not in quick list but will be searched on Yahoo Finance.")

        if st.session_state['analyze_clicked'] and st.session_state['current_ticker']:
            ticker_to_analyze = st.session_state['current_ticker']
            exchange_to_use = st.session_state['current_exchange']
            
            with st.spinner(f"🔍 Fetching data for {ticker_to_analyze}..."):
                try:
                    analyzer = get_cached_analyzer(ticker_to_analyze, exchange_to_use)
                    
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
                            chip_bg = "rgba(34,211,143,0.12)" if ch >= 0 else "rgba(255,93,122,0.12)"
                            chip_color = "#22d38f" if ch >= 0 else "#ff5d7a"
                            st.markdown(f'<div class="live-price-box"><div class="company-name">{analyzer.company_name}</div><div class="{color}">{cur}{cp:.2f} <span style="font-size:1.6rem;">{arrow}</span></div><div class="price-change" style="background:{chip_bg};color:{chip_color};">{cur}{abs(ch):.2f} ({ch_pct:+.2f}%)</div><p class="source-tag">Source: {analyzer.data_source}</p></div>', unsafe_allow_html=True)
                        elif cp:
                            st.markdown(f'<div class="live-price-box"><div class="company-name">{analyzer.company_name}</div><div style="font-size:3.1rem;font-weight:900;color:#f4f6fb;">{cur}{cp:.2f}</div><p class="source-tag">Source: {analyzer.data_source}</p></div>', unsafe_allow_html=True)

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
                <div class="icon">🏦</div>
                <h2>Welcome to Finshare Pro</h2>
                <p>Type any ticker above, select exchange, and click Analyze</p>
                <p class="muted">Works for ALL Indian stocks (.NS) and US stocks</p>
            </div>''', unsafe_allow_html=True)

    with tab_news:
        if st.session_state.get('analyze_clicked') and st.session_state.get('current_ticker'):
            try:
                analyzer = get_cached_analyzer(st.session_state['current_ticker'], st.session_state['current_exchange'])
                if analyzer.live_price_data.get('current_price'):
                    create_news_dashboard(analyzer)
                else:
                    st.error(f"❌ Could not fetch data for **{st.session_state['current_ticker']}**. Try again in a moment.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)[:100]}. Please try again.")
        else:
            st.markdown('''<div class="empty-state">
                <div class="icon">📰</div>
                <h2>No stock selected yet</h2>
                <p>Search and analyze a stock in the <b>🔍 Stock Analysis</b> tab first</p>
                <p class="muted">Its news feed and sentiment will appear here automatically</p>
            </div>''', unsafe_allow_html=True)

    with tab2:
        st.markdown("### 🛡️ Stress Tests")
        col1, col2 = st.columns([2, 1])
        with col1:
            st2_t = st.text_input("Ticker", value=st.session_state.get('current_ticker', 'AAPL'), key="stress_ticker")
        with col2:
            st2_e = st.selectbox("Exchange", ["NSE India (.NS)","BSE India (.BO)","US Market"], key="stress_exchange")
        if st.button("🛡️ Run Stress Tests", type="primary", key="stress_btn"):
            if not st2_t:
                st.warning("Please enter a ticker.")
            else:
                with st.spinner("Running stress tests..."):
                    try:
                        a2 = get_cached_analyzer(st2_t.strip().upper(), st2_e)
                        if a2.live_price_data.get('current_price'):
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
            ta_e = st.selectbox("Exchange", ["NSE India (.NS)","BSE India (.BO)","US Market"], key="ta_exchange")
        if st.button("📈 Run Technical Analysis", type="primary", key="ta_btn"):
            if not ta_t:
                st.warning("Please enter a ticker.")
            else:
                with st.spinner("Calculating..."):
                    try:
                        a3 = get_cached_analyzer(ta_t.strip().upper(), ta_e)
                        if a3.live_price_data.get('current_price'):
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
    st.markdown(f'<div class="app-footer">Finshare Pro &nbsp;•&nbsp; {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()