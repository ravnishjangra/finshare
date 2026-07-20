"""Technical Analysis Dashboard

Covers trend (SMA/EMA, Bollinger Bands, Golden/Death Cross), momentum
(RSI, MACD, Stochastic Oscillator), trend strength (ADX/DMI), and
volume (volume bars + volume MA + On-Balance Volume) and volatility
(ATR%, rolling annualized historical volatility, Bollinger Band width).
No external TA library is used (none is in requirements.txt), so every
indicator below is computed directly from OHLCV with pandas/numpy.
"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from theme import COLORS, style_fig, status_pill, metric_card


def _wilder_smooth(series, period):
    """Wilder's smoothing (used by RSI/ATR/ADX) - an EMA variant with alpha=1/period."""
    return series.ewm(alpha=1 / period, adjust=False).mean()


def _compute_adx(high, low, close, period=14):
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=high.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=high.index)

    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)

    atr = _wilder_smooth(tr, period)
    plus_di = 100 * _wilder_smooth(plus_dm, period) / atr.replace(0, np.nan)
    minus_di = 100 * _wilder_smooth(minus_dm, period) / atr.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = _wilder_smooth(dx.fillna(0), period)
    return plus_di, minus_di, adx, atr


def _compute_stochastic(high, low, close, k_period=14, d_period=3):
    lowest_low = low.rolling(k_period).min()
    highest_high = high.rolling(k_period).max()
    percent_k = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)
    percent_d = percent_k.rolling(d_period).mean()
    return percent_k, percent_d


def _compute_obv(close, volume):
    direction = np.sign(close.diff().fillna(0))
    return (direction * volume).fillna(0).cumsum()


