"""News fetching from free sources: Google News RSS + yfinance.

No API key required for either source. Google News RSS is the primary
source since it's a stable public endpoint; yfinance's .get_news() is
an undocumented Yahoo endpoint that changes shape across versions, so
it's parsed defensively and used only as a supplement.

This module is completely independent of core/analyzer.py and
core/fallback.py — it never touches the price/financials fetch path,
so it can't affect yfinance rate-limit behavior for the search flow.
"""

import time
from datetime import datetime, timezone
from urllib.parse import quote_plus

import feedparser
import yfinance as yf

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

# General market feeds for the "Market Pulse" sub-tab — not tied to a
# specific ticker, shown alongside company-specific news.
MARKET_RSS_FEEDS = {
    "Economic Times Markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Moneycontrol": "https://www.moneycontrol.com/rss/marketreports.xml",
    "Business Standard Markets": "https://www.business-standard.com/rss/markets-106.rss",
    "Mint Markets": "https://www.livemint.com/rss/markets",
    "Financial Express": "https://www.financialexpress.com/feed/",
}


def _to_iso(struct_time):
    if not struct_time:
        return None
    try:
        return datetime.fromtimestamp(time.mktime(struct_time), tz=timezone.utc).isoformat()
    except (OverflowError, ValueError):
        return None


def fetch_google_news(query, limit=10):
    """Fetch recent news for a free-text query via Google News RSS."""
    url = GOOGLE_NEWS_RSS.format(query=quote_plus(query))
    try:
        feed = feedparser.parse(url)
    except Exception:
        return []

    items = []
    for entry in feed.entries[:limit]:
        published = _to_iso(getattr(entry, "published_parsed", None))
        source = None
        if hasattr(entry, "source") and entry.source:
            source = entry.source.get("title")

        items.append({
            "title": getattr(entry, "title", "").strip(),
            "link": getattr(entry, "link", None),
            "source": source or "Google News",
            "published": published,
        })
    return items


def fetch_yfinance_news(symbol, limit=8):
    """Best-effort fetch of yfinance's undocumented news feed.

    Returns [] on any failure rather than raising — this is a bonus
    source layered on top of Google News, never a dependency, and it
    never touches the shared ticker cache used by the price/search flow.
    """
    items = []
    try:
        ticker = yf.Ticker(symbol)
        raw_news = ticker.get_news(count=limit) or []
    except Exception:
        return items

    for article in raw_news:
        content = article.get("content", article) if isinstance(article, dict) else {}
        title = content.get("title")
        if not title:
            continue

        link = None
        click_through = content.get("clickThroughUrl") or content.get("canonicalUrl")
        if isinstance(click_through, dict):
            link = click_through.get("url")

        provider = content.get("provider")
        source = provider.get("displayName") if isinstance(provider, dict) else "Yahoo Finance"
        published = content.get("pubDate") or content.get("displayTime")

        items.append({
            "title": title.strip(),
            "link": link,
            "source": source or "Yahoo Finance",
            "published": published,
        })
    return items


def get_company_news(company_name, symbol=None, limit=12):
    """Combined, de-duplicated news for a specific searched stock.

    Searches Google News for the company name and merges in whatever
    yfinance's bonus news feed returns for the symbol, if available.
    """
    google_items = fetch_google_news(company_name, limit=limit)
    yf_items = fetch_yfinance_news(symbol, limit=limit) if symbol else []

    combined = google_items + yf_items
    seen_titles = set()
    deduped = []
    for item in combined:
        key = item["title"].lower().strip()
        if key in seen_titles or not key:
            continue
        seen_titles.add(key)
        deduped.append(item)

    deduped.sort(key=lambda i: i["published"] or "", reverse=True)
    return deduped[:limit]


def get_market_news(limit_per_feed=5):
    """General market/macro headlines, not tied to a specific stock."""
    all_items = []
    for source_name, url in MARKET_RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
        except Exception:
            continue

        for entry in feed.entries[:limit_per_feed]:
            published = _to_iso(getattr(entry, "published_parsed", None))
            all_items.append({
                "title": getattr(entry, "title", "").strip(),
                "link": getattr(entry, "link", None),
                "source": source_name,
                "published": published,
            })

    all_items.sort(key=lambda i: i["published"] or "", reverse=True)
    return all_items