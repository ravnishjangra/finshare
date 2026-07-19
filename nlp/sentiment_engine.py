"""Lightweight financial headline sentiment scoring.

Ensembles two independent, fully local signals — no network calls, no
LLM/API cost, nothing fabricated:
    1. VADER (general-purpose sentiment), extended with financial terms
    2. A weighted financial phrase lexicon (Indian-market aware)

If the optional `vaderSentiment` package isn't installed, this falls
back to lexicon-only scoring rather than failing — the news tab
should never break just because sentiment scoring degrades.
"""

from functools import lru_cache

from nlp.sentiment_lexicon import (
    FINANCIAL_VADER_TERMS,
    INDIA_NEGATIVE,
    INDIA_POSITIVE,
    STRONG_NEGATIVE,
    STRONG_POSITIVE,
)

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _vader = SentimentIntensityAnalyzer()
    _vader.lexicon.update(FINANCIAL_VADER_TERMS)
    _VADER_AVAILABLE = True
except Exception:
    _vader = None
    _VADER_AVAILABLE = False


def _lexicon_score(text_lower):
    score, matches = 0.0, 0
    for phrase, weight in STRONG_POSITIVE.items():
        if phrase in text_lower:
            score += weight
            matches += 1
    for phrase, weight in STRONG_NEGATIVE.items():
        if phrase in text_lower:
            score += weight
            matches += 1
    for phrase in INDIA_POSITIVE:
        if phrase in text_lower:
            score += 0.3
            matches += 1
    for phrase in INDIA_NEGATIVE:
        if phrase in text_lower:
            score -= 0.3
            matches += 1
    if matches:
        score = score / (matches ** 0.5)  # dampen effect of many matches
    return max(-1.0, min(1.0, score))


def _neutral_result():
    return {"score": 0.0, "label": "NEUTRAL", "confidence": 0.4}


@lru_cache(maxsize=2048)
def analyze_sentiment(text):
    """Score a headline for financial sentiment.

    Returns {"score": -1..1, "label": POSITIVE/NEGATIVE/NEUTRAL, "confidence": 0..1}
    """
    if not text:
        return _neutral_result()

    text_lower = text.lower()
    financial_score = _lexicon_score(text_lower)

    if _VADER_AVAILABLE:
        vader_score = _vader.polarity_scores(text)["compound"]
        final_score = vader_score * 0.45 + financial_score * 0.55
        agree = abs(vader_score - financial_score) < 0.6
        confidence = 0.75 if agree else 0.55
    else:
        final_score = financial_score
        confidence = 0.5

    final_score = max(-1.0, min(1.0, final_score))

    if final_score > 0.15:
        label = "POSITIVE"
    elif final_score < -0.15:
        label = "NEGATIVE"
    else:
        label = "NEUTRAL"

    if final_score == 0.0:
        confidence = 0.4

    return {"score": round(final_score, 3), "label": label, "confidence": round(confidence, 2)}


def analyze_articles_batch(articles):
    """articles: list of {"title": ..., ...}. Attaches a "sentiment" key
    to each (mutates and returns the same list)."""
    for article in articles:
        article["sentiment"] = analyze_sentiment(article.get("title", ""))
    return articles


def aggregate_sentiment(sentiments):
    """Combine multiple analyze_sentiment() results into one summary."""
    if not sentiments:
        return {"score": 0.0, "label": "NEUTRAL", "article_count": 0,
                "label_distribution": {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}, "confidence": 0.0}

    avg_score = sum(s["score"] for s in sentiments) / len(sentiments)
    labels = [s["label"] for s in sentiments]
    label_counts = {
        "POSITIVE": labels.count("POSITIVE"),
        "NEGATIVE": labels.count("NEGATIVE"),
        "NEUTRAL": labels.count("NEUTRAL"),
    }
    dominant_label = max(label_counts, key=label_counts.get)

    return {
        "score": round(avg_score, 3),
        "label": dominant_label,
        "article_count": len(sentiments),
        "label_distribution": label_counts,
        "confidence": round(sum(s["confidence"] for s in sentiments) / len(sentiments), 2),
    }