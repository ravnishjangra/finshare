"""Benjamin Graham Valuation"""
class GrahamValuation:
    @staticmethod
    def calculate(eps, growth_rate, bond_yield=0.07):
        if eps is None or eps <= 0: return 0
        return eps * (8.5 + 2 * growth_rate * 100) * 4.4 / (bond_yield * 100)