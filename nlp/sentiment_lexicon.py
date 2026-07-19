"""Financial sentiment lexicon (Indian-market aware).

A general-purpose sentiment analyzer (VADER, etc.) doesn't know that
"beat estimates" is positive or that "lower circuit" is bad news —
this is domain vocabulary a finance-focused scorer needs explicitly.
Purely a keyword/pattern lexicon: no network calls, no fabricated
figures, just a transparent heuristic weighting of headline text.
"""

STRONG_POSITIVE = {
    "record profit": 0.95, "beat expectations": 0.90, "beats expectations": 0.90,
    "beat estimates": 0.90, "beats estimates": 0.90, "raised guidance": 0.90,
    "strong growth": 0.85, "blockbuster": 0.85, "surge": 0.80, "soar": 0.80,
    "breakthrough": 0.85, "upgrade": 0.75, "outperform": 0.75,
    "market leader": 0.80, "dividend increase": 0.70, "buyback announcement": 0.70,
    "new contract": 0.65, "expansion": 0.60, "all-time high": 0.85,
    "record high": 0.85, "multibagger": 0.80, "order win": 0.65,
    "bonus issue": 0.75, "stock split": 0.65, "rights issue": 0.50,
}

STRONG_NEGATIVE = {
    "bankruptcy": -1.00, "fraud": -0.95, "investigation": -0.85,
    "guidance cut": -0.85, "missed expectations": -0.80, "miss expectations": -0.80,
    "missed estimates": -0.80, "miss estimates": -0.80, "downgrade": -0.75,
    "underperform": -0.75, "plunge": -0.80, "crash": -0.90, "scandal": -0.90,
    "lawsuit": -0.80, "restructuring": -0.60, "layoffs": -0.65,
    "debt crisis": -0.85, "regulatory fine": -0.80, "profit warning": -0.85,
    "sebi action": -0.85, "sebi ban": -0.90, "rbi penalty": -0.80,
    "npa increase": -0.75, "asset quality deterioration": -0.75,
    "lower circuit": -0.85, "auditor resignation": -0.80, "promoter pledge": -0.70,
}

# Terms not in VADER's general-purpose lexicon by default — merged
# into a SentimentIntensityAnalyzer instance's .lexicon before use.
FINANCIAL_VADER_TERMS = {
    "beat": 2.0, "beats": 2.0, "upgrade": 2.5, "upgraded": 2.5,
    "downgrade": -2.5, "downgraded": -2.5, "miss": -2.0, "missed": -2.0,
    "rally": 1.5, "surge": 2.0, "plunge": -2.0, "crash": -3.0,
    "bullish": 2.0, "bearish": -2.0, "outperform": 2.0, "underperform": -2.0,
    "dividend": 1.0, "buyback": 1.5, "bankruptcy": -4.0, "default": -3.0,
}

INDIA_POSITIVE = [
    "make in india", "atmanirbhar", "pli scheme",
    "production linked incentive", "china plus one",
]
INDIA_NEGATIVE = [
    "policy uncertainty", "retrospective tax", "regulatory hurdle",
    "import restriction", "export ban",
]