"""Market Movers & Stock Screener - Top Gainers, Losers & Custom Screening"""
import streamlit as st
import pandas as pd

def get_market_movers(market='india', limit=5):
    """Get top gainers and losers"""
    try:
        from tradingview_screener import Query
        
        gainers = Query().select('name', 'close', 'change', 'volume')\
            .set_markets(market)\
            .get_scanner_data(sort='change|desc', limit=limit)
        
        losers = Query().select('name', 'close', 'change', 'volume')\
            .set_markets(market)\
            .get_scanner_data(sort='change|asc', limit=limit)
        
        return gainers, losers
    except Exception:
        return None, None

def show_market_movers():
    """Display market movers in Streamlit"""
    st.markdown("### 🚀 Market Movers")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔴 Top Losers**")
        losers = None
        try:
            from tradingview_screener import Query
            losers = Query().select('name', 'close', 'change', 'volume')\
                .set_markets('india')\
                .get_scanner_data(sort='change|asc', limit=5)
        except:
            pass
        
        if losers is not None and not losers.empty:
            for _, row in losers.iterrows():
                change = row.get('change', 0)
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;padding:0.3rem 0;"
                    f"border-bottom:1px solid rgba(255,255,255,0.05);'>"
                    f"<span style='color:#e2e8f0;font-size:0.85rem;'>{row.get('name','N/A')[:20]}</span>"
                    f"<span style='color:#ef4444;font-weight:600;font-size:0.85rem;'>{change:.2f}%</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.caption("Data not available")
    
    with col2:
        st.markdown("**🟢 Top Gainers**")
        gainers = None
        try:
            from tradingview_screener import Query
            gainers = Query().select('name', 'close', 'change', 'volume')\
                .set_markets('india')\
                .get_scanner_data(sort='change|desc', limit=5)
        except:
            pass
        
        if gainers is not None and not gainers.empty:
            for _, row in gainers.iterrows():
                change = row.get('change', 0)
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;padding:0.3rem 0;"
                    f"border-bottom:1px solid rgba(255,255,255,0.05);'>"
                    f"<span style='color:#e2e8f0;font-size:0.85rem;'>{row.get('name','N/A')[:20]}</span>"
                    f"<span style='color:#10b981;font-weight:600;font-size:0.85rem;'>+{change:.2f}%</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.caption("Data not available")

def show_stock_screener():
    """Advanced Stock Screener with custom filters"""
    st.markdown("### 🔍 Stock Screener")
    st.caption("Filter stocks by fundamentals and technicals")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        market = st.selectbox("Market", ["india", "america"], key="screener_market")
    
    with col2:
        sector = st.selectbox("Sector", [
            "All", "Technology", "Banking", "Pharmaceuticals", "Automobiles", 
            "Energy", "FMCG", "Metals", "Real Estate", "IT Services"
        ], key="screener_sector")
    
    with col3:
        sort_by = st.selectbox("Sort By", [
            "Market Cap", "P/E Ratio", "ROE", "Revenue Growth", "Dividend Yield", "Change %"
        ], key="screener_sort")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        pe_min = st.number_input("P/E Min", value=0, step=1, key="pe_min")
        pe_max = st.number_input("P/E Max", value=100, step=1, key="pe_max")
    
    with col2:
        roe_min = st.number_input("ROE Min %", value=0, step=1, key="roe_min")
        roe_max = st.number_input("ROE Max %", value=100, step=1, key="roe_max")
    
    with col3:
        mcap_min = st.selectbox("Market Cap Min", 
            ["Any", "100 Cr", "500 Cr", "1000 Cr", "5000 Cr", "10000 Cr", "1L Cr"], key="mcap_min")
    
    with col4:
        div_min = st.number_input("Div Yield Min %", value=0.0, step=0.5, key="div_min")
    
    if st.button("🔍 Screen Stocks", type="primary", use_container_width=True):
        with st.spinner("Scanning market..."):
            try:
                from tradingview_screener import Query
                
                query = Query().select(
                    'name', 'close', 'change', 'market_cap_basic',
                    'price_earnings_ttm', 'return_on_equity',
                    'revenue_growth_yoy', 'dividend_yield', 'volume'
                ).set_markets(market)
                
                # Apply filters
                if pe_min > 0:
                    query = query.where('price_earnings_ttm', '>', pe_min)
                if pe_max < 100:
                    query = query.where('price_earnings_ttm', '<', pe_max)
                if roe_min > 0:
                    query = query.where('return_on_equity', '>', roe_min)
                if roe_max < 100:
                    query = query.where('return_on_equity', '<', roe_max)
                if div_min > 0:
                    query = query.where('dividend_yield', '>', div_min)
                
                # Market cap filter
                mcap_map = {
                    "100 Cr": 1e10, "500 Cr": 5e10, "1000 Cr": 1e11,
                    "5000 Cr": 5e11, "10000 Cr": 1e12, "1L Cr": 1e13
                }
                if mcap_min != "Any":
                    query = query.where('market_cap_basic', '>', mcap_map.get(mcap_min, 0))
                
                # Sort mapping
                sort_map = {
                    "Market Cap": 'market_cap_basic|desc',
                    "P/E Ratio": 'price_earnings_ttm|asc',
                    "ROE": 'return_on_equity|desc',
                    "Revenue Growth": 'revenue_growth_yoy|desc',
                    "Dividend Yield": 'dividend_yield|desc',
                    "Change %": 'change|desc',
                }
                
                results = query.get_scanner_data(sort=sort_map.get(sort_by, 'market_cap_basic|desc'), limit=20)
                
                if results is not None and not results.empty:
                    # Format data
                    display_df = pd.DataFrame({
                        'Stock': results.get('name', 'N/A'),
                        'Price': results.get('close', 0).round(2),
                        'Change %': results.get('change', 0).round(2),
                        'P/E': results.get('price_earnings_ttm', 0).round(1),
                        'ROE %': results.get('return_on_equity', 0).round(1),
                        'Rev Growth %': results.get('revenue_growth_yoy', 0).round(1),
                        'Div Yield %': results.get('dividend_yield', 0).round(2),
                        'Volume': results.get('volume', 0).apply(lambda x: f'{x/1e5:.1f}L' if x > 0 else 'N/A'),
                    })
                    
                    st.markdown(f"**Found {len(display_df)} stocks**")
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.warning("No stocks match your criteria. Try broadening filters.")
            
            except Exception as e:
                st.warning("Screener temporarily unavailable. Try again later.")
                st.caption(f"Error: {str(e)[:100]}")