"""Financial Models Dashboard - Performance, Beneish, DuPont, Composite, Ohlson, Fear & Greed"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from models.beneish import BeneishMScore
from models.dupont import DuPontAnalysis
from models.performance_ratios import PerformanceRatios
from models.composite_score import CompositeScore
from models.piotroski import PiotroskiFScore
from models.altman import AltmanZScore
from models.ohlson import OhlsonOScore
from models.fear_greed import FearGreedIndex
from theme import COLORS, style_fig, progress_bar, card_html, status_pill

def create_financial_models_dashboard(analyzer):
    st.markdown('<div class="section-header">📊 Advanced Financial Models</div>', unsafe_allow_html=True)
    
    income = analyzer.financials.get('income')
    balance = analyzer.financials.get('balance')
    cashflow = analyzer.financials.get('cashflow')
    prices = analyzer.financials.get('prices')
    info = analyzer.financials.get('info', {})
    ratios = analyzer.ratios
    market_cap = analyzer.live_price_data.get('market_cap', 0)
    
    if income is None or income.empty:
        st.warning("Financial statements not available for advanced models.")
        return
    
    # ===== SECTION 1: FEAR & GREED INDEX =====
    st.markdown("### 😱 Fear & Greed Index")
    
    fg = FearGreedIndex.calculate(prices, info)
    if fg:
        col1, col2 = st.columns([1, 2])
        with col1:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=fg['score'],
                number={'font': {'color': fg['color'], 'size': 48, 'family': 'Inter, sans-serif'}},
                title={'text': "Fear & Greed", 'font': {'family': 'Inter, sans-serif'}},
                gauge={
                    'axis': {'range': [0, 100], 'tickcolor': COLORS['text_3']},
                    'bar': {'color': fg['color']},
                    'bgcolor': COLORS['bg_2'],
                    'steps': [
                        {'range': [0, 25], 'color': "rgba(255,93,122,0.25)"},
                        {'range': [25, 45], 'color': "rgba(245,185,66,0.25)"},
                        {'range': [45, 55], 'color': "rgba(170,177,197,0.25)"},
                        {'range': [55, 75], 'color': "rgba(94,234,212,0.25)"},
                        {'range': [75, 100], 'color': "rgba(34,211,143,0.25)"},
                    ],
                    'threshold': {'line': {'color': COLORS['text_1'], 'width': 3}, 'value': fg['score']}
                }
            ))
            fig.update_layout(height=250)
            st.plotly_chart(style_fig(fig), use_container_width=True)
            st.markdown(f"<h3 style='text-align:center;color:{fg['color']};'>{fg['sentiment']}</h3>", unsafe_allow_html=True)
            st.caption(f"💡 {fg['advice']}")
        
        with col2:
            for factor, score in fg['factors'].items():
                s = int(score) if pd.notna(score) and not np.isnan(score) else 12
                factor_color = COLORS['up'] if s > 15 else COLORS['neutral'] if s > 8 else COLORS['down']
                st.markdown(progress_bar(factor, s, 25, color=factor_color), unsafe_allow_html=True)
    
    # ===== SECTION 2: PERFORMANCE METRICS =====
    st.markdown("### 📈 Performance Metrics")
    
    risk_free = 0.06 if analyzer.currency == 'USD' else 0.07
    perf = PerformanceRatios.calculate(prices, info, risk_free_rate=risk_free)
    
    if perf:
        cols = st.columns(5)
        for col, (label, val) in zip(cols, [
            ('Annual Return', f"{perf['annual_return']}%"),
            ('Volatility', f"{perf['annual_volatility']}%"),
            ('Sharpe Ratio', f"{perf['sharpe_ratio']}"),
            ('Sortino Ratio', f"{perf['sortino_ratio']}"),
            ('Max Drawdown', f"{perf['max_drawdown']}%"),
        ]):
            with col: st.metric(label, val)
        
        cols = st.columns(5)
        for col, (label, val) in zip(cols, [
            ("Jensen's Alpha", f"{perf['jensens_alpha']}%"),
            ('Beta', f"{perf['beta']}"),
            ('Treynor Ratio', f"{perf['treynor_ratio']}"),
            ('Info Ratio*' if perf.get('information_ratio_is_approx') else 'Info Ratio', f"{perf['information_ratio']}"),
            ('Calmar Ratio', f"{perf['calmar_ratio']}"),
        ]):
            with col: st.metric(label, val)
        if perf.get('information_ratio_is_approx'):
            st.caption("*Approximate - no benchmark index series available, so this uses the stock's own volatility instead of true tracking error vs. a benchmark.")
        
        with st.expander("🔍 Risk Metrics (VaR & CVaR)"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("VaR 95%", f"{perf['var_95']}%", delta_color="inverse")
            c2.metric("VaR 99%", f"{perf['var_99']}%", delta_color="inverse")
            c3.metric("CVaR 95%", f"{perf['cvar_95']}%", delta_color="inverse")
            c4.metric("Win/Loss Ratio", f"{perf['win_loss_ratio']}")

        # ── Visualizations: risk-adjusted ratio comparison + underwater chart ──
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            ratio_names = ['Sharpe', 'Sortino', 'Treynor', 'Info Ratio', 'Calmar']
            ratio_vals = [perf['sharpe_ratio'], perf['sortino_ratio'], perf['treynor_ratio'],
                          perf['information_ratio'], perf['calmar_ratio']]
            ratio_colors = [COLORS['up'] if v >= 0 else COLORS['down'] for v in ratio_vals]

            fig = go.Figure(go.Bar(
                x=ratio_vals, y=ratio_names, orientation='h',
                marker=dict(color=ratio_colors, line=dict(color=COLORS['border_strong'], width=1)),
                text=[f"{v:.2f}" for v in ratio_vals], textposition='outside',
                textfont=dict(color=COLORS['text_1'], size=12),
            ))
            fig.add_vline(x=0, line_color=COLORS['border_strong'], line_width=1)
            fig.update_layout(
                title="Risk-Adjusted Ratios",
                height=280, margin=dict(l=10, r=30, t=45, b=20),
                xaxis=dict(title="Ratio Value", zeroline=True),
                yaxis=dict(autorange='reversed'),
                showlegend=False,
            )
            st.plotly_chart(style_fig(fig), use_container_width=True)

        with chart_col2:
            close = prices['Close']
            rets = close.pct_change().dropna()
            cum = (1 + rets).cumprod()
            running_max = cum.expanding().max()
            underwater = (cum - running_max) / running_max * 100

            fig = go.Figure(go.Scatter(
                x=underwater.index, y=underwater.values, mode='lines',
                line=dict(color=COLORS['down'], width=1.5),
                fill='tozeroy', fillcolor='rgba(255,93,122,0.18)',
                name='Drawdown',
                hovertemplate='%{x|%b %Y}: %{y:.1f}%<extra></extra>',
            ))
            fig.update_layout(
                title=f"Underwater Chart (Max DD: {perf['max_drawdown']}%)",
                height=280, margin=dict(l=10, r=20, t=45, b=20),
                yaxis=dict(title="Drawdown %", ticksuffix="%"),
                showlegend=False,
            )
            st.plotly_chart(style_fig(fig), use_container_width=True)

        # Returns distribution with VaR/CVaR markers
        with st.expander("📉 Daily Returns Distribution", expanded=False):
            close = prices['Close']
            rets = (close.pct_change().dropna() * 100)
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=rets, nbinsx=60, marker=dict(color=COLORS['accent_1'], opacity=0.75),
                name='Daily Returns',
            ))
            fig.add_vline(x=perf['var_95']/ (252**0.5), line_dash='dash', line_color=COLORS['neutral'],
                          annotation_text="VaR 95% (daily-scale)", annotation_font_color=COLORS['neutral'])
            fig.add_vline(x=0, line_color=COLORS['border_strong'], line_width=1)
            fig.update_layout(
                height=280, margin=dict(l=20, r=20, t=20, b=20),
                xaxis=dict(title="Daily Return %"), yaxis=dict(title="Frequency"),
                showlegend=False, bargap=0.02,
            )
            st.plotly_chart(style_fig(fig), use_container_width=True)
            st.caption("VaR/CVaR figures above are annualized (√252-scaled); the dashed line here rescales VaR 95% back to a single-day magnitude for comparison against the daily histogram.")
    
    # ===== SECTION 3: EARNINGS QUALITY =====
    st.markdown("### 🔍 Earnings Quality & Fraud Detection")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**Beneish M-Score**")
        st.caption("Earnings manipulation detection")
        m_score = BeneishMScore.calculate(income, balance, cashflow)
        if m_score:
            m_inner = (
                f"<h2 style='color:{m_score['color']};text-align:center;margin:0;'>{m_score['m_score']}</h2>"
                f"<p style='text-align:center;color:{m_score['color']};margin:0.35rem 0 0 0;'><b>{m_score['risk']}</b></p>"
            )
            st.markdown(card_html(m_inner, accent=m_score['color']), unsafe_allow_html=True)
            with st.expander("📋 Components", expanded=False):
                st.caption(m_score['interpretation'])
                comps = m_score['components']
                flags = m_score.get('flags', {})
                names = list(comps.keys())
                vals = list(comps.values())
                bar_colors = [COLORS['down'] if flags.get(n) == 'elevated' else COLORS['accent_3'] for n in names]
                fig = go.Figure(go.Bar(
                    x=vals, y=names, orientation='h',
                    marker=dict(color=bar_colors, line=dict(color=COLORS['border_strong'], width=1)),
                    text=[f"{v:.2f}" for v in vals], textposition='outside',
                    textfont=dict(color=COLORS['text_1'], size=11),
                ))
                fig.add_vline(x=1.0, line_dash='dash', line_color=COLORS['text_3'],
                              annotation_text="baseline = 1.0", annotation_font_size=10,
                              annotation_font_color=COLORS['text_3'])
                fig.update_layout(
                    height=300, margin=dict(l=10, r=40, t=10, b=20),
                    xaxis=dict(title="Index Value (1.0 = no YoY change)"),
                    yaxis=dict(autorange='reversed'), showlegend=False,
                )
                st.plotly_chart(style_fig(fig), use_container_width=True)
                st.caption("🔴 Red bars = elevated (>1.2, or TATA > 3%) — moved in the direction associated with earnings manipulation.")
        else:
            st.warning("Insufficient data")
    
    with col2:
        st.markdown("**Piotroski F-Score**")
        st.caption("Financial strength (0-9)")
        f_score = PiotroskiFScore.calculate(income, balance, cashflow)
        f_color = f_score.get('color', '#94a3b8')
        f_inner = (
            f"<h2 style='color:{f_color};text-align:center;margin:0;'>{f_score['score']}/9</h2>"
            f"<p style='text-align:center;color:{f_color};margin:0.35rem 0 0 0;'><b>{f_score['rating']}</b></p>"
        )
        st.markdown(card_html(f_inner, accent=f_color), unsafe_allow_html=True)
    
    with col3:
        st.markdown("**Altman Z-Score**")
        st.caption("Bankruptcy prediction")
        z_score = AltmanZScore.calculate(balance, income, market_cap)
        if z_score and z_score.get('z_score') and not pd.isna(z_score['z_score']):
            z_color = z_score.get('color', '#94a3b8')
            z_inner = (
                f"<h2 style='color:{z_color};text-align:center;margin:0;'>{z_score['z_score']:.2f}</h2>"
                f"<p style='text-align:center;color:{z_color};margin:0.35rem 0 0 0;'><b>{z_score['zone']}</b></p>"
            )
            st.markdown(card_html(z_inner, accent=z_color), unsafe_allow_html=True)
            st.caption(f"Probability: {z_score.get('probability','N/A')}")
        else:
            st.warning("Insufficient data")
    
    with col4:
        st.markdown("**Ohlson O-Score**")
        st.caption("Bankruptcy probability (1980)")
        o_score = OhlsonOScore.calculate(income, balance, info)
        if o_score:
            o_inner = (
                f"<h2 style='color:{o_score['color']};text-align:center;margin:0;'>{o_score['probability']}</h2>"
                f"<p style='text-align:center;color:{o_score['color']};margin:0.35rem 0 0 0;'><b>{o_score['risk']}</b></p>"
            )
            st.markdown(card_html(o_inner, accent=o_score['color']), unsafe_allow_html=True)
            st.caption(o_score['interpretation'])
            with st.expander("📋 Score Contribution Breakdown", expanded=False):
                contrib = o_score.get('contributions', {})
                if contrib:
                    names = list(contrib.keys()) + ['= O-Score']
                    vals = list(contrib.values()) + [0]
                    fig = go.Figure(go.Waterfall(
                        orientation='v',
                        measure=['relative'] * (len(names) - 1) + ['total'],
                        x=names,
                        y=vals,
                        connector={'line': {'color': COLORS['text_3']}},
                        increasing={'marker': {'color': COLORS['down']}},
                        decreasing={'marker': {'color': COLORS['up']}},
                        totals={'marker': {'color': COLORS['accent_1']}},
                    ))
                    fig.update_layout(
                        height=340, margin=dict(l=10, r=10, t=10, b=90),
                        xaxis=dict(tickangle=-35, tickfont=dict(size=10)),
                        yaxis=dict(title="Contribution to O-Score"), showlegend=False,
                    )
                    st.plotly_chart(style_fig(fig), use_container_width=True)
                    st.caption("Each bar is the exact weighted contribution of that factor to the O-Score (they sum to the total). Red = pushes distress risk up, green = pushes it down.")
                for k, v in o_score['components'].items():
                    st.caption(f"• {k}: {v}")
        else:
            st.warning("Insufficient data")
    
    # ===== SECTION 4: DUPONT ANALYSIS =====
    st.markdown("### 🧩 DuPont ROE Decomposition")
    st.caption("ROE = Net Margin × Asset Turnover × Equity Multiplier — a multiplicative identity, so factors are shown as trend lines and an exact YoY bridge rather than a summed waterfall.")

    dupont = DuPontAnalysis.calculate(income, balance, ratios)

    if dupont:
        t3 = dupont['three_step']
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Net Profit Margin", f"{t3['net_margin']}%")
        m2.metric("Asset Turnover", f"{t3['asset_turnover']}x")
        m3.metric("Equity Multiplier", f"{t3['equity_multiplier']}x")
        m4.metric("ROE (3-Step)", f"{t3['roe']}%")

        if dupont.get('five_step'):
            t5 = dupont['five_step']
            st.caption(
                f"5-Step: Tax Burden {t5['tax_burden']} × Interest Burden {t5['interest_burden']} × "
                f"Operating Margin {t5['operating_margin']}% × Asset Turnover {t5['asset_turnover']}x × "
                f"Equity Multiplier {t5['equity_multiplier']}x = ROE {t5['roe']}%"
            )

        col1, col2 = st.columns(2)

        # ── Multi-year trend: each driver on its own normalized axis ──
        with col1:
            trend = dupont.get('trend')
            if trend and len(trend['labels']) >= 2:
                st.markdown("**Multi-Year Driver Trends**")
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Scatter(
                    x=trend['labels'], y=trend['net_margin'], name='Net Margin %',
                    line=dict(color=COLORS['accent_1'], width=2.5), mode='lines+markers',
                ), secondary_y=False)
                fig.add_trace(go.Scatter(
                    x=trend['labels'], y=trend['roe'], name='ROE %',
                    line=dict(color=COLORS['up'], width=2.5, dash='dot'), mode='lines+markers',
                ), secondary_y=False)
                fig.add_trace(go.Bar(
                    x=trend['labels'], y=trend['asset_turnover'], name='Asset Turnover (x)',
                    marker=dict(color='rgba(79,209,255,0.35)'),
                ), secondary_y=True)
                fig.add_trace(go.Bar(
                    x=trend['labels'], y=trend['equity_multiplier'], name='Equity Multiplier (x)',
                    marker=dict(color='rgba(155,107,245,0.35)'),
                ), secondary_y=True)
                fig.update_layout(
                    height=320, margin=dict(l=10, r=10, t=20, b=10), barmode='group',
                    legend=dict(orientation='h', y=-0.2),
                )
                fig.update_yaxes(title_text="Margin / ROE %", secondary_y=False)
                fig.update_yaxes(title_text="Turnover / Multiplier (x)", secondary_y=True)
                st.plotly_chart(style_fig(fig), use_container_width=True)
            else:
                st.info("Need 2+ years of statements for a trend chart.")

        # ── ROE bridge: exact additive attribution of the YoY ROE change ──
        with col2:
            bridge = dupont.get('bridge')
            if bridge:
                st.markdown(f"**ROE Bridge: {bridge['start_label']} → {bridge['end_label']}**")
                names = ['ROE ' + bridge['start_label'], 'Margin Effect', 'Turnover Effect', 'Leverage Effect', 'ROE ' + bridge['end_label']]
                measures = ['absolute', 'relative', 'relative', 'relative', 'total']
                values = [bridge['roe_start'], bridge['margin_effect'], bridge['turnover_effect'], bridge['leverage_effect'], 0]

                fig = go.Figure(go.Waterfall(
                    orientation='v', measure=measures, x=names, y=values,
                    connector={'line': {'color': COLORS['text_3']}},
                    increasing={'marker': {'color': COLORS['up']}},
                    decreasing={'marker': {'color': COLORS['down']}},
                    totals={'marker': {'color': COLORS['accent_1']}},
                    text=[f"{v:+.2f}%" if m == 'relative' else f"{v:.2f}%" for v, m in zip(
                        [bridge['roe_start'], bridge['margin_effect'], bridge['turnover_effect'], bridge['leverage_effect'], bridge['roe_end']],
                        measures)],
                    textposition='outside',
                ))
                fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10), showlegend=False,
                                   yaxis=dict(title="ROE %"))
                st.plotly_chart(style_fig(fig), use_container_width=True)
                st.caption("Exact sequential-substitution decomposition — the three effects sum precisely to the change in ROE.")
            else:
                st.info("Need 2+ years of statements for a YoY ROE bridge.")
    else:
        st.warning("Insufficient data for DuPont analysis")
    
    # Rating legend
    st.markdown("---")
    st.markdown("### 📊 Rating Scale")
    col1, col2, col3, col4, col5 = st.columns(5)
    legend = [
        (col1, "EXCELLENT", "80-100", "#10b981"),
        (col2, "GOOD", "60-79", "#34d399"),
        (col3, "FAIR", "40-59", "#f59e0b"),
        (col4, "POOR", "20-39", "#f97316"),
        (col5, "CRITICAL", "0-19", "#ef4444"),
    ]
    for col, label, rng, color in legend:
        with col:
            inner = f"{status_pill(label, color)}<br><span style='color:{COLORS['text_3']};font-size:0.7rem;'>{rng}</span>"
            st.markdown(card_html(inner, accent=color, center=True), unsafe_allow_html=True)
    
    # ===== SECTION 5: COMPOSITE HEALTH SCORE =====
    st.markdown("### 🏆 Composite Financial Health Score")
    
    composite = CompositeScore.calculate(ratios, f_score, z_score)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=composite['score'],
            number={'font': {'color': composite['color'], 'size': 48, 'family': 'Inter, sans-serif'}},
            title={'text': "Health Score", 'font': {'family': 'Inter, sans-serif'}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': COLORS['text_3']},
                'bar': {'color': composite['color']},
                'bgcolor': COLORS['bg_2'],
                'steps': [
                    {'range': [0, 40], 'color': "rgba(255,93,122,0.18)"},
                    {'range': [40, 60], 'color': "rgba(245,185,66,0.18)"},
                    {'range': [60, 80], 'color': "rgba(34,211,143,0.18)"},
                    {'range': [80, 100], 'color': "rgba(34,211,143,0.32)"},
                ]
            }
        ))
        fig.update_layout(height=250, margin=dict(t=30, b=0))
        st.plotly_chart(style_fig(fig), use_container_width=True)
        st.markdown(f"<h3 style='text-align:center;color:{composite['color']};'>{composite['rating']}</h3>", unsafe_allow_html=True)
    
    with col2:
        for category, score in composite['breakdown'].items():
            s = int(score) if pd.notna(score) and not np.isnan(score) else 0
            bar_color = COLORS['up'] if s >= 70 else COLORS['neutral'] if s >= 40 else COLORS['down']
            st.markdown(progress_bar(category, s, 100, color=bar_color), unsafe_allow_html=True)