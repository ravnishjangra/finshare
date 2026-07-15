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
        # Default return when insufficient data or market closed
        default_return = {
            'score': 50, 'max_score': 100,
            'sentiment': '⚪ Neutral', 'color': '#94a3b8',
            'advice': 'Insufficient data or market closed. Default neutral sentiment.',
            'factors': {'Momentum': 12.5, 'Volatility': 12.5, 'Volume': 7.5, 'RSI': 7.5, 'MA Distance': 5, 'Drawdown': 5}
        }
        
        if prices_df is None or prices_df.empty or len(prices_df) < 20:
            return default_return
        
        close = prices_df['Close']
        volume = prices_df['Volume'] if 'Volume' in prices_df.columns else None
        
        # Check if market is closed (all volume = 0 or NaN)
        if volume is not None and (volume.tail(5).sum() == 0 or volume.isna().all()):
            volume = None
        
        scores = {}
        
        # 1. Price Momentum (25 points)
        try:
            high_52w = info.get('fiftyTwoWeekHigh', close.max())
            low_52w = info.get('fiftyTwoWeekLow', close.min())
            current = close.iloc[-1]
            
            if high_52w and low_52w and high_52w != low_52w and pd.notna(current):
                momentum_score = ((current - low_52w) / (high_52w - low_52w)) * 25
                momentum_score = max(0, min(25, momentum_score))
            else:
                momentum_score = 12.5
        except:
            momentum_score = 12.5
        scores['Momentum'] = round(float(momentum_score), 1) if pd.notna(momentum_score) else 12.5
        
        # 2. Volatility (25 points)
        try:
            returns = close.pct_change().dropna()
            if len(returns) > 20:
                vol_20d = returns.tail(20).std() * np.sqrt(252) * 100
                vol_60d = returns.tail(60).std() * np.sqrt(252) * 100 if len(returns) >= 60 else vol_20d
                
                if pd.notna(vol_20d) and pd.notna(vol_60d) and vol_60d > 0:
                    if vol_20d > vol_60d * 1.3: vol_score = 5
                    elif vol_20d > vol_60d * 1.1: vol_score = 10
                    elif vol_20d < vol_60d * 0.7: vol_score = 22
                    elif vol_20d < vol_60d * 0.9: vol_score = 18
                    else: vol_score = 15
                else:
                    vol_score = 15
            else:
                vol_score = 12.5
        except:
            vol_score = 12.5
        scores['Volatility'] = round(float(vol_score), 1)
        
        # 3. Volume Momentum (15 points)
        try:
            if volume is not None and len(volume) >= 20:
                avg_vol_5 = volume.tail(5).mean()
                avg_vol_20 = volume.tail(20).mean()
                price_5d_ret = (close.iloc[-1] / close.iloc[-5] - 1) if len(close) >= 5 else 0
                
                if pd.notna(avg_vol_5) and pd.notna(avg_vol_20) and avg_vol_20 > 0:
                    if avg_vol_5 > avg_vol_20 * 1.2 and price_5d_ret > 0: vol_momentum_score = 12
                    elif avg_vol_5 > avg_vol_20 * 1.2 and price_5d_ret < 0: vol_momentum_score = 3
                    elif avg_vol_5 < avg_vol_20 * 0.8: vol_momentum_score = 7
                    else: vol_momentum_score = 8
                else:
                    vol_momentum_score = 7.5
            else:
                vol_momentum_score = 7.5
        except:
            vol_momentum_score = 7.5
        scores['Volume'] = round(float(vol_momentum_score), 1)
        
        # 4. RSI (15 points)
        try:
            if len(close) >= 14:
                delta = close.diff()
                gain = delta.clip(lower=0).rolling(14).mean()
                loss = (-delta.clip(upper=0)).rolling(14).mean()
                rs = gain / loss.replace(0, np.nan)
                rsi = 100 - (100 / (1 + rs))
                rsi_now = rsi.iloc[-1]
                
                if pd.notna(rsi_now) and not np.isnan(rsi_now):
                    if rsi_now > 70: rsi_score = 13
                    elif rsi_now > 60: rsi_score = 10
                    elif rsi_now > 40: rsi_score = 7
                    elif rsi_now > 30: rsi_score = 4
                    else: rsi_score = 2
                else:
                    rsi_score = 7.5
            else:
                rsi_score = 7.5
        except:
            rsi_score = 7.5
        scores['RSI'] = round(float(rsi_score), 1)
        
        # 5. Moving Average Distance (10 points)
        try:
            if len(close) >= 50:
                sma20 = close.rolling(20).mean().iloc[-1]
                if pd.notna(sma20) and sma20 > 0:
                    price_vs_sma20 = ((close.iloc[-1] / sma20) - 1) * 100
                    if price_vs_sma20 > 5: ma_score = 9
                    elif price_vs_sma20 > 2: ma_score = 7
                    elif price_vs_sma20 > -2: ma_score = 5
                    elif price_vs_sma20 > -5: ma_score = 3
                    else: ma_score = 1
                else:
                    ma_score = 5
            else:
                ma_score = 5
        except:
            ma_score = 5
        scores['MA Distance'] = round(float(ma_score), 1)
        
        # 6. Drawdown (10 points)
        try:
            if len(close) >= 60:
                peak_60d = close.tail(60).max()
                if pd.notna(peak_60d) and peak_60d > 0:
                    drawdown = ((close.iloc[-1] - peak_60d) / peak_60d) * 100
                    if drawdown > -2: dd_score = 9
                    elif drawdown > -5: dd_score = 7
                    elif drawdown > -10: dd_score = 5
                    elif drawdown > -20: dd_score = 3
                    else: dd_score = 1
                else:
                    dd_score = 5
            else:
                dd_score = 5
        except:
            dd_score = 5
        scores['Drawdown'] = round(float(dd_score), 1)
        
        # Total score with NaN protection
        total = 0
        count = 0
        for v in scores.values():
            if pd.notna(v) and not np.isnan(v):
                total += v
                count += 1
        
        if count > 0:
            total = (total / count) * 6  # Scale to 100
        else:
            total = 50
        
        total = max(0, min(100, total))
        if np.isnan(total) or total <= 0:
            total = 50
        
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
            'score': int(round(total)),
            'max_score': 100,
            'sentiment': sentiment,
            'color': color,
            'advice': advice,
            'factors': {k: round(float(v), 1) if pd.notna(v) and not np.isnan(v) else 0 for k, v in scores.items()}
        }