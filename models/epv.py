"""Earnings Power Value (Greenwald / Columbia Business School Model)"""
import pandas as pd


def _safe_get(df, keys, col=0):
    if df is None or df.empty:
        return None
    if isinstance(keys, str):
        keys = [keys]
    for key in keys:
        if key in df.index and len(df.columns) > col:
            val = df.loc[key].iloc[col]
            if pd.notna(val):
                return float(val)
    return None


class EarningsPowerValue:
    """
    EPV = Normalized NOPAT / WACC  (no growth assumed - this part was already
    theoretically correct in the old version).

    What's fixed vs. the previous version:
      1. "Normalization" used to be two arbitrary haircuts (revenue x0.9,
         margin x0.8) applied to a single year's numbers. Real EPV normalizes
         by averaging revenue and operating margin across a full cycle
         (multiple years) so one unusually good/bad year doesn't skew the
         result. This version averages up to 5 years of actual reported
         revenue/margin when a multi-year income statement is available, and
         only falls back to a single-year haircut when it isn't.
      2. Tax rate is no longer hardcoded to 25% everywhere - callers can pass
         the company's own effective tax rate.
      3. Optional maintenance-capex adjustment: if average capex materially
         exceeds average D&A (i.e. the company is spending more than it needs
         to just to stand still), the excess is treated as growth capex and
         subtracted from normalized NOPAT before capitalizing. When capex is
         close to D&A (the steady-state assumption Greenwald's method already
         relies on), no extra adjustment is made.
    """

    @staticmethod
    def _normalize_from_history(income_df, years=5):
        """Average revenue and operating margin across up to `years` of
        reported financials. Returns (avg_revenue, avg_margin) or (None, None)
        if there isn't enough data to do this properly."""
        if income_df is None or income_df.empty:
            return None, None

        n = min(years, len(income_df.columns))
        revs, margins = [], []
        for col in range(n):
            rev = _safe_get(income_df, ['Total Revenue', 'Revenue'], col)
            op_inc = _safe_get(income_df, ['Operating Income', 'EBIT'], col)
            if rev and rev > 0 and op_inc is not None:
                revs.append(rev)
                margins.append(op_inc / rev)

        if len(revs) < 2:  # need at least 2 years to call it "normalized"
            return None, None

        avg_rev = sum(revs) / len(revs)
        avg_margin = sum(margins) / len(margins)
        return avg_rev, avg_margin

    @staticmethod
    def _maintenance_capex_adjustment(cashflow_df, years=5):
        """Excess of average capex over average D&A -> treated as growth
        capex and stripped out. Returns 0 if data isn't available (i.e. we
        fall back to the classic Greenwald steady-state assumption that
        capex ~= D&A, so no adjustment is needed)."""
        if cashflow_df is None or cashflow_df.empty:
            return 0.0

        n = min(years, len(cashflow_df.columns))
        capexs, deprs = [], []
        for col in range(n):
            capex = _safe_get(cashflow_df, ['Capital Expenditure', 'Purchase Of PPE'], col)
            depr = _safe_get(cashflow_df, ['Depreciation And Amortization', 'Depreciation'], col)
            if capex is not None:
                capexs.append(abs(capex))
            if depr is not None:
                deprs.append(abs(depr))

        if not capexs or not deprs:
            return 0.0

        avg_capex = sum(capexs) / len(capexs)
        avg_depr = sum(deprs) / len(deprs)
        return max(0.0, avg_capex - avg_depr)

    @staticmethod
    def calculate(revenue, operating_margin, tax_rate, wacc, shares,
                   income_df=None, cashflow_df=None):
        if not shares or shares <= 0 or wacc <= 0:
            return 0

        # Try real multi-year normalization first
        norm_rev, norm_margin = EarningsPowerValue._normalize_from_history(income_df)

        if norm_rev is None:
            # Fallback: no multi-year data available, use single-year figures
            # with a clearly-labeled conservative haircut (same spirit as the
            # old code, but only used when we truly can't do better).
            if not revenue or revenue <= 0:
                return 0
            norm_rev = revenue * 0.9
            norm_margin = max(operating_margin * 0.8, 0.05)
        else:
            norm_margin = max(norm_margin, 0.02)

        nopat = norm_rev * norm_margin * (1 - tax_rate)

        maint_adj = EarningsPowerValue._maintenance_capex_adjustment(cashflow_df)
        sustainable_earnings = max(nopat - maint_adj * (1 - tax_rate), 0)

        epv = sustainable_earnings / wacc
        return epv / shares