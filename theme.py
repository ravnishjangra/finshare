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
    "surface": "#131826",
    "surface_hover": "#171d2e",
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

    "text_1": "#f4f6fb",
    "text_2": "#aab1c5",
    "text_3": "#6b7488",
}

# Ordered palette for multi-series charts (peer comparisons, factor bars, etc.)
SERIES_PALETTE = [
    COLORS["accent_1"], COLORS["accent_3"], COLORS["up"],
    COLORS["neutral"], COLORS["accent_2"], COLORS["down"],
    "#5eead4", "#c084fc",
]

# Reusable up/down color picker for bars, deltas, candlesticks
def signed_color(value: float) -> str:
    return COLORS["up"] if value is not None and value >= 0 else COLORS["down"]

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
)


def style_fig(fig):
    """Apply the shared dark theme to any Plotly figure in-place and return it."""
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig


# ── HTML snippet helpers (for st.markdown(..., unsafe_allow_html=True)) ───
def metric_card(label: str, value: str, delta: str = None, positive: bool = True) -> str:
    """Small stat card matching the .card style in app.py's CSS."""
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
    """
    Colored badge for 0-N scored models (Piotroski, Altman, etc.).
    thresholds are fractions of max_score marking weak/moderate/strong cutoffs.
    """
    frac = 0 if max_score == 0 else score / max_score
    if frac < thresholds[0]:
        color, bg = COLORS["down"], COLORS["down_soft"]
    elif frac < thresholds[1]:
        color, bg = COLORS["neutral"], "rgba(245,185,66,0.15)"
    else:
        color, bg = COLORS["up"], COLORS["up_soft"]
    return (
        f'<div class="card animate-in" style="text-align:center;">'
        f'<div style="font-size:1.6rem;font-weight:800;color:{color};">{score:.1f}<span style="color:{COLORS["text_3"]};font-size:1rem;">/{max_score:.0f}</span></div>'
        f'<div class="metric-label">{label}</div>'
        f'<div style="margin-top:0.5rem;height:6px;border-radius:3px;background:{COLORS["border"]};overflow:hidden;">'
        f'<div style="height:100%;width:{frac*100:.0f}%;background:{color};border-radius:3px;"></div>'
        f'</div></div>'
    )