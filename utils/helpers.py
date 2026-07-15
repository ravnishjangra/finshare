"""Helper functions"""
import yfinance as yf
import pandas as pd
from config import PEER_GROUPS

def detect_peer_group(ticker):
    """Find peers dynamically by sector from Yahoo Finance"""
    # Check predefined groups first (faster)
    for group_name, tickers in PEER_GROUPS.items():
        if ticker in tickers:
            return group_name, [t for t in tickers if t != ticker]
    
    # Dynamic: search Yahoo Finance for same-sector stocks
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        sector = info.get('sector', '')
        
        if not sector:
            return None, []
        
        # Build search pool from all predefined groups
        common_tickers = []
        for group_tickers in PEER_GROUPS.values():
            for t in group_tickers:
                if t not in common_tickers and t != ticker:
                    common_tickers.append(t)
        
        # Add extra Indian tickers for broader coverage
        common_tickers.extend([
            'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS',
            'TATASTEEL.NS', 'JSWSTEEL.NS', 'ITC.NS', 'SBIN.NS', 'BHARTIARTL.NS',
            'WIPRO.NS', 'TECHM.NS', 'SUNPHARMA.NS', 'DRREDDY.NS', 'MARUTI.NS',
            'TITAN.NS', 'ASIANPAINT.NS', 'NESTLEIND.NS', 'HINDUNILVR.NS'
        ])
        
        # Find matching sector peers
        peers = []
        for t in common_tickers:
            if len(peers) >= 5:
                break
            try:
                t_info = yf.Ticker(t).info
                if t_info.get('sector') == sector and t != ticker:
                    peers.append(t)
            except:
                continue
        
        if peers:
            return f"{sector} Peers", peers[:5]
    except:
        pass
    
    return None, []

def get_peer_comparison(main_ticker, peer_tickers):
    """Get comparison table for peer tickers"""
    data = []
    for ticker in peer_tickers:
        try:
            s = yf.Ticker(ticker)
            info = s.info
            if not info or len(info) < 3:
                continue
            
            is_ind = ticker.endswith('.NS') or ticker.endswith('.BO')
            p_cur = 'INR' if is_ind else 'USD'
            mcap = info.get('marketCap', 0) or 0
            mcap_disp = round(mcap/1e7, 1) if p_cur == 'INR' else round(mcap/1e9, 1)
            
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            data.append({
                'Ticker': ticker.replace('.NS', '').replace('.BO', ''),
                'Company': (info.get('longName') or ticker)[:25],
                'Price': f"{'₹' if p_cur=='INR' else '$'}{price:.2f}" if price else 'N/A',
                'Market Cap': f"{'₹' if p_cur=='INR' else '$'}{mcap_disp} {'Cr' if p_cur=='INR' else 'B'}",
                'P/E': round(info.get('trailingPE', 0), 1) if info.get('trailingPE') else 'N/A',
                'ROE %': round((info.get('returnOnEquity', 0) or 0) * 100, 1),
                'D/E': round(info.get('debtToEquity', 0) or 0, 2),
                'Beta': round(info.get('beta', 0) or 0, 2),
                'Div Yield %': round((info.get('dividendYield', 0) or 0) * 100, 2) if info.get('dividendYield') and (info.get('dividendYield') or 0) * 100 < 50 else 'N/A',
            })
        except:
            continue
    
    df = pd.DataFrame(data)
    
    # Highlight the main ticker
    if not df.empty:
        def highlight_main(row):
            if row['Ticker'] == main_ticker.replace('.NS', '').replace('.BO', ''):
                return ['background-color: rgba(102,126,234,0.2)'] * len(row)
            return [''] * len(row)
        df = df.style.apply(highlight_main, axis=1)
    
    return df