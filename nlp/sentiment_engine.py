"""Financial headline sentiment scoring.

Engine priority, in order:
    1. FinBERT (ProsusAI/finbert) — a BERT model fine-tuned specifically on
       financial text, via the `transformers` library. This is the primary
       scorer whenever it's available, since it actually understands
       financial phrasing ("beat on the top line", "guided down") rather
       than relying on a hand-built keyword list.
    2. VADER (general-purpose sentiment) + the financial/India phrase
       lexicon — the ORIGINAL local, no-download scorer this module used
       before FinBERT was added. This remains fully in place as an
       automatic fallback.
    3. Lexicon-only — if even VADER's package isn't installed.

FinBERT requires `transformers` + a torch/tf backend and downloads a
~400MB model the first time it's used, so it can fail to load for
several reasons (package not installed, no internet on first run, out
of memory, etc). Loading is attempted lazily, exactly once, wrapped in
a broad try/except — any failure permanently (for the process lifetime)
falls back to VADER+lexicon rather than raising. Nothing about the
original VADER/lexicon path was removed or changed; it's still the
exact scorer used when FinBERT isn't available.

In both paths, the India-specific phrase lexicon (sentiment_lexicon.py)
is blended in, since neither VADER nor FinBERT's training data has much
exposure to Indian-market-specific phrasing like "promoter pledge" or
"PLI scheme".
"""

from functools import lru_cache

from nlp.sentiment_lexicon import (
    FINANCIAL_VADER_TERMS,
    INDIA_NEGATIVE,
    INDIA_POSITIVE,
    STRONG_NEGATIVE,
    STRONG_POSITIVE,
)

# ── VADER (fallback engine #2) — unchanged from before FinBERT was added ──
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _vader = SentimentIntensityAnalyzer()
    _vader.lexicon.update(FINANCIAL_VADER_TERMS)
    _VADER_AVAILABLE = True
except Exception:
    _vader = None
    _VADER_AVAILABLE = False

# ── FinBERT (primary engine #1) — lazy-loaded, never imported eagerly ──
_finbert_pipe = None
_finbert_load_attempted = False
_FINBERT_AVAILABLE = False
_FINBERT_LOAD_ERROR = None


def _load_finbert():
    """Attempt to build the FinBERT pipeline exactly once per process.

    Returns the pipeline callable, or None if unavailable for any reason
    (package missing, no internet for the model download, etc).
    """
    global _finbert_pipe, _finbert_load_attempted, _FINBERT_AVAILABLE, _FINBERT_LOAD_ERROR
    if _finbert_load_attempted:
        return _finbert_pipe

    _finbert_load_attempted = True
    try:
        from transformers import pipeline
        _finbert_pipe = pipeline(
            "text-classification",
            model="ProsusAI/finbert",
            top_k=None,       # return scores for all 3 classes, not just the top one
            truncation=True,
        )
        _FINBERT_AVAILABLE = True
    except Exception as e:
        _finbert_pipe = None
        _FINBERT_AVAILABLE = False
        _FINBERT_LOAD_ERROR = str(e)
    return _finbert_pipe


def _finbert_scores(texts):
    """Batch-score a list of headline strings with FinBERT.

    Returns a list of {"score": -1..1, "top_label": str, "confidence": 0..1}
    aligned 1:1 with `texts`, or None if FinBERT isn't available / the call
    fails (caller should fall back to VADER+lexicon in that case).
    """
    pipe = _load_finbert()
    if pipe is None:
        return None
    try:
        raw = pipe(list(texts))
    except Exception:
        return None

    results = []
    for item in raw:
        # top_k=None returns a list of {"label": ..., "score": ...} per class
        probs = {d["label"].lower(): d["score"] for d in item}
        pos = probs.get("positive", 0.0)
        neg = probs.get("negative", 0.0)
        score = pos - neg  # -1..1, continuous (more informative than just the top label)
        top_label = max(probs, key=probs.get) if probs else "neutral"
        confidence = probs.get(top_label, 0.5)
        results.append({"score": score, "top_label": top_label, "confidence": confidence})
    return results


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


