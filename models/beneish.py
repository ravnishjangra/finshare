"""Beneish M-Score - Earnings Manipulation Detection"""
import pandas as pd
import numpy as np

class BeneishMScore:
    """
    M-Score > -1.78 = Likely manipulator
    Based on 8 financial ratios tracking year-over-year changes
    """
    
    @staticmethod
    def calculate(income_df, balance_df, cashflow_df):
        try:
            if income_df is None or balance_df is None or cashflow_df is None:
                return None
            if income_df.empty or balance_df.empty or len(income_df.columns) < 2:
                return None
            
            inc_cols = income_df.columns[:2]
            bal_cols = balance_df.columns[:2]
            cf_cols = cashflow_df.columns[:2]
            
            c, p = 0, 1  # current, previous
            
            # Helper
            def get_val(df, keys, col_idx):
                for k in keys:
                    if k in df.index and col_idx < len(df.columns):
                        v = df.loc[k, df.columns[col_idx]]
                        if pd.notna(v): return float(v)
                return 0
            
            # 1. Days Sales in Receivables Index (DSRI)
            rev_c = get_val(income_df, ['Total Revenue', 'Revenue'], c)
            rev_p = get_val(income_df, ['Total Revenue', 'Revenue'], p)
            rec_c = get_val(balance_df, ['Accounts Receivable', 'Receivables'], c)
            rec_p = get_val(balance_df, ['Accounts Receivable', 'Receivables'], p)
            
            dsri = (rec_c/rev_c) / (rec_p/rev_p) if rev_c and rev_p and rec_p else 1
            
            # 2. Gross Margin Index (GMI) = GM(t-1) / GM(t), where GM = Gross Profit / Revenue.
            # NOTE: previously this incorrectly used (Revenue-GrossProfit)/Revenue (a COGS
            # margin) instead of the gross margin itself - that inverted the ratio's meaning.
            gp_c = get_val(income_df, ['Gross Profit'], c)
            gp_p = get_val(income_df, ['Gross Profit'], p)
            if not gp_c and rev_c:
                cogs_c = get_val(income_df, ['Cost Of Revenue', 'Cost of Goods Sold', 'Cost of Revenue'], c)
                gp_c = rev_c - cogs_c if cogs_c else gp_c
            if not gp_p and rev_p:
                cogs_p = get_val(income_df, ['Cost Of Revenue', 'Cost of Goods Sold', 'Cost of Revenue'], p)
                gp_p = rev_p - cogs_p if cogs_p else gp_p
            gm_c = gp_c / rev_c if rev_c else 0
            gm_p = gp_p / rev_p if rev_p else 0
            gmi = gm_p / gm_c if gm_c else 1
            
            # 3. Asset Quality Index (AQI)
            ta_c = get_val(balance_df, ['Total Assets'], c)
            ta_p = get_val(balance_df, ['Total Assets'], p)
            ca_c = get_val(balance_df, ['Current Assets'], c)
            ca_p = get_val(balance_df, ['Current Assets'], p)
            ppe_c = get_val(balance_df, ['Property Plant Equipment', 'Net PPE'], c)
            ppe_p = get_val(balance_df, ['Property Plant Equipment', 'Net PPE'], p)
            
            non_ca_c = ta_c - ca_c - ppe_c
            non_ca_p = ta_p - ca_p - ppe_p
            aqi = (non_ca_c/ta_c) / (non_ca_p/ta_p) if ta_c and ta_p and non_ca_p else 1
            
            # 4. Sales Growth Index (SGI)
            sgi = rev_c / rev_p if rev_p else 1
            
            # 5. Depreciation Index (DEPI)
            dep_c = get_val(cashflow_df, ['Depreciation', 'Depreciation & Amortization'], c)
            dep_p = get_val(cashflow_df, ['Depreciation', 'Depreciation & Amortization'], p)
            depi = (dep_p/(dep_p+ppe_p)) / (dep_c/(dep_c+ppe_c)) if dep_c and dep_p and ppe_c and ppe_p else 1
            
            # 6. SG&A Index (SGAI)
            sga_c = get_val(income_df, ['Selling General Administrative', 'SG&A Expense'], c)
            sga_p = get_val(income_df, ['Selling General Administrative', 'SG&A Expense'], p)
            sgai = (sga_c/rev_c) / (sga_p/rev_p) if rev_c and rev_p and sga_p else 1
            
            # 7. Leverage Index (LVGI) = Leverage(t) / Leverage(t-1), where
            # Leverage = Total Debt / Total Assets. NOTE: previously this computed
            # (Debt+Assets)/Assets, which is not a leverage ratio at all - it produced
            # a number just above 1 regardless of actual debt load and barely moved
            # year over year, silently muting a real fraud-detection signal.
            td_c = get_val(balance_df, ['Total Debt', 'Long Term Debt'], c)
            td_p = get_val(balance_df, ['Total Debt', 'Long Term Debt'], p)
            lev_c = td_c / ta_c if ta_c else 0
            lev_p = td_p / ta_p if ta_p else 0
            lvgi = lev_c / lev_p if lev_p else 1
            
            # 8. Total Accruals to Total Assets (TATA)
            ni_c = get_val(income_df, ['Net Income'], c)
            ocf_c = get_val(cashflow_df, ['Operating Cash Flow'], c)
            tata = (ni_c - ocf_c) / ta_c if ta_c else 0
            
            # M-Score calculation
            m_score = (-4.84 + 0.92*dsri + 0.528*gmi + 0.404*aqi + 0.892*sgi 
                      + 0.115*depi - 0.172*sgai + 4.679*tata - 0.327*lvgi)
            
            if m_score > -1.78:
                risk = "🔴 High Manipulation Risk"
                interpretation = "Financial statements may be manipulated. Exercise caution."
                color = '#ef4444'
            elif m_score > -2.22:
                risk = "🟡 Moderate Risk"
                interpretation = "Some warning signs present. Review carefully."
                color = '#f59e0b'
            else:
                risk = "🟢 Low Risk"
                interpretation = "Financial statements appear reliable."
                color = '#10b981'
            
            components = {
                'DSRI (Receivables)': round(dsri, 2),
                'GMI (Gross Margin)': round(gmi, 2),
                'AQI (Asset Quality)': round(aqi, 2),
                'SGI (Sales Growth)': round(sgi, 2),
                'DEPI (Depreciation)': round(depi, 2),
                'SGAI (SG&A)': round(sgai, 2),
                'LVGI (Leverage)': round(lvgi, 2),
                'TATA (Accruals)': round(tata, 4),
            }

            # A component index materially above 1.0 (roughly >1.2, the rule-of-thumb
            # threshold used in the Beneish literature) signals that ratio moved in the
            # manipulation-consistent direction year over year. TATA is on a different
            # scale (a fraction of total assets, not an index around 1) so it uses its
            # own threshold instead.
            flags = {}
            for name, val in components.items():
                if name.startswith('TATA'):
                    flags[name] = 'elevated' if val > 0.03 else 'normal'
                else:
                    flags[name] = 'elevated' if val > 1.2 else 'normal'

            return {
                'm_score': round(m_score, 2),
                'risk': risk,
                'color': color,
                'interpretation': interpretation,
                'components': components,
                'flags': flags,
            }
        except:
            return None