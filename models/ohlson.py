"""Ohlson O-Score - Bankruptcy Probability (1980)"""
import pandas as pd
import numpy as np

class OhlsonOScore:
    """
    O-Score > 0.5 = High bankruptcy risk
    Uses 9 financial variables for prediction
    """
    
    @staticmethod
    def calculate(income_df, balance_df, info):
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
                        if pd.notna(v): return float(v)
                return 0
            
            # Get financial data
            ta = get_val(balance_df, ['Total Assets'], 0)
            tl = get_val(balance_df, ['Total Liabilities'], 0)
            wc = get_val(balance_df, ['Working Capital'], 0)
            cl = get_val(balance_df, ['Current Liabilities'], 0)
            ca = get_val(balance_df, ['Current Assets'], 0)
            
            if not wc and ca and cl:
                wc = ca - cl
            
            ni = get_val(income_df, ['Net Income', 'Net Income Common Stockholders'], 0)
            ni_prev = get_val(income_df, ['Net Income', 'Net Income Common Stockholders'], 1) if len(income_df.columns) > 1 else 0
            ebit = get_val(income_df, ['EBIT', 'Operating Income'], 0)
            rev = get_val(income_df, ['Total Revenue', 'Revenue'], 0)
            
            if ta <= 0:
                return None
            
            # Market value
            mcap = info.get('marketCap', 0) or 0
            
            # 9 Variables
            # Size: log(total assets / GNP deflator). Simplified: log(TA)
            size = np.log(ta) if ta > 0 else 0
            
            # TLTA: Total Liabilities / Total Assets
            tlta = tl / ta if ta > 0 else 0
            
            # WCTA: Working Capital / Total Assets
            wcta = wc / ta if ta > 0 else 0
            
            # CLCA: Current Liabilities / Current Assets
            clca = cl / ca if ca > 0 else 0
            
            # OENEG: 1 if TL > TA, else 0
            oeneg = 1 if tl > ta else 0
            
            # NITA: Net Income / Total Assets
            nita = ni / ta if ta > 0 else 0
            
            # FUTL: EBIT / Total Liabilities
            futl = ebit / tl if tl > 0 else 0
            
            # INTWO: 1 if negative NI in last 2 years, else 0
            intwo = 1 if (ni < 0 and ni_prev < 0) else 0
            
            # CHIN: (NI - NI_prev) / (|NI| + |NI_prev|)
            chin = (ni - ni_prev) / (abs(ni) + abs(ni_prev)) if (abs(ni) + abs(ni_prev)) > 0 else 0
            
            # O-Score formula
            o_score = (-1.32 - 0.407*size + 6.03*tlta - 1.43*wcta + 0.076*clca 
                      - 2.37*nita - 1.83*futl + 0.285*intwo - 1.72*oeneg - 0.521*chin)
            
            # Convert to probability
            prob = 1 / (1 + np.exp(-o_score))
            
            if prob > 0.5:
                risk = "🔴 High Risk"
                interpretation = f"High probability ({prob*100:.0f}%) of financial distress within 2 years."
                color = '#ef4444'
            elif prob > 0.2:
                risk = "🟡 Moderate Risk"
                interpretation = f"Moderate probability ({prob*100:.0f}%) of financial distress. Monitor closely."
                color = '#f59e0b'
            else:
                risk = "🟢 Low Risk"
                interpretation = f"Low probability ({prob*100:.0f}%) of financial distress."
                color = '#10b981'
            
            return {
                'o_score': round(o_score, 2),
                'probability': f"{prob*100:.1f}%",
                'risk': risk,
                'color': color,
                'interpretation': interpretation,
                'components': {
                    'Size (log TA)': round(size, 2),
                    'TL/TA': round(tlta, 3),
                    'WC/TA': round(wcta, 3),
                    'CL/CA': round(clca, 3),
                    'NI/TA': round(nita, 3),
                    'EBIT/TL': round(futl, 3),
                    'Negative NI 2yr': intwo,
                    'TL > TA': oeneg,
                    'NI Change': round(chin, 3),
                }
            }
        except:
            return None