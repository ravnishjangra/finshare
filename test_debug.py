"""Debug script to test data fetching for RELIANCE.NS"""
import yfinance as yf
import time

print("=" * 50)
print("TEST 1: yfinance direct")
print("=" * 50)

try:
    stock = yf.Ticker("RELIANCE.NS")
    info = stock.info
    
    print(f"Total keys in info: {len(info)}")
    print(f"Price: {info.get('currentPrice')}")
    print(f"Market Cap: {info.get('marketCap')}")
    print(f"Long Name: {info.get('longName')}")
    print(f"Sector: {info.get('sector')}")
    print(f"Beta: {info.get('beta')}")
    print(f"PE Ratio: {info.get('trailingPE')}")
    print(f"ROE: {info.get('returnOnEquity')}")
    print(f"Currency: {info.get('currency')}")
    print(f"Shares Outstanding: {info.get('sharesOutstanding')}")
    
except Exception as e:
    print(f"❌ yfinance failed: {e}")

time.sleep(1)

print("\n" + "=" * 50)
print("TEST 2: yahooquery direct")
print("=" * 50)

try:
    from yahooquery import Ticker as YQTicker
    t = YQTicker("RELIANCE.NS")
    
    # Test modules
    modules = t.get_modules(['price', 'summaryDetail', 'defaultKeyStatistics', 'financialData'])
    print(f"Modules received: {list(modules.keys())}")
    
    price_data = modules.get('price', {}).get("RELIANCE.NS", {})
    print(f"\nPrice data keys: {list(price_data.keys()) if price_data else 'EMPTY'}")
    print(f"Market price: {price_data.get('regularMarketPrice', {}).get('raw') if price_data else 'N/A'}")
    print(f"Market cap: {price_data.get('marketCap', {}).get('raw') if price_data else 'N/A'}")
    
    # Test quotes
    quote = t.quotes
    if quote and len(quote) > 0:
        q = quote[0]
        print(f"\nQuote keys: {list(q.keys())[:10]}...")
        print(f"Price from quote: {q.get('regularMarketPrice')}")
        print(f"Market cap from quote: {q.get('marketCap')}")
        print(f"Long name: {q.get('longName')}")
    else:
        print("\n❌ Quotes is EMPTY")
    
except Exception as e:
    print(f"❌ yahooquery failed: {e}")

time.sleep(1)

print("\n" + "=" * 50)
print("TEST 3: Your analyzer class")
print("=" * 50)

try:
    # Import your analyzer
    import sys
    sys.path.insert(0, '.')
    from core.analyzer import ProFinancialAnalyzer
    
    analyzer = ProFinancialAnalyzer("RELIANCE", exchange="NSE")
    print(f"Resolved ticker: {analyzer.ticker}")
    
    result = analyzer.get_live_price()
    print(f"get_live_price() returned: {result}")
    print(f"Data source: {analyzer.data_source}")
    print(f"Live price data: {analyzer.live_price_data}")
    
except Exception as e:
    print(f"❌ Analyzer failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("DEBUG COMPLETE")
print("=" * 50)