def create_technical_dashboard(analyzer):
    st.markdown('<div class="section-header">📈 Technical Analysis</div>', unsafe_allow_html=True)
    prices = analyzer.financials.get('prices')
    if prices is None or prices.empty:
        st.warning("No price data.")
        return

    close = prices['Close']
    high = prices['High'] if 'High' in prices.columns else close
    low = prices['Low'] if 'Low' in prices.columns else close
    volume = prices['Volume'] if 'Volume' in prices.columns else pd.Series(0, index=close.index)
    cur = analyzer.currency_symbol
    open_price = prices['Open'] if 'Open' in prices.columns else close

    # ── Momentum: RSI ──
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain / loss))

    # ── Momentum: MACD ──
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    hist = macd - signal

    # ── Momentum: Stochastic Oscillator ──
    stoch_k, stoch_d = _compute_stochastic(high, low, close)

    # ── Trend: SMA/EMA + Bollinger Bands ──
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    upper = sma20 + 2 * std20
    lower = sma20 - 2 * std20

    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()

    # ── Trend Strength: ADX/DMI ──
    plus_di, minus_di, adx, atr = _compute_adx(high, low, close)
    atr_pct = (atr / close * 100)

    # ── Volatility: rolling annualized historical volatility ──
    daily_ret = close.pct_change()
    hist_vol_20 = daily_ret.rolling(20).std() * np.sqrt(252) * 100

    # ── Volume: volume MA + OBV ──
    vol_ma20 = volume.rolling(20).mean()
    obv = _compute_obv(close, volume)

    # ── Headline metrics ──
    rsi_now = rsi.iloc[-1]
    macd_bullish = macd.iloc[-1] > signal.iloc[-1]
    macd_sig = "Bullish" if macd_bullish else "Bearish"
    macd_color = COLORS['up'] if macd_bullish else COLORS['down']
    golden_cross = sma50.iloc[-1] > sma200.iloc[-1]
    trend = "Golden Cross" if golden_cross else "Death Cross"
    trend_color = COLORS['up'] if golden_cross else COLORS['down']
    adx_now = adx.iloc[-1] if pd.notna(adx.iloc[-1]) else 0
    adx_strength = "Strong" if adx_now > 25 else ("Weak/Range" if adx_now < 20 else "Developing")
    vol_ratio = (volume.iloc[-1] / vol_ma20.iloc[-1]) if vol_ma20.iloc[-1] else 1
    stoch_now = stoch_k.iloc[-1] if pd.notna(stoch_k.iloc[-1]) else 50

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("RSI (14)", f"{rsi_now:.1f}", "Overbought" if rsi_now > 70 else ("Oversold" if rsi_now < 30 else "Neutral"))
    with col2:
        st.markdown(
            metric_card("MACD", f"{macd.iloc[-1]:.2f}", value_color=macd_color,
                        footer=status_pill(macd_sig, macd_color)),
            unsafe_allow_html=True,
        )
    col3.metric("Stochastic %K", f"{stoch_now:.0f}", "Overbought" if stoch_now > 80 else ("Oversold" if stoch_now < 20 else "Neutral"))
    col4.metric("ADX (14)", f"{adx_now:.1f}", adx_strength)
    col5.metric("ATR (14)", f"{atr_pct.iloc[-1]:.2f}%", "of price")
    col6.metric("Volume vs 20D Avg", f"{vol_ratio:.2f}x", "Elevated" if vol_ratio > 1.5 else "Normal")

    col7, col8, col9 = st.columns(3)
    with col7:
        st.markdown(
            metric_card("Trend (50/200 SMA)", trend, value_color=trend_color),
            unsafe_allow_html=True,
        )
    col8.metric("Hist. Volatility (20D, ann.)", f"{hist_vol_20.iloc[-1]:.1f}%")
    col9.metric("Close", f"{cur}{close.iloc[-1]:.2f}")

    st.markdown("---")
    idx = slice(-180, None)

    # ===== CHART 1: Price & Bollinger Bands =====
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=close.index[idx], y=upper.iloc[idx],
        line=dict(color=COLORS['text_3'], width=1, dash='dash'), name='Upper BB'))
    fig1.add_trace(go.Scatter(x=close.index[idx], y=sma20.iloc[idx],
        line=dict(color=COLORS['neutral'], width=1.5), name='20 MA'))
    fig1.add_trace(go.Scatter(x=close.index[idx], y=lower.iloc[idx],
        line=dict(color=COLORS['text_3'], width=1, dash='dash'),
        fill='tonexty', fillcolor='rgba(109,94,248,0.06)', name='Lower BB'))
    fig1.add_trace(go.Scatter(x=close.index[idx], y=sma50.iloc[idx],
        line=dict(color=COLORS['accent_2'], width=1, dash='dot'), name='50 SMA'))
    fig1.add_trace(go.Scatter(x=close.index[idx], y=close.iloc[idx],
        line=dict(color=COLORS['accent_1'], width=2), name='Price'))
    fig1.update_layout(height=350, title="Price & Bollinger Bands",
        margin=dict(l=10, r=10, t=35, b=10), hovermode='x unified',
        legend=dict(orientation='h', y=1.05))
    st.plotly_chart(style_fig(fig1), use_container_width=True)

    # ===== CHART 2: Volume + OBV =====
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    vol_colors = [COLORS['up'] if c >= o else COLORS['down']
                  for c, o in zip(close.iloc[idx], open_price.iloc[idx])]
    fig2.add_trace(go.Bar(x=volume.index[idx], y=volume.iloc[idx],
        marker_color=vol_colors, name='Volume', opacity=0.7), secondary_y=False)
    fig2.add_trace(go.Scatter(x=vol_ma20.index[idx], y=vol_ma20.iloc[idx],
        line=dict(color=COLORS['neutral'], width=1.5), name='Vol 20D Avg'), secondary_y=False)
    fig2.add_trace(go.Scatter(x=obv.index[idx], y=obv.iloc[idx],
        line=dict(color=COLORS['accent_3'], width=1.5), name='OBV'), secondary_y=True)
    fig2.update_layout(height=280, title="Volume & On-Balance Volume",
        margin=dict(l=10, r=10, t=35, b=10), hovermode='x unified',
        legend=dict(orientation='h', y=1.05))
    fig2.update_yaxes(title_text="Volume", secondary_y=False)
    fig2.update_yaxes(title_text="OBV", secondary_y=True)
    st.plotly_chart(style_fig(fig2), use_container_width=True)

    # ===== CHART 3: RSI + Stochastic (combined oscillators) =====
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=rsi.index[idx], y=rsi.iloc[idx],
        line=dict(color=COLORS['accent_3'], width=2), name='RSI'))
    fig3.add_trace(go.Scatter(x=stoch_k.index[idx], y=stoch_k.iloc[idx],
        line=dict(color=COLORS['accent_1'], width=1.5, dash='dot'), name='Stoch %K'))
    fig3.add_hline(y=70, line_dash="dash", line_color=COLORS['down'],
                   annotation_text="Overbought 70")
    fig3.add_hline(y=30, line_dash="dash", line_color=COLORS['up'],
                   annotation_text="Oversold 30")
    fig3.update_layout(height=280, title="RSI (14) & Stochastic (14,3)",
        margin=dict(l=10, r=10, t=35, b=10), hovermode='x unified',
        legend=dict(orientation='h', y=1.05),
        yaxis=dict(range=[0, 100], title="Value"))
    st.plotly_chart(style_fig(fig3), use_container_width=True)

    # ===== CHART 4: MACD =====
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=macd.index[idx], y=macd.iloc[idx],
        line=dict(color=COLORS['accent_1'], width=2), name='MACD'))
    fig4.add_trace(go.Scatter(x=signal.index[idx], y=signal.iloc[idx],
        line=dict(color=COLORS['neutral'], width=1.5), name='Signal'))
    macd_colors = [COLORS['up'] if h >= 0 else COLORS['down'] for h in hist.iloc[idx]]
    fig4.add_trace(go.Bar(x=hist.index[idx], y=hist.iloc[idx],
        marker_color=macd_colors, name='Histogram'))
    fig4.update_layout(height=280, title="MACD (12,26,9)",
        margin=dict(l=10, r=10, t=35, b=10), hovermode='x unified',
        legend=dict(orientation='h', y=1.05),
        yaxis=dict(title="Value"))
    st.plotly_chart(style_fig(fig4), use_container_width=True)

    # ===== CHART 5: ATR% + Historical Volatility =====
    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(x=atr_pct.index[idx], y=atr_pct.iloc[idx],
        line=dict(color=COLORS['accent_3'], width=1.8), name='ATR %',
        fill='tozeroy', fillcolor='rgba(79,209,255,0.08)'))
    fig5.add_trace(go.Scatter(x=hist_vol_20.index[idx], y=hist_vol_20.iloc[idx],
        line=dict(color=COLORS['accent_2'], width=1.8, dash='dot'), name='Hist Vol %'))
    fig5.update_layout(height=280, title="ATR% & Historical Volatility (20D, ann.)",
        margin=dict(l=10, r=10, t=35, b=10), hovermode='x unified',
        legend=dict(orientation='h', y=1.05),
        yaxis=dict(title="%"))
    st.plotly_chart(style_fig(fig5), use_container_width=True)

    # ── ADX / DMI trend-strength panel ──
    with st.expander("📐 ADX / Directional Movement Index (Trend Strength)", expanded=False):
        fig_adx = go.Figure()
        fig_adx.add_trace(go.Scatter(x=adx.index[idx], y=adx.iloc[idx],
            line=dict(color=COLORS['accent_1'], width=2.2), name='ADX'))
        fig_adx.add_trace(go.Scatter(x=plus_di.index[idx], y=plus_di.iloc[idx],
            line=dict(color=COLORS['up'], width=1.5), name='+DI'))
        fig_adx.add_trace(go.Scatter(x=minus_di.index[idx], y=minus_di.iloc[idx],
            line=dict(color=COLORS['down'], width=1.5), name='-DI'))
        fig_adx.add_hline(y=25, line_dash="dash", line_color=COLORS['text_3'],
                          annotation_text="Trending threshold")
        fig_adx.update_layout(height=320, margin=dict(t=20, b=20),
                              yaxis=dict(title="Value"))
        st.plotly_chart(style_fig(fig_adx), use_container_width=True)
        st.caption(
            "ADX above ~25 signals a genuine trend (up or down); below ~20 suggests a range-bound market where "
            "trend-following signals (MACD, moving-average crosses) are less reliable. +DI above -DI favors an uptrend "
            "and vice versa."
        )