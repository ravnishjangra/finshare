"""Market Movers & Stock Screener - Top Gainers, Losers & Custom Screening"""
import streamlit as st
import pandas as pd

def show_market_movers():
    """Display market movers in Streamlit"""
    st.markdown("### 🚀 Market Movers")
    
    market = st.selectbox("Market", ["india", "america"], key="movers_market")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔴 Top Losers**")
        try:
            from tradingview_screener import Query
            _, losers = (Query()
                .select('name', 'close', 'change', 'volume')
                .set_markets(market)
                .order_by('change', ascending=True)
                .limit(5)
                .get_scanner_data())
            
            if losers is not None and not losers.empty:
                for _, row in losers.iterrows():
                    change = row.get('change', 0)
                    st.markdown(
                        f"<div style='display:flex;justify-content:space-between;padding:0.3rem 0;"
                        f"border-bottom:1px solid rgba(255,255,255,0.05);'>"
                        f"<span style='color:#e2e8f0;font-size:0.85rem;'>{str(row.get('name','N/A'))[:20]}</span>"
                        f"<span style='color:#ef4444;font-weight:600;font-size:0.85rem;'>{change:.2f}%</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
            else:
                st.caption("Data not available")
        except Exception:
            st.caption("Temporarily unavailable")
    
    with col2:
        st.markdown("**🟢 Top Gainers**")
        try:
            from tradingview_screener import Query
            _, gainers = (Query()
                .select('name', 'close', 'change', 'volume')
                .set_markets(market)
                .order_by('change', ascending=False)
                .limit(5)
                .get_scanner_data())
            
            if gainers is not None and not gainers.empty:
                for _, row in gainers.iterrows():
                    change = row.get('change', 0)
                    st.markdown(
                        f"<div style='display:flex;justify-content:space-between;padding:0.3rem 0;"
                        f"border-bottom:1px solid rgba(255,255,255,0.05);'>"
                        f"<span style='color:#e2e8f0;font-size:0.85rem;'>{str(row.get('name','N/A'))[:20]}</span>"
                        f"<span style='color:#10b981;font-weight:600;font-size:0.85rem;'>+{change:.2f}%</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
            else:
                st.caption("Data not available")
        except Exception:
            st.caption("Temporarily unavailable")

def show_stock_screener():
    """Stock Screener - fetch then filter client-side"""
    st.markdown("### 🔍 Stock Screener")
    st.caption("Sort and filter stocks (data fetched from TradingView)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        market = st.selectbox("Market", ["india", "america"], key="screener_market")
    
    with col2:
        sort_by = st.selectbox("Sort By", [
            "Market Cap", "Change %", "Volume", "Price"
        ], key="screener_sort")
    
    with col3:
        limit = st.selectbox("Results", [20, 50, 100], index=0, key="screener_limit")
    
    if st.button("🔍 Fetch Stocks", type="primary", use_container_width=True):
        with st.spinner("Fetching data..."):
            try:
                from tradingview_screener import Query
                
                sort_map = {
                    "Market Cap": ('market_cap_basic', False),
                    "Change %": ('change', False),
                    "Volume": ('volume', False),
                    "Price": ('close', False),
                }
                
                sort_col, sort_asc = sort_map.get(sort_by, ('market_cap_basic', False))
                
                _, results = (Query()
                    .select('name', 'close', 'change', 'market_cap_basic',
                           'price_earnings_ttm', 'return_on_equity',
                           'revenue_growth_yoy', 'dividend_yield', 'volume')
                    .set_markets(market)
                    .order_by(sort_col, ascending=sort_asc)
                    .limit(limit)
                    .get_scanner_data())
                
                if results is not None and not results.empty:
                    display_df = pd.DataFrame({
                        'Stock': results.get('name', 'N/A'),
                        'Price ₹': results.get('close', 0).round(2),
                        'Change %': results.get('change', 0).round(2),
                        'P/E': results.get('price_earnings_ttm', 0).apply(lambda x: round(x, 1) if pd.notna(x) and x > 0 else 'N/A'),
                        'ROE %': results.get('return_on_equity', 0).apply(lambda x: round(x, 1) if pd.notna(x) else 'N/A'),
                        'Rev Growth %': results.get('revenue_growth_yoy', 0).apply(lambda x: round(x, 1) if pd.notna(x) else 'N/A'),
                        'Div Yield %': results.get('dividend_yield', 0).apply(lambda x: round(x, 2) if pd.notna(x) else 'N/A'),
                    })
                    
                    st.markdown(f"**Showing top {len(display_df)} stocks by {sort_by}**")
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.warning("No data available.")
            
            except Exception as e:
                st.warning(f"Screener temporarily unavailable.")