def _label_for(score):
    if score > 0.15:
        return "POSITIVE"
    if score < -0.15:
        return "NEGATIVE"
    return "NEUTRAL"


def _neutral_result():
    return {"score": 0.0, "label": "NEUTRAL", "confidence": 0.4, "engine": "none"}


def engine_status():
    """Report which engines are available and which one is currently active.
    Useful for the dashboard to show the user what actually scored the news."""
    _load_finbert()  # make sure the lazy load has been attempted
    if _FINBERT_AVAILABLE:
        active = "finbert"
    elif _VADER_AVAILABLE:
        active = "vader+lexicon"
    else:
        active = "lexicon"
    return {
        "finbert_available": _FINBERT_AVAILABLE,
        "finbert_error": _FINBERT_LOAD_ERROR,
        "vader_available": _VADER_AVAILABLE,
        "active_engine": active,
    }


def _blend_with_lexicon(primary_score, lexicon_score, primary_weight=0.75):
    """Blend the primary model's score with the India/financial phrase
    lexicon match, if the lexicon actually matched anything on this text."""
    if lexicon_score == 0.0:
        return primary_score
    return primary_score * primary_weight + lexicon_score * (1 - primary_weight)


@lru_cache(maxsize=2048)
def analyze_sentiment(text):
    """Score a single headline for financial sentiment.

    Returns {"score": -1..1, "label": POSITIVE/NEGATIVE/NEUTRAL,
             "confidence": 0..1, "engine": "finbert"|"vader+lexicon"|"lexicon"}
    """
    if not text:
        return _neutral_result()

    text_lower = text.lower()
    lexicon_score = _lexicon_score(text_lower)

    fb = _finbert_scores([text])
    if fb:
        final_score = _blend_with_lexicon(fb[0]["score"], lexicon_score)
        confidence = round(min(0.97, fb[0]["confidence"]), 2)
        engine = "finbert"
    elif _VADER_AVAILABLE:
        vader_score = _vader.polarity_scores(text)["compound"]
        final_score = vader_score * 0.45 + lexicon_score * 0.55
        agree = abs(vader_score - lexicon_score) < 0.6
        confidence = 0.75 if agree else 0.55
        engine = "vader+lexicon"
    else:
        final_score = lexicon_score
        confidence = 0.5
        engine = "lexicon"

    final_score = max(-1.0, min(1.0, final_score))
    label = _label_for(final_score)

    if final_score == 0.0 and engine != "finbert":
        confidence = 0.4

    return {"score": round(final_score, 3), "label": label, "confidence": round(confidence, 2), "engine": engine}


def analyze_articles_batch(articles):
    """articles: list of {"title": ..., ...}. Attaches a "sentiment" key
    to each (mutates and returns the same list).

    When FinBERT is available, all headlines are scored in a single batched
    model call (much faster than scoring one-by-one) and each result is
    still blended with the local lexicon. If FinBERT is unavailable or the
    batch call fails for any reason, this transparently falls back to
    scoring each headline individually with analyze_sentiment(), which
    itself falls back to VADER+lexicon.
    """
    if not articles:
        return articles

    texts = [a.get("title", "") or "" for a in articles]
    fb_batch = _finbert_scores(texts) if any(texts) else None

    if fb_batch is not None and len(fb_batch) == len(articles):
        for article, fb, text in zip(articles, fb_batch, texts):
            if not text:
                article["sentiment"] = _neutral_result()
                continue
            lexicon_score = _lexicon_score(text.lower())
            final_score = _blend_with_lexicon(fb["score"], lexicon_score)
            final_score = max(-1.0, min(1.0, final_score))
            article["sentiment"] = {
                "score": round(final_score, 3),
                "label": _label_for(final_score),
                "confidence": round(min(0.97, fb["confidence"]), 2),
                "engine": "finbert",
            }
    else:
        # FinBERT unavailable or the batch call failed — fall back per-article,
        # which itself resolves to VADER+lexicon (or lexicon-only).
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