"""Fama-French Factor Analysis - FIXED"""
class FactorInvesting:
    FACTORS = {
        'Value': "High Book-to-Market minus Low",
        'Size': "Small-cap minus Large-cap (SMB)",
        'Momentum': "Winners minus Losers (past 12 months)",
        'Quality': "High ROE, Low Debt minus Low ROE, High Debt",
        'Low Volatility': "Low Beta minus High Beta",
    }
    
    @staticmethod
    def analyze_factor_exposure(analyzer):
        exposures = {}
        # SAFELY get info dict
        info = analyzer.financials.get('info', {}) if hasattr(analyzer, 'financials') else {}
        if not isinstance(info, dict):
            info = {}
        ratios = analyzer.ratios if hasattr(analyzer, 'ratios') else {}
        prices = analyzer.financials.get('prices', None) if hasattr(analyzer, 'financials') else None
        
        pb = ratios.get('P/B Ratio') if isinstance(ratios, dict) else None
        if pb and pb > 0:
            if pb < 1.5: exposures['Value'] = {'score': 'Deep Value', 'detail': f'P/B: {pb:.1f}', 'color': '#10b981'}
            elif pb < 3: exposures['Value'] = {'score': 'Fair Value', 'detail': f'P/B: {pb:.1f}', 'color': '#f59e0b'}
            else: exposures['Value'] = {'score': 'Growth', 'detail': f'P/B: {pb:.1f}', 'color': '#ef4444'}
        
        # SAFELY get market cap
        mcap = 0
        if hasattr(analyzer, 'live_price_data') and isinstance(analyzer.live_price_data, dict):
            mcap = analyzer.live_price_data.get('market_cap', 0) or 0
        if mcap == 0 and info:
            mcap = info.get('marketCap', 0) or 0
        
        if mcap > 0:
            if mcap > 1e11: exposures['Size'] = {'score': 'Mega Cap', 'detail': analyzer._format_amount(mcap), 'color': '#94a3b8'}
            elif mcap > 1e10: exposures['Size'] = {'score': 'Large Cap', 'detail': analyzer._format_amount(mcap), 'color': '#667eea'}
            elif mcap > 2e9: exposures['Size'] = {'score': 'Mid Cap', 'detail': analyzer._format_amount(mcap), 'color': '#f59e0b'}
            else: exposures['Size'] = {'score': 'Small Cap', 'detail': analyzer._format_amount(mcap), 'color': '#10b981'}
        
        if prices is not None and hasattr(prices, 'columns') and 'Close' in prices.columns and len(prices) >= 252:
            try:
                ret_12m = (prices['Close'].iloc[-1] / prices['Close'].iloc[-252] - 1) * 100
                if ret_12m > 30: exposures['Momentum'] = {'score': 'Strong', 'detail': f'12M: {ret_12m:.0f}%', 'color': '#10b981'}
                elif ret_12m > 10: exposures['Momentum'] = {'score': 'Positive', 'detail': f'12M: {ret_12m:.0f}%', 'color': '#667eea'}
                elif ret_12m > -10: exposures['Momentum'] = {'score': 'Neutral', 'detail': f'12M: {ret_12m:.0f}%', 'color': '#f59e0b'}
                else: exposures['Momentum'] = {'score': 'Negative', 'detail': f'12M: {ret_12m:.0f}%', 'color': '#ef4444'}
            except: pass
        
        roe = ratios.get('ROE') if isinstance(ratios, dict) else None
        de = ratios.get('Debt to Equity') if isinstance(ratios, dict) else None
        if roe is not None and de is not None:
            if roe > 20 and de < 0.5: exposures['Quality'] = {'score': 'High Quality', 'detail': f'ROE: {roe:.0f}%, D/E: {de:.1f}', 'color': '#10b981'}
            elif roe > 10 and de < 1.5: exposures['Quality'] = {'score': 'Moderate', 'detail': f'ROE: {roe:.0f}%, D/E: {de:.1f}', 'color': '#f59e0b'}
            else: exposures['Quality'] = {'score': 'Low', 'detail': f'ROE: {roe:.0f}%, D/E: {de:.1f}', 'color': '#ef4444'}
        
        beta = 1.0
        if hasattr(analyzer, 'live_price_data') and isinstance(analyzer.live_price_data, dict):
            beta = analyzer.live_price_data.get('beta', 1.0) or 1.0
        if beta == 1.0 and info:
            beta = info.get('beta', 1.0) or 1.0
        
        if beta < 0.7: exposures['Low Vol'] = {'score': 'Very Low', 'detail': f'Beta: {beta:.2f}', 'color': '#10b981'}
        elif beta < 1.0: exposures['Low Vol'] = {'score': 'Low', 'detail': f'Beta: {beta:.2f}', 'color': '#667eea'}
        elif beta < 1.3: exposures['Low Vol'] = {'score': 'Moderate', 'detail': f'Beta: {beta:.2f}', 'color': '#f59e0b'}
        else: exposures['Low Vol'] = {'score': 'High', 'detail': f'Beta: {beta:.2f}', 'color': '#ef4444'}
        
        return exposures