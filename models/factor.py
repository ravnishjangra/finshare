"""Quantitative Factor Investing - Fama-French style factor exposure analysis"""
import pandas as pd
import numpy as np
from scipy import stats


class FactorInvesting:
    """Calculate factor exposures using 5 years of monthly returns"""
    
    FACTOR_DESCRIPTIONS = {
        'Value': 'Low P/B, low P/E = cheap relative to fundamentals',
        'Size': 'Market cap classification (Small/Mid/Large)',
        'Momentum': 'Price trend strength over 6-12 months',
        'Quality': 'High ROE, ROA, stable earnings',
        'Low Volatility': 'Lower beta and price fluctuations',
    }
    
    @staticmethod
    def analyze_factor_exposure(prices_df, info, ratios):
        exposures = {}
        
        if prices_df is None or prices_df.empty or len(prices_df) < 252:
            return FactorInvesting._fallback_exposures(info, ratios)
        
        close = prices_df['Close']
        exposures['Size'] = FactorInvesting._calculate_size(info)
        exposures['Value'] = FactorInvesting._calculate_value(ratios, info)
        exposures['Momentum'] = FactorInvesting._calculate_momentum(close)
        exposures['Quality'] = FactorInvesting._calculate_quality(ratios, close)
        exposures['Low Volatility'] = FactorInvesting._calculate_low_volatility(close, info)
        
        return exposures
    
    @staticmethod
    def _calculate_size(info):
        """Size factor based on market cap - detects INR vs USD"""
        mcap = info.get('marketCap', 0) or 0
        currency = info.get('currency', 'USD')
        is_inr = (currency == 'INR')
        
        if is_inr:
            cr = mcap / 1e7
            if cr > 500000:
                return {'score': 95, 'classification': 'Mega Cap', 'detail': f'MCap: ₹{cr/100000:.1f}L Cr', 'color': '#94a3b8'}
            elif cr > 100000:
                return {'score': 85, 'classification': 'Mega Cap', 'detail': f'MCap: ₹{cr/100000:.1f}L Cr', 'color': '#94a3b8'}
            elif cr > 10000:
                return {'score': 70, 'classification': 'Large Cap', 'detail': f'MCap: ₹{cr:.0f} Cr', 'color': '#667eea'}
            elif cr > 2000:
                return {'score': 50, 'classification': 'Mid Cap', 'detail': f'MCap: ₹{cr:.0f} Cr', 'color': '#f59e0b'}
            elif cr > 200:
                return {'score': 30, 'classification': 'Small Cap', 'detail': f'MCap: ₹{cr:.0f} Cr', 'color': '#10b981'}
            else:
                return {'score': 15, 'classification': 'Micro Cap', 'detail': f'MCap: ₹{cr:.0f} Cr', 'color': '#ef4444'}
        else:
            if mcap > 1e12:
                return {'score': 90, 'classification': 'Mega Cap', 'detail': f'MCap: ${mcap/1e12:.1f}T', 'color': '#94a3b8'}
            elif mcap > 1e11:
                return {'score': 75, 'classification': 'Large Cap', 'detail': f'MCap: ${mcap/1e9:.0f}B', 'color': '#667eea'}
            elif mcap > 2e10:
                return {'score': 55, 'classification': 'Mid Cap', 'detail': f'MCap: ${mcap/1e9:.0f}B', 'color': '#f59e0b'}
            elif mcap > 2e9:
                return {'score': 35, 'classification': 'Small Cap', 'detail': f'MCap: ${mcap/1e9:.1f}B', 'color': '#10b981'}
            else:
                return {'score': 15, 'classification': 'Micro Cap', 'detail': f'MCap: ${mcap/1e6:.0f}M', 'color': '#ef4444'}
    
    @staticmethod
    def _calculate_value(ratios, info):
        pe = ratios.get('P/E Ratio')
        pb = ratios.get('P/B Ratio')
        de = ratios.get('Debt to Equity')
        
        score = 50
        signals = []
        
        if pe and pe > 0:
            if pe < 12:
                score += 25
                signals.append(f'Low P/E: {pe:.1f}')
            elif pe < 18:
                score += 15
                signals.append(f'Moderate P/E: {pe:.1f}')
            elif pe < 25:
                score += 5
                signals.append(f'Fair P/E: {pe:.1f}')
            else:
                score -= 10
                signals.append(f'High P/E: {pe:.1f}')
        else:
            signals.append('No P/E (negative earnings)')
            score -= 15
        
        if pb and pb > 0:
            if pb < 1.5:
                score += 20
                signals.append(f'Low P/B: {pb:.2f} (Deep Value)')
            elif pb < 3:
                score += 10
                signals.append(f'Moderate P/B: {pb:.2f}')
            elif pb < 5:
                score += 0
                signals.append(f'Fair P/B: {pb:.2f}')
            else:
                score -= 10
                signals.append(f'High P/B: {pb:.2f} (Growth)')
        
        if de is not None:
            if de < 0.5:
                score += 5
            elif de > 2:
                score -= 10
        
        score = max(0, min(100, score))
        
        if score >= 80:
            classification, color = 'Deep Value', '#10b981'
        elif score >= 60:
            classification, color = 'Value', '#34d399'
        elif score >= 40:
            classification, color = 'Fair Value', '#f59e0b'
        elif score >= 20:
            classification, color = 'Growth', '#f97316'
        else:
            classification, color = 'Expensive', '#ef4444'
        
        return {'score': score, 'classification': classification, 'detail': ' | '.join(signals[:3]), 'color': color}
    
    @staticmethod
    def _calculate_momentum(close):
        """Momentum factor - handles limited price history gracefully"""
        try:
            if close is None or len(close) < 21:
                return {'score': 50, 'classification': 'No Data', 'detail': 'Need more price history', 'color': '#94a3b8'}
            
            current = close.iloc[-1]
            returns = {}
            
            for period, days in [('1M', 21), ('3M', 63), ('6M', 126), ('12M', 252)]:
                if len(close) >= days:
                    past = close.iloc[-days]
                    if past and past > 0:
                        ret = ((current - past) / past) * 100
                        if not pd.isna(ret):
                            returns[period] = ret
            
            if not returns:
                return {'score': 50, 'classification': 'No Data', 'detail': f'Only {len(close)} days of data', 'color': '#94a3b8'}
            
            # Weighted return - normalize based on available data
            weights = {'1M': 0.25, '3M': 0.35, '6M': 0.25, '12M': 0.15}
            available_weights = {p: weights.get(p, 0.25) for p in returns}
            total_weight = sum(available_weights.values())
            
            if total_weight > 0:
                normalized = {p: w/total_weight for p, w in available_weights.items()}
                weighted_return = sum(returns.get(p, 0) * normalized.get(p, 0) for p in returns)
            else:
                weighted_return = sum(returns.values()) / len(returns)
            
            if weighted_return > 50: score = 95
            elif weighted_return > 30: score = 85
            elif weighted_return > 15: score = 75
            elif weighted_return > 5: score = 60
            elif weighted_return > -5: score = 50
            elif weighted_return > -15: score = 35
            elif weighted_return > -30: score = 20
            else: score = 10
            
            # Trend analysis
            trend = ''
            if len(close) >= 126:
                sma50 = close.rolling(50).mean()
                sma200 = close.rolling(200).mean()
                above_50 = 1 if close.iloc[-1] > sma50.iloc[-1] else 0
                above_200 = 1 if close.iloc[-1] > sma200.iloc[-1] else 0
                
                if above_50 and above_200:
                    score = min(100, score + 10)
                    trend = 'Strong Uptrend 📈'
                elif above_50:
                    trend = 'Short-term Uptrend'
                elif above_200:
                    trend = 'Long-term Support'
                else:
                    trend = 'Downtrend 📉'
                    score = max(0, score - 10)
            elif len(close) >= 50:
                sma50 = close.rolling(50).mean()
                if close.iloc[-1] > sma50.iloc[-1]:
                    trend = 'Above 50-day MA'
                else:
                    trend = 'Below 50-day MA'
            
            if score >= 80: classification, color = 'Strong Momentum', '#10b981'
            elif score >= 60: classification, color = 'Positive', '#34d399'
            elif score >= 40: classification, color = 'Neutral', '#f59e0b'
            elif score >= 20: classification, color = 'Negative', '#f97316'
            else: classification, color = 'Weak', '#ef4444'
            
            detail_parts = [f"{p}: {returns[p]:+.1f}%" for p in ['1M', '3M', '6M', '12M'] if p in returns]
            if trend:
                detail_parts.append(trend)
            if len(close) < 252:
                detail_parts.append(f'({len(close)} days)')
            
            return {'score': score, 'classification': classification, 'detail': ' | '.join(detail_parts), 'color': color, 'returns': returns}
            
        except Exception:
            return {'score': 50, 'classification': 'Error', 'detail': 'Calculation error', 'color': '#94a3b8'}
    
    @staticmethod
    def _calculate_quality(ratios, close):
        roe = ratios.get('ROE')
        roa = ratios.get('ROA')
        net_margin = ratios.get('Net Profit Margin')
        de = ratios.get('Debt to Equity')
        
        score = 50
        signals = []
        
        if roe is not None:
            if roe > 25:
                score += 25
                signals.append(f'Excellent ROE: {roe:.1f}%')
            elif roe > 15:
                score += 15
                signals.append(f'Strong ROE: {roe:.1f}%')
            elif roe > 10:
                score += 8
                signals.append(f'Good ROE: {roe:.1f}%')
            elif roe > 0:
                score += 0
                signals.append(f'Low ROE: {roe:.1f}%')
            else:
                score -= 15
                signals.append(f'Negative ROE: {roe:.1f}%')
        else:
            signals.append('ROE not available')
        
        if net_margin is not None:
            if net_margin > 20:
                score += 10
                signals.append(f'High Margin: {net_margin:.1f}%')
            elif net_margin > 10:
                score += 5
            elif net_margin < 0:
                score -= 10
                signals.append(f'Negative Margin')
        
        if roa is not None:
            if roa > 10: score += 5
            elif roa < 0: score -= 5
        
        if de is not None:
            if de > 2:
                score -= 10
                signals.append(f'High Debt: D/E={de:.2f}')
            elif de > 1:
                score -= 3
        
        if close is not None and len(close) >= 252:
            returns = close.pct_change().dropna()
            if len(returns) > 0:
                volatility = returns.std() * np.sqrt(252) * 100
                if volatility < 20:
                    score += 5
                    signals.append('Stable earnings')
                elif volatility > 50:
                    score -= 5
        
        score = max(0, min(100, score))
        
        if score >= 80: classification, color = 'Excellent', '#10b981'
        elif score >= 60: classification, color = 'High Quality', '#34d399'
        elif score >= 40: classification, color = 'Average', '#f59e0b'
        elif score >= 20: classification, color = 'Below Average', '#f97316'
        else: classification, color = 'Poor', '#ef4444'
        
        return {'score': score, 'classification': classification, 'detail': ' | '.join(signals[:3]), 'color': color}
    
    @staticmethod
    def _calculate_low_volatility(close, info):
        beta = info.get('beta', 1.0) or 1.0
        
        if close is not None and len(close) >= 252:
            daily_returns = close.pct_change().dropna()
            ann_vol = daily_returns.std() * np.sqrt(252) * 100 if len(daily_returns) > 0 else 30
        else:
            ann_vol = 30
        
        vol_score = max(0, 100 - ann_vol * 2)
        beta_score = max(0, 100 - abs(beta - 1) * 40)
        score = max(0, min(100, int(vol_score * 0.5 + beta_score * 0.3 + 20)))
        
        signals = [f'Vol: {ann_vol:.1f}%', f'Beta: {beta:.2f}']
        
        if ann_vol < 20: classification, color = 'Very Low Risk', '#10b981'
        elif ann_vol < 30: classification, color = 'Low Risk', '#34d399'
        elif ann_vol < 40: classification, color = 'Moderate Risk', '#f59e0b'
        elif ann_vol < 55: classification, color = 'High Risk', '#f97316'
        else: classification, color = 'Very High Risk', '#ef4444'
        
        return {'score': score, 'classification': classification, 'detail': ' | '.join(signals), 'color': color, 'volatility': ann_vol, 'beta': beta}
    
    @staticmethod
    def _fallback_exposures(info, ratios):
        exposures = {}
        exposures['Size'] = FactorInvesting._calculate_size(info)
        exposures['Value'] = FactorInvesting._calculate_value(ratios, info)
        exposures['Momentum'] = {'score': 50, 'classification': 'No Data', 'detail': 'Need 1yr price history', 'color': '#94a3b8'}
        exposures['Quality'] = FactorInvesting._calculate_quality(ratios, None)
        exposures['Low Volatility'] = {'score': 50, 'classification': 'No Data', 'detail': f"Beta: {info.get('beta', 'N/A')}", 'color': '#94a3b8', 'volatility': None, 'beta': info.get('beta')}
        return exposures
    
    @staticmethod
    def get_factor_summary(exposures):
        return {
            'factors': exposures,
            'avg_score': np.mean([e['score'] for e in exposures.values() if e.get('score')]),
            'strongest': max(exposures.items(), key=lambda x: x[1].get('score', 0))[0] if exposures else None,
            'weakest': min(exposures.items(), key=lambda x: x[1].get('score', 0))[0] if exposures else None,
        }