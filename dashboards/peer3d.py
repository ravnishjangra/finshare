"""3D Peer Comparison Scatter.

Pure visualization on top of the peer comparison DataFrame that app.py
already builds via utils.helpers.get_peer_comparison() — this module
makes no network calls of its own and never touches the fetch/cache
path, so it can't add any yfinance rate-limit risk.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from theme import COLORS, style_fig_3d, animated_config


def _to_numeric(series):
    return pd.to_numeric(series, errors="coerce")


def create_peer_3d_scatter(pdf: pd.DataFrame, main_ticker: str = None):
    """pdf: the DataFrame already returned by utils.helpers.get_peer_comparison().
    Plots P/E × ROE % × D/E as a 3D scatter, colored by Dividend Yield,
    with the currently-analyzed ticker highlighted."""
    if pdf is None or pdf.empty or len(pdf) < 2:
        return

    df = pdf.copy()
    df["P/E_num"] = _to_numeric(df["P/E"])
    df["ROE_num"] = _to_numeric(df["ROE %"])
    df["DE_num"] = _to_numeric(df["D/E"])
    df["DivY_num"] = _to_numeric(df["Div Yield %"]).fillna(0)

    plot_df = df.dropna(subset=["P/E_num", "ROE_num", "DE_num"])
    if len(plot_df) < 2:
        return

    main_ticker_clean = (main_ticker or "").replace(".NS", "").replace(".BO", "")
    is_main = plot_df["Ticker"] == main_ticker_clean
    sizes = [16 if m else 9 for m in is_main]
    line_widths = [2.5 if m else 1 for m in is_main]
    line_colors = [COLORS["accent_3"] if m else COLORS["bg_1"] for m in is_main]

    st.markdown('<div class="section-header">🧊 3D Peer Landscape</div>', unsafe_allow_html=True)
    st.caption("Valuation (P/E) × Quality (ROE %) × Leverage (D/E), colored by dividend yield — your stock highlighted in cyan")

    fig = go.Figure(data=[go.Scatter3d(
        x=plot_df["P/E_num"], y=plot_df["ROE_num"], z=plot_df["DE_num"],
        mode="markers+text",
        text=plot_df["Ticker"],
        textposition="top center",
        textfont=dict(color=COLORS["text_2"], size=10),
        marker=dict(
            size=sizes,
            color=plot_df["DivY_num"],
            colorscale=[[0.0, COLORS["accent_1"]], [0.5, COLORS["accent_2"]], [1.0, COLORS["up"]]],
            colorbar=dict(title="Div Yld %", tickfont=dict(color=COLORS["text_3"]), len=0.65),
            line=dict(width=line_widths, color=line_colors),
            opacity=0.9,
        ),
        customdata=plot_df["Company"],
        hovertemplate="<b>%{text}</b> — %{customdata}<br>P/E: %{x:.1f}<br>ROE: %{y:.1f}%<br>D/E: %{z:.2f}<extra></extra>",
    )])
    fig = style_fig_3d(fig, x_title="P/E Ratio", y_title="ROE %", z_title="Debt/Equity", height=520)
    st.plotly_chart(fig, use_container_width=True, config=animated_config())