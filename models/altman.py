"""Altman Z-Score - Bankruptcy Prediction with Interpretation"""
import pandas as pd

class AltmanZScore:
    
    # Multiple possible key names for each field
    # NOTE: 'retained_earnings' and 'total_equity' used to be merged into one
    # list. That silently substituted TOTAL EQUITY for RETAINED EARNINGS
    # whenever the latter wasn't reported (common for many data feeds) - and
    # that same blended value was then reused to *back into* Total Assets via
    # TA = TL + "RE" in the fallback below. If the value picked up was truly
    # retained earnings (a subset of equity, missing paid-in capital etc.),
    # that fallback understated Total Assets, which inflates every ratio that
    # divides by TA (X1, X2, X3, X5). They're now kept as separate keys.
    KEY_MAP = {
        'current_assets': ['Current Assets', 'Current Assets, Total', 'Total Current Assets'],
        'current_liabilities': ['Current Liabilities', 'Current Liabilities, Total', 'Total Current Liabilities'],
        'total_assets': ['Total Assets', 'Total Assets, Total'],
        'retained_earnings': ['Retained Earnings'],
        'total_equity': ['Stockholders Equity', 'Total Stockholder Equity',
                          'Total Equity', 'Common Stock Equity', 'Total Equity Gross Minority Interest'],
        'ebit': ['EBIT', 'Operating Income', 'Operating Income, Total'],
        'total_liabilities': ['Total Liabilities', 'Total Liabilities Net Minority Interest', 
                              'Total Liabilities, Total'],
        'revenue': ['Total Revenue', 'Revenue', 'Total Revenue, Total'],
    }
    
    @staticmethod
    def _safe_get(df, keys, col):
        """Get first matching value from DataFrame"""
        if df is None or df.empty:
            return 0
        for key in keys:
            if key in df.index:
                try:
                    val = df.loc[key, col]
                    if pd.notna(val) and val != 0:
                        return float(val)
                except:
                    continue
        return 0
    
    @staticmethod
    def calculate(balance_df, income_df, market_cap):
        if balance_df is None or income_df is None or balance_df.empty or income_df.empty:
            return None
        
        try:
            bal_col = balance_df.columns[0]
            inc_col = income_df.columns[0]
            
            # Get values using key map
            ca = AltmanZScore._safe_get(balance_df, AltmanZScore.KEY_MAP['current_assets'], bal_col)
            cl = AltmanZScore._safe_get(balance_df, AltmanZScore.KEY_MAP['current_liabilities'], bal_col)
            ta = AltmanZScore._safe_get(balance_df, AltmanZScore.KEY_MAP['total_assets'], bal_col)
            re_val = AltmanZScore._safe_get(balance_df, AltmanZScore.KEY_MAP['retained_earnings'], bal_col)
            total_equity = AltmanZScore._safe_get(balance_df, AltmanZScore.KEY_MAP['total_equity'], bal_col)
            tl = AltmanZScore._safe_get(balance_df, AltmanZScore.KEY_MAP['total_liabilities'], bal_col)
            ebit = AltmanZScore._safe_get(income_df, AltmanZScore.KEY_MAP['ebit'], inc_col)
            sales = AltmanZScore._safe_get(income_df, AltmanZScore.KEY_MAP['revenue'], inc_col)
            
            # Fallback: if Total Assets not found, back into it via the
            # accounting identity TA = TL + Total Equity (NOT retained
            # earnings, which is only a slice of equity).
            if ta <= 0 and tl > 0 and total_equity > 0:
                ta = tl + total_equity
            
            if ta <= 0:
                return None
            
            # X2 needs actual retained earnings. If a feed doesn't report it
            # separately, using total equity in its place materially overstates
            # X2 (equity is always >= retained earnings), so we degrade
            # gracefully to 0 rather than silently substituting the wrong figure.
            x2_re = re_val if re_val else 0
            
            wc = ca - cl
            x1 = wc / ta
            x2 = x2_re / ta
            x3 = ebit / ta
            x4 = (market_cap or 0) / tl if tl and tl > 0 else 0
            x5 = sales / ta
            
            z = 1.2*x1 + 1.4*x2 + 3.3*x3 + 0.6*x4 + 1.0*x5
            
            # Zone classification
            if z > 2.99:
                zone = "🟢 SAFE ZONE"
                risk_level = "Very Low"
                probability = "< 5%"
                interpretation = "Company appears financially healthy with a low likelihood of bankruptcy based on current financials."
                color = '#10b981'
            elif z > 1.81:
                zone = "🟡 GREY ZONE"
                risk_level = "Moderate"
                probability = "5% - 20%"
                interpretation = "Company shows some warning signs. Monitor financials closely and review debt levels."
                color = '#f59e0b'
            else:
                zone = "🔴 DISTRESS ZONE"
                risk_level = "High"
                probability = "> 20%"
                interpretation = "Company is showing significant financial distress signals. High probability of bankruptcy without intervention."
                color = '#ef4444'
            
            return {
                'z_score': round(z, 2),
                'zone': zone,
                'color': color,
                'risk_level': risk_level,
                'probability': probability,
                'interpretation': interpretation,
                'components': {
                    'X1 (Working Capital/TA)': {'value': round(x1, 3), 'weight': 1.2, 'signal': 'Liquidity'},
                    'X2 (Retained Earnings/TA)': {'value': round(x2, 3), 'weight': 1.4, 'signal': 'Cumulative Profitability'},
                    'X3 (EBIT/TA)': {'value': round(x3, 3), 'weight': 3.3, 'signal': 'Operating Efficiency'},
                    'X4 (Market Cap/TL)': {'value': round(x4, 3), 'weight': 0.6, 'signal': 'Market Confidence'},
                    'X5 (Sales/TA)': {'value': round(x5, 3), 'weight': 1.0, 'signal': 'Asset Utilization'},
                }
            }
        except Exception as e:
            return None