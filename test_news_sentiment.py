"""Live test: fetch REAL, CURRENT news for a stock and the broader market,
then run the sentiment engine on it end-to-end.

This is a live/integration test, not a unit test with mocked data - it hits
Google News RSS (and yfinance's bonus news feed) for whatever is happening
right now, so the point is to confirm the news + NLP pipeline in
news/news_engine.py and nlp/sentiment_engine.py actually works together
against today's real headlines, not canned fixtures.

Run it directly:
    python test_news_sentiment.py [SYMBOL] [COMPANY NAME]

Defaults to RELIANCE.NS / "Reliance Industries" if no args are given.
"""
import sys
from datetime import datetime, timezone

sys.path.insert(0, '.')

from news.news_engine import get_company_news, get_market_news  # noqa: E402
from nlp.sentiment_engine import analyze_articles_batch, aggregate_sentiment  # noqa: E402


def _age(iso_ts):
    if not iso_ts:
        return "unknown time"
    try:
        ts = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        secs = (datetime.now(timezone.utc) - ts).total_seconds()
        if secs < 3600:
            return f"{max(1, int(secs // 60))}m ago"
        if secs < 86400:
            return f"{int(secs // 3600)}h ago"
        return f"{int(secs // 86400)}d ago"
    except Exception:
        return "unknown time"


def run(symbol="RELIANCE.NS", company_name="Reliance Industries"):
    print("=" * 70)
    print(f"LIVE NEWS + SENTIMENT TEST — {company_name} ({symbol})")
    print(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # ── 1. Company-specific news, fetched live ──
    print("\n[1] Fetching live company news (Google News RSS + yfinance)...")
    try:
        articles = get_company_news(company_name, symbol=symbol, limit=12)
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
        articles = []

    if not articles:
        print("⚠️  No articles returned. This can mean: (a) the news source is "
              "temporarily unreachable in this environment, (b) the network/domain "
              "is blocked, or (c) there's genuinely sparse coverage for this name "
              "right now. It is NOT necessarily a bug — rerun during market hours "
              "or with a large-cap name to sanity check.")
    else:
        print(f"✅ Retrieved {len(articles)} live headlines\n")
        scored = analyze_articles_batch(list(articles))
        for a in scored:
            s = a["sentiment"]
            arrow = "🟢" if s["label"] == "POSITIVE" else ("🔴" if s["label"] == "NEGATIVE" else "🟡")
            print(f"  {arrow} [{s['score']:+.2f}] ({_age(a.get('published'))}, {a.get('source')}) {a['title'][:90]}")

        summary = aggregate_sentiment([a["sentiment"] for a in scored])
        print("\n  --- Aggregate sentiment ---")
        print(f"  Score: {summary['score']:+.3f}  |  Label: {summary['label']}  |  "
              f"Confidence: {summary['confidence']:.2f}  |  N={summary['article_count']}")
        print(f"  Distribution: {summary['label_distribution']}")

    # ── 2. General market pulse, fetched live ──
    print("\n[2] Fetching live market-wide headlines (Economic Times, Moneycontrol, etc.)...")
    try:
        market_articles = get_market_news(limit_per_feed=4)
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
        market_articles = []

    if not market_articles:
        print("⚠️  No market headlines returned (see note above about network/source availability).")
    else:
        scored_market = analyze_articles_batch(list(market_articles))
        print(f"✅ Retrieved {len(scored_market)} live market headlines\n")
        for a in scored_market[:10]:
            s = a["sentiment"]
            arrow = "🟢" if s["label"] == "POSITIVE" else ("🔴" if s["label"] == "NEGATIVE" else "🟡")
            print(f"  {arrow} [{s['score']:+.2f}] ({a.get('source')}) {a['title'][:90]}")

        market_summary = aggregate_sentiment([a["sentiment"] for a in scored_market])
        print("\n  --- Market-wide aggregate sentiment ---")
        print(f"  Score: {market_summary['score']:+.3f}  |  Label: {market_summary['label']}  |  "
              f"N={market_summary['article_count']}")

    print("\n" + "=" * 70)
    print("TEST COMPLETE — pipeline exercised against live, current headlines.")
    print("=" * 70)


if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 else "RELIANCE.NS"
    name = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Reliance Industries"
    run(sym, name)