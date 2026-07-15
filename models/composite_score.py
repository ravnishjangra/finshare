"""Composite Financial Health Score"""
import numpy as np

class CompositeScore:
    """Weighted score combining all financial metrics into one rating"""
    
    @staticmethod
    def calculate(ratios, piotroski_score=None, altman_score=None, factor_exposures=None):
        score = 0
        max_score = 0
        breakdown = {}
        
        # 1. Profitability (30%)
        profitability = 0
        p_max = 0
        for metric, weight, good_range in [
            ('ROE', 10, (15, 100)),
            ('Net Profit Margin', 10, (10, 100)),
            ('Operating Margin', 5, (10, 100)),
            ('Revenue Growth (YoY)', 5, (10, 500)),
        ]:
            val = ratios.get(metric)
            p_max += weight
            if val is not None:
                low, high = good_range
                if val >= high: profitability += weight
                elif val >= low: profitability += weight * 0.7
                elif val > 0: profitability += weight * 0.3
        
        score += profitability
        max_score += p_max
        breakdown['Profitability'] = round(profitability / p_max * 100) if p_max > 0 else 0
        
        # 2. Financial Health (25%)
        health = 0
        h_max = 0
        for metric, weight, good_range in [
            ('Debt to Equity', 10, (0, 1)),
            ('Current Ratio', 8, (1.5, 100)),
            ('Quick Ratio', 7, (1.0, 100)),
        ]:
            val = ratios.get(metric)
            h_max += weight
            if val is not None:
                low, high = good_range
                if val <= high and val >= low: health += weight
                elif val > 0: health += weight * 0.4
        
        score += health
        max_score += h_max
        breakdown['Financial Health'] = round(health / h_max * 100) if h_max > 0 else 0
        
        # 3. Valuation (20%)
        valuation = 0
        v_max = 0
        for metric, weight, good_range in [
            ('P/E Ratio', 8, (5, 20)),
            ('P/B Ratio', 6, (0.5, 3)),
            ('P/S Ratio', 6, (0.5, 5)),
        ]:
            val = ratios.get(metric)
            v_max += weight
            if val is not None and val > 0:
                low, high = good_range
                if low <= val <= high: valuation += weight
                elif val < low: valuation += weight * 0.6
                elif val < high * 2: valuation += weight * 0.3
        
        score += valuation
        max_score += v_max
        breakdown['Valuation'] = round(valuation / v_max * 100) if v_max > 0 else 0
        
        # 4. Piotroski Bonus (15%)
        if piotroski_score and piotroski_score.get('score'):
            ps = piotroski_score['score']
            score += (ps / 9) * 15
        max_score += 15
        breakdown['Piotroski'] = round(piotroski_score['score'] / 9 * 100) if piotroski_score else 0
        
        # 5. Altman Bonus (10%)
        if altman_score and altman_score.get('z_score'):
            z = altman_score['z_score']
            if z > 2.99: score += 10
            elif z > 1.81: score += 5
            else: score += 2
        max_score += 10
        breakdown['Altman'] = round(altman_score.get('z_score', 0) / 3 * 100) if altman_score else 0
        
        final_score = round(score / max_score * 100) if max_score > 0 else 0
        
        if final_score >= 80: rating, color = '🟢 EXCELLENT', '#10b981'
        elif final_score >= 60: rating, color = '🟡 GOOD', '#f59e0b'
        elif final_score >= 40: rating, color = '🟠 FAIR', '#f97316'
        else: rating, color = '🔴 POOR', '#ef4444'
        
        return {
            'score': final_score,
            'rating': rating,
            'color': color,
            'breakdown': breakdown,
            'max_possible': 100,
        }