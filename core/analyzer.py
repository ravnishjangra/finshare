"""Main Financial Analyzer - Robust data fetching with caching"""
import yfinance as yf
import pandas as pd
import numpy as np
import time
import streamlit as st
from config import CURRENCY_SYMBOLS, INDIAN_STOCKS_DB
from core.fallback import MultiSourceFetcher

# ===== CACHING FUNCTIONS (prevents rate limiting) =====

@st.cache_data(ttl=300)  # Cache for 5 minutes
def cached_yahoo_info(ticker):
    """Cached Yahoo Finance info - reduces API calls"""
    stock = yf.Ticker(ticker)
    return stock.info

@st.cache_data(ttl=3600)  # Cache for 1 hour
def cached_financials(ticker):
    """Cached financial statements - reduces API calls"""
    stock = yf.Ticker(ticker)
    return stock.financials, stock.balance_sheet, stock.cashflow

@st.cache_data(ttl=300)  # Cache for 5 minutes
def cached_yahooquery_data(ticker):
    """Cached yahooquery data"""
    from yahooquery import Ticker as YQTicker
    t = YQTicker(ticker)
    quote = t.quotes
    if quote and len(quote) > 0:
        return quote[0]
    return None

@st.cache_data(ttl=86400)  # Cache for 24 hours
def cached_price_history(ticker):
    """Cached 5-year price history"""
    stock = yf.Ticker(ticker)
    return stock.history(period="5y")


