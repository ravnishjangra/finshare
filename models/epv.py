"""Earnings Power Value (Columbia Model)"""
class EarningsPowerValue:
    @staticmethod
    def calculate(revenue, operating_margin, tax_rate, wacc, shares):
        if not revenue or revenue <= 0 or not shares or shares <= 0 or wacc <= 0:
            return 0
        sustainable_rev = revenue * 0.9
        sustainable_margin = max(operating_margin * 0.8, 0.05)
        nopat = sustainable_rev * sustainable_margin * (1 - tax_rate)
        epv = nopat / wacc
        return epv / shares