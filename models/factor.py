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
        """
        Calculate factor exposures from price history and fundamentals.
        
        Args:
            prices_df: DataFrame with 'Close' column (5 years of daily data)
            info: dict from yfinance (market cap, sector, etc.)
            ratios: dict of calculated financial ratios
        
        Returns:
            dict of factor exposures with scores and details
        """
        exposures = {}
        
        if prices_df is None or prices_df.empty or len(prices_df) < 252:
            return FactorInvesting._fallback_exposures(info, ratios)
        
        close = prices_df['Close']
        
        # ===== SIZE FACTOR =====
        exposures['Size'] = FactorInvesting._calculate_size(info)
        
        # ===== VALUE FACTOR =====
        exposures['Value'] = FactorInvesting._calculate_value(ratios, info)
        
        # ===== MOMENTUM FACTOR =====
        exposures['Momentum'] = FactorInvesting._calculate_momentum(close)
        
        # ===== QUALITY FACTOR =====
        exposures['Quality'] = FactorInvesting._calculate_quality(ratios, close)
        
        # ===== LOW VOLATILITY FACTOR =====
        exposures['Low Volatility'] = FactorInvesting._calculate_low_volatility(close, info)
        
        return exposures
    
    @staticmethod
    def _calculate_size(info):
        """Size factor based on market cap"""
        mcap = info.get('marketCap', 0) or 0
        
        if mcap > 1e12:  # > $1 Trillion / ₹1 Lakh Cr
            return {
                'score': 90,
                'classification': 'Mega Cap',
                'detail': f'MCap: ${mcap/1e12:.1f}T' if mcap > 1e12 else f'MCap: ₹{mcap/1e7:.0f} Cr',
                'color': '#94a3b8'
            }
        elif mcap > 1e11:  # > $100 Billion
            return {
                'score': 75,
                'classification': 'Large Cap',
                'detail': f'MCap: ${mcap/1e9:.0f}B' if mcap > 1e9 else f'MCap: ₹{mcap/1e7:.0f} Cr',
                'color': '#667eea'
            }
        elif mcap > 2e10:  # > $20 Billion
            return {
                'score': 55,
                'classification': 'Mid Cap',
                'detail': f'MCap: ${mcap/1e9:.0f}B',
                'color': '#f59e0b'
            }
        elif mcap > 2e9:  # > $2 Billion
            return {
                'score': 35,
                'classification': 'Small Cap',
                'detail': f'MCap: ${mcap/1e9:.1f}B',
                'color': '#10b981'
            }
        else:
            return {
                'score': 15,
                'classification': 'Micro Cap',
                'detail': f'MCap: ${mcap/1e6:.0f}M',
                'color': '#ef4444'
            }
    
    @staticmethod
    def _calculate_value(ratios, info):
        """Value factor - how cheap is the stock?"""
        pe = ratios.get('P/E Ratio')
        pb = ratios.get('P/B Ratio')
        de = ratios.get('Debt to Equity')
        
        score = 50  # Neutral start
        signals = []
        
        # P/E based scoring
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
        
        # P/B based scoring
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
        
        # D/E adjustment
        if de is not None:
            if de < 0.5:
                score += 5
            elif de > 2:
                score -= 10
        
        score = max(0, min(100, score))
        
        if score >= 80:
            classification = 'Deep Value'
            color = '#10b981'
        elif score >= 60:
            classification = 'Value'
            color = '#34d399'
        elif score >= 40:
            classification = 'Fair Value'
            color = '#f59e0b'
        elif score >= 20:
            classification = 'Growth'
            color = '#f97316'
        else:
            classification = 'Expensive'
            color = '#ef4444'
        
        return {
            'score': score,
            'classification': classification,
            'detail': ' | '.join(signals[:3]),
            'color': color
        }
    
    @staticmethod
    def _calculate_momentum(close):
        """Momentum factor using 1, 3, 6, 12 month returns"""
        try:
            if len(close) < 252:
                return {'score': 50, 'classification': 'Insufficient Data', 'detail': 'Need 1 year of data', 'color': '#94a3b8'}
            
            current = close.iloc[-1]
            
            # Calculate returns for different periods
            returns = {}
            for period, days, weight in [('1M', 21, 0.15), ('3M', 63, 0.25), ('6M', 126, 0.30), ('12M', 252, 0.30)]:
                if len(close) >= days:
                    past = close.iloc[-days]
                    ret = ((current - past) / past) * 100
                    returns[period] = ret
            
            if not returns:
                return {'score': 50, 'classification': 'Neutral', 'detail': 'No momentum data', 'color': '#94a3b8'}
            
            # Weighted momentum score
            weights = {'1M': 0.15, '3M': 0.25, '6M': 0.30, '12M': 0.30}
            weighted_return = sum(returns.get(p, 0) * weights.get(p, 0) for p in returns)
            
            # Convert to 0-100 score
            if weighted_return > 50:
                score = 95
            elif weighted_return > 30:
                score = 85
            elif weighted_return > 15:
                score = 75
            elif weighted_return > 5:
                score = 60
            elif weighted_return > -5:
                score = 50
            elif weighted_return > -15:
                score = 35
            elif weighted_return > -30:
                score = 20
            else:
                score = 10
            
            # Calculate trend consistency
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
            else:
                trend = 'N/A'
            
            if score >= 80:
                classification = 'Strong Momentum'
                color = '#10b981'
            elif score >= 60:
                classification = 'Positive'
                color = '#34d399'
            elif score >= 40:
                classification = 'Neutral'
                color = '#f59e0b'
            elif score >= 20:
                classification = 'Negative'
                color = '#f97316'
            else:
                classification = 'Weak'
                color = '#ef4444'
            
            detail_parts = [f"{p}: {returns[p]:+.1f}%" for p in ['6M', '12M'] if p in returns]
            detail_parts.append(trend)
            
            return {
                'score': score,
                'classification': classification,
                'detail': ' | '.join(detail_parts),
                'color': color,
                'returns': returns
            }
            
        except Exception:
            return {'score': 50, 'classification': 'Error', 'detail': 'Calculation error', 'color': '#94a3b8'}
    
    @staticmethod
    def _calculate_quality(ratios, close):
        """Quality factor - profitability and stability"""
        roe = ratios.get('ROE')
        roa = ratios.get('ROA')
        net_margin = ratios.get('Net Profit Margin')
        de = ratios.get('Debt to Equity')
        
        score = 50
        signals = []
        
        # ROE scoring (most important)
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
        
        # Net Margin
        if net_margin is not None:
            if net_margin > 20:
                score += 10
                signals.append(f'High Margin: {net_margin:.1f}%')
            elif net_margin > 10:
                score += 5
            elif net_margin < 0:
                score -= 10
                signals.append(f'Negative Margin')
        
        # ROA
        if roa is not None:
            if roa > 10:
                score += 5
            elif roa < 0:
                score -= 5
        
        # Debt penalty
        if de is not None:
            if de > 2:
                score -= 10
                signals.append(f'High Debt: D/E={de:.2f}')
            elif de > 1:
                score -= 3
        
        # Earnings stability (from price volatility)
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
        
        if score >= 80:
            classification = 'Excellent'
            color = '#10b981'
        elif score >= 60:
            classification = 'High Quality'
            color = '#34d399'
        elif score >= 40:
            classification = 'Average'
            color = '#f59e0b'
        elif score >= 20:
            classification = 'Below Average'
            color = '#f97316'
        else:
            classification = 'Poor'
            color = '#ef4444'
        
        return {
            'score': score,
            'classification': classification,
            'detail': ' | '.join(signals[:3]),
            'color': color
        }
    
    @staticmethod
    def _calculate_low_volatility(close, info):
        """Low Volatility factor - beta and price stability"""
        beta = info.get('beta', 1.0) or 1.0
        
        # Calculate annualized volatility
        if close is not None and len(close) >= 252:
            daily_returns = close.pct_change().dropna()
            if len(daily_returns) > 0:
                ann_vol = daily_returns.std() * np.sqrt(252) * 100
            else:
                ann_vol = 30  # Default
        else:
            ann_vol = 30
        
        # Score based on volatility and beta
        vol_score = max(0, 100 - ann_vol * 2)  # Lower vol = higher score
        beta_score = max(0, 100 - abs(beta - 1) * 40)  # Beta near 1 is neutral
        
        score = int(vol_score * 0.5 + beta_score * 0.3 + 20)  # Base of 20
        score = max(0, min(100, score))
        
        signals = [f'Vol: {ann_vol:.1f}%', f'Beta: {beta:.2f}']
        
        if ann_vol < 20:
            classification = 'Very Low Risk'
            color = '#10b981'
        elif ann_vol < 30:
            classification = 'Low Risk'
            color = '#34d399'
        elif ann_vol < 40:
            classification = 'Moderate Risk'
            color = '#f59e0b'
        elif ann_vol < 55:
            classification = 'High Risk'
            color = '#f97316'
        else:
            classification = 'Very High Risk'
            color = '#ef4444'
        
        return {
            'score': score,
            'classification': classification,
            'detail': ' | '.join(signals),
            'color': color,
            'volatility': ann_vol,
            'beta': beta
        }
    
    @staticmethod
    def _fallback_exposures(info, ratios):
        """Fallback when price data is insufficient"""
        exposures = {}
        exposures['Size'] = FactorInvesting._calculate_size(info)
        exposures['Value'] = FactorInvesting._calculate_value(ratios, info)
        exposures['Momentum'] = {'score': 50, 'classification': 'No Data', 'detail': 'Need 1yr price history', 'color': '#94a3b8'}
        exposures['Quality'] = FactorInvesting._calculate_quality(ratios, None)
        exposures['Low Volatility'] = {
            'score': 50, 'classification': 'No Data', 
            'detail': f"Beta: {info.get('beta', 'N/A')}", 
            'color': '#94a3b8',
            'volatility': None, 'beta': info.get('beta')
        }
        return exposures
    
    @staticmethod
    def get_factor_summary(exposures):
        """Generate overall factor profile summary"""
        scores = []
        for factor, data in exposures.items():
            if factor == 'Size':
                scores.append(f"{data['classification']}")
            elif data.get('score'):
                scores.append(f"{factor}: {data['score']}/100")
        
        return {
            'factors': exposures,
            'avg_score': np.mean([e['score'] for e in exposures.values() if e.get('score')]),
            'strongest': max(exposures.items(), key=lambda x: x[1].get('score', 0))[0] if exposures else None,
            'weakest': min(exposures.items(), key=lambda x: x[1].get('score', 0))[0] if exposures else None,
        }


def create_factor_investing_dashboard(analyzer):
    """Render the Factor Investing dashboard"""
    import streamlit as st
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    st.markdown('<div class="section-header">🎯 Quantitative Factor Investing</div>', unsafe_allow_html=True)
    st.caption("Fama-French style factor analysis using 5-year returns and fundamentals")
    
    info = analyzer.financials.get('info', {})
    ratios = analyzer.ratios
    prices = analyzer.financials.get('prices')
    
    exposures = FactorInvesting.analyze_factor_exposure(prices, info, ratios)
    
    # Display factor cards
    st.markdown("### 📊 Factor Exposure Scores")
    cols = st.columns(5)
    
    for col, (factor, data) in zip(cols, exposures.items()):
        with col:
            score = data.get('score', 'N/A')
            classification = data.get('classification', 'N/A')
            color = data.get('color', '#94a3b8')
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1e293b, #0f172a); border: 2px solid {color}; 
                        padding: 1rem; border-radius: 12px; text-align: center; min-height: 160px;">
                <div style="font-size: 0.75rem; color: #94a3b8; margin-bottom: 0.5rem;">{factor}</div>
                <div style="font-size: 2rem; font-weight: 900; color: {color};">{score}</div>
                <div style="font-size: 0.85rem; font-weight: 600; color: {color};">{classification}</div>
                <div style="font-size: 0.65rem; color: #94a3b8; margin-top: 0.5rem;">{data.get('detail', '')[:60]}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Factor descriptions
    with st.expander("📖 What do these factors mean?"):
        for factor, desc in FactorInvesting.FACTOR_DESCRIPTIONS.items():
            st.markdown(f"**{factor}**: {desc}")
    
    # Overall summary
    st.markdown("### 🎯 Overall Factor Profile")
    summary = FactorInvesting.get_factor_summary(exposures)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Average Score", f"{summary['avg_score']:.0f}/100")
    with col2:
        st.metric("Strongest Factor", summary['strongest'])
    with col3:
        st.metric("Weakest Factor", summary['weakest'])
    
    # Radar chart
    categories = list(exposures.keys())
    scores = [exposures[cat].get('score', 50) for cat in categories]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        name='Factor Exposure',
        line=dict(color='#667eea', width=2),
        fillcolor='rgba(102,126,234,0.3)'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        height=400,
        template='plotly_white'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed breakdown
    st.markdown("### 📈 Factor Details")
    for factor, data in exposures.items():
        with st.expander(f"{factor}: {data.get('classification', 'N/A')} ({data.get('score', 'N/A')}/100)"):
            st.write(f"**{data.get('detail', 'No details')}**")
            if factor == 'Momentum' and 'returns' in data:
                returns = data['returns']
                if returns:
                    fig = go.Figure()
                    periods = list(returns.keys())
                    values = list(returns.values())
                    colors = ['#10b981' if v > 0 else '#ef4444' for v in values]
                    fig.add_trace(go.Bar(x=periods, y=values, marker_color=colors,
                                        text=[f'{v:+.1f}%' for v in values], textposition='outside'))
                    fig.add_hline(y=0, line_color='#94a3b8', line_width=1)
                    fig.update_layout(title='Momentum Returns by Period', template='plotly_white', height=300)
                    st.plotly_chart(fig, use_container_width=True)