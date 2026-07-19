"""DuPont Analysis - ROE Decomposition

3-Step: ROE = Net Margin x Asset Turnover x Equity Multiplier
5-Step: ROE = Tax Burden x Interest Burden x Operating Margin x Asset Turnover x Leverage

Both are MULTIPLICATIVE identities. A previous version of this module fed the raw
factor values into a plotly Waterfall chart, which only makes sense for additive
series - adding a margin percentage to a turnover ratio to an equity multiplier does
not reconstruct ROE, so the chart was numerically meaningless as well as ugly.

This version keeps the multiplicative math for the headline numbers, but ALSO computes
a proper ROE bridge: the exact, additive year-over-year attribution of the change in
ROE to each driver, using sequential (chain) substitution. That identity is exact:

    ROE_t - ROE_(t-1) = MarginEffect + TurnoverEffect + LeverageEffect

so it is legitimate to put on a waterfall chart. It also returns a multi-year time
series of the raw factors so the dashboard can plot trend lines instead of (or next
to) a single-period snapshot.
"""
import pandas as pd


class DuPontAnalysis:

    @staticmethod
    def _get_val(df, keys, col_idx):
        for k in keys:
            if k in df.index and col_idx < len(df.columns):
                v = df.loc[k, df.columns[col_idx]]
                if pd.notna(v) and v != 0:
                    return float(v)
        return 0

    @classmethod
    def _period_components(cls, income_df, balance_df, col_idx):
        """3-step + 5-step components for a single reporting period (year)."""
        g = lambda df, keys: cls._get_val(df, keys, col_idx)

        rev = g(income_df, ['Total Revenue', 'Revenue'])
        ni = g(income_df, ['Net Income', 'Net Income Common Stockholders'])
        ebit = g(income_df, ['EBIT', 'Operating Income'])
        ebt = g(income_df, ['Pretax Income', 'Income Before Tax'])
        ta = g(balance_df, ['Total Assets'])
        eq = g(balance_df, ['Stockholders Equity', 'Total Stockholder Equity', 'Total Equity', 'Common Stock Equity'])

        if not all([rev, ni, ta, eq]):
            return None

        net_margin = ni / rev
        asset_turnover = rev / ta
        equity_multiplier = ta / eq
        roe = net_margin * asset_turnover * equity_multiplier

        out = {
            'net_margin': net_margin,
            'asset_turnover': asset_turnover,
            'equity_multiplier': equity_multiplier,
            'roe': roe,
        }

        if ebit and ebt:
            tax_burden = ni / ebt if ebt else 1
            interest_burden = ebt / ebit if ebit else 1
            op_margin = ebit / rev
            out.update({
                'tax_burden': tax_burden,
                'interest_burden': interest_burden,
                'op_margin': op_margin,
                'roe_5step': tax_burden * interest_burden * op_margin * asset_turnover * equity_multiplier,
            })
        return out

    @staticmethod
    def calculate(income_df, balance_df, ratios):
        try:
            if income_df is None or balance_df is None:
                return None
            if income_df.empty or balance_df.empty:
                return None

            n_years = min(len(income_df.columns), len(balance_df.columns), 5)
            if n_years < 1:
                return None

            periods = []
            labels = []
            for i in range(n_years):
                comp = DuPontAnalysis._period_components(income_df, balance_df, i)
                if comp is None:
                    continue
                periods.append(comp)
                try:
                    labels.append(str(pd.to_datetime(income_df.columns[i]).year))
                except Exception:
                    labels.append(str(income_df.columns[i])[:10])

            if not periods:
                return None

            # Most recent period is index 0 in the source data; reverse to chronological
            periods_chrono = list(reversed(periods))
            labels_chrono = list(reversed(labels))

            current = periods[0]
            net_margin = current['net_margin'] * 100
            asset_turnover = current['asset_turnover']
            equity_multiplier = current['equity_multiplier']
            roe_3step = current['roe'] * 100

            has_5step = 'roe_5step' in current
            tax_burden = interest_burden = op_margin = roe_5step = None
            if has_5step:
                tax_burden = current['tax_burden']
                interest_burden = current['interest_burden']
                op_margin = current['op_margin'] * 100
                roe_5step = current['roe_5step'] * 100

            # ROE Bridge: exact sequential-substitution attribution of the
            # year-over-year change in ROE to Margin / Turnover / Leverage.
            bridge = None
            if len(periods) >= 2:
                prev = periods[1]
                m0, t0, l0 = prev['net_margin'], prev['asset_turnover'], prev['equity_multiplier']
                m1, t1, l1 = current['net_margin'], current['asset_turnover'], current['equity_multiplier']

                roe0 = m0 * t0 * l0
                roe1 = m1 * t1 * l1

                margin_effect = (m1 - m0) * t0 * l0
                turnover_effect = m1 * (t1 - t0) * l0
                leverage_effect = m1 * t1 * (l1 - l0)

                bridge = {
                    'start_label': labels[1],
                    'end_label': labels[0],
                    'roe_start': round(roe0 * 100, 2),
                    'roe_end': round(roe1 * 100, 2),
                    'margin_effect': round(margin_effect * 100, 2),
                    'turnover_effect': round(turnover_effect * 100, 2),
                    'leverage_effect': round(leverage_effect * 100, 2),
                }

            # Multi-year trend series (chronological order)
            trend = {
                'labels': labels_chrono,
                'net_margin': [round(p['net_margin'] * 100, 2) for p in periods_chrono],
                'asset_turnover': [round(p['asset_turnover'], 3) for p in periods_chrono],
                'equity_multiplier': [round(p['equity_multiplier'], 2) for p in periods_chrono],
                'roe': [round(p['roe'] * 100, 2) for p in periods_chrono],
            }

            return {
                'roe': round(ratios.get('ROE', roe_3step), 1),
                'three_step': {
                    'net_margin': round(net_margin, 1),
                    'asset_turnover': round(asset_turnover, 3),
                    'equity_multiplier': round(equity_multiplier, 2),
                    'roe': round(roe_3step, 1),
                },
                'five_step': {
                    'tax_burden': round(tax_burden, 3),
                    'interest_burden': round(interest_burden, 3),
                    'operating_margin': round(op_margin, 1),
                    'asset_turnover': round(asset_turnover, 3),
                    'equity_multiplier': round(equity_multiplier, 2),
                    'roe': round(roe_5step, 1),
                } if has_5step else None,
                'bridge': bridge,
                'trend': trend if len(periods_chrono) >= 2 else None,
            }
        except Exception:
            return None