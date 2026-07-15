"""Piotroski F-Score (0-9) - Financial Strength Breakdown"""
import pandas as pd
import numpy as np

class PiotroskiFScore:
    @staticmethod
    def calculate(income_df, balance_df, cashflow_df):
        if income_df is None or balance_df is None or cashflow_df is None:
            return {'score': 0, 'rating': 'N/A', 'details': ['Insufficient data'],
                    'breakdown': {}, 'error': True}
        if income_df.empty or balance_df.empty:
            return {'score': 0, 'rating': 'N/A', 'details': ['Financial data not available'],
                    'breakdown': {}, 'error': True}
        
        try:
            cols = income_df.columns[:2]
            if len(cols) < 2:
                return {'score': 0, 'rating': 'N/A', 'details': ['Need 2 years of data'],
                        'breakdown': {}, 'error': True}
            
            profitability = {'score': 0, 'max': 4, 'items': []}
            leverage = {'score': 0, 'max': 3, 'items': []}
            efficiency = {'score': 0, 'max': 2, 'items': []}
            total_score = 0
            
            # ===== PROFITABILITY (0-4) =====
            ni_key = next((k for k in ['Net Income', 'Net Income Common Stockholders'] if k in income_df.index), None)
            ni = None
            if ni_key:
                ni = income_df.loc[ni_key, cols[0]]
                if pd.notna(ni) and ni > 0:
                    total_score += 1
                    profitability['score'] += 1
                    profitability['items'].append({'name': 'Net Income', 'status': 'pass', 'detail': 'Positive'})
                else:
                    profitability['items'].append({'name': 'Net Income', 'status': 'fail', 'detail': 'Negative'})
            else:
                profitability['items'].append({'name': 'Net Income', 'status': 'na', 'detail': 'Data missing'})
            
            ocf_key = next((k for k in ['Operating Cash Flow'] if k in cashflow_df.index), None)
            ocf_val = None
            if ocf_key:
                ocf_val = cashflow_df.loc[ocf_key, cashflow_df.columns[0]]
                if pd.notna(ocf_val) and ocf_val > 0:
                    total_score += 1
                    profitability['score'] += 1
                    profitability['items'].append({'name': 'Operating Cash Flow', 'status': 'pass', 'detail': 'Positive'})
                else:
                    profitability['items'].append({'name': 'Operating Cash Flow', 'status': 'fail', 'detail': 'Negative'})
            else:
                profitability['items'].append({'name': 'Operating Cash Flow', 'status': 'na', 'detail': 'Data missing'})
            
            # ROA increasing
            asset_key = next((k for k in ['Total Assets'] if k in balance_df.index), None)
            if ni_key and asset_key and len(cols) > 1:
                try:
                    assets_curr = balance_df.loc[asset_key, balance_df.columns[0]]
                    assets_prev = balance_df.loc[asset_key, balance_df.columns[1]]
                    ni_curr = income_df.loc[ni_key, cols[0]]
                    ni_prev = income_df.loc[ni_key, cols[1]]
                    if all(pd.notna(x) and x > 0 for x in [assets_curr, assets_prev]):
                        roa_curr = ni_curr / assets_curr
                        roa_prev = ni_prev / assets_prev
                        if roa_curr > roa_prev:
                            total_score += 1
                            profitability['score'] += 1
                            profitability['items'].append({'name': 'ROA Trend', 'status': 'pass', 
                                                           'detail': f'Improving ({roa_curr*100:.1f}% vs {roa_prev*100:.1f}%)'})
                        else:
                            profitability['items'].append({'name': 'ROA Trend', 'status': 'fail',
                                                           'detail': f'Declining ({roa_curr*100:.1f}% vs {roa_prev*100:.1f}%)'})
                    else:
                        profitability['items'].append({'name': 'ROA Trend', 'status': 'na', 'detail': 'Cannot calculate'})
                except:
                    profitability['items'].append({'name': 'ROA Trend', 'status': 'na', 'detail': 'Error'})
            else:
                profitability['items'].append({'name': 'ROA Trend', 'status': 'na', 'detail': 'Data missing'})
            
            # OCF > Net Income (earnings quality)
            if ocf_key and ni_key and ocf_val is not None and ni is not None:
                if ocf_val > ni:
                    total_score += 1
                    profitability['score'] += 1
                    profitability['items'].append({'name': 'Earnings Quality', 'status': 'pass', 'detail': 'OCF > Net Income'})
                else:
                    profitability['items'].append({'name': 'Earnings Quality', 'status': 'fail', 'detail': 'OCF < Net Income'})
            else:
                profitability['items'].append({'name': 'Earnings Quality', 'status': 'na', 'detail': 'Data missing'})
            
            # ===== LEVERAGE & LIQUIDITY (0-3) =====
            debt_key = next((k for k in ['Long Term Debt', 'Total Debt'] if k in balance_df.index), None)
            if debt_key and len(balance_df.columns) > 1:
                d_curr = balance_df.loc[debt_key, balance_df.columns[0]]
                d_prev = balance_df.loc[debt_key, balance_df.columns[1]]
                if pd.notna(d_curr) and pd.notna(d_prev):
                    if d_curr < d_prev:
                        total_score += 1
                        leverage['score'] += 1
                        leverage['items'].append({'name': 'Debt Level', 'status': 'pass', 'detail': 'Decreasing'})
                    else:
                        leverage['items'].append({'name': 'Debt Level', 'status': 'fail', 'detail': 'Increasing'})
                else:
                    leverage['items'].append({'name': 'Debt Level', 'status': 'na', 'detail': 'Data missing'})
            else:
                leverage['items'].append({'name': 'Debt Level', 'status': 'na', 'detail': 'Data missing'})
            
            ca_key = next((k for k in ['Current Assets'] if k in balance_df.index), None)
            cl_key = next((k for k in ['Current Liabilities'] if k in balance_df.index), None)
            if ca_key and cl_key and len(balance_df.columns) > 1:
                try:
                    ca_c = balance_df.loc[ca_key, balance_df.columns[0]]
                    cl_c = balance_df.loc[cl_key, balance_df.columns[0]]
                    ca_p = balance_df.loc[ca_key, balance_df.columns[1]]
                    cl_p = balance_df.loc[cl_key, balance_df.columns[1]]
                    if all(pd.notna(x) and x > 0 for x in [ca_c, cl_c, ca_p, cl_p]):
                        cr_curr = ca_c / cl_c
                        cr_prev = ca_p / cl_p
                        if cr_curr > cr_prev:
                            total_score += 1
                            leverage['score'] += 1
                            leverage['items'].append({'name': 'Current Ratio', 'status': 'pass',
                                                      'detail': f'Improving ({cr_curr:.2f} vs {cr_prev:.2f})'})
                        else:
                            leverage['items'].append({'name': 'Current Ratio', 'status': 'fail',
                                                      'detail': f'Declining ({cr_curr:.2f} vs {cr_prev:.2f})'})
                    else:
                        leverage['items'].append({'name': 'Current Ratio', 'status': 'na', 'detail': 'Cannot calculate'})
                except:
                    leverage['items'].append({'name': 'Current Ratio', 'status': 'na', 'detail': 'Error'})
            else:
                leverage['items'].append({'name': 'Current Ratio', 'status': 'na', 'detail': 'Data missing'})
            
            # No share dilution
            shares_key = next((k for k in ['Diluted Average Shares', 'Basic Average Shares'] if k in income_df.index), None)
            if shares_key and len(income_df.columns) > 1:
                s_curr = income_df.loc[shares_key, cols[0]]
                s_prev = income_df.loc[shares_key, cols[1]]
                if pd.notna(s_curr) and pd.notna(s_prev):
                    if s_curr <= s_prev:
                        total_score += 1
                        leverage['score'] += 1
                        leverage['items'].append({'name': 'Share Dilution', 'status': 'pass', 'detail': 'No dilution'})
                    else:
                        leverage['items'].append({'name': 'Share Dilution', 'status': 'fail', 'detail': 'Dilution detected'})
                else:
                    leverage['items'].append({'name': 'Share Dilution', 'status': 'na', 'detail': 'Data missing'})
            else:
                leverage['items'].append({'name': 'Share Dilution', 'status': 'na', 'detail': 'Data missing'})
            
            # ===== OPERATING EFFICIENCY (0-2) =====
            gp_key = next((k for k in ['Gross Profit'] if k in income_df.index), None)
            rev_key = next((k for k in ['Total Revenue', 'Revenue'] if k in income_df.index), None)
            if gp_key and rev_key and len(cols) > 1:
                try:
                    gp_c = income_df.loc[gp_key, cols[0]]
                    rev_c = income_df.loc[rev_key, cols[0]]
                    gp_p = income_df.loc[gp_key, cols[1]]
                    rev_p = income_df.loc[rev_key, cols[1]]
                    if all(pd.notna(x) and x > 0 for x in [gp_c, rev_c, gp_p, rev_p]):
                        gm_curr = gp_c / rev_c
                        gm_prev = gp_p / rev_p
                        if gm_curr > gm_prev:
                            total_score += 1
                            efficiency['score'] += 1
                            efficiency['items'].append({'name': 'Gross Margin', 'status': 'pass',
                                                        'detail': f'Improving ({gm_curr*100:.1f}% vs {gm_prev*100:.1f}%)'})
                        else:
                            efficiency['items'].append({'name': 'Gross Margin', 'status': 'fail',
                                                        'detail': f'Declining ({gm_curr*100:.1f}% vs {gm_prev*100:.1f}%)'})
                    else:
                        efficiency['items'].append({'name': 'Gross Margin', 'status': 'na', 'detail': 'Cannot calculate'})
                except:
                    efficiency['items'].append({'name': 'Gross Margin', 'status': 'na', 'detail': 'Error'})
            else:
                efficiency['items'].append({'name': 'Gross Margin', 'status': 'na', 'detail': 'Data missing'})
            
            # Asset turnover improving
            if rev_key and asset_key and len(cols) > 1:
                try:
                    rev_c = income_df.loc[rev_key, cols[0]]
                    rev_p = income_df.loc[rev_key, cols[1]]
                    a_c = balance_df.loc[asset_key, balance_df.columns[0]]
                    a_p = balance_df.loc[asset_key, balance_df.columns[1]]
                    if all(pd.notna(x) and x > 0 for x in [rev_c, a_c, rev_p, a_p]):
                        at_curr = rev_c / a_c
                        at_prev = rev_p / a_p
                        if at_curr > at_prev:
                            total_score += 1
                            efficiency['score'] += 1
                            efficiency['items'].append({'name': 'Asset Turnover', 'status': 'pass',
                                                        'detail': f'Improving ({at_curr:.3f} vs {at_prev:.3f})'})
                        else:
                            efficiency['items'].append({'name': 'Asset Turnover', 'status': 'fail',
                                                        'detail': f'Declining ({at_curr:.3f} vs {at_prev:.3f})'})
                    else:
                        efficiency['items'].append({'name': 'Asset Turnover', 'status': 'na', 'detail': 'Cannot calculate'})
                except:
                    efficiency['items'].append({'name': 'Asset Turnover', 'status': 'na', 'detail': 'Error'})
            else:
                efficiency['items'].append({'name': 'Asset Turnover', 'status': 'na', 'detail': 'Data missing'})
            
            # Build breakdown
            def get_stars(score, max_score):
                filled = score
                empty = max_score - score
                return '★' * filled + '☆' * empty
            
            breakdown = {
                'total': f'{total_score} / 9',
                'profitability': {
                    'stars': get_stars(profitability['score'], 4),
                    'score': f'{profitability["score"]} / 4',
                    'items': profitability['items']
                },
                'leverage': {
                    'stars': get_stars(leverage['score'], 3),
                    'score': f'{leverage["score"]} / 3',
                    'items': leverage['items']
                },
                'efficiency': {
                    'stars': get_stars(efficiency['score'], 2),
                    'score': f'{efficiency["score"]} / 2',
                    'items': efficiency['items']
                }
            }
            
            if total_score >= 7:
                rating, color = '🟢 STRONG', '#10b981'
            elif total_score >= 4:
                rating, color = '🟡 AVERAGE', '#f59e0b'
            else:
                rating, color = '🔴 WEAK', '#ef4444'
            
            return {
                'score': total_score,
                'rating': rating,
                'color': color,
                'breakdown': breakdown,
                'details': [f"{item['name']}: {'✅' if item['status']=='pass' else '❌' if item['status']=='fail' else '⚠️'} {item['detail']}" 
                           for cat in [profitability, leverage, efficiency] 
                           for item in cat['items']],
                'error': False
            }
            
        except Exception as e:
            return {'score': 0, 'rating': 'N/A', 'details': [f'Error: {str(e)[:50]}'],
                    'breakdown': {}, 'error': True}