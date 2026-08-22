"""
HISTORY AGENT - Tax History & Trend Analysis
Handles multi-year filing comparison, trend analysis, and historical insights
"""

from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict


class HistoryAgent:
    """Agent for tax history and trend analysis"""

    def __init__(self):
        self.current_year = 2025
        self.years_to_compare = 5  # Last 5 years

    def compare_with_previous_year(
        self,
        current_filing: Dict,
        previous_filing: Optional[Dict]
    ) -> Dict:
        """Compare current year vs previous year"""

        if not previous_filing:
            return {
                "comparison_available": False,
                "message": "No previous year data available for comparison"
            }

        # Income comparison
        current_income = current_filing.get("total_income", 0)
        previous_income = previous_filing.get("total_income", 0)
        income_change = current_income - previous_income
        income_change_pct = (income_change / previous_income * 100) if previous_income > 0 else 0

        # Tax comparison
        current_tax = current_filing.get("total_tax_liability", 0)
        previous_tax = previous_filing.get("total_tax_liability", 0)
        tax_change = current_tax - previous_tax
        tax_change_pct = (tax_change / previous_tax * 100) if previous_tax > 0 else 0

        # Deduction comparison
        current_deductions = current_filing.get("total_deductions", 0)
        previous_deductions = previous_filing.get("total_deductions", 0)
        deduction_change = current_deductions - previous_deductions

        # Effective tax rate
        current_effective_rate = (current_tax / current_income * 100) if current_income > 0 else 0
        previous_effective_rate = (previous_tax / previous_income * 100) if previous_income > 0 else 0

        return {
            "comparison_available": True,
            "year_over_year": {
                "income": {
                    "current": current_income,
                    "previous": previous_income,
                    "change": income_change,
                    "change_percentage": round(income_change_pct, 1)
                },
                "tax_liability": {
                    "current": current_tax,
                    "previous": previous_tax,
                    "change": tax_change,
                    "change_percentage": round(tax_change_pct, 1)
                },
                "deductions": {
                    "current": current_deductions,
                    "previous": previous_deductions,
                    "change": deduction_change
                },
                "effective_tax_rate": {
                    "current": round(current_effective_rate, 1),
                    "previous": round(previous_effective_rate, 1),
                    "change": round(current_effective_rate - previous_effective_rate, 1)
                }
            },
            "insights": self._generate_yoy_insights(
                income_change_pct, tax_change_pct, deduction_change
            )
        }

    def _generate_yoy_insights(
        self,
        income_change_pct: float,
        tax_change_pct: float,
        deduction_change: float
    ) -> List[str]:
        """Generate insights from year-over-year comparison"""

        insights = []

        if income_change_pct > 10:
            insights.append("Significant income increase!")
        elif income_change_pct < -5:
            insights.append("Income decreased.")

        if tax_change_pct > 15:
            insights.append("Tax liability increased faster than income.")
        elif tax_change_pct < -10:
            insights.append("Better tax efficiency!")

        if deduction_change < 0:
            insights.append("Deductions decreased.")
        elif deduction_change > 50000:
            insights.append("Increased deductions!")

        return insights

    def analyze_multi_year_trends(
        self,
        filing_history: List[Dict]
    ) -> Dict:
        """Analyze trends over multiple years"""

        if len(filing_history) < 2:
            return {
                "trend_analysis_available": False,
                "message": "Need at least 2 years of data"
            }

        sorted_filings = sorted(
            filing_history,
            key=lambda x: x.get("filing_year", 0),
            reverse=True
        )

        incomes = [f.get("total_income", 0) for f in sorted_filings]
        taxes = [f.get("total_tax_liability", 0) for f in sorted_filings]

        avg_income_growth = 0
        if len(incomes) >= 2 and incomes[-1] > 0:
            years = len(incomes) - 1
            avg_income_growth = ((incomes[0] / incomes[-1]) ** (1/years) - 1) * 100

        yearly_data = []
        for filing in sorted_filings:
            income = filing.get("total_income", 0)
            tax = filing.get("total_tax_liability", 0)
            yearly_data.append({
                "year": filing.get("filing_year"),
                "income": income,
                "tax": tax,
                "effective_rate": round((tax / income * 100), 1) if income > 0 else 0
            })

        return {
            "trend_analysis_available": True,
            "summary": {
                "years_analyzed": len(sorted_filings),
                "total_tax_paid": sum(taxes),
                "average_income_growth": round(avg_income_growth, 1)
            },
            "yearly_breakdown": yearly_data,
            "trend_insights": ["Steady income growth" if avg_income_growth > 0 else "Review income sources"]
        }

    def benchmark_performance(
        self,
        user_filing: Dict,
        benchmark_data: Optional[Dict] = None
    ) -> Dict:
        """Compare user performance with benchmarks"""

        income = user_filing.get("total_income", 0)

        if income < 500000:
            benchmark_deductions = 50000
            benchmark_tax_rate = 5
        elif income < 1000000:
            benchmark_deductions = 100000
            benchmark_tax_rate = 12
        elif income < 2000000:
            benchmark_deductions = 150000
            benchmark_tax_rate = 18
        else:
            benchmark_deductions = 200000
            benchmark_tax_rate = 25

        user_deductions = user_filing.get("total_deductions", 0)
        user_tax = user_filing.get("total_tax_liability", 0)
        user_rate = (user_tax / income * 100) if income > 0 else 0

        return {
            "income": income,
            "user": {
                "deductions": user_deductions,
                "effective_tax_rate": round(user_rate, 1)
            },
            "benchmark": {
                "deductions": benchmark_deductions,
                "effective_tax_rate": benchmark_tax_rate
            },
            "comparison": {
                "deductions_vs_benchmark": user_deductions - benchmark_deductions,
                "performance": "ABOVE" if user_rate < benchmark_tax_rate else "BELOW"
            }
        }
