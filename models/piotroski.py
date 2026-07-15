"""Piotroski F-Score (0-9)"""
import pandas as pd

class PiotroskiFScore:
    @staticmethod
    def calculate(income_df, balance_df, cashflow_df):
        score = 0
        details = []
        if income_df is None or balance_df is None or cashflow_df is None:
            return {'score': 0, 'rating': 'N/A', 'details': ['Insufficient data']}
        if income_df.empty or balance_df.empty:
            return {'score': 0, 'rating': 'N/A', 'details': ['Financial data not available']}
        try:
            cols = income_df.columns[:2]
            if len(cols) < 2:
                return {'score': 0, 'rating': 'N/A', 'details': ['Need 2 years of data']}
            
            ni_key = next((k for k in ['Net Income', 'Net Income Common Stockholders'] if k in income_df.index), None)
            if ni_key:
                ni = income_df.loc[ni_key, cols[0]]
                if pd.notna(ni) and ni > 0: score += 1; details.append("✅ Positive Net Income")
                else: details.append("❌ Negative Net Income")
            
            ocf_key = next((k for k in ['Operating Cash Flow'] if k in cashflow_df.index), None)
            if ocf_key and pd.notna(cashflow_df.loc[ocf_key, cashflow_df.columns[0]]) and cashflow_df.loc[ocf_key, cashflow_df.columns[0]] > 0:
                score += 1; details.append("✅ Positive Operating Cash Flow")
            else: details.append("❌ Negative OCF")
            
            asset_key = next((k for k in ['Total Assets'] if k in balance_df.index), None)
            if ni_key and asset_key and len(cols) > 1:
                assets_curr = balance_df.loc[asset_key, balance_df.columns[0]]
                assets_prev = balance_df.loc[asset_key, balance_df.columns[1]]
                ni_curr = income_df.loc[ni_key, cols[0]]
                ni_prev = income_df.loc[ni_key, cols[1]]
                if assets_curr and assets_prev and assets_curr > 0 and assets_prev > 0:
                    if (ni_curr/assets_curr) > (ni_prev/assets_prev): score += 1; details.append("✅ ROA Increasing")
                    else: details.append("❌ ROA Declining")
            
            if ocf_key and ni_key and pd.notna(ni) and cashflow_df.loc[ocf_key, cashflow_df.columns[0]] > ni:
                score += 1; details.append("✅ OCF > Net Income")
            
            debt_key = next((k for k in ['Long Term Debt', 'Total Debt'] if k in balance_df.index), None)
            if debt_key and len(balance_df.columns) > 1:
                d_curr = balance_df.loc[debt_key, balance_df.columns[0]]
                d_prev = balance_df.loc[debt_key, balance_df.columns[1]]
                if pd.notna(d_curr) and pd.notna(d_prev) and d_curr < d_prev: score += 1; details.append("✅ Debt Decreasing")
            
            ca_key = next((k for k in ['Current Assets'] if k in balance_df.index), None)
            cl_key = next((k for k in ['Current Liabilities'] if k in balance_df.index), None)
            if ca_key and cl_key and len(balance_df.columns) > 1:
                ca_c = balance_df.loc[ca_key, balance_df.columns[0]]; cl_c = balance_df.loc[cl_key, balance_df.columns[0]]
                ca_p = balance_df.loc[ca_key, balance_df.columns[1]]; cl_p = balance_df.loc[cl_key, balance_df.columns[1]]
                if all(pd.notna(x) and x > 0 for x in [ca_c, cl_c, ca_p, cl_p]):
                    if (ca_c/cl_c) > (ca_p/cl_p): score += 1; details.append("✅ Current Ratio Improving")
            
            shares_key = next((k for k in ['Diluted Average Shares', 'Basic Average Shares'] if k in income_df.index), None)
            if shares_key and len(income_df.columns) > 1:
                s_curr = income_df.loc[shares_key, cols[0]]; s_prev = income_df.loc[shares_key, cols[1]]
                if pd.notna(s_curr) and pd.notna(s_prev) and s_curr <= s_prev: score += 1; details.append("✅ No Share Dilution")
            
            gp_key = next((k for k in ['Gross Profit'] if k in income_df.index), None)
            rev_key = next((k for k in ['Total Revenue', 'Revenue'] if k in income_df.index), None)
            if gp_key and rev_key and len(cols) > 1:
                gp_c = income_df.loc[gp_key, cols[0]]; rev_c = income_df.loc[rev_key, cols[0]]
                gp_p = income_df.loc[gp_key, cols[1]]; rev_p = income_df.loc[rev_key, cols[1]]
                if all(pd.notna(x) and x > 0 for x in [gp_c, rev_c, gp_p, rev_p]):
                    if (gp_c/rev_c) > (gp_p/rev_p): score += 1; details.append("✅ Gross Margin Improving")
            
            if rev_key and asset_key and len(cols) > 1:
                rev_c = income_df.loc[rev_key, cols[0]]; rev_p = income_df.loc[rev_key, cols[1]]
                a_c = balance_df.loc[asset_key, balance_df.columns[0]]; a_p = balance_df.loc[asset_key, balance_df.columns[1]]
                if all(pd.notna(x) and x > 0 for x in [rev_c, a_c, rev_p, a_p]):
                    if (rev_c/a_c) > (rev_p/a_p): score += 1; details.append("✅ Asset Turnover Improving")
                        
        except Exception as e:
            details.append(f"⚠️ Error: {str(e)[:50]}")
        
        rating = "🟢 STRONG" if score >= 7 else "🟡 AVERAGE" if score >= 4 else "🔴 WEAK"
        return {'score': score, 'rating': rating, 'details': details}