"""Multi-source price fetcher with working fallbacks"""
import streamlit as st
import requests
import re
import yfinance as yf
import pandas as pd

class MultiSourceFetcher:
    @staticmethod
    def fetch_price(ticker):
        """Try multiple sources until one returns a valid price"""
        sources = [
            ('yahooquery', MultiSourceFetcher._try_yahooquery),
            ('twelvedata', MultiSourceFetcher._try_twelvedata),
            ('alphavantage', MultiSourceFetcher._try_alphavantage),
            ('google', MultiSourceFetcher._try_google_finance),
            ('yfinance_history', MultiSourceFetcher._try_yfinance_history),
        ]
        
        for name, func in sources:
            try:
                result = func(ticker)
                if result and result.get('current_price') and result['current_price'] > 0:
                    return result
            except:
                continue
        return None

    @staticmethod
    def _try_yahooquery(ticker):
        try:
            from yahooquery import Ticker as YQTicker
            t = YQTicker(ticker)
            data = t.price.get(ticker, {})
            if data and 'regularMarketPrice' in data and data['regularMarketPrice'] > 0:
                return {'current_price': data['regularMarketPrice'], 'source': 'yahooquery'}
        except:
            pass
        return None

    @staticmethod
    def _try_twelvedata(ticker):
        api_key = st.secrets.get("TWELVEDATA_API_KEY", "")
        if not api_key: return None
        try:
            url = f"https://api.twelvedata.com/price?symbol={ticker}&apikey={api_key}"
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if 'price' in data and float(data['price']) > 0:
                    return {'current_price': float(data['price']), 'source': 'Twelve Data'}
        except:
            pass
        return None

    @staticmethod
    def _try_alphavantage(ticker):
        api_key = st.secrets.get("ALPHAVANTAGE_API_KEY", "")
        if not api_key: return None
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={api_key}"
            resp = requests.get(url, timeout=8)
            data = resp.json()
            if 'Global Quote' in data:
                price = float(data['Global Quote'].get('05. price', 0))
                if price > 0:
                    return {'current_price': price, 'source': 'Alpha Vantage'}
        except:
            pass
        return None

    @staticmethod
    def _try_google_finance(ticker):
        try:
            if ticker.endswith('.NS'): gf = f'NSE:{ticker[:-3]}'
            elif ticker.endswith('.BO'): gf = f'BOM:{ticker[:-3]}'
            else: gf = ticker
            url = f'https://www.google.com/finance/quote/{gf}'
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)
            if resp.status_code == 200:
                match = re.search(r'data-last-price="([^"]*)"', resp.text)
                if match:
                    price = float(match.group(1).replace(',', ''))
                    if price > 0:
                        return {'current_price': price, 'source': 'Google Finance'}
        except:
            pass
        return None

    @staticmethod
    def _try_yfinance_history(ticker):
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period='5d')
            if not hist.empty and 'Close' in hist.columns:
                last = hist['Close'].iloc[-1]
                if pd.notna(last) and last > 0:
                    return {'current_price': float(last), 'source': 'Yahoo Finance (history)'}
        except:
            pass
        return None