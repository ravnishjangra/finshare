"""News & Sentiment Dashboard — premium headline feed for the searched stock.

Pulls from news/news_engine.py (Google News RSS + yfinance bonus feed,
both free, no API key) and scores each headline with
nlp/sentiment_engine.py — FinBERT (a finance-tuned BERT model) when
available, automatically falling back to the original local VADER +
financial-lexicon scorer if FinBERT can't be loaded (package missing,
no internet for the model download, etc). Either way, no article text
is sent anywhere — scoring is local to the process.

This module never touches core/analyzer.py, core/fallback.py, or the
yfinance ticker cache used by the price-fetch path — it only reads
`analyzer.company_name` / `analyzer.ticker` / `analyzer.financials`
after the analyzer has already been built by app.py.
"""

from datetime import datetime, timezone

import streamlit as st
import plotly.graph_objects as go

from theme import COLORS, style_fig, section_header, info_box, news_card, gauge_chart, animated_config
from news.news_engine import get_company_news, get_market_news
from nlp.sentiment_engine import analyze_articles_batch, aggregate_sentiment, engine_status


def _time_ago(iso_ts):
    if not iso_ts:
        return "Recently"
    try:
        ts = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - ts
        secs = delta.total_seconds()
        if secs < 3600:
            return f"{max(1, int(secs // 60))}m ago"
        if secs < 86400:
            return f"{int(secs // 3600)}h ago"
        days = int(secs // 86400)
        if days < 7:
            return f"{days}d ago"
        return ts.strftime("%d %b %Y")
    except Exception:
        return "Recently"


@st.cache_data(ttl=600, show_spinner=False)
def _cached_company_news(company_name, symbol):
    return get_company_news(company_name, symbol=symbol, limit=14)


@st.cache_data(ttl=900, show_spinner=False)
def _cached_market_news():
    return get_market_news(limit_per_feed=5)


def _sentiment_distribution_chart(dist: dict):
    labels = ["Positive", "Neutral", "Negative"]
    values = [dist.get("POSITIVE", 0), dist.get("NEUTRAL", 0), dist.get("NEGATIVE", 0)]
    colors = [COLORS["up"], COLORS["neutral"], COLORS["down"]]

    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[str(v) for v in values], textposition="outside",
        textfont=dict(color=COLORS["text_1"], size=13, family="Manrope, Inter, sans-serif"),
        hovertemplate="%{y}: %{x} headlines<extra></extra>",
    ))
    fig.update_layout(
        height=200, showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(tickfont=dict(size=12, color=COLORS["text_2"])),
        margin=dict(l=10, r=30, t=10, b=10),
        bargap=0.45,
    )
    return style_fig(fig)


def _sentiment_timeline_chart(articles):
    """Scatter of sentiment score vs. headline order (most-recent-first reversed
    to read left-to-right chronologically) — shows the recent narrative arc."""
    scored = [a for a in articles if a.get("sentiment")]
    if len(scored) < 3:
        return None
    scored = list(reversed(scored))
    x = list(range(1, len(scored) + 1))
    y = [a["sentiment"]["score"] for a in scored]
    colors = [COLORS["up"] if v > 0.15 else (COLORS["down"] if v < -0.15 else COLORS["neutral"]) for v in y]
    hover = [a["title"][:60] + ("…" if len(a["title"]) > 60 else "") for a in scored]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines+markers",
        line=dict(color=COLORS["accent_1"], width=2, shape="spline"),
        marker=dict(size=9, color=colors, line=dict(width=1.5, color=COLORS["bg_0"])),
        text=hover, hovertemplate="%{text}<br>Score: %{y:.2f}<extra></extra>",
        fill="tozeroy", fillcolor="rgba(109,94,248,0.08)",
    ))
    fig.add_hline(y=0, line_dash="dot", line_color=COLORS["border_strong"])
    fig.update_layout(
        height=230,
        xaxis=dict(title="Older → Newer", showticklabels=False),
        yaxis=dict(range=[-1.05, 1.05], title="Sentiment"),
        margin=dict(l=40, r=20, t=20, b=30),
    )
    return style_fig(fig)


