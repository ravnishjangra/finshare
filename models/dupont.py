"""DuPont Analysis - ROE Decomposition"""
import pandas as pd

class DuPontAnalysis:
    """
    3-Step: ROE = Net Margin × Asset Turnover × Equity Multiplier
    5-Step: ROE = Tax Burden × Interest Burden × Operating Margin × Asset Turnover × Leverage
    """
    
    @staticmethod
    def calculate(income_df, balance_df, ratios):
        try:
            if income_df is None or balance_df is None:
                return None
            if income_df.empty or balance_df.empty:
                return None
            
            col = income_df.columns[0]
            bal_col = balance_df.columns[0]
            
            def get_val(df, keys, col_idx):
                for k in keys:
                    if k in df.index and col_idx < len(df.columns):
                        v = df.loc[k, df.columns[col_idx]]
                        if pd.notna(v) and v != 0: return float(v)
                return 0
            
            rev = get_val(income_df, ['Total Revenue', 'Revenue'], 0)
            ni = get_val(income_df, ['Net Income', 'Net Income Common Stockholders'], 0)
            ebit = get_val(income_df, ['EBIT', 'Operating Income'], 0)
            ebt = get_val(income_df, ['Pretax Income', 'Income Before Tax'], 0)
            ta = get_val(balance_df, ['Total Assets'], 0)
            eq = get_val(balance_df, ['Stockholders Equity', 'Total Stockholder Equity', 'Total Equity', 'Common Stock Equity'], 0)
            
            if not all([rev, ni, ta, eq]):
                return None
            
            # 3-Step
            net_margin = ni / rev * 100
            asset_turnover = rev / ta
            equity_multiplier = ta / eq
            roe_3step = net_margin / 100 * asset_turnover * equity_multiplier * 100
            
            # 5-Step
            if ebit and ebt:
                tax_burden = ni / ebt if ebt else 1
                interest_burden = ebt / ebit if ebit else 1
                op_margin = ebit / rev * 100
                roe_5step = tax_burden * interest_burden * (op_margin/100) * asset_turnover * equity_multiplier * 100
                has_5step = True
            else:
                tax_burden = None
                interest_burden = None
                op_margin = None
                roe_5step = None
                has_5step = False
            
            return {
                'roe': round(ratios.get('ROE', roe_3step), 1),
                'three_step': {
                    'net_margin': round(net_margin, 1),
                    'asset_turnover': round(asset_turnover, 3),
                    'equity_multiplier': round(equity_multiplier, 2),
                    'roe': round(roe_3step, 1),
                },
                'five_step': {
                    'tax_burden': round(tax_burden, 3) if tax_burden else None,
                    'interest_burden': round(interest_burden, 3) if interest_burden else None,
                    'operating_margin': round(op_margin, 1) if op_margin else None,
                    'asset_turnover': round(asset_turnover, 3),
                    'equity_multiplier': round(equity_multiplier, 2),
                    'roe': round(roe_5step, 1) if roe_5step else None,
                } if has_5step else None,
            }
        except:
            return None