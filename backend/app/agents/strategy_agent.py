"""
STRATEGY AGENT - Financial planning and tax optimization
Identifies missed deductions, recommends tax-saving actions, provides next-best decisions
"""

class StrategyAgent:
    def __init__(self):
        self.investment_opportunities = {
            "80c_elss": {
                "name": "ELSS (Equity Linked Savings Scheme)",
                "section": "80C",
                "limit": 150000,
                "annual_return": 0.12,  # 12% average
                "lock_in": 3,
                "priority": "HIGH"
            },
            "80c_ppf": {
                "name": "Public Provident Fund (PPF)",
                "section": "80C",
                "limit": 150000,
                "annual_return": 0.075,  # 7.5%
                "lock_in": 15,
                "priority": "HIGH"
            },
            "80c_lic": {
                "name": "LIC Insurance Premium",
                "section": "80C",
                "limit": 150000,
                "annual_return": 0.04,  # 4%
                "lock_in": 0,
                "priority": "MEDIUM"
            },
            "80d_health": {
                "name": "Health Insurance Premium",
                "section": "80D",
                "limit_self": 25000,
                "limit_senior": 50000,
                "annual_return": 0,
                "priority": "HIGH"
            },
            "nps": {
                "name": "National Pension Scheme",
                "section": "80CCC",
                "limit": 150000,
                "annual_return": 0.08,
                "lock_in": "until_retirement",
                "priority": "MEDIUM"
            },
            "home_loan_principal": {
                "name": "Home Loan Principal Repayment",
                "section": "80C",
                "limit": 150000,
                "annual_return": 0,
                "priority": "MEDIUM"
            }
        }

    def identify_missed_deductions(self, user_profile, filing_data):
        """Identify deductions user might have missed"""
        missed = []
        
        # Check for common missed deductions
        if user_profile.get("has_health_insurance") and filing_data.get("80d_claimed", 0) == 0:
            missed.append({
                "deduction": "80D Health Insurance",
                "potential_savings": min(50000, user_profile.get("age", 30) > 60 and 50000 or 25000) * 0.30,
                "description": "You have health insurance but didn't claim deduction",
                "action": "Collect insurance premium receipts"
            })
        
        if user_profile.get("has_home_loan") and filing_data.get("80emi_claimed", 0) == 0:
            avg_interest = user_profile.get("home_loan_balance", 0) * 0.06
            missed.append({
                "deduction": "80EMI Home Loan Interest",
                "potential_savings": avg_interest * 0.30,
                "description": "You have home loan but didn't claim interest deduction",
                "action": "Get Statement of Interest from bank"
            })
        
        if user_profile.get("has_education_loan") and filing_data.get("80e_claimed", 0) == 0:
            avg_interest = user_profile.get("education_loan_amount", 0) * 0.08
            missed.append({
                "deduction": "80E Education Loan Interest",
                "potential_savings": avg_interest * 0.30,
                "description": "You have education loan but didn't claim interest deduction",
                "action": "Get Statement of Interest from lender"
            })
        
        if user_profile.get("is_parent") and filing_data.get("80g_claimed", 0) == 0:
            missed.append({
                "deduction": "80G Donations",
                "potential_savings": 10000 * 0.30,
                "description": "Consider donating to registered charities (100% deduction for Section 80G)",
                "action": "Donate ₹10K-20K to registered NGOs"
            })
        
        return missed

    def recommend_tax_saving_actions(self, income_data, current_tax):
        """Recommend specific tax-saving actions"""
        total_income = income_data.get("total_income", 0)
        recommendations = []
        potential_savings = 0
        
        # Based on income bracket
        if 1000000 <= total_income < 1500000:
            # Recommend ELSS
            elss_investment = 150000
            elss_tax_benefit = elss_investment * 0.30
            recommendations.append({
                "action": "Invest in ELSS",
                "amount": elss_investment,
                "tax_saving": elss_tax_benefit,
                "description": "₹1.5L investment saves ₹45K tax + potential 12% annual returns",
                "timeline": "Before March 31",
                "priority": "HIGH"
            })
            potential_savings += elss_tax_benefit
            
            # Recommend PPF top-up
            ppf_investment = 50000
            ppf_tax_benefit = ppf_investment * 0.30
            recommendations.append({
                "action": "Top-up PPF",
                "amount": ppf_investment,
                "tax_saving": ppf_tax_benefit,
                "description": "₹50K PPF saves ₹15K tax + guaranteed 7.5% returns",
                "timeline": "Before March 31",
                "priority": "MEDIUM"
            })
            potential_savings += ppf_tax_benefit
        
        elif total_income >= 1500000:
            # For higher income: max out all deductions
            recommendations.append({
                "action": "Max out 80C investments",
                "amount": 150000,
                "tax_saving": 45000,
                "description": "Invest maximum ₹1.5L in ELSS/PPF/LIC",
                "timeline": "Before March 31",
                "priority": "HIGH"
            })
            potential_savings += 45000
            
            # Consider NPS for additional 80CCC
            recommendations.append({
                "action": "Invest in NPS",
                "amount": 50000,
                "tax_saving": 15000,
                "description": "₹50K additional NPS investment (Section 80CCC)",
                "timeline": "Before March 31",
                "priority": "HIGH"
            })
            potential_savings += 15000
        
        return {
            "recommendations": recommendations,
            "total_potential_savings": potential_savings,
            "new_estimated_tax": max(0, current_tax - potential_savings)
        }

    def get_next_best_actions(self, user_profile, filing_data, risk_analysis):
        """Provide next-best decisions ranked by priority"""
        actions = []
        
        # Priority 1: Fix audit flags
        if risk_analysis["risk_level"] in ["RED", "YELLOW"]:
            for flag in risk_analysis["audit_flags"][:3]:
                actions.append({
                    "priority": 1,
                    "action": f"Fix {flag['type']} flag",
                    "details": flag["reason"],
                    "deadline": "Before filing",
                    "impact": "Reduce audit risk"
                })
        
        # Priority 2: Collect missing deductions
        missed = self.identify_missed_deductions(user_profile, filing_data)
        for missed_deduction in missed[:2]:
            actions.append({
                "priority": 2,
                "action": f"Claim {missed_deduction['deduction']}",
                "details": missed_deduction["description"],
                "potential_savings": missed_deduction["potential_savings"],
                "deadline": "Before March 31",
                "impact": "Reduce tax liability"
            })
        
        # Priority 3: Tax-saving investments
        tax_saving_recs = self.recommend_tax_saving_actions(
            filing_data,
            filing_data.get("tax_liability", 0)
        )
        
        for rec in tax_saving_recs["recommendations"][:2]:
            actions.append({
                "priority": 3,
                "action": rec["action"],
                "amount": rec["amount"],
                "tax_saving": rec["tax_saving"],
                "deadline": rec["timeline"],
                "impact": "Reduce tax + build wealth"
            })
        
        # Priority 4: Post-filing actions
        actions.append({
            "priority": 4,
            "action": "Plan for next financial year",
            "details": "Review budget and create investment plan for next FY",
            "deadline": "By April 30",
            "impact": "Better tax planning"
        })
        
        # Sort by priority
        actions.sort(key=lambda x: x["priority"])
        
        return actions

    def generate_financial_narrative(self, filing_data, historical_data=None):
        """Generate financial health narrative for user"""
        total_income = filing_data.get("total_income", 0)
        total_tax = filing_data.get("recommended_tax", 0)
        total_deductions = filing_data.get("total_deductions", 0)
        
        narrative = {
            "summary": f"Your ₹{total_income:,} annual income",
            "tax_burden": f"Tax burden: {(total_tax/total_income*100):.1f}% of gross income",
            "savings_rate": f"Deduction utilization: {(total_deductions/total_income*100):.1f}%",
            "wealth_trajectory": ""
        }
        
        # Wealth trajectory
        if total_income >= 2000000:
            narrative["wealth_trajectory"] = "You're in top 5% earners. Focus on wealth creation over tax savings."
        elif total_income >= 1500000:
            narrative["wealth_trajectory"] = "Strong income. Max out tax deductions and build diversified portfolio."
        elif total_income >= 1000000:
            narrative["wealth_trajectory"] = "Good income. Invest in ELSS + PPF for tax-efficient wealth creation."
        else:
            narrative["wealth_trajectory"] = "Build emergency fund (3-6 months) before aggressive investing."
        
        return narrative

    def score_financial_health(self, user_profile, filing_data):
        """Generate financial health score (0-100)"""
        score = 50  # Base score
        
        # Income stability (if multi-year data available)
        if user_profile.get("employment_years", 1) >= 3:
            score += 10
        
        # Tax efficiency
        tax_rate = filing_data.get("effective_tax_rate", 0)
        if tax_rate < 0.15:  # Less than 15% is good
            score += 15
        elif tax_rate < 0.20:
            score += 10
        
        # Deduction utilization
        deduction_ratio = filing_data.get("deduction_ratio", 0)
        if 0.3 <= deduction_ratio <= 0.5:
            score += 15
        elif deduction_ratio > 0.5:
            score += 10
        
        # Investment diversity (if data available)
        investment_types = len(filing_data.get("investments", {}))
        if investment_types >= 3:
            score += 10
        elif investment_types >= 2:
            score += 5
        
        # Emergency fund (from profile)
        if user_profile.get("savings", 0) >= filing_data.get("total_income", 0) * 0.5:
            score += 15
        elif user_profile.get("savings", 0) >= filing_data.get("total_income", 0) * 0.25:
            score += 10
        
        # Audit risk (low risk is good)
        audit_risk = filing_data.get("audit_risk_score", 5)
        if audit_risk <= 3:
            score += 10
        elif audit_risk <= 5:
            score += 5
        
        return min(100, max(0, score))
