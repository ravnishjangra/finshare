"""Market Movers & Stock Screener"""
import streamlit as st
import pandas as pd

def _fetch_tv_data(market, sort_col, ascending, limit, fields):
    """Fetch data from TradingView scanner"""
    from tradingview_screener import Query
    
    query = Query().select(*fields).set_markets(market)
    if sort_col:
        query = query.order_by(sort_col, ascending=ascending)
    query = query.limit(limit)
    
    total, data = query.get_scanner_data()
    return data

def show_market_movers():
    st.markdown("### 🚀 Market Movers")
    
    market = st.selectbox("Market", ["india", "america"], key="movers_market")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔴 Top Losers**")
        try:
            losers = _fetch_tv_data(market, 'change', True, 10, ['name', 'close', 'change'])
            if losers is not None and not losers.empty:
                # Only filter extreme outliers for movers
                losers = losers[losers['change'] > -50]  # Keep reasonable drops
                losers = losers.head(5)
                
                if losers.empty:
                    st.caption("No significant movers")
                else:
                    for _, row in losers.iterrows():
                        change = row.get('change', 0)
                        st.markdown(
                            f"<div style='display:flex;justify-content:space-between;padding:0.3rem 0;"
                            f"border-bottom:1px solid rgba(255,255,255,0.05);'>"
                            f"<span style='color:#e2e8f0;font-size:0.85rem;'>{str(row.get('name','N/A'))[:20]}</span>"
                            f"<span style='color:#ef4444;font-weight:600;font-size:0.85rem;'>{change:.2f}%</span>"
                            f"</div>", unsafe_allow_html=True)
            else:
                st.caption("No data")
        except Exception as e:
            st.caption("Temporarily unavailable")
    
    with col2:
        st.markdown("**🟢 Top Gainers**")
        try:
            gainers = _fetch_tv_data(market, 'change', False, 10, ['name', 'close', 'change'])
            if gainers is not None and not gainers.empty:
                # Only filter extreme outliers
                gainers = gainers[gainers['change'] < 100]  # Keep reasonable gains
                gainers = gainers.head(5)
                
                if gainers.empty:
                    st.caption("No significant movers")
                else:
                    for _, row in gainers.iterrows():
                        change = row.get('change', 0)
                        st.markdown(
                            f"<div style='display:flex;justify-content:space-between;padding:0.3rem 0;"
                            f"border-bottom:1px solid rgba(255,255,255,0.05);'>"
                            f"<span style='color:#e2e8f0;font-size:0.85rem;'>{str(row.get('name','N/A'))[:20]}</span>"
                            f"<span style='color:#10b981;font-weight:600;font-size:0.85rem;'>+{change:.2f}%</span>"
                            f"</div>", unsafe_allow_html=True)
            else:
                st.caption("No data")
        except Exception:
            st.caption("Temporarily unavailable")

def show_stock_screener():
    st.markdown("### 🔍 Stock Screener")
    st.caption("Top stocks by category")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        market = st.selectbox("Market", ["india", "america"], key="screener_market")
    with col2:
        sort_by = st.selectbox("Sort By", ["Market Cap", "Change %", "Volume", "Price"], key="screener_sort")
    with col3:
        limit = st.selectbox("Results", [20, 50, 100], index=0, key="screener_limit")
    
    if st.button("🔍 Fetch Stocks", type="primary", use_container_width=True):
        with st.spinner("Fetching data..."):
            sort_map = {
                "Market Cap": ('market_cap_basic', False),
                "Change %": ('change', False),
                "Volume": ('volume', False),
                "Price": ('close', False),
            }
            sort_col, sort_asc = sort_map.get(sort_by, ('market_cap_basic', False))
            
            fields = ['name', 'close', 'change', 'market_cap_basic',
                     'price_earnings_ttm', 'return_on_equity',
                     'revenue_growth_yoy', 'dividend_yield', 'volume']
            
            try:
                results = _fetch_tv_data(market, sort_col, sort_asc, limit, fields)
                
                if results is not None and not results.empty:
                    display_df = pd.DataFrame({
                        'Stock': results.get('name', 'N/A'),
                        'Price': results.get('close', 0).round(2),
                        'Change %': results.get('change', 0).round(2),
                        'P/E': results.get('price_earnings_ttm', 0).apply(lambda x: round(x, 1) if pd.notna(x) and x > 0 else 'N/A'),
                        'ROE %': results.get('return_on_equity', 0).apply(lambda x: round(x, 1) if pd.notna(x) else 'N/A'),
                    })
                    st.markdown(f"**Top {len(display_df)} by {sort_by}**")
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.warning("No data available.")
            except Exception:
                st.warning("Screener temporarily unavailable.")