class ProFinancialAnalyzer:
    def __init__(self, ticker, exchange="Auto"):
        self.original_ticker = ticker.upper().strip()
        self.ticker = self._resolve_ticker(ticker.upper().strip(), exchange)
        self.stock = None
        self.financials = {}
        self.ratios = {}
        self.live_price_data = {}
        self.currency = 'USD'
        self.currency_symbol = '$'
        self.company_name = ''
        self.data_source = 'Yahoo Finance'

    def _resolve_ticker(self, ticker, exchange):
        if exchange == "NSE": return ticker + '.NS' if not ticker.endswith('.NS') else ticker
        elif exchange == "BSE": return ticker + '.BO' if not ticker.endswith('.BO') else ticker
        elif ticker in INDIAN_STOCKS_DB: return INDIAN_STOCKS_DB[ticker]
        return ticker

    def get_live_price(self):
        """Get price using CACHED data sources"""
        
        # Try 1: Cached yahooquery (best for Cloud)
        q = cached_yahooquery_data(self.ticker)
        if q and isinstance(q, dict):
            price = q.get('regularMarketPrice')
            if price and price > 0:
                self.live_price_data = {
                    'current_price': price, 'market_cap': q.get('marketCap'),
                    'previous_close': q.get('regularMarketPreviousClose'),
                    'open': q.get('regularMarketOpen'), 'day_high': q.get('regularMarketDayHigh'),
                    'day_low': q.get('regularMarketDayLow'), 'volume': q.get('regularMarketVolume'),
                    'beta': q.get('beta'), 'fifty_two_week_high': q.get('fiftyTwoWeekHigh'),
                    'fifty_two_week_low': q.get('fiftyTwoWeekLow'),
                }
                self.live_price_data = {k: v for k, v in self.live_price_data.items() if v is not None}
                self.data_source = 'Yahoo Finance'
                return True

        # Try 2: Cached Yahoo Finance info
        try:
            info = cached_yahoo_info(self.ticker)
            if info and isinstance(info, dict) and len(info) > 5:
                price = info.get('currentPrice') or info.get('regularMarketPrice')
                if price and price > 0:
                    self._populate_from_info(info)
                    self.data_source = 'Yahoo Finance'
                    return True
        except: pass

        # Try 3: Alternate exchange (cached)
        alts = []
        if self.ticker.endswith('.NS'): alts = [self.ticker.replace('.NS', '.BO')]
        elif self.ticker.endswith('.BO'): alts = [self.ticker.replace('.BO', '.NS')]
        else: alts = [self.ticker + '.NS', self.ticker + '.BO']
        
        for alt in alts:
            try:
                info = cached_yahoo_info(alt)
                if info and isinstance(info, dict) and len(info) > 5:
                    p = info.get('currentPrice') or info.get('regularMarketPrice')
                    if p and p > 0:
                        self.stock = yf.Ticker(alt)
                        self.ticker = alt
                        self._populate_from_info(info)
                        self.data_source = 'Yahoo Finance (alt)'
                        return True
            except: pass

        # Try 4: History
        try:
            self.stock = yf.Ticker(self.ticker)
            hist = self.stock.history(period='5d')
            if not hist.empty and 'Close' in hist.columns:
                last = hist['Close'].iloc[-1]
                if pd.notna(last) and last > 0:
                    self.live_price_data = {'current_price': float(last)}
                    self.data_source = 'Yahoo Finance (history)'
                    return True
        except: pass
        
        return False

    def _populate_from_info(self, info):
        self.live_price_data = {
            'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),
            'previous_close': info.get('previousClose') or info.get('regularMarketPreviousClose'),
            'open': info.get('open') or info.get('regularMarketOpen'),
            'day_high': info.get('dayHigh') or info.get('regularMarketDayHigh'),
            'day_low': info.get('dayLow') or info.get('regularMarketDayLow'),
            'volume': info.get('volume') or info.get('regularMarketVolume'),
            'market_cap': info.get('marketCap'),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
            'beta': info.get('beta'), 'recommendation': info.get('recommendationKey'),
            'number_of_analysts': info.get('numberOfAnalystOpinions'),
        }
        self.live_price_data = {k: v for k, v in self.live_price_data.items() if v is not None}

    def fetch_financial_data(self):
        """Fetch financial data using CACHED sources"""
        
        # Get cached info
        info = {}
        try:
            info = cached_yahoo_info(self.ticker)
        except: pass
        
        # Fallback to yahooquery for info
        if not info or len(info) < 5:
            q = cached_yahooquery_data(self.ticker)
            if q and isinstance(q, dict):
                info = {
                    'longName': q.get('longName', self.original_ticker),
                    'sector': q.get('sector', 'N/A'), 'industry': q.get('industry', 'N/A'),
                    'marketCap': q.get('marketCap'), 'currency': q.get('currency'),
                    'beta': q.get('beta'), 'trailingPE': q.get('trailingPE'),
                    'returnOnEquity': q.get('returnOnEquity'),
                    'debtToEquity': q.get('debtToEquity'),
                    'dividendYield': q.get('dividendYield'),
                    'revenueGrowth': q.get('revenueGrowth'),
                    'profitMargins': q.get('profitMargins'),
                    'currentRatio': q.get('currentRatio'),
                }
        
        self.financials['info'] = info
        self.company_name = info.get('longName', self.original_ticker) or self.original_ticker
        self.financials['sector'] = info.get('sector', 'N/A')
        self.financials['industry'] = info.get('industry', 'N/A')

        # Get cached financial statements
        try:
            income, balance, cashflow = cached_financials(self.ticker)
        except:
            income = pd.DataFrame()
            balance = pd.DataFrame()
            cashflow = pd.DataFrame()
        
        # Try alternate ticker if empty
        if income.empty:
            alts = []
            if self.ticker.endswith('.NS'): alts = [self.ticker.replace('.NS', '.BO')]
            elif self.ticker.endswith('.BO'): alts = [self.ticker.replace('.BO', '.NS')]
            else: alts = [self.ticker + '.NS', self.ticker + '.BO']
            for alt in alts:
                try:
                    income, balance, cashflow = cached_financials(alt)
                    if not income.empty:
                        self.ticker = alt
                        break
                except: pass

        self.financials['income'] = income
        self.financials['balance'] = balance
        self.financials['cashflow'] = cashflow

        # Get cached price history
        try:
            self.financials['prices'] = cached_price_history(self.ticker)
        except:
            self.financials['prices'] = pd.DataFrame()

        self._detect_currency()
        return True

    def _detect_currency(self):
        if self.ticker.endswith('.NS') or self.ticker.endswith('.BO'):
            self.currency = 'INR'; self.currency_symbol = '₹'; return
        info = self.financials.get('info', {})
        currency = info.get('currency') or info.get('financialCurrency')
        if currency:
            self.currency = currency
            self.currency_symbol = CURRENCY_SYMBOLS.get(currency, '$'); return
        if self.original_ticker in INDIAN_STOCKS_DB:
            self.currency = 'INR'; self.currency_symbol = '₹'; return
        self.currency = 'USD'; self.currency_symbol = '$'

    def _format_amount(self, value):
        if value is None or pd.isna(value): return 'N/A'
        if self.currency == 'INR':
            cr = value / 1e7
            return f"{self.currency_symbol}{cr:.0f} Cr" if abs(cr) >= 100 else f"{self.currency_symbol}{cr:.1f} Cr"
        b = value / 1e9
        return f"{self.currency_symbol}{b:.2f}B" if abs(b) >= 1 else f"{self.currency_symbol}{value/1e6:.1f}M"

    def _safe_get(self, df, keys, col=0):
        if df is None or df.empty: return None
        if isinstance(keys, str): keys = [keys]
        for key in keys:
            if key in df.index and len(df.columns) > col:
                val = df.loc[key].iloc[col]
                if pd.notna(val): return val
        return None

    def calculate_all_ratios(self):
        try:
            income = self.financials.get('income')
            balance = self.financials.get('balance')
            prices = self.financials.get('prices')
            cp = self.live_price_data.get('current_price')
            info = self.financials.get('info', {})

            if income is not None and not income.empty:
                rev = self._safe_get(income, ['Total Revenue', 'Revenue'])
                ni = self._safe_get(income, ['Net Income', 'Net Income Common Stockholders'])
                gp = self._safe_get(income, ['Gross Profit'])
                oi = self._safe_get(income, ['Operating Income', 'EBIT'])
                rev_p = self._safe_get(income, ['Total Revenue', 'Revenue'], 1)

                if rev and rev > 0:
                    if ni: self.ratios['Net Profit Margin'] = (ni/rev)*100
                    if gp: self.ratios['Gross Profit Margin'] = (gp/rev)*100
                    if oi: self.ratios['Operating Margin'] = (oi/rev)*100
                    if rev_p and rev_p > 0: self.ratios['Revenue Growth (YoY)'] = ((rev-rev_p)/rev_p)*100

                ni_p = self._safe_get(income, ['Net Income', 'Net Income Common Stockholders'], 1)
                if ni and ni_p and ni_p != 0: self.ratios['Net Income Growth (YoY)'] = ((ni-ni_p)/ni_p)*100

                if balance is not None and not balance.empty:
                    eq = self._safe_get(balance, ['Stockholders Equity', 'Total Stockholder Equity', 'Total Equity'])
                    ast = self._safe_get(balance, ['Total Assets'])
                    ca = self._safe_get(balance, ['Current Assets'])
                    cl = self._safe_get(balance, ['Current Liabilities'])
                    td = self._safe_get(balance, ['Total Debt']) or self._safe_get(balance, ['Long Term Debt'])
                    if eq and eq > 0:
                        if ni: self.ratios['ROE'] = (ni/eq)*100
                        if td: self.ratios['Debt to Equity'] = td/eq
                    if ast and ast > 0 and ni: self.ratios['ROA'] = (ni/ast)*100
                    if ca and cl and cl > 0:
                        self.ratios['Current Ratio'] = ca/cl
                        inv = self._safe_get(balance, ['Inventory', 'Inventories'])
                        if inv: self.ratios['Quick Ratio'] = (ca-inv)/cl
                    if rev and ast and ast > 0: self.ratios['Asset Turnover'] = rev/ast

                if cp and cp > 0:
                    shares = self._safe_get(income, ['Diluted Average Shares']) or self._safe_get(income, ['Basic Average Shares'])
                    if shares and shares > 0:
                        if ni:
                            eps = ni/shares; self.ratios['EPS'] = eps
                            if eps > 0: self.ratios['P/E Ratio'] = cp/eps
                        if eq and eq > 0: self.ratios['P/B Ratio'] = cp/(eq/shares)
                        if rev and rev > 0: self.ratios['P/S Ratio'] = cp/(rev/shares)

            for key, ratio_key, mult in [
                ('returnOnEquity', 'ROE', 100), ('returnOnAssets', 'ROA', 100),
                ('profitMargins', 'Net Profit Margin', 100), ('debtToEquity', 'Debt to Equity', 1),
                ('trailingPE', 'P/E Ratio', 1), ('priceToBook', 'P/B Ratio', 1),
                ('trailingEps', 'EPS', 1), ('revenueGrowth', 'Revenue Growth (YoY)', 100),
                ('dividendYield', 'Dividend Yield', 100), ('currentRatio', 'Current Ratio', 1),
            ]:
                if ratio_key not in self.ratios and info.get(key):
                    try: self.ratios[ratio_key] = info[key] * mult
                    except: pass
            return True
        except: return True