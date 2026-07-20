"""
Finshare Pro — Shared Theme
Import this in any dashboards/*.py or models/*.py file to keep colors,
fonts, and Plotly chart styling consistent with the main app.py CSS.

Usage:
    from theme import COLORS, PLOTLY_LAYOUT, style_fig

    fig = go.Figure(...)
    fig = style_fig(fig)  # applies dark theme, fonts, gridlines
"""

# ── Color palette (mirrors the :root CSS variables in app.py) ──────────────
COLORS = {
    "bg_0": "#05070d",
    "bg_1": "#0a0e17",
    "bg_2": "#10141f",
    "surface": "rgba(19, 24, 38, 0.6)",
    "surface_hover": "rgba(23, 29, 46, 0.7)",
    "border": "rgba(148, 163, 253, 0.10)",
    "border_strong": "rgba(148, 163, 253, 0.22)",

    "accent_1": "#6d5ef8",   # indigo
    "accent_2": "#9b6bf5",   # violet
    "accent_3": "#4fd1ff",   # cyan

    "up": "#22d38f",
    "up_soft": "rgba(34, 211, 143, 0.15)",
    "down": "#ff5d7a",
    "down_soft": "rgba(255, 93, 122, 0.15)",
    "neutral": "#f5b942",
    "neutral_soft": "rgba(245, 185, 66, 0.15)",

    "text_1": "#f4f6fb",
    "text_2": "#aab1c5",
    "text_3": "#6b7488",
}

SERIES_PALETTE = [
    COLORS["accent_1"], COLORS["accent_3"], COLORS["up"],
    COLORS["neutral"], COLORS["accent_2"], COLORS["down"],
    "#5eead4", "#c084fc",
]

# ── Glassmorphism CSS Injection ─────────────────────────────────────────
GLASS_CSS = """
<style>
/* Glass background for cards */
.card, .stMetric, div[data-testid="stMetric"], 
.stExpander, div[data-testid="stExpander"],
.css-1r6slb0, .css-keje6w {
    background: rgba(19, 24, 38, 0.45) !important;
    backdrop-filter: blur(14px) !important;
    -webkit-backdrop-filter: blur(14px) !important;
    border: 1px solid rgba(148, 163, 253, 0.12) !important;
    border-radius: 16px !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
}

/* Card hover - intensify glass */
.card:hover, .news-card:hover {
    background: rgba(23, 29, 46, 0.65) !important;
    border-color: rgba(148, 163, 253, 0.25) !important;
    box-shadow: 0 12px 40px rgba(109, 94, 248, 0.12) !important;
}

/* Sidebar glass */
.css-1d391kg, section[data-testid="stSidebar"] > div {
    background: rgba(10, 14, 23, 0.7) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(148, 163, 253, 0.08) !important;
}

/* Input fields glass */
.stTextInput input, .stSelectbox > div > div {
    background: rgba(19, 24, 38, 0.5) !important;
    backdrop-filter: blur(8px) !important;
    -webkit-backdrop-filter: blur(8px) !important;
    border: 1px solid rgba(148, 163, 253, 0.15) !important;
    border-radius: 12px !important;
    color: #f4f6fb !important;
}

/* Buttons glass */
.stButton button {
    background: rgba(109, 94, 248, 0.2) !important;
    backdrop-filter: blur(8px) !important;
    -webkit-backdrop-filter: blur(8px) !important;
    border: 1px solid rgba(109, 94, 248, 0.3) !important;
    border-radius: 12px !important;
    color: #f4f6fb !important;
    transition: all 0.3s ease !important;
}

.stButton button:hover {
    background: rgba(109, 94, 248, 0.35) !important;
    border-color: rgba(109, 94, 248, 0.5) !important;
    box-shadow: 0 4px 20px rgba(109, 94, 248, 0.2) !important;
}

/* Tabs glass */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(19, 24, 38, 0.4) !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
    border-radius: 14px !important;
    padding: 4px !important;
    gap: 4px !important;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    color: #aab1c5 !important;
}

.stTabs [aria-selected="true"] {
    background: rgba(109, 94, 248, 0.25) !important;
    color: #f4f6fb !important;
}

/* News cards glass */
.news-card {
    background: rgba(19, 24, 38, 0.45) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(148, 163, 253, 0.10) !important;
    border-radius: 14px !important;
}

/* Section headers */
.section-header {
    font-size: 1.5rem;
    font-weight: 700;
    color: #f4f6fb;
    margin-bottom: 1rem;
}

/* Metric labels */
.metric-label {
    font-size: 0.75rem;
    color: #6b7488;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.metric-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #f4f6fb;
}

/* App background with gradient for glass to show through */
.stApp {
    background: linear-gradient(135deg, #05070d 0%, #0a0e17 30%, #0d1117 60%, #0a0e17 100%) !important;
}
</style>
"""


