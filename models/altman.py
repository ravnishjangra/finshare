"""Altman Z-Score - Bankruptcy Prediction"""
class AltmanZScore:
    @staticmethod
    def calculate(balance_df, income_df, market_cap):
        if balance_df is None or income_df is None or balance_df.empty or income_df.empty:
            return None
        try:
            col = balance_df.columns[0]
            inc_col = income_df.columns[0]
            
            ca = next((balance_df.loc[k, col] for k in ['Current Assets'] if k in balance_df.index), 0)
            cl = next((balance_df.loc[k, col] for k in ['Current Liabilities'] if k in balance_df.index), 0)
            ta = next((balance_df.loc[k, col] for k in ['Total Assets'] if k in balance_df.index), 0)
            re_val = next((balance_df.loc[k, col] for k in ['Retained Earnings', 'Stockholders Equity', 'Total Equity'] if k in balance_df.index), 0)
            ebit = next((income_df.loc[k, inc_col] for k in ['EBIT', 'Operating Income'] if k in income_df.index), 0)
            tl = next((balance_df.loc[k, col] for k in ['Total Liabilities'] if k in balance_df.index), ta)
            sales = next((income_df.loc[k, inc_col] for k in ['Total Revenue', 'Revenue'] if k in income_df.index), 0)
            
            if ta <= 0: return None
            
            wc = ca - cl
            x1 = wc / ta if ta else 0
            x2 = re_val / ta if ta else 0
            x3 = ebit / ta if ta else 0
            x4 = (market_cap or 0) / tl if tl else 0
            x5 = sales / ta if ta else 0
            
            z = 1.2*x1 + 1.4*x2 + 3.3*x3 + 0.6*x4 + 1.0*x5
            
            if z > 2.99: zone, risk = "🟢 SAFE ZONE", "Low bankruptcy risk"
            elif z > 1.81: zone, risk = "🟡 GREY ZONE", "Moderate risk"
            else: zone, risk = "🔴 DISTRESS ZONE", "High bankruptcy risk"
            
            return {'z_score': round(z, 2), 'zone': zone, 'risk': risk}
        except:
            return None