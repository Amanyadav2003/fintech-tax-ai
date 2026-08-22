"""
SCENARIO AGENT - What-If Tax Modeling
Handles scenario modeling, tax projections, and what-if analysis
"""

from typing import Dict, List, Optional
from .tax_agent import TaxAgent
from .strategy_agent import StrategyAgent


class ScenarioAgent:
    """Agent for tax scenario modeling and what-if analysis"""

    def __init__(self):
        self.tax_agent = TaxAgent()
        self.strategy_agent = StrategyAgent()

    def model_investment_scenario(
        self,
        base_income: Dict,
        additional_investments: Dict,
        current_deductions: Dict
    ) -> Dict:
        """Model impact of additional investments"""

        scenarios = []

        # Base scenario (no additional)
        base_total_income = sum(base_income.values())
        base_result = self.tax_agent.process_filing(base_income, current_deductions)
        base_tax_old = base_result["tax_old_regime"]["total_tax"]
        base_tax_new = base_result["tax_new_regime"]["total_tax"]

        scenarios.append({
            "name": "Current (No Additional)",
            "tax_old": base_tax_old,
            "tax_new": base_tax_new
        })

        # 80C scenarios
        for investment_name, amount in additional_investments.items():
            new_deductions = current_deductions.copy()
            new_deductions["investments"] = (
                current_deductions.get("investments", 0) + amount
            )

            result = self.tax_agent.process_filing(base_income, new_deductions)
            tax_old = result["tax_old_regime"]["total_tax"]
            tax_new = result["tax_new_regime"]["total_tax"]

            savings_old = base_tax_old - tax_old
            savings_new = base_tax_new - tax_new

            scenarios.append({
                "name": investment_name,
                "investment_amount": amount,
                "tax_old": tax_old,
                "tax_new": tax_new,
                "potential_savings_old": savings_old,
                "potential_savings_new": savings_new,
                "roi": (savings_old / amount * 100) if amount > 0 else 0
            })

        return {
            "base_income": base_total_income,
            "base_tax_old": base_tax_old,
            "base_tax_new": base_tax_new,
            "scenarios": scenarios,
            "optimal_scenario": min(scenarios, key=lambda x: x.get("tax_new", float("inf")))
        }

    def model_salary_structure(
        self,
        total_compensation: float,
        salary_breakdown: Dict,
        target_deductions: float
    ) -> Dict:
        """Model different salary structures for tax efficiency"""

        base_salary = salary_breakdown.get("basic_salary", total_compensation * 0.6)
        hra = salary_breakdown.get("hra", total_compensation * 0.15)
        bonus = salary_breakdown.get("bonus", 0)
        perquisites = salary_breakdown.get("perquisites", 0)

        # Scenario 1: High salary, low bonus
        income_high_salary = {
            "salary": base_salary + bonus,
            "interest": 0,
            "dividend": 0,
            "rental_income": 0,
            "professional_fees": 0
        }

        # Scenario 2: Split salary and bonus
        income_split = {
            "salary": base_salary,
            "interest": 0,
            "dividend": 0,
            "rental_income": 0,
            "professional_fees": 0
        }

        # Calculate for each
        result_high = self.tax_agent.calculate_tax_old_regime(
            base_salary + bonus,
            target_deductions
        )
        result_split = self.tax_agent.calculate_tax_old_regime(
            base_salary,
            target_deductions
        )

        return {
            "scenarios": [
                {
                    "name": "High Fixed Salary",
                    "breakdown": {
                        "basic": base_salary + bonus,
                        "hra": 0,
                        "bonus": 0,
                        "perquisites": 0
                    },
                    "tax": result_high["total_tax"],
                    "take_home": total_compensation - result_high["total_tax"]
                },
                {
                    "name": "With HRA",
                    "breakdown": {
                        "basic": total_compensation * 0.5,
                        "hra": hra,
                        "bonus": bonus,
                        "perquisites": perquisites
                    },
                    "tax": result_split["total_tax"],
                    "take_home": total_compensation - result_split["total_tax"]
                }
            ],
            "recommendation": "Higher HRA reduces taxable income if living in rented accommodation"
        }

    def model_regime_comparison(
        self,
        income_data: Dict,
        deductions_data: Dict
    ) -> Dict:
        """Compare old vs new regime with different deduction levels"""

        total_income = sum(income_data.values())

        deductions_levels = [
            ("No Deductions", 0),
            ("80C Only (₹1.5L)", 150000),
            ("80C + 80D (₹1.75L)", 175000),
            ("Max Deductions (₹2.5L)", 250000)
        ]

        results = []

        for name, deduction in deductions_levels:
            tax_old = self.tax_agent.calculate_tax_old_regime(total_income, deduction)
            tax_new = self.tax_agent.calculate_tax_new_regime(total_income)

            results.append({
                "deduction_level": name,
                "total_deductions": deduction,
                "old_regime_tax": tax_old["total_tax"],
                "new_regime_tax": tax_new["total_tax"],
                "difference": tax_old["total_tax"] - tax_new["total_tax"],
                "recommended_regime": "new" if tax_new["total_tax"] < tax_old["total_tax"] else "old"
            })

        # Find optimal
        best = min(results, key=lambda x: min(x["old_regime_tax"], x["new_regime_tax"]))

        return {
            "total_income": total_income,
            "analysis": results,
            "optimal": best,
            "crossover_point": self._find_crossover_point(total_income)
        }

    def _find_crossover_point(self, income: float) -> Optional[float]:
        """Find income level where new regime becomes better"""

        for deduction in [0, 50000, 100000, 150000, 200000]:
            tax_old = self.tax_agent.calculate_tax_old_regime(income, deduction)
            tax_new = self.tax_agent.calculate_tax_new_regime(income)

            if tax_new["total_tax"] < tax_old["total_tax"]:
                return income

        return None

    def project_quarterly_tax(
        self,
        annual_INCOME: float,
        income_pattern: str
    ) -> Dict:
        """Project quarterly tax payments (advance tax)"""

        if income_pattern == "salaried":
            # Mostly salary - tax already deducted
            quarters = [
                {"quarter": "Q1", "percentage": 15, "expected": annual_INCOME * 0.15 * 0.1},
                {"quarter": "Q2", "percentage": 30, "expected": annual_INCOME * 0.15 * 0.1},
                {"quarter": "Q3", "percentage": 45, "expected": annual_INCOME * 0.15 * 0.1},
                {"quarter": "Q4", "percentage": 100, "expected": annual_INCOME * 0.15 * 0.7}
            ]
        else:
            # Uneven income - pay more upfront
            quarters = [
                {"quarter": "Q1", "percentage": 30, "expected": annual_INCOME * 0.15 * 0.3},
                {"quarter": "Q2", "percentage": 60, "expected": annual_INCOME * 0.15 * 0.3},
                {"quarter": "Q3", "percentage": 100, "expected": annual_INCOME * 0.15 * 0.4}
            ]

        return {
            "annual_income": annual_INCOME,
            "estimated_tax": annual_INCOME * 0.15,
            "quarterly_breakdown": quarters,
            "due_dates": [
                "June 15",
                "September 15",
                "December 15",
                "March 15"
            ]
        }

    def model_income_change(
        self,
        base_income: float,
        scenarios: List[Dict]
    ) -> Dict:
        """Model tax impact with different income levels"""

        results = []

        for scenario in scenarios:
            income_change = scenario.get("change_percentage", 0)
            new_income = base_income * (1 + income_change / 100)

            tax_old = self.tax_agent.calculate_tax_old_regime(new_income, 150000)
            tax_new = self.tax_agent.calculate_tax_new_regime(new_income)

            results.append({
                "scenario": scenario.get("name", f"{income_change}% change"),
                "income": new_income,
                "tax_old": tax_old["total_tax"],
                "tax_new": tax_new["total_tax"],
                "effective_rate_old": (tax_old["total_tax"] / new_income * 100),
                "effective_rate_new": (tax_new["total_tax"] / new_income * 100)
            })

        return {
            "base_income": base_income,
            "scenarios": results
        }

    def calculate_tax_liability_brackets(
        self,
        income: float,
        regime: str = "old"
    ) -> Dict:
        """Show tax calculation by brackets"""

        if regime == "old":
            slabs = self.tax_agent.old_regime_slabs
        else:
            slabs = self.tax_agent.new_regime_slabs

        previous_limit = 0
        bracket_details = []

        for limit, rate in slabs:
            if income <= previous_limit:
                break

            taxable_in_slab = min(income, limit) - previous_limit
            tax_in_slab = taxable_in_slab * rate

            bracket_details.append({
                "from": previous_limit,
                "to": limit,
                "rate": rate * 100,
                "taxable_amount": taxable_in_slab,
                "tax": tax_in_slab
            })

            previous_limit = limit

        total_tax = sum(b["tax"] for b in bracket_details)

        return {
            "regime": regime,
            "total_income": income,
            "total_tax": total_tax,
            "effective_rate": (total_tax / income * 100) if income > 0 else 0,
            "bracket_breakdown": bracket_details
        }

    def get_optimal_investment_mix(
        self,
        available_amount: float,
        income_bracket: str
    ) -> Dict:
        """Get optimal investment mix for tax savings"""

        # Investment options with tax benefit
        investments = [
            {"name": "ELSS", "section": "80C", "max": 150000, "return": 12, "lock_in": 3},
            {"name": "PPF", "section": "80C", "max": 150000, "return": 7.5, "lock_in": 15},
            {"name": "NPS", "section": "80CCC", "max": 50000, "return": 8, "lock_in": "retirement"},
            {"name": "Health Insurance", "section": "80D", "max": 25000, "return": 0, "lock_in": 0},
            {"name": "Home Loan Principal", "section": "80C", "max": 150000, "return": 0, "lock_in": 0}
        ]

        # Prioritize based on income bracket
        if income_bracket == "high":  # > 15L
            allocation = [
                {"invest": "ELSS", "amount": 150000, "savings": 45000},
                {"invest": "NPS", "amount": 50000, "savings": 15000},
                {"invest": "Health Insurance", "amount": 25000, "savings": 7500},
                {"invest": "Home Loan Principal", "amount": 75000, "savings": 22500}
            ]
        elif income_bracket == "medium":  # 5-15L
            allocation = [
                {"invest": "PPF", "amount": 150000, "savings": 45000},
                {"invest": "ELSS", "amount": 100000, "savings": 30000},
                {"invest": "Health Insurance", "amount": 25000, "savings": 7500}
            ]
        else:  # < 5L
            allocation = [
                {"invest": "PPF", "amount": 50000, "savings": 15000},
                {"invest": "Health Insurance", "amount": 25000, "savings": 7500}
            ]

        total_invested = sum(a["invest"] for a in allocation)
        total_savings = sum(a["savings"] for a in allocation)

        return {
            "available_amount": available_amount,
            "recommended_allocation": allocation,
            "total_invested": total_invested,
            "total_tax_savings": total_savings,
            "roi": (total_savings / available_amount * 100) if available_amount > 0 else 0
        }

    def compare_spouse_filing(
        self,
        income_self: float,
        income_spouse: float,
        deductions_self: float,
        deductions_spouse: float
    ) -> Dict:
        """Compare jointly vs separately for filing"""

        # Separate filing
        tax_self_separate = self.tax_agent.calculate_tax_old_regime(income_self, deductions_self)
        tax_spouse_separate = self.tax_agent.calculate_tax_old_regime(income_spouse, deductions_spouse)
        total_separate = tax_self_separate["total_tax"] + tax_spouse_separate["total_tax"]

        # Combined (if one person claims all)
        combined_income = income_self + income_spouse
        combined_deductions = deductions_self + deductions_spouse
        tax_combined = self.tax_agent.calculate_tax_old_regime(combined_income, combined_deductions)

        savings = total_separate - tax_combined["total_tax"]

        return {
            "separate_filing": {
                "self_tax": tax_self_separate["total_tax"],
                "spouse_tax": tax_spouse_separate["total_tax"],
                "total": total_separate
            },
            "combined_filing": {
                "total_tax": tax_combined["total_tax"]
            },
            "potential_savings": savings,
            "recommendation": "File separately" if savings <= 0 else f"Save ₹{savings:,.0f} by combining deductions"
        }

    def analyze_itax_implications(
        self,
        asset_sales: List[Dict],
        total_income: float
    ) -> Dict:
        """Analyze capital gains tax implications"""

        short_term_gains = 0
        long_term_gains = 0

        for asset in asset_sales:
            if asset.get("holding_period", 0) < 365:
                short_term_gains += asset.get("gain", 0)
            else:
                long_term_gains += asset.get("gain", 0)

        # Short term (taxed as regular income)
        tax_short = self.tax_agent.calculate_tax_old_regime(
            total_income + short_term_gains,
            100000
        )

        # Long term (20% with indexation)
        tax_long = self.tax_agent.calculate_tax_new_regime(total_income)  # Simplified

        return {
            "short_term_gains": short_term_gains,
            "long_term_gains": long_term_gains,
            "short_term_tax": tax_short["total_tax"] - 30000,  # Rough estimate
            "long_term_tax": long_term_gains * 0.2,
            "total_tax_impact": (tax_short["total_tax"] - 30000) + (long_term_gains * 0.2),
            "recommendation": "Hold assets > 1 year for lower tax" if short_term_gains > 0 else ""
        }
