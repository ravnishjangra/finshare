"""Residual Income Valuation Model"""
import pandas as pd
import numpy as np

class ResidualIncome:
    """
    Residual Income = Net Income - (Equity × Cost of Equity)
    Intrinsic Value = Book Value + PV of Future Residual Income
    """
    
    @staticmethod
    def calculate(income_df, balance_df, info, current_price, risk_free_rate=0.07, market_return=0.12):
        try:
            if income_df is None or balance_df is None or income_df.empty or balance_df.empty:
                return None
            
            col = income_df.columns[0]
            bal_col = balance_df.columns[0]
            
            # Get required data
            ni = next((income_df.loc[k, col] for k in ['Net Income', 'Net Income Common Stockholders'] 
                      if k in income_df.index), None)
            eq = next((balance_df.loc[k, bal_col] for k in ['Stockholders Equity', 'Total Stockholder Equity', 
                                                            'Total Equity', 'Common Stock Equity'] 
                      if k in balance_df.index), None)
            
            # Get shares
            shares = next((income_df.loc[k, col] for k in ['Diluted Average Shares', 'Basic Average Shares'] 
                          if k in income_df.index), None)
            if not shares:
                shares = info.get('sharesOutstanding', 1)
            
            if not ni or not eq or not shares or shares <= 0:
                return None
            
            bvps = eq / shares
            eps = ni / shares
            
            # Cost of equity using CAPM
            beta = info.get('beta', 1.0) or 1.0
            cost_of_equity = risk_free_rate + beta * (market_return - risk_free_rate)
            
            # Current residual income
            residual_income = eps - (bvps * cost_of_equity)
            
            # Growth assumption (use ROE - Cost of Equity as growth proxy)
            roe = ni / eq if eq > 0 else 0.10
            growth = max(0, min(roe - cost_of_equity, 0.05))  # Cap at 5%
            
            # PV of residual income (10 year projection)
            pv_ri = 0
            ri_current = residual_income
            for year in range(1, 11):
                ri_current = ri_current * (1 + growth)
                pv_ri += ri_current / (1 + cost_of_equity) ** year
            
            # Terminal value
            terminal_ri = ri_current * 1.02 / (cost_of_equity - 0.02) if cost_of_equity > 0.02 else 0
            pv_terminal = terminal_ri / (1 + cost_of_equity) ** 10
            
            intrinsic_bvps = bvps + pv_ri + pv_terminal
            upside = ((intrinsic_bvps / current_price) - 1) * 100 if current_price > 0 else 0
            
            if upside > 20:
                recommendation = "🟢 Undervalued"
            elif upside > 0:
                recommendation = "🟡 Fair Value"
            else:
                recommendation = "🔴 Overvalued"
            
            return {
                'intrinsic_value': round(intrinsic_bvps, 2),
                'current_price': current_price,
                'upside': round(upside, 1),
                'book_value_ps': round(bvps, 2),
                'residual_income': round(residual_income, 2),
                'cost_of_equity': round(cost_of_equity * 100, 1),
                'growth_rate': round(growth * 100, 1),
                'recommendation': recommendation
            }
        except:
            return None