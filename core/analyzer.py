"""Main Financial Analyzer - yfinance primary with retry, yahooquery backup"""
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time
from config import CURRENCY_SYMBOLS, INDIAN_STOCKS_DB

# ===== GLOBAL TICKER CACHE (10-min TTL) =====
_TICKER_CACHE = {}

def _get_cached_ticker(symbol):
    """Get or create yfinance Ticker - auto-refresh every 10 minutes"""
    now = time.time()
    if symbol not in _TICKER_CACHE or (now - _TICKER_CACHE[symbol]['time']) > 600:
        if symbol not in _TICKER_CACHE:
            time.sleep(3.0)  # 3 sec delay only for NEW tickers (rate limit protection)
        _TICKER_CACHE[symbol] = {
            'ticker': yf.Ticker(symbol),
            'time': now
        }
    return _TICKER_CACHE[symbol]['ticker']


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
        self._info_cache = None

    def _resolve_ticker(self, ticker, exchange):
        if exchange == "NSE":
            return ticker + '.NS' if not ticker.endswith('.NS') else ticker
        elif exchange == "BSE":
            return ticker + '.BO' if not ticker.endswith('.BO') else ticker
        elif ticker in INDIAN_STOCKS_DB:
            return INDIAN_STOCKS_DB[ticker]
        elif ticker.endswith('.NS') or ticker.endswith('.BO'):
            return ticker
        return ticker

    def _try_yfinance(self):
        """Primary source with retry - works for all stocks"""
        for attempt in range(2):
            try:
                stock = _get_cached_ticker(self.ticker)
                info = stock.info
                
                if not info or not isinstance(info, dict) or len(info) < 3:
                    if attempt == 0:
                        time.sleep(5)  # 5 sec retry delay
                        continue
                    return False, {}, None
                
                price = info.get('currentPrice') or info.get('regularMarketPrice')
                if not price or price <= 0:
                    if attempt == 0:
                        time.sleep(5)  # 5 sec retry delay
                        continue
                    return False, {}, None
                
                mcap = info.get('marketCap')
                if not mcap:
                    shares = info.get('sharesOutstanding')
                    if shares and shares > 0:
                        mcap = price * shares
                        info['marketCap'] = mcap
                
                return True, info, stock
                
            except Exception:
                if attempt == 0:
                    time.sleep(5)  # 5 sec retry delay
                else:
                    return False, {}, None
        
        return False, {}, None

    # ... rest unchanged ...
    def _try_yahooquery(self):
        """Backup source"""
        try:
            from yahooquery import Ticker as YQTicker
            t = YQTicker(self.ticker)
            
            quote = t.quotes
            q = quote[0] if quote and len(quote) > 0 else {}
            
            if not isinstance(q, dict) or not q.get('regularMarketPrice'):
                return False, {}
            
            current_price = q.get('regularMarketPrice')
            
            try:
                modules = t.get_modules(['price', 'summaryDetail', 'defaultKeyStatistics', 'financialData'])
                price_data = modules.get('price', {}).get(self.ticker, {}) or {}
                summary = modules.get('summaryDetail', {}).get(self.ticker, {}) or {}
                stats = modules.get('defaultKeyStatistics', {}).get(self.ticker, {}) or {}
                fin_data = modules.get('financialData', {}).get(self.ticker, {}) or {}
            except:
                price_data = {}
                summary = {}
                stats = {}
                fin_data = {}
            
            def _safe_raw(d, key):
                val = d.get(key, {}) if isinstance(d, dict) else {}
                if isinstance(val, dict):
                    return val.get('raw')
                return val
            
            info = {
                'currentPrice': current_price,
                'regularMarketPrice': current_price,
                'previousClose': _safe_raw(price_data, 'regularMarketPreviousClose') or q.get('regularMarketPreviousClose'),
                'open': _safe_raw(price_data, 'regularMarketOpen') or q.get('regularMarketOpen'),
                'dayHigh': _safe_raw(price_data, 'regularMarketDayHigh') or q.get('regularMarketDayHigh'),
                'dayLow': _safe_raw(price_data, 'regularMarketDayLow') or q.get('regularMarketDayLow'),
                'volume': _safe_raw(price_data, 'regularMarketVolume') or q.get('regularMarketVolume'),
                'marketCap': _safe_raw(price_data, 'marketCap') or q.get('marketCap') or _safe_raw(summary, 'marketCap'),
                'beta': _safe_raw(stats, 'beta') or q.get('beta'),
                'trailingPE': _safe_raw(summary, 'trailingPE') or q.get('trailingPE'),
                'returnOnEquity': _safe_raw(fin_data, 'returnOnEquity') or q.get('returnOnEquity'),
                'debtToEquity': _safe_raw(fin_data, 'debtToEquity') or q.get('debtToEquity'),
                'profitMargins': _safe_raw(fin_data, 'profitMargins') or q.get('profitMargins'),
                'revenueGrowth': _safe_raw(fin_data, 'revenueGrowth') or q.get('revenueGrowth'),
                'dividendYield': _safe_raw(summary, 'dividendYield') or q.get('dividendYield'),
                'recommendationKey': q.get('recommendationKey'),
                'fiftyTwoWeekHigh': _safe_raw(summary, 'fiftyTwoWeekHigh') or q.get('fiftyTwoWeekHigh'),
                'fiftyTwoWeekLow': _safe_raw(summary, 'fiftyTwoWeekLow') or q.get('fiftyTwoWeekLow'),
                'longName': q.get('longName', self.original_ticker),
                'sector': q.get('sector', 'N/A'),
                'industry': q.get('industry', 'N/A'),
                'currency': q.get('currency', 'USD'),
                'sharesOutstanding': _safe_raw(stats, 'sharesOutstanding') or q.get('sharesOutstanding'),
            }
            
            if not info.get('marketCap') and info.get('sharesOutstanding') and current_price:
                info['marketCap'] = info['sharesOutstanding'] * current_price
            
            info = {k: v for k, v in info.items() if v is not None}
            
            if not info.get('currentPrice') or info['currentPrice'] <= 0:
                return False, {}
            
            return True, info
            
        except Exception:
            return False, {}

    def _try_api_fallback(self):
        """Last resort - Twelve Data / Alpha Vantage"""
        try:
            url = f"https://api.twelvedata.com/price?symbol={self.ticker}&apikey=d697a0e8caf443d8b644e82f7e03f70b"
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if 'price' in data and float(data['price']) > 0:
                    return {'currentPrice': float(data['price'])}, 'Twelve Data'
        except:
            pass

        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={self.ticker}&apikey=KRERC8NQM61HUNI3"
            resp = requests.get(url, timeout=8)
            data = resp.json()
            if 'Global Quote' in data:
                price = float(data['Global Quote'].get('05. price', 0))
                if price > 0:
                    return {'currentPrice': price}, 'Alpha Vantage'
        except:
            pass
        
        return {}, None

    def get_live_price(self):
        """Priority: 1) yfinance (with retry) 2) yahooquery 3) API fallbacks"""
        
        success, info, stock = self._try_yfinance()
        if success:
            self._populate_from_info(info)
            self._info_cache = info
            self.stock = stock
            self.data_source = 'Yahoo Finance'
            return True

        success, info = self._try_yahooquery()
        if success and info.get('currentPrice'):
            self._populate_from_info(info)
            self._info_cache = info
            self.data_source = 'Yahoo Finance (yahooquery)'
            self.stock = _get_cached_ticker(self.ticker)
            return True

        info, source = self._try_api_fallback()
        if info:
            self.live_price_data = {'current_price': info.get('currentPrice')}
            self._info_cache = info
            self.data_source = source
            try:
                self.stock = _get_cached_ticker(self.ticker)
            except:
                pass
            return True

        return False

    def _populate_from_info(self, info):
        if not isinstance(info, dict):
            return
        self.live_price_data = {
            'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),
            'previous_close': info.get('previousClose') or info.get('regularMarketPreviousClose'),
            'open': info.get('open') or info.get('regularMarketOpen'),
            'day_high': info.get('dayHigh') or info.get('regularMarketDayHigh'),
            'day_low': info.get('dayLow') or info.get('regularMarketDayLow'),
            'volume': info.get('volume') or info.get('regularMarketVolume'),
            'market_cap': info.get('marketCap'),
            'beta': info.get('beta'),
            'recommendation': info.get('recommendationKey') or info.get('recommendation'),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
        }
        self.live_price_data = {k: v for k, v in self.live_price_data.items() if v is not None}

    def fetch_financial_data(self):
        if self._info_cache:
            info = self._info_cache
        else:
            if not self.stock:
                self.stock = _get_cached_ticker(self.ticker)
            try:
                info = self.stock.info
            except:
                info = {}

        if not info or (isinstance(info, dict) and len(info) < 5):
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
                            'trailingPE': q.get('trailingPE'),
                            'returnOnEquity': q.get('returnOnEquity'),
                            'debtToEquity': q.get('debtToEquity'),
                            'profitMargins': q.get('profitMargins'),
                            'revenueGrowth': q.get('revenueGrowth'),
                            'dividendYield': q.get('dividendYield'),
                        }
            except:
                pass

        self.financials['info'] = info if isinstance(info, dict) else {}
        self.company_name = (info.get('longName') or info.get('shortName') or self.original_ticker) if isinstance(info, dict) else self.original_ticker
        self.financials['sector'] = info.get('sector', 'N/A') if isinstance(info, dict) else 'N/A'
        self.financials['industry'] = info.get('industry', 'N/A') if isinstance(info, dict) else 'N/A'

        try:
            if self.stock:
                self.financials['income'] = self.stock.financials
                self.financials['balance'] = self.stock.balance_sheet
                self.financials['cashflow'] = self.stock.cashflow
                self.financials['prices'] = self.stock.history(period="5y")
            else:
                self._set_empty_financials()
        except:
            self._set_empty_financials()

        self._detect_currency()
        return True

    def _set_empty_financials(self):
        self.financials['income'] = pd.DataFrame()
        self.financials['balance'] = pd.DataFrame()
        self.financials['cashflow'] = pd.DataFrame()
        self.financials['prices'] = pd.DataFrame()

    def _detect_currency(self):
        if self.ticker.endswith('.NS') or self.ticker.endswith('.BO'):
            self.currency = 'INR'
            self.currency_symbol = '₹'
            return
        info = self.financials.get('info', {})
        if isinstance(info, dict):
            currency = info.get('currency') or info.get('financialCurrency')
            if currency:
                self.currency = currency
                self.currency_symbol = CURRENCY_SYMBOLS.get(currency, '$')
                return
        if self.original_ticker in INDIAN_STOCKS_DB:
            self.currency = 'INR'
            self.currency_symbol = '₹'
            return
        self.currency = 'USD'
        self.currency_symbol = '$'

    def _format_amount(self, value):
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return 'N/A'
        if self.currency == 'INR':
            cr = value / 1e7
            return f"{self.currency_symbol}{cr:.0f} Cr" if abs(cr) >= 100 else f"{self.currency_symbol}{cr:.1f} Cr"
        b = value / 1e9
        return f"{self.currency_symbol}{b:.2f}B" if abs(b) >= 1 else f"{self.currency_symbol}{value/1e6:.1f}M"

    def _safe_get(self, df, keys, col=0):
        if df is None or df.empty:
            return None
        if isinstance(keys, str):
            keys = [keys]
        for key in keys:
            if key in df.index and len(df.columns) > col:
                val = df.loc[key].iloc[col]
                if pd.notna(val):
                    return val
        return None

    def calculate_all_ratios(self):
        try:
            income = self.financials.get('income')
            balance = self.financials.get('balance')
            cashflow = self.financials.get('cashflow')
            info = self.financials.get('info', {})
            cp = self.live_price_data.get('current_price')

            LIMITS = {
                'Debt to Equity': (0, 20),
                'P/E Ratio': (0, 1000),
                'P/B Ratio': (0, 100),
                'P/S Ratio': (0, 100),
                'ROE': (-100, 100),
                'ROA': (-100, 100),
                'ROCE': (-100, 100),
                'Net Profit Margin': (-100, 100),
                'Gross Profit Margin': (0, 100),
                'Operating Margin': (-100, 100),
                'EBITDA Margin': (0, 100),
                'Revenue Growth (YoY)': (-200, 500),
                'Earnings Growth (YoY)': (-200, 500),
            }

            if isinstance(info, dict):
                ratio_map = [
                    ('returnOnEquity', 'ROE', 100),
                    ('returnOnAssets', 'ROA', 100),
                    ('profitMargins', 'Net Profit Margin', 100),
                    ('debtToEquity', 'Debt to Equity', 1),
                    ('trailingPE', 'P/E Ratio', 1),
                    ('priceToBook', 'P/B Ratio', 1),
                    ('trailingEps', 'EPS', 1),
                    ('revenueGrowth', 'Revenue Growth (YoY)', 100),
                    ('currentRatio', 'Current Ratio', 1),
                    ('earningsGrowth', 'Earnings Growth (YoY)', 100),
                    ('priceToSales', 'P/S Ratio', 1),
                    ('bookValue', 'Book Value Per Share', 1),
                    ('ebitda', 'EBITDA', 1),
                ]
                for key, ratio_key, mult in ratio_map:
                    val = info.get(key)
                    if val is not None and ratio_key not in self.ratios:
                        try:
                            calculated = float(val) * mult
                            if ratio_key in LIMITS:
                                low, high = LIMITS[ratio_key]
                                if calculated < low or calculated > high:
                                    continue
                            self.ratios[ratio_key] = calculated
                        except (ValueError, TypeError):
                            pass

            if 'Dividend Yield' not in self.ratios:
                try:
                    if cashflow is not None and not cashflow.empty and cp and cp > 0:
                        dividends_paid = self._safe_get(cashflow, [
                            'Dividends Paid', 'Cash Dividends Paid', 'Common Stock Dividends'
                        ])
                        shares = self._safe_get(income, [
                            'Diluted Average Shares', 'Basic Average Shares'
                        ]) if income is not None else None
                        
                        if dividends_paid and shares and shares > 0:
                            dps = abs(dividends_paid) / shares
                            div_yield = (dps / cp) * 100
                            if 0 <= div_yield <= 50:
                                self.ratios['Dividend Yield'] = div_yield
                except:
                    pass
            
            if 'Dividend Yield' not in self.ratios:
                yf_div = info.get('dividendYield') if isinstance(info, dict) else None
                if yf_div is not None:
                    try:
                        div_yield = float(yf_div) * 100
                        if 0 <= div_yield <= 50:
                            self.ratios['Dividend Yield'] = div_yield
                    except (ValueError, TypeError):
                        pass

            if income is not None and not income.empty:
                rev = self._safe_get(income, ['Total Revenue', 'Revenue'])
                ni = self._safe_get(income, ['Net Income', 'Net Income Common Stockholders'])
                gp = self._safe_get(income, ['Gross Profit'])
                oi = self._safe_get(income, ['Operating Income', 'EBIT'])
                ebitda = self._safe_get(income, ['EBITDA', 'Normalized EBITDA'])
                rev_p = self._safe_get(income, ['Total Revenue', 'Revenue'], 1)
                ni_p = self._safe_get(income, ['Net Income', 'Net Income Common Stockholders'], 1)

                if rev and rev > 0:
                    if ni and 'Net Profit Margin' not in self.ratios:
                        self.ratios['Net Profit Margin'] = (ni / rev) * 100
                    if gp and 'Gross Profit Margin' not in self.ratios:
                        self.ratios['Gross Profit Margin'] = (gp / rev) * 100
                    if oi and 'Operating Margin' not in self.ratios:
                        self.ratios['Operating Margin'] = (oi / rev) * 100
                    if ebitda and 'EBITDA Margin' not in self.ratios:
                        self.ratios['EBITDA Margin'] = (ebitda / rev) * 100
                    if rev_p and rev_p > 0 and 'Revenue Growth (YoY)' not in self.ratios:
                        self.ratios['Revenue Growth (YoY)'] = ((rev - rev_p) / rev_p) * 100
                    if ni_p and ni_p != 0 and 'Earnings Growth (YoY)' not in self.ratios:
                        growth = ((ni - ni_p) / abs(ni_p)) * 100
                        if -200 <= growth <= 500:
                            self.ratios['Earnings Growth (YoY)'] = growth

                shares = self._safe_get(income, ['Diluted Average Shares', 'Basic Average Shares'])
                if shares and shares > 0 and cp:
                    if ni and 'EPS' not in self.ratios:
                        self.ratios['EPS'] = ni / shares
                    if rev and 'Revenue Per Share' not in self.ratios:
                        rps = rev / shares
                        self.ratios['Revenue Per Share'] = rps
                        if rps > 0 and 'P/S Ratio' not in self.ratios:
                            self.ratios['P/S Ratio'] = cp / rps

                if balance is not None and not balance.empty:
                    eq = self._safe_get(balance, ['Stockholders Equity', 'Total Stockholder Equity', 'Total Equity'])
                    ast = self._safe_get(balance, ['Total Assets'])
                    ca = self._safe_get(balance, ['Current Assets'])
                    cl = self._safe_get(balance, ['Current Liabilities'])
                    td = self._safe_get(balance, ['Total Debt', 'Long Term Debt'])
                    inv = self._safe_get(balance, ['Inventory', 'Inventories'])
                    
                    if eq and eq > 0:
                        if ni and 'ROE' not in self.ratios:
                            self.ratios['ROE'] = (ni / eq) * 100
                        if shares and shares > 0 and 'Book Value Per Share' not in self.ratios:
                            self.ratios['Book Value Per Share'] = eq / shares
                        if td and 'Debt to Equity' not in self.ratios:
                            de = td / eq
                            if 0 <= de <= 20:
                                self.ratios['Debt to Equity'] = de
                    
                    if ast and ast > 0:
                        if ni and 'ROA' not in self.ratios:
                            self.ratios['ROA'] = (ni / ast) * 100
                        if rev and 'Asset Turnover' not in self.ratios:
                            self.ratios['Asset Turnover'] = rev / ast
                        if oi and 'ROCE' not in self.ratios:
                            roce = (oi / ast) * 100
                            if -100 <= roce <= 100:
                                self.ratios['ROCE'] = roce
                    
                    if ca and cl and cl > 0:
                        if 'Current Ratio' not in self.ratios:
                            self.ratios['Current Ratio'] = ca / cl
                        if inv and 'Quick Ratio' not in self.ratios:
                            self.ratios['Quick Ratio'] = (ca - inv) / cl

            self.ratios = {k: v for k, v in self.ratios.items() if v is not None}
            return True
        except:
            return True