def inject_glass():
    """Call once in app.py to enable glassmorphism globally."""
    import streamlit as st
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


def signed_color(value: float) -> str:
    return COLORS["up"] if value is not None and value >= 0 else COLORS["down"]


def sentiment_color(label: str) -> tuple:
    label = (label or "NEUTRAL").upper()
    if label == "POSITIVE":
        return COLORS["up"], COLORS["up_soft"]
    if label == "NEGATIVE":
        return COLORS["down"], COLORS["down_soft"]
    return COLORS["neutral"], COLORS["neutral_soft"]


# ── Plotly layout template ──────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color=COLORS["text_2"], size=12),
    title_font=dict(family="Inter, sans-serif", color=COLORS["text_1"], size=15),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_2"], size=11),
        bordercolor=COLORS["border"],
    ),
    xaxis=dict(
        gridcolor=COLORS["border"],
        zerolinecolor=COLORS["border_strong"],
        linecolor=COLORS["border"],
        tickfont=dict(color=COLORS["text_3"], size=11),
    ),
    yaxis=dict(
        gridcolor=COLORS["border"],
        zerolinecolor=COLORS["border_strong"],
        linecolor=COLORS["border"],
        tickfont=dict(color=COLORS["text_3"], size=11),
    ),
    margin=dict(l=40, r=30, t=50, b=40),
    hoverlabel=dict(
        bgcolor=COLORS["surface"],
        bordercolor=COLORS["border_strong"],
        font=dict(family="Inter, sans-serif", color=COLORS["text_1"], size=12),
    ),
    colorway=SERIES_PALETTE,
    bargap=0.28,
    bargroupgap=0.12,
)


def style_fig(fig):
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig


def animated_config():
    return {
        "displayModeBar": "hover",
        "displaylogo": False,
        "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d", "toggleSpikelines"],
        "toImageButtonOptions": {"format": "png", "scale": 2},
    }


def metric_card(label: str, value: str, delta: str = None, positive: bool = True) -> str:
    delta_html = ""
    if delta:
        color = COLORS["up"] if positive else COLORS["down"]
        bg = COLORS["up_soft"] if positive else COLORS["down_soft"]
        delta_html = (
            f'<span style="background:{bg};color:{color};font-size:0.75rem;'
            f'font-weight:700;padding:0.15rem 0.5rem;border-radius:999px;margin-left:0.4rem;">'
            f'{delta}</span>'
        )
    return (
        f'<div class="card animate-in">'
        f'<div class="metric-value">{value}{delta_html}</div>'
        f'<div class="metric-label">{label}</div>'
        f'</div>'
    )


def section_header(icon: str, title: str) -> str:
    return f'<div class="section-header">{icon} {title}</div>'


def info_box(text: str) -> str:
    return f'<div class="info-box">{text}</div>'


def score_badge(label: str, score: float, max_score: float, thresholds=(0.33, 0.66)) -> str:
    frac = 0 if max_score == 0 else score / max_score
    if frac < thresholds[0]:
        color, bg = COLORS["down"], COLORS["down_soft"]
    elif frac < thresholds[1]:
        color, bg = COLORS["neutral"], COLORS["neutral_soft"]
    else:
        color, bg = COLORS["up"], COLORS["up_soft"]
    return (
        f'<div class="card animate-in" style="text-align:center;">'
        f'<div style="font-size:1.6rem;font-weight:800;color:{color};">{score:.1f}<span style="color:{COLORS["text_3"]};font-size:1rem;">/{max_score:.0f}</span></div>'
        f'<div class="metric-label">{label}</div>'
        f'<div style="margin-top:0.5rem;height:6px;border-radius:3px;background:{COLORS["border"]};overflow:hidden;">'
        f'<div class="grow-bar" style="height:100%;width:{frac*100:.0f}%;background:{color};border-radius:3px;"></div>'
        f'</div></div>'
    )


def sentiment_pill(label: str, score: float = None) -> str:
    color, bg = sentiment_color(label)
    dot = "●"
    txt = label.title() if label else "Neutral"
    score_txt = f" {score:+.2f}" if isinstance(score, (int, float)) else ""
    return (
        f'<span style="display:inline-flex;align-items:center;gap:0.35rem;background:{bg};'
        f'color:{color};font-size:0.72rem;font-weight:700;letter-spacing:0.3px;'
        f'padding:0.22rem 0.65rem;border-radius:999px;white-space:nowrap;">'
        f'{dot} {txt}{score_txt}</span>'
    )


def news_card(title: str, source: str, time_ago: str, link: str, label: str = "NEUTRAL", score: float = None) -> str:
    color, _ = sentiment_color(label)
    safe_title = title if title else "Untitled"
    href = link or "#"
    target = ' target="_blank" rel="noopener noreferrer"' if link else ""
    return (
        f'<a href="{href}"{target} style="text-decoration:none;">'
        f'<div class="news-card animate-in" style="border-left:3px solid {color};">'
        f'<div class="news-card-title">{safe_title}</div>'
        f'<div class="news-card-meta">'
        f'<span class="news-card-source">{source}</span>'
        f'<span class="news-card-dot">•</span>'
        f'<span class="news-card-time">{time_ago}</span>'
        f'<span style="margin-left:auto;">{sentiment_pill(label, score)}</span>'
        f'</div></div></a>'
    )


VALUE_COLORSCALE = [
    [0.0, COLORS["down"]],
    [0.5, COLORS["neutral"]],
    [1.0, COLORS["up"]],
]

BRAND_COLORSCALE = [
    [0.0, COLORS["accent_1"]],
    [0.5, COLORS["accent_2"]],
    [1.0, COLORS["accent_3"]],
]


def scene3d(x_title="", y_title="", z_title="", eye=(1.6, 1.5, 1.15)):
    axis = dict(
        title=dict(font=dict(color=COLORS["text_3"], size=11)),
        backgroundcolor=COLORS["bg_1"],
        gridcolor=COLORS["border"],
        zerolinecolor=COLORS["border_strong"],
        showbackground=True,
        color=COLORS["text_3"],
        tickfont=dict(color=COLORS["text_3"], size=9),
    )
    return dict(
        xaxis={**axis, "title": {**axis["title"], "text": x_title}},
        yaxis={**axis, "title": {**axis["title"], "text": y_title}},
        zaxis={**axis, "title": {**axis["title"], "text": z_title}},
        camera=dict(eye=dict(x=eye[0], y=eye[1], z=eye[2]), up=dict(x=0, y=0, z=1)),
        aspectmode="cube",
        bgcolor="rgba(0,0,0,0)",
    )


def style_fig_3d(fig, x_title="", y_title="", z_title="", eye=(1.6, 1.5, 1.15), height=520):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=COLORS["text_2"], size=12),
        title_font=dict(family="Inter, sans-serif", color=COLORS["text_1"], size=15),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=COLORS["text_2"], size=11)),
        hoverlabel=dict(
            bgcolor=COLORS["surface"],
            bordercolor=COLORS["border_strong"],
            font=dict(family="Inter, sans-serif", color=COLORS["text_1"], size=12),
        ),
        scene=scene3d(x_title, y_title, z_title, eye=eye),
        height=height,
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig


def gauge_chart(value: float, title: str = "Sentiment", lo: float = -1.0, hi: float = 1.0):
    import plotly.graph_objects as go

    color = COLORS["up"] if value > 0.15 else (COLORS["down"] if value < -0.15 else COLORS["neutral"])
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"font": {"color": color, "size": 34, "family": "Inter, sans-serif"}, "valueformat": ".2f"},
        title={"text": title, "font": {"color": COLORS["text_2"], "size": 13, "family": "Inter, sans-serif"}},
        gauge={
            "axis": {"range": [lo, hi], "tickcolor": COLORS["text_3"], "tickfont": {"color": COLORS["text_3"], "size": 10}},
            "bar": {"color": color, "thickness": 0.28},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [lo, -0.15], "color": COLORS["down_soft"]},
                {"range": [-0.15, 0.15], "color": COLORS["neutral_soft"]},
                {"range": [0.15, hi], "color": COLORS["up_soft"]},
            ],
            "threshold": {"line": {"color": color, "width": 3}, "thickness": 0.8, "value": value},
        },
    ))
    fig.update_layout(height=220, margin=dict(l=20, r=20, t=40, b=10))
    return style_fig(fig)