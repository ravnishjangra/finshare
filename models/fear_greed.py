"""Fear & Greed Index - Stock-specific sentiment gauge"""
import pandas as pd
import numpy as np

class FearGreedIndex:
    """
    0-100 scale: 0-25 = Extreme Fear, 25-45 = Fear, 45-55 = Neutral, 55-75 = Greed, 75-100 = Extreme Greed
    Based on 6 factors: Momentum, Volatility, Volume, RSI, Distance from MA, Drawdown
    """
    
    @staticmethod
    def calculate(prices_df, info):
        if prices_df is None or prices_df.empty or len(prices_df) < 60:
            return None
        
        close = prices_df['Close']
        volume = prices_df['Volume'] if 'Volume' in prices_df.columns else None
        
        scores = {}
        
        # 1. Price Momentum (25 points) - how far from 52w high/low
        high_52w = info.get('fiftyTwoWeekHigh', close.max())
        low_52w = info.get('fiftyTwoWeekLow', close.min())
        current = close.iloc[-1]
        
        if high_52w and low_52w and high_52w != low_52w:
            momentum_score = ((current - low_52w) / (high_52w - low_52w)) * 25
        else:
            momentum_score = 12.5
        scores['Momentum'] = round(momentum_score, 1)
        
        # 2. Volatility (25 points) - higher vol = more fear
        returns = close.pct_change().dropna()
        if len(returns) > 20:
            vol_20d = returns.tail(20).std() * np.sqrt(252) * 100
            vol_60d = returns.tail(60).std() * np.sqrt(252) * 100 if len(returns) >= 60 else vol_20d
            
            # Compare short-term vs medium-term volatility
            if vol_20d > vol_60d * 1.3:
                vol_score = 5  # High fear
            elif vol_20d > vol_60d * 1.1:
                vol_score = 10
            elif vol_20d < vol_60d * 0.7:
                vol_score = 22  # Low fear (stable)
            elif vol_20d < vol_60d * 0.9:
                vol_score = 18
            else:
                vol_score = 15
        else:
            vol_score = 12.5
        scores['Volatility'] = round(vol_score, 1)
        
        # 3. Volume Momentum (15 points) - rising volume with price = greed
        if volume is not None and len(volume) >= 20:
            avg_vol_5 = volume.tail(5).mean()
            avg_vol_20 = volume.tail(20).mean()
            price_5d_ret = (close.iloc[-1] / close.iloc[-5] - 1) if len(close) >= 5 else 0
            
            if avg_vol_5 > avg_vol_20 * 1.2 and price_5d_ret > 0:
                vol_momentum_score = 12  # Greed - rising volume + rising price
            elif avg_vol_5 > avg_vol_20 * 1.2 and price_5d_ret < 0:
                vol_momentum_score = 3   # Fear - high volume selling
            elif avg_vol_5 < avg_vol_20 * 0.8:
                vol_momentum_score = 7   # Low interest
            else:
                vol_momentum_score = 8
        else:
            vol_momentum_score = 7.5
        scores['Volume'] = round(vol_momentum_score, 1)
        
        # 4. RSI (15 points)
        if len(close) >= 14:
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_now = rsi.iloc[-1]
            
            if rsi_now > 70:
                rsi_score = 13  # Greed (overbought)
            elif rsi_now > 60:
                rsi_score = 10
            elif rsi_now > 40:
                rsi_score = 7
            elif rsi_now > 30:
                rsi_score = 4
            else:
                rsi_score = 2  # Fear (oversold)
        else:
            rsi_score = 7.5
        scores['RSI'] = round(rsi_score, 1)
        
        # 5. Moving Average Distance (10 points)
        if len(close) >= 50:
            sma20 = close.rolling(20).mean().iloc[-1]
            sma50 = close.rolling(50).mean().iloc[-1]
            price_vs_sma20 = ((current / sma20) - 1) * 100
            
            if price_vs_sma20 > 5:
                ma_score = 9   # Greed - way above MA
            elif price_vs_sma20 > 2:
                ma_score = 7
            elif price_vs_sma20 > -2:
                ma_score = 5
            elif price_vs_sma20 > -5:
                ma_score = 3
            else:
                ma_score = 1   # Fear - way below MA
        else:
            ma_score = 5
        scores['MA Distance'] = round(ma_score, 1)
        
        # 6. Drawdown (10 points) - current drawdown from peak
        if len(close) >= 60:
            peak_60d = close.tail(60).max()
            drawdown = ((current - peak_60d) / peak_60d) * 100
            
            if drawdown > -2:
                dd_score = 9   # Near highs = greed
            elif drawdown > -5:
                dd_score = 7
            elif drawdown > -10:
                dd_score = 5
            elif drawdown > -20:
                dd_score = 3
            else:
                dd_score = 1   # Deep drawdown = fear
        else:
            dd_score = 5
        scores['Drawdown'] = round(dd_score, 1)
        
        # Total score
        total = sum(scores.values())
        
        # Classification
        if total >= 75:
            sentiment = "🟢 Extreme Greed"
            color = '#10b981'
            advice = "Market may be overbought. Consider taking profits."
        elif total >= 55:
            sentiment = "🟡 Greed"
            color = '#34d399'
            advice = "Positive sentiment. Stay invested but cautious."
        elif total >= 45:
            sentiment = "⚪ Neutral"
            color = '#94a3b8'
            advice = "Mixed signals. Wait for clearer direction."
        elif total >= 25:
            sentiment = "🟠 Fear"
            color = '#f59e0b'
            advice = "Negative sentiment. Look for buying opportunities."
        else:
            sentiment = "🔴 Extreme Fear"
            color = '#ef4444'
            advice = "Market may be oversold. Potential buying opportunity."
        
        return {
            'score': round(total),
            'max_score': 100,
            'sentiment': sentiment,
            'color': color,
            'advice': advice,
            'factors': scores
        }