"""Advanced DCF Valuation Model"""
import numpy as np

class AdvancedDCF:
    def __init__(self, fcf, shares, current_price, revenue_growth, beta, risk_free_rate, market_return):
        self.fcf = fcf
        self.shares = shares
        self.current_price = current_price
        self.revenue_growth = revenue_growth
        self.beta = beta
        self.risk_free_rate = risk_free_rate
        self.market_return = market_return
        cost_of_equity = risk_free_rate + beta * (market_return - risk_free_rate)
        cost_of_debt = risk_free_rate + 0.03
        self.wacc = 0.75 * cost_of_equity + 0.25 * cost_of_debt * (1 - 0.25)

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
        intrinsic_value = enterprise_value / self.shares if self.shares > 0 else 0
        upside = ((intrinsic_value / self.current_price) - 1) * 100 if self.current_price > 0 else 0
        bear_iv = intrinsic_value * 0.6
        bull_iv = intrinsic_value * 1.5
        
        if upside > 30: rec, rc = "STRONG BUY 🟢", "#10b981"
        elif upside > 10: rec, rc = "BUY 🟢", "#34d399"
        elif upside > -10: rec, rc = "HOLD 🟡", "#f59e0b"
        elif upside > -30: rec, rc = "SELL 🔴", "#ef4444"
        else: rec, rc = "STRONG SELL 🔴", "#dc2626"
        
        return {'intrinsic_value': intrinsic_value, 'current_price': self.current_price,
                'upside': upside, 'wacc': self.wacc, 'pv_fcfs': pv_fcfs,
                'terminal_value': terminal_value, 'pv_terminal': pv_terminal,
                'enterprise_value': enterprise_value, 'projections': projections,
                'bear_case': bear_iv, 'bull_case': bull_iv, 'recommendation': rec, 'rec_color': rc}