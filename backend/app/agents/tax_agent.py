"""
TAX AGENT - Core tax calculation engine
Handles ITR calculations, deduction matching, tax liability computation
"""

class TaxAgent:
    calculation_version = "fy2025-26"
    tax_year = "FY 2025-26 (AY 2026-27)"
    cess_rate = 0.04
    def __init__(self):
        self.old_regime_slabs = [
            (250000, 0),           # Up to 2.5L: 0%
            (500000, 0.05),        # 2.5L-5L: 5%
            (1000000, 0.20),       # 5L-10L: 20%
            (float('inf'), 0.30),  # Above 10L: 30%
        ]
        
        self.new_regime_slabs = [
            (400000, 0),           # Up to 4L: 0%
            (800000, 0.05),        # 4L-8L: 5%
            (1200000, 0.10),       # 8L-12L: 10%
            (1600000, 0.15),       # 12L-16L: 15%
            (2000000, 0.20),       # 16L-20L: 20%
            (2400000, 0.25),       # 20L-24L: 25%
            (float('inf'), 0.30),  # Above 24L: 30%
        ]
        
        self.standard_deduction_old = 50000  # Old regime
        self.standard_deduction_new = 75000  # New regime

    def calculate_tax_old_regime(self, income, deductions):
        """Calculate tax under old regime with deductions"""
        taxable_income = max(0, income - deductions - self.standard_deduction_old)
        tax, slab_breakdown = self._calculate_from_slabs(taxable_income, self.old_regime_slabs)
        
        rebate, marginal_relief = self._calculate_rebate(taxable_income, tax, "old")
        tax_after_rebate = max(0, tax - rebate - marginal_relief)
        cess = tax_after_rebate * self.cess_rate
        total_tax = tax_after_rebate + cess
        
        return {
            "gross_income": income,
            "total_deductions": deductions,
            "standard_deduction": self.standard_deduction_old,
            "taxable_income": taxable_income,
            "tax_before_cess": tax,
            "rebate_87a": rebate,
            "marginal_relief": marginal_relief,
            "tax_after_rebate": tax_after_rebate,
            "health_education_cess": cess,
            "total_tax": total_tax,
            "slab_breakdown": slab_breakdown,
            "calculation_agent": "Tax Agent",
            "regime": "old"
        }

    def calculate_tax_new_regime(self, income):
        """Calculate tax under new regime (no deductions except standard)"""
        taxable_income = max(0, income - self.standard_deduction_new)
        tax, slab_breakdown = self._calculate_from_slabs(taxable_income, self.new_regime_slabs)
        
        rebate, marginal_relief = self._calculate_rebate(taxable_income, tax, "new")
        tax_after_rebate = max(0, tax - rebate - marginal_relief)
        cess = tax_after_rebate * self.cess_rate
        total_tax = tax_after_rebate + cess
        
        return {
            "gross_income": income,
            "standard_deduction": self.standard_deduction_new,
            "taxable_income": taxable_income,
            "tax_before_cess": tax,
            "rebate_87a": rebate,
            "marginal_relief": marginal_relief,
            "tax_after_rebate": tax_after_rebate,
            "health_education_cess": cess,
            "total_tax": total_tax,
            "slab_breakdown": slab_breakdown,
            "calculation_agent": "Tax Agent",
            "regime": "new"
        }

    def _calculate_from_slabs(self, income, slabs):
        """Calculate tax from income slabs"""
        tax = 0
        breakdown = []
        previous_limit = 0
        
        for limit, rate in slabs:
            if income <= previous_limit:
                break
            
            taxable_in_slab = min(income, limit) - previous_limit
            slab_tax = taxable_in_slab * rate
            tax += slab_tax
            upper_label = f"₹{limit:,.0f}" if limit != float('inf') else "above"
            breakdown.append({
                "from": previous_limit,
                "to": None if limit == float('inf') else limit,
                "amount": taxable_in_slab,
                "rate": rate,
                "tax": slab_tax,
                "label": f"₹{previous_limit:,.0f}-{upper_label}: {rate * 100:g}% = ₹{slab_tax:,.0f}",
            })
            previous_limit = limit
        
        return tax, breakdown

    def _calculate_rebate(self, taxable_income, slab_tax, regime):
        """Apply Section 87A and the FY 2025-26 marginal-relief ceiling."""
        threshold, maximum_rebate = ((500000, 12500) if regime == "old" else (1200000, 60000))
        rebate = min(slab_tax, maximum_rebate) if taxable_income <= threshold else 0
        tax_after_rebate = max(0, slab_tax - rebate)
        marginal_relief = max(0, tax_after_rebate - (taxable_income - threshold)) if regime == "new" and taxable_income > threshold else 0
        return rebate, marginal_relief

    def match_deductions(self, income_data, deductions_data):
        """Match and validate deductions against income"""
        matched_deductions = {
            "80c_investments": 0,           # Up to 1.5L
            "80d_health_insurance": 0,      # Up to 25K (self) / 50K (senior)
            "80e_education_loan": 0,        # No limit
            "80emi_home_loan": 0,           # Interest only
            "80g_donations": 0,             # 50% or 100% of income
            "other": 0
        }
        
        # Section 80C - Investments (up to 1.5L)
        if "investments" in deductions_data:
            matched_deductions["80c_investments"] = min(deductions_data["investments"], 150000)
        
        # Section 80D - Health Insurance
        age = income_data.get("age", 30)
        max_80d = 50000 if age > 60 else 25000
        if "health_insurance" in deductions_data:
            matched_deductions["80d_health_insurance"] = min(deductions_data["health_insurance"], max_80d)
        
        # Section 80E - Education Loan Interest
        if "education_loan_interest" in deductions_data:
            matched_deductions["80e_education_loan"] = deductions_data["education_loan_interest"]
        
        # Section 80EMI - Home Loan Interest
        if "home_loan_interest" in deductions_data:
            matched_deductions["80emi_home_loan"] = deductions_data["home_loan_interest"]
        
        # Section 80G - Donations (50% of income)
        max_80g = income_data.get("total_income", 0) * 0.5
        if "donations" in deductions_data:
            matched_deductions["80g_donations"] = min(deductions_data["donations"], max_80g)
        
        total_deductions = sum(matched_deductions.values())
        
        return {
            "matched_deductions": matched_deductions,
            "total_deductions": total_deductions,
            "deduction_limit_warnings": self._check_deduction_limits(deductions_data, age)
        }

    def _check_deduction_limits(self, deductions_data, age):
        """Check for deduction limit violations"""
        warnings = []
        
        if deductions_data.get("investments", 0) > 150000:
            warnings.append({
                "type": "80c_limit_exceeded",
                "message": "Section 80C investment limit is ₹1.5L",
                "excess": deductions_data["investments"] - 150000
            })
        
        max_80d = 50000 if age > 60 else 25000
        if deductions_data.get("health_insurance", 0) > max_80d:
            warnings.append({
                "type": "80d_limit_exceeded",
                "message": f"Section 80D health insurance limit is ₹{max_80d}",
                "excess": deductions_data["health_insurance"] - max_80d
            })
        
        return warnings

    def recommend_regime(self, tax_old, tax_new):
        """Recommend optimal tax regime"""
        savings = abs(tax_old - tax_new)
        recommended = "new" if tax_new < tax_old else "old"
        
        return {
            "recommended_regime": recommended,
            "tax_old_regime": tax_old,
            "tax_new_regime": tax_new,
            "potential_savings": savings,
            "savings_percentage": (savings / tax_old * 100) if tax_old > 0 else 0
        }

    def process_filing(self, income_data, deductions_data):
        """Main method to process complete tax filing"""
        total_income = sum([
            income_data.get("salary", 0),
            income_data.get("interest", 0),
            income_data.get("dividend", 0),
            income_data.get("rental_income", 0),
            income_data.get("professional_fees", 0),
        ])
        
        # Match deductions
        deduction_result = self.match_deductions(income_data, deductions_data)
        total_deductions = deduction_result["total_deductions"]
        
        # Calculate tax under both regimes
        tax_old = self.calculate_tax_old_regime(total_income, total_deductions)
        tax_new = self.calculate_tax_new_regime(total_income)
        
        # Recommendation
        recommendation = self.recommend_regime(
            tax_old["total_tax"],
            tax_new["total_tax"]
        )
        
        return {
            "calculation_version": self.calculation_version,
            "total_income": total_income,
            "deductions": deduction_result,
            "tax_old_regime": tax_old,
            "tax_new_regime": tax_new,
            "recommendation": recommendation
        }
