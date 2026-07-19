"""Advanced DCF Valuation Model"""
import numpy as np
import pandas as pd


def _safe_get(df, keys, col=0):
    """Same convention as analyzer._safe_get / other models: col 0 = most recent."""
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


class AdvancedDCF:
    """
    Two-stage FCFF DCF with a Gordon Growth terminal value.

    Key fixes vs. the previous version:
      1. WACC now uses the company's ACTUAL capital structure (market value of
         equity vs. total debt) instead of a fixed 75/25 split.
      2. Cost of debt is derived from actual interest expense / total debt when
         available, instead of a flat Rf + 3% guess.
      3. Enterprise Value is correctly bridged to Equity Value (EV - Net Debt)
         before dividing by share count. The old version divided EV directly by
         shares, which overstates intrinsic value per share for any company
         carrying net debt (and understates it for net-cash companies).
    """

    def __init__(self, fcf, shares, current_price, revenue_growth, beta,
                 risk_free_rate, market_return,
                 total_debt=0.0, cash=0.0, interest_expense=None,
                 tax_rate=0.25, market_cap=None,
                 balance_df=None, income_df=None):
        self.fcf = fcf
        self.shares = shares
        self.current_price = current_price
        self.revenue_growth = revenue_growth
        self.beta = beta
        self.risk_free_rate = risk_free_rate
        self.market_return = market_return
        self.tax_rate = tax_rate

        # ---- Pull actual capital structure from financials if a balance
        # sheet was supplied and explicit values weren't passed in ----
        if balance_df is not None:
            if not total_debt:
                total_debt = _safe_get(balance_df, ['Total Debt', 'Long Term Debt']) or 0.0
            if not cash:
                cash = _safe_get(balance_df, ['Cash And Cash Equivalents',
                                               'Cash Cash Equivalents And Short Term Investments',
                                               'Cash']) or 0.0

        if interest_expense is None and income_df is not None:
            interest_expense = _safe_get(income_df, ['Interest Expense', 'Interest Expense Non Operating'])

        self.total_debt = total_debt or 0.0
        self.cash = cash or 0.0
        self.net_debt = self.total_debt - self.cash

        # ---- Cost of equity: CAPM (unchanged, this was already correct) ----
        cost_of_equity = risk_free_rate + beta * (market_return - risk_free_rate)

        # ---- Cost of debt: from actual interest burden when we can compute
        # it sensibly, else a credit-spread proxy over the risk-free rate ----
        if interest_expense and self.total_debt > 0:
            implied_cod = abs(interest_expense) / self.total_debt
            # sanity-bound it: no company reliably borrows at less than Rf,
            # or absurdly more than Rf + 10%, given data noise
            cost_of_debt = min(max(implied_cod, risk_free_rate + 0.005), risk_free_rate + 0.10)
        else:
            cost_of_debt = risk_free_rate + 0.03  # fallback proxy spread

        # ---- Capital structure weights from ACTUAL market values ----
        equity_value = market_cap if market_cap else (current_price * shares if current_price and shares else 0)
        total_capital = equity_value + self.total_debt
        if total_capital > 0:
            e_weight = equity_value / total_capital
            d_weight = self.total_debt / total_capital
        else:
            # no data at all -> fall back to an all-equity assumption rather
            # than silently guessing a capital structure
            e_weight, d_weight = 1.0, 0.0

        self.cost_of_equity = cost_of_equity
        self.cost_of_debt = cost_of_debt
        self.e_weight = e_weight
        self.d_weight = d_weight
        self.wacc = e_weight * cost_of_equity + d_weight * cost_of_debt * (1 - tax_rate)

    def project_cashflows(self, years=10):
        projections = []
        fcf = self.fcf
        for year in range(1, years + 1):
            growth = self.revenue_growth * (1 - (year - 1) * 0.07)
            growth = max(growth, 0.025)
            fcf = fcf * (1 + growth)
            pv = fcf / (1 + self.wacc) ** year
            projections.append({'year': year, 'growth': growth, 'fcf': fcf, 'pv_fcf': pv})
        return projections

    def calculate(self):
        projections = self.project_cashflows(10)
        pv_fcfs = sum(p['pv_fcf'] for p in projections)
        last_fcf = projections[-1]['fcf']
        terminal_value = last_fcf * 1.025 / (self.wacc - 0.025) if self.wacc > 0.025 else last_fcf * 20
        pv_terminal = terminal_value / (1 + self.wacc) ** 10
        enterprise_value = pv_fcfs + pv_terminal

        # Bridge EV -> Equity Value (this step was missing before)
        equity_value = enterprise_value - self.net_debt

        intrinsic_value = equity_value / self.shares if self.shares > 0 else 0
        upside = ((intrinsic_value / self.current_price) - 1) * 100 if self.current_price > 0 else 0
        bear_iv = intrinsic_value * 0.6
        bull_iv = intrinsic_value * 1.5

        if upside > 30: rec, rc = "STRONG BUY 🟢", "#10b981"
        elif upside > 10: rec, rc = "BUY 🟢", "#34d399"
        elif upside > -10: rec, rc = "HOLD 🟡", "#f59e0b"
        elif upside > -30: rec, rc = "SELL 🔴", "#ef4444"
        else: rec, rc = "STRONG SELL 🔴", "#dc2626"

        return {'intrinsic_value': intrinsic_value, 'current_price': self.current_price,
                'upside': upside, 'wacc': self.wacc,
                'cost_of_equity': self.cost_of_equity, 'cost_of_debt': self.cost_of_debt,
                'e_weight': self.e_weight, 'd_weight': self.d_weight,
                'net_debt': self.net_debt,
                'pv_fcfs': pv_fcfs, 'terminal_value': terminal_value, 'pv_terminal': pv_terminal,
                'enterprise_value': enterprise_value, 'equity_value': equity_value,
                'projections': projections,
                'bear_case': bear_iv, 'bull_case': bull_iv, 'recommendation': rec, 'rec_color': rc}