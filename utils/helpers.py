"""Helper functions"""
import yfinance as yf
import pandas as pd
from config import PEER_GROUPS

def detect_peer_group(ticker):
    for group_name, tickers in PEER_GROUPS.items():
        if ticker in tickers: return group_name, tickers
    return None, []

def get_peer_comparison(main_ticker, peer_tickers):
    data = []
    for ticker in peer_tickers:
        try:
            s = yf.Ticker(ticker); info = s.info
            if not info: continue
            is_ind = ticker.endswith('.NS') or ticker.endswith('.BO')
            p_cur = 'INR' if is_ind else 'USD'
            mcap = info.get('marketCap', 0) or 0
            mcap_disp = round(mcap/1e7, 1) if p_cur=='INR' else round(mcap/1e9, 1)
            data.append({
                'Ticker': ticker.replace('.NS','').replace('.BO',''),
                'Company': info.get('longName', ticker)[:25],
                'Market Cap': f"{'₹' if p_cur=='INR' else '$'}{mcap_disp} {'Cr' if p_cur=='INR' else 'B'}",
                'P/E': round(info.get('trailingPE',0),1) if info.get('trailingPE') else 'N/A',
                'ROE %': round((info.get('returnOnEquity',0) or 0)*100, 1),
                'D/E': round(info.get('debtToEquity',0) or 0, 2),
            })
        except: continue
    return pd.DataFrame(data)