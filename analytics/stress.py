"""Stress Test Engine - Distinct Scenario Library

Previously this engine ran the *same* handful of shock formulas at several
magnitudes (Market Crash -10/-20/-30/-50%, Rate Hike/Cut +/-100/200bps,
Inflation Spike 5/10/15%, ...). That's really one scenario repeated with a
slider, not a stress-test suite - every row told you the same story at a
different volume.

This version instead models a library of DISTINCT, named real-world (or
historically-grounded) scenarios. Each one has its own narrative, its own
base severity, its own sector sensitivity profile, and its own sensitivity
to beta - a governance scandal doesn't care about the stock's beta, but a
market-wide rate shock does. No two scenarios share a formula.
"""
import pandas as pd


class StressTestEngine:
    def __init__(self, current_price, sector, industry, beta, currency, market_cap):
        self.price = current_price
        self.sector = sector or "Unknown"
        self.industry = industry or "Unknown"
        self.beta = beta or 1.0
        self.currency = currency
        self.market_cap = market_cap or 0

    # Each scenario: (name, category, description, base_shock, beta_sensitivity,
    #                 sector_multipliers)
    # base_shock: fractional price move at beta=1 / neutral sector (e.g. -0.30 = -30%)
    # beta_sensitivity: 0 = fully idiosyncratic (beta irrelevant), 1 = fully
    #                    market-driven (shock scales linearly with beta)
    # sector_multipliers: dict of sector -> multiplier on the shock magnitude;
    #                      sectors not listed use 1.0
    SCENARIOS = [
        dict(name="2008-Style Global Financial Crisis", category="Systemic",
             desc="Credit freeze + deleveraging shock across all asset classes, echoing 2008.",
             base=-0.38, beta_sens=1.0,
             sector_mult={"Financial Services": 1.35, "Real Estate": 1.3, "Consumer Defensive": 0.6, "Healthcare": 0.65}),

        dict(name="2020-Style Pandemic Crash (V-Shaped)", category="Systemic",
             desc="Sudden lockdown shock with a fast, sharp initial drawdown.",
             base=-0.30, beta_sens=0.9,
             sector_mult={"Healthcare": 0.5, "Technology": 0.55, "Consumer Cyclical": 1.35, "Energy": 1.45, "Industrials": 1.2}),

        dict(name="Black Monday-Style Single-Day Crash", category="Systemic",
             desc="Program-trading-driven single-session crash, amplified by high-beta names.",
             base=-0.22, beta_sens=1.4,
             sector_mult={}),

        dict(name="Dot-Com Style Valuation Bubble Burst", category="Systemic",
             desc="Multiple compression hits richly-valued growth names hardest.",
             base=-0.32, beta_sens=0.6,
             sector_mult={"Technology": 1.75, "Consumer Defensive": 0.5, "Utilities": 0.4}),

        dict(name="Aggressive Central Bank Rate Hike Cycle", category="Macro",
             desc="Sustained tightening (like 2022) compresses valuations, especially rate-sensitive sectors.",
             base=-0.16, beta_sens=0.8,
             sector_mult={"Real Estate": 1.6, "Technology": 1.4, "Financial Services": 0.6, "Utilities": 1.3}),

        dict(name="Surprise Rate-Cut Easing Cycle", category="Macro",
             desc="Central bank pivots to easing, boosting risk assets broadly.",
             base=0.09, beta_sens=0.7,
             sector_mult={"Real Estate": 1.4, "Technology": 1.3, "Financial Services": 0.7}),

        dict(name="Stagflation (High Inflation + Weak Growth)", category="Macro",
             desc="Margins squeezed by input costs while demand stalls.",
             base=-0.18, beta_sens=0.5,
             sector_mult={"Consumer Defensive": 0.55, "Energy": 0.4, "Consumer Cyclical": 1.5, "Industrials": 1.3}),

        dict(name="Currency Crisis - Sharp Rupee Depreciation", category="Macro",
             desc="Rapid currency depreciation; export-heavy sectors gain, import/debt-heavy sectors suffer.",
             base=-0.11, beta_sens=0.3,
             sector_mult={"Technology": -0.5, "Healthcare": -0.3, "Energy": 1.6, "Consumer Cyclical": 1.3}),

        dict(name="Sovereign Credit Rating Downgrade", category="Macro",
             desc="Rating agency downgrade raises the cost of capital economy-wide.",
             base=-0.10, beta_sens=0.6,
             sector_mult={"Financial Services": 1.5, "Real Estate": 1.4}),

        dict(name="Heavy FII Outflow Episode", category="Macro",
             desc="Foreign institutional investors pull capital from the market rapidly (common India-specific shock).",
             base=-0.13, beta_sens=1.2,
             sector_mult={"Financial Services": 1.2}),

        dict(name="Banking System Liquidity / Credit Crunch", category="Financial",
             desc="Interbank lending seizes up; credit-dependent sectors are starved of funding.",
             base=-0.20, beta_sens=0.5,
             sector_mult={"Financial Services": 1.9, "Real Estate": 1.6, "Consumer Defensive": 0.5}),

        dict(name="Bond Market Selloff / Yield Spike", category="Financial",
             desc="Long-end yields spike sharply, repricing every duration-sensitive asset.",
             base=-0.11, beta_sens=0.6,
             sector_mult={"Financial Services": 1.4, "Real Estate": 1.6, "Utilities": 1.3}),

        dict(name="Corporate Governance Scandal / Fraud Allegation", category="Idiosyncratic",
             desc="Company-specific trust breakdown; largely disconnected from market beta.",
             base=-0.35, beta_sens=0.05,
             sector_mult={}),

        dict(name="Company-Specific Debt Default", category="Idiosyncratic",
             desc="Failure to service debt obligations triggers a credit event.",
             base=-0.50, beta_sens=0.0,
             sector_mult={}),

        dict(name="Promoter Pledge Unwind / Block-Deal Selloff", category="Idiosyncratic",
             desc="Forced selling from pledged-share margin calls or a large block deal (India-specific).",
             base=-0.22, beta_sens=0.2,
             sector_mult={}),

        dict(name="Cyberattack / Major Data Breach", category="Idiosyncratic",
             desc="Operational and reputational shock from a security incident.",
             base=-0.15, beta_sens=0.1,
             sector_mult={"Technology": 1.3, "Financial Services": 1.3}),

        dict(name="Sector-Specific Regulatory Crackdown", category="Regulatory",
             desc="New rules or an antitrust/compliance action targets the company's sector.",
             base=-0.22, beta_sens=0.2,
             sector_mult={"Technology": 1.35, "Financial Services": 1.3, "Healthcare": 1.2}),

        dict(name="Trade War / Tariff Escalation", category="Macro",
             desc="Tariffs and export restrictions hit globally-exposed, trade-dependent sectors hardest.",
             base=-0.13, beta_sens=0.5,
             sector_mult={"Technology": 1.5, "Industrials": 1.5, "Consumer Defensive": 0.5}),

        dict(name="Oil / Energy Price Shock", category="Macro",
             desc="Sharp spike in crude prices raises input costs economy-wide, except for energy producers.",
             base=-0.14, beta_sens=0.4,
             sector_mult={"Energy": -1.2, "Industrials": 1.4, "Consumer Cyclical": 1.3}),

        dict(name="Geopolitical Conflict / Border Tensions", category="Geopolitical",
             desc="Regional military tension weighs on risk sentiment broadly.",
             base=-0.12, beta_sens=0.7,
             sector_mult={"Energy": 0.5}),

        dict(name="Full-Scale War Scenario", category="Geopolitical",
             desc="Extreme tail-risk conflict scenario with broad economic disruption.",
             base=-0.42, beta_sens=0.6,
             sector_mult={"Energy": 0.4}),

        dict(name="Global Recession", category="Macro",
             desc="Broad demand contraction across consumer and industrial sectors.",
             base=-0.25, beta_sens=0.8,
             sector_mult={"Consumer Cyclical": 1.5, "Industrials": 1.4, "Consumer Defensive": 0.45, "Healthcare": 0.5}),

        dict(name="Pandemic Resurgence (New Variant)", category="Systemic",
             desc="A fresh wave of a health crisis reintroduces lockdown-style risk.",
             base=-0.17, beta_sens=0.5,
             sector_mult={"Healthcare": -0.4, "Consumer Cyclical": 1.5, "Energy": 1.2}),

        dict(name="Global Supply Chain Disruption", category="Macro",
             desc="Logistics and input-supply bottlenecks squeeze production-heavy businesses.",
             base=-0.12, beta_sens=0.4,
             sector_mult={"Industrials": 1.5, "Consumer Cyclical": 1.4, "Technology": 1.2}),

        dict(name="Domestic Political / Election Uncertainty", category="Geopolitical",
             desc="Policy-continuity uncertainty ahead of a major election.",
             base=-0.08, beta_sens=0.6,
             sector_mult={"Financial Services": 1.3}),

        dict(name="Flash Crash (Algorithmic/Technical)", category="Systemic",
             desc="A brief, sharp technical dislocation driven by automated trading, disproportionately hitting volatile names.",
             base=-0.09, beta_sens=1.8,
             sector_mult={}),

        dict(name="Liquidity Squeeze on Thinly-Traded Stock", category="Idiosyncratic",
             desc="Redemption pressure meets low float/turnover, amplifying price impact.",
             base=-0.10, beta_sens=0.2,
             sector_mult={}),

        dict(name="Bull Market Melt-Up", category="Positive",
             desc="Broad-based euphoric rally with strong risk appetite.",
             base=0.25, beta_sens=1.0,
             sector_mult={}),

        dict(name="Short Squeeze / Momentum Spike", category="Positive",
             desc="Rapid, idiosyncratic upside move from a crowded short unwind.",
             base=0.18, beta_sens=0.3,
             sector_mult={}),

        dict(name="Rotation Into Defensives (Risk-Off)", category="Rotation",
             desc="Capital rotates out of growth/cyclicals into defensive, income-generating sectors.",
             base=-0.10, beta_sens=0.3,
             sector_mult={"Consumer Defensive": -0.6, "Utilities": -0.6, "Technology": 1.4, "Consumer Cyclical": 1.3}),
    ]

    def _severity(self, loss_pct):
        if loss_pct >= 8:
            return '🟢 POSITIVE'
        if loss_pct <= -40:
            return '💀 EXTREME'
        if loss_pct <= -25:
            return '🔴 CRITICAL'
        if loss_pct <= -12:
            return '🟠 HIGH'
        if loss_pct < 0:
            return '🟡 MODERATE'
        return '🟢 LOW/NEUTRAL'

    def run_all_tests(self):
        results = []
        b = self.beta
        p = self.price

        for sc in self.SCENARIOS:
            sector_mult = sc['sector_mult'].get(self.sector, 1.0)
            beta_adj = 1 + (b - 1) * sc['beta_sens']
            shock = sc['base'] * sector_mult * beta_adj
            # Clamp to a plausible single-scenario range so an extreme
            # beta/sector combination can't produce a nonsensical >100% move
            shock = max(-0.97, min(0.60, shock))
            impact_price = round(p * (1 + shock), 2)
            loss_pct = round(shock * 100, 1)
            results.append({
                'Test': sc['name'],
                'Category': sc['category'],
                'Impact Price': impact_price,
                'Loss %': loss_pct,
                'Severity': self._severity(loss_pct),
                'Description': sc['desc'],
            })

        # Two pure tail-risk scenarios that aren't beta/sector driven at all
        results.append({
            'Test': 'Bankruptcy (Total Loss)', 'Category': 'Idiosyncratic',
            'Impact Price': 0, 'Loss %': -100.0, 'Severity': '💀 EXTREME',
            'Description': 'Complete loss of equity value in insolvency/liquidation.',
        })

        # Liquidity-tier sensitivity: smaller market caps see a harsher illiquidity discount
        illiquidity_discount = -0.18 if (self.market_cap and self.market_cap < 5e10) else -0.10
        results.append({
            'Test': 'Market-Cap Liquidity Discount Event', 'Category': 'Idiosyncratic',
            'Impact Price': round(p * (1 + illiquidity_discount), 2),
            'Loss %': round(illiquidity_discount * 100, 1),
            'Severity': self._severity(illiquidity_discount * 100),
            'Description': 'Forced-selling discount, harsher for smaller-cap/less liquid names.',
        })

        return pd.DataFrame(results)