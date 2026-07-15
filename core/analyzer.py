"""Main Financial Analyzer - Twelve Data Primary Source (800 free calls/day)"""
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import streamlit as st
from config import CURRENCY_SYMBOLS, INDIAN_STOCKS_DB

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
        self.data_source = 'Twelve Data'
        self.api_key = self._get_api_key()

    def _get_api_key(self):
        try:
            return st.secrets.get("TWELVEDATA_API_KEY", "")
        except:
            return "d697a0e8caf443d8b644e82f7e03f70b"  # Fallback

    def _resolve_ticker(self, ticker, exchange):
        if exchange == "NSE": return ticker + '.NS' if not ticker.endswith('.NS') else ticker
        elif exchange == "BSE": return ticker + '.BO' if not ticker.endswith('.BO') else ticker
        elif ticker in INDIAN_STOCKS_DB: return INDIAN_STOCKS_DB[ticker]
        return ticker

    def _call_twelve_data(self, endpoint, params):
        """Make Twelve Data API call"""
        base_url = "https://api.twelvedata.com"
        params['apikey'] = self.api_key
        try:
            resp = requests.get(f"{base_url}/{endpoint}", params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if 'code' not in data:  # No error
                    return data
        except:
            pass
        return None

    def get_live_price(self):
        """Get all data from Twelve Data first, fallback to yahooquery/yfinance"""
        
        # === TWELVE DATA (Primary - 1 API call for everything) ===
        if self.api_key:
            data = self._call_twelve_data("quote", {
                'symbol': self.ticker,
                'interval': '1day'
            })
            
            if data:
                price = float(data.get('close', 0))
                if price > 0:
                    self.live_price_data = {
                        'current_price': price,
                        'previous_close': float(data.get('previous_close', 0)) or None,
                        'open': float(data.get('open', 0)) or None,
                        'day_high': float(data.get('high', 0)) or None,
                        'day_low': float(data.get('low', 0)) or None,
                        'volume': int(data.get('volume', 0)) or None,
                        'fifty_two_week_high': float(data.get('fifty_two_week_high', 0)) or None,
                        'fifty_two_week_low': float(data.get('fifty_two_week_low', 0)) or None,
                    }
                    self.live_price_data = {k: v for k, v in self.live_price_data.items() if v is not None}
                    self.data_source = 'Twelve Data'
                    # Also get stats for ratios
                    self._fetch_twelve_stats()
                    return True

        # === FALLBACK: yahooquery ===
        try:
            from yahooquery import Ticker as YQTicker
            t = YQTicker(self.ticker)
            quote = t.quotes
            if quote and len(quote) > 0:
                q = quote[0]
                if isinstance(q, dict):
                    price = q.get('regularMarketPrice')
                    if price and price > 0:
                        self.live_price_data = {
                            'current_price': price,
                            'market_cap': q.get('marketCap'),
                            'previous_close': q.get('regularMarketPreviousClose'),
                            'beta': q.get('beta'),
                        }
                        self.live_price_data = {k: v for k, v in self.live_price_data.items() if v is not None}
                        self.data_source = 'Yahoo Finance'
                        self.stock = yf.Ticker(self.ticker)
                        return True
        except:
            pass

        # === FALLBACK: yfinance ===
        try:
            self.stock = yf.Ticker(self.ticker)
            info = self.stock.info
            if info and isinstance(info, dict):
                price = info.get('currentPrice') or info.get('regularMarketPrice')
                if price and price > 0:
                    self._populate_from_info(info)
                    self.data_source = 'Yahoo Finance'
                    return True
        except:
            pass

        # === LAST RESORT: yfinance history ===
        try:
            if self.stock is None:
                self.stock = yf.Ticker(self.ticker)
            hist = self.stock.history(period='5d')
            if not hist.empty:
                last = hist['Close'].iloc[-1]
                if pd.notna(last) and last > 0:
                    self.live_price_data = {'current_price': float(last)}
                    self.data_source = 'Yahoo Finance (history)'
                    return True
        except:
            pass

        return False

    def _fetch_twelve_stats(self):
        """Fetch statistics/ratios from Twelve Data (1 API call)"""
        data = self._call_twelve_data("statistics", {'symbol': self.ticker})
        if data:
            stats = data.get('statistics', {})
            self.financials['twelve_stats'] = stats
            
            # Extract key metrics
            valuations = stats.get('valuations', {})
            financials_stats = stats.get('financials', {})
            
            self.ratios.update({
                'P/E Ratio': float(valuations.get('trailing_pe', 0)) or None,
                'EPS': float(financials_stats.get('earnings_per_share', 0)) or None,
                'ROE': float(financials_stats.get('return_on_equity', 0)) or None,
                'ROA': float(financials_stats.get('return_on_assets', 0)) or None,
                'Debt to Equity': float(financials_stats.get('debt_to_equity', 0)) or None,
                'Current Ratio': float(financials_stats.get('current_ratio', 0)) or None,
                'Dividend Yield': float(financials_stats.get('dividend_yield', 0)) or None,
                'Net Profit Margin': float(financials_stats.get('net_profit_margin', 0)) or None,
                'Operating Margin': float(financials_stats.get('operating_margin', 0)) or None,
                'Gross Profit Margin': float(financials_stats.get('gross_margin', 0)) or None,
            })

    def _populate_from_info(self, info):
        if not isinstance(info, dict): return
        self.live_price_data = {
            'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),
            'previous_close': info.get('previousClose') or info.get('regularMarketPreviousClose'),
            'open': info.get('open') or info.get('regularMarketOpen'),
            'day_high': info.get('dayHigh') or info.get('regularMarketDayHigh'),
            'day_low': info.get('dayLow') or info.get('regularMarketDayLow'),
            'volume': info.get('volume') or info.get('regularMarketVolume'),
            'market_cap': info.get('marketCap'),
            'beta': info.get('beta'),
            'recommendation': info.get('recommendationKey'),
        }
        self.live_price_data = {k: v for k, v in self.live_price_data.items() if v is not None}

    def fetch_financial_data(self):
        """Get financial data - Twelve Data stats already fetched, supplement with yfinance"""
        
        # We already have Twelve Data stats from get_live_price()
        
        # Get yfinance data for statements
        if not self.stock:
            self.stock = yf.Ticker(self.ticker)

        info = {}
        try:
            info = self.stock.info
        except:
            pass

        # Fallback to yahooquery
        if not info or len(info) < 5:
            try:
                from yahooquery import Ticker as YQTicker
                t = YQTicker(self.ticker)
                quote = t.quotes
                if quote and len(quote) > 0:
                    q = quote[0]
                    if isinstance(q, dict):
                        info = {
                            'longName': q.get('longName', self.original_ticker),
                            'sector': q.get('sector', 'N/A'),
                            'industry': q.get('industry', 'N/A'),
                            'marketCap': q.get('marketCap'),
                            'currency': q.get('currency'),
                            'beta': q.get('beta'),
                        }
            except:
                pass

        self.financials['info'] = info if isinstance(info, dict) else {}
        self.company_name = info.get('longName', self.original_ticker) if isinstance(info, dict) else self.original_ticker
        self.financials['sector'] = info.get('sector', 'N/A') if isinstance(info, dict) else 'N/A'
        self.financials['industry'] = info.get('industry', 'N/A') if isinstance(info, dict) else 'N/A'

        # Financial statements from yfinance
        try:
            self.financials['income'] = self.stock.financials
            self.financials['balance'] = self.stock.balance_sheet
            self.financials['cashflow'] = self.stock.cashflow
        except:
            self.financials['income'] = pd.DataFrame()
            self.financials['balance'] = pd.DataFrame()
            self.financials['cashflow'] = pd.DataFrame()

        # Price history
        try:
            self.financials['prices'] = self.stock.history(period="5y")
        except:
            self.financials['prices'] = pd.DataFrame()

        self._detect_currency()
        return True

    def _detect_currency(self):
        if self.ticker.endswith('.NS') or self.ticker.endswith('.BO'):
            self.currency = 'INR'; self.currency_symbol = '₹'; return
        info = self.financials.get('info', {})
        if isinstance(info, dict):
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
        """Ratios already populated from Twelve Data stats + yfinance fallback"""
        try:
            income = self.financials.get('income')
            balance = self.financials.get('balance')
            cp = self.live_price_data.get('current_price')
            info = self.financials.get('info', {})

            # Supplement with yfinance calculations if statements available
            if income is not None and not income.empty:
                rev = self._safe_get(income, ['Total Revenue', 'Revenue'])
                ni = self._safe_get(income, ['Net Income', 'Net Income Common Stockholders'])
                rev_p = self._safe_get(income, ['Total Revenue', 'Revenue'], 1)

                if rev and rev > 0:
                    if ni and 'Net Profit Margin' not in self.ratios:
                        self.ratios['Net Profit Margin'] = (ni/rev)*100
                    if rev_p and rev_p > 0 and 'Revenue Growth (YoY)' not in self.ratios:
                        self.ratios['Revenue Growth (YoY)'] = ((rev-rev_p)/rev_p)*100

                if balance is not None and not balance.empty:
                    eq = self._safe_get(balance, ['Stockholders Equity', 'Total Stockholder Equity', 'Total Equity'])
                    ast = self._safe_get(balance, ['Total Assets'])
                    ca = self._safe_get(balance, ['Current Assets'])
                    cl = self._safe_get(balance, ['Current Liabilities'])
                    
                    if eq and eq > 0 and ni and 'ROE' not in self.ratios:
                        self.ratios['ROE'] = (ni/eq)*100
                    if ast and ast > 0 and ni and 'ROA' not in self.ratios:
                        self.ratios['ROA'] = (ni/ast)*100
                    if ca and cl and cl > 0 and 'Current Ratio' not in self.ratios:
                        self.ratios['Current Ratio'] = ca/cl

                if cp and cp > 0:
                    shares = self._safe_get(income, ['Diluted Average Shares']) or self._safe_get(income, ['Basic Average Shares'])
                    if shares and shares > 0 and ni:
                        eps = ni/shares
                        if 'EPS' not in self.ratios: self.ratios['EPS'] = eps
                        if eps > 0 and 'P/E Ratio' not in self.ratios:
                            self.ratios['P/E Ratio'] = cp/eps

            # Info dict fallback
            if isinstance(info, dict):
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
            
            # Clean None values
            self.ratios = {k: v for k, v in self.ratios.items() if v is not None}
            return True
        except: return True