def _render_feed(articles, empty_msg):
    if not articles:
        st.markdown(info_box(f"📭 {empty_msg}"), unsafe_allow_html=True)
        return
    for a in articles:
        sent = a.get("sentiment", {})
        st.markdown(
            news_card(
                title=a.get("title", ""),
                source=a.get("source", "Unknown"),
                time_ago=_time_ago(a.get("published")),
                link=a.get("link"),
                label=sent.get("label", "NEUTRAL"),
                score=sent.get("score"),
            ),
            unsafe_allow_html=True,
        )


def create_news_dashboard(analyzer):
    st.markdown(section_header("📰", "News & Sentiment"), unsafe_allow_html=True)

    status = engine_status()
    if status["active_engine"] == "finbert":
        st.caption("🧠 Sentiment engine: **FinBERT** (ProsusAI/finbert) — finance-tuned BERT, blended with an India-market phrase lexicon.")
    elif status["active_engine"] == "vader+lexicon":
        reason = " (FinBERT unavailable in this environment)" if not status["finbert_available"] else ""
        st.caption(f"🔤 Sentiment engine: **VADER + financial lexicon** fallback{reason}.")
    else:
        st.caption("🔤 Sentiment engine: **lexicon-only** fallback (VADER not installed).")

    company_name = getattr(analyzer, "company_name", None) or getattr(analyzer, "original_ticker", "")
    symbol = getattr(analyzer, "ticker", None)
    sector = (analyzer.financials or {}).get("sector") if getattr(analyzer, "financials", None) else None

    if not company_name:
        st.info("Search a stock above to load its news feed.")
        return

    with st.spinner(f"Fetching headlines for {company_name}..."):
        try:
            raw_articles = _cached_company_news(company_name, symbol)
        except Exception:
            raw_articles = []
        articles = analyze_articles_batch(list(raw_articles)) if raw_articles else []

    tab_company, tab_market = st.tabs([f"🏢 {company_name}", "🌐 Market Pulse"])

    with tab_company:
        if not articles:
            st.markdown(
                info_box("📭 No recent headlines found for this stock right now. Free news sources can be sparse for smaller-cap names — try again shortly."),
                unsafe_allow_html=True,
            )
        else:
            summary = aggregate_sentiment([a["sentiment"] for a in articles])

            gcol, dcol, tcol = st.columns([1, 1, 1.3])
            with gcol:
                st.plotly_chart(gauge_chart(summary["score"], title="Overall Tone"), use_container_width=True, config=animated_config())
            with dcol:
                st.markdown(
                    f'<div style="padding-top:0.5rem;">'
                    f'<div class="metric-label" style="margin-bottom:0.6rem;">SENTIMENT MIX ({summary["article_count"]} headlines)</div>'
                    f'</div>', unsafe_allow_html=True,
                )
                st.plotly_chart(_sentiment_distribution_chart(summary["label_distribution"]), use_container_width=True, config=animated_config())
            with tcol:
                timeline = _sentiment_timeline_chart(articles)
                if timeline is not None:
                    st.markdown('<div class="metric-label" style="margin-bottom:0.4rem;">RECENT NARRATIVE ARC</div>', unsafe_allow_html=True)
                    st.plotly_chart(timeline, use_container_width=True, config=animated_config())
                else:
                    st.markdown(
                        f'<div class="card" style="height:100%;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;">'
                        f'<div class="metric-value" style="color:{COLORS["text_2"]};font-size:1rem;">Not enough headlines yet</div>'
                        f'<div class="metric-label">for a narrative timeline</div></div>',
                        unsafe_allow_html=True,
                    )

            st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
            _render_feed(articles, "No headlines available.")

            engine_label = {
                "finbert": "FinBERT (financial-domain BERT) blended with a keyword lexicon",
                "vader+lexicon": "VADER + a keyword/financial lexicon heuristic",
                "lexicon": "a keyword/financial lexicon heuristic",
            }.get(status["active_engine"], "a local heuristic")
            st.caption(
                f"Sentiment is scored locally on headline text only using {engine_label} — "
                "a directional read, not investment advice. Sources: Google News RSS, Yahoo Finance."
            )

    with tab_market:
        with st.spinner("Fetching market headlines..."):
            try:
                market_articles = _cached_market_news()
            except Exception:
                market_articles = []
            market_articles = analyze_articles_batch(list(market_articles)) if market_articles else []
        _render_feed(market_articles, "Market headlines unavailable right now.")