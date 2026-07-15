"""Stress Test Engine - 30 Scenarios"""
import numpy as np
import pandas as pd

class StressTestEngine:
    def __init__(self, current_price, sector, industry, beta, currency, market_cap):
        self.price = current_price
        self.sector = sector
        self.industry = industry
        self.beta = beta or 1.0
        self.currency = currency
        self.market_cap = market_cap or 0

    def run_all_tests(self):
        results = []
        b = self.beta
        p = self.price

        for pct in [-10, -20, -30, -50]:
            impact = p * (1 + pct/100 * b)
            loss = (impact/p - 1) * 100
            sev = '🔴 CRITICAL' if loss < -30 else '🟠 HIGH' if loss < -20 else '🟡 MODERATE' if loss < -10 else '🟢 LOW'
            results.append({'Test': f'Market Crash ({abs(pct)}%)', 'Impact Price': round(impact,2), 'Loss %': round(loss,1), 'Severity': sev})

        for pct in [10, 20, 30]:
            impact = p * (1 + pct/100 * b)
            gain = (impact/p - 1) * 100
            results.append({'Test': f'Bull Rally (+{pct}%)', 'Impact Price': round(impact,2), 'Loss %': round(gain,1), 'Severity': '🟢 POSITIVE'})

        for bps in [100, 200, -100, -200]:
            rs = 1.5 if self.sector in ['Financial Services'] else 1.0
            ipct = -bps/100 * 0.05 * b * rs
            impact = p * (1 + ipct)
            sev = '🔴 CRITICAL' if ipct < -0.1 else '🟠 HIGH' if ipct < -0.05 else '🟡 MODERATE'
            results.append({'Test': f'Rate {"Hike" if bps>0 else "Cut"} ({abs(bps)}bps)', 'Impact Price': round(impact,2), 'Loss %': round(ipct*100,1), 'Severity': sev})

        for inf in [5, 10, 15]:
            ins = 0.8 if self.sector in ['Consumer Defensive'] else 1.2
            ipct = -inf/100 * 0.03 * b * ins
            impact = p * (1 + ipct)
            results.append({'Test': f'Inflation Spike ({inf}%)', 'Impact Price': round(impact,2), 'Loss %': round(ipct*100,1), 'Severity': '🔴 CRITICAL' if ipct < -0.15 else '🟠 HIGH'})

        for pct in [5, 10, -5, -10]:
            fs = 1.3 if self.sector in ['Technology'] else 0.7
            ipct = -pct/100 * 0.02 * fs if self.currency == 'INR' else pct/100 * 0.01 * fs
            impact = p * (1 + ipct)
            results.append({'Test': f'Currency Shock ({abs(pct)}%)', 'Impact Price': round(impact,2), 'Loss %': round(ipct*100,1), 'Severity': '🟡 MODERATE'})

        for mult in [2, 3]:
            ipct = -0.05 * mult * b
            impact = p * (1 + ipct)
            results.append({'Test': f'VIX Spike (x{mult})', 'Impact Price': round(impact,2), 'Loss %': round(ipct*100,1), 'Severity': '🔴 CRITICAL' if mult >= 3 else '🟠 HIGH'})

        for pct in [-50, -75, -90]:
            impact = p * (1 + pct/100)
            results.append({'Test': f'Stock Collapse ({abs(pct)}%)', 'Impact Price': round(impact,2), 'Loss %': pct, 'Severity': '🔴 CRITICAL'})

        results.append({'Test': 'Bankruptcy (100% Loss)', 'Impact Price': 0, 'Loss %': -100, 'Severity': '💀 MAXIMUM'})
        results.append({'Test': 'Liquidity Crisis', 'Impact Price': round(p*0.85,2), 'Loss %': -15, 'Severity': '🟠 HIGH'})
        results.append({'Test': 'Governance Scandal', 'Impact Price': round(p*0.60,2), 'Loss %': -40, 'Severity': '🔴 CRITICAL'})
        results.append({'Test': 'Geopolitical Conflict', 'Impact Price': round(p*0.80,2), 'Loss %': -20, 'Severity': '🟠 HIGH'})

        impact = p * (1.15 if self.sector in ['Healthcare', 'Technology'] else 0.70)
        results.append({'Test': 'Pandemic Scenario', 'Impact Price': round(impact,2), 'Loss %': round((impact/p-1)*100,1), 'Severity': '🟢 WINNER' if impact > p else '🔴 LOSER'})

        impact = p * (0.65 if self.sector in ['Consumer Cyclical'] else 0.85)
        results.append({'Test': 'Recession', 'Impact Price': round(impact,2), 'Loss %': round((impact/p-1)*100,1), 'Severity': '🔴 CRITICAL'})

        results.append({'Test': 'War Scenario', 'Impact Price': round(p*0.55,2), 'Loss %': -45, 'Severity': '💀 EXTREME'})

        return pd.DataFrame(results)