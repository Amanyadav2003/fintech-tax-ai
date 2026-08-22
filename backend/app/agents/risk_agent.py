"""
RISK AGENT - Audit risk detection and compliance flagging
Identifies aggressive deductions, anomalies, and compliance issues
"""

class RiskAgent:
    def __init__(self):
        # Benchmark data: income_bracket -> (deduction_type -> median, p75, p90, audit_risk%)
        self.benchmarks = {
            (0, 500000): {
                "80c": {"median": 20000, "p75": 50000, "p90": 75000, "audit_rate": 2},
                "80d": {"median": 5000, "p75": 15000, "p90": 25000, "audit_rate": 1},
                "medical": {"median": 5000, "p75": 20000, "p90": 40000, "audit_rate": 8},
                "donations": {"median": 2000, "p75": 10000, "p90": 25000, "audit_rate": 3},
            },
            (500000, 1000000): {
                "80c": {"median": 75000, "p75": 125000, "p90": 150000, "audit_rate": 3},
                "80d": {"median": 12000, "p75": 25000, "p90": 40000, "audit_rate": 2},
                "medical": {"median": 20000, "p75": 50000, "p90": 80000, "audit_rate": 10},
                "donations": {"median": 10000, "p75": 50000, "p90": 100000, "audit_rate": 5},
            },
            (1000000, 2000000): {
                "80c": {"median": 110000, "p75": 145000, "p90": 150000, "audit_rate": 4},
                "80d": {"median": 20000, "p75": 35000, "p90": 50000, "audit_rate": 2},
                "medical": {"median": 50000, "p75": 100000, "p90": 150000, "audit_rate": 12},
                "donations": {"median": 40000, "p75": 150000, "p90": 250000, "audit_rate": 7},
            },
            (2000000, float('inf')): {
                "80c": {"median": 120000, "p75": 145000, "p90": 150000, "audit_rate": 5},
                "80d": {"median": 30000, "p75": 45000, "p90": 75000, "audit_rate": 3},
                "medical": {"median": 80000, "p75": 150000, "p90": 250000, "audit_rate": 15},
                "donations": {"median": 100000, "p75": 300000, "p90": 500000, "audit_rate": 10},
            }
        }

    def get_benchmark(self, income):
        """Get benchmark data for income bracket"""
        for (min_income, max_income), data in self.benchmarks.items():
            if min_income <= income < max_income:
                return data
        return self.benchmarks[(2000000, float('inf'))]

    def check_deduction_anomaly(self, deduction_type, amount, income):
        """Check if deduction is anomalous vs benchmark"""
        benchmark = self.get_benchmark(income)
        deduction_data = benchmark.get(deduction_type, {})
        
        if not deduction_data or amount == 0:
            return {"flag": False, "risk_level": "LOW", "reason": None}
        
        median = deduction_data["median"]
        p90 = deduction_data["p90"]
        audit_rate = deduction_data["audit_rate"]
        
        # Risk scoring
        if amount > p90:
            return {
                "flag": True,
                "risk_level": "HIGH",
                "reason": f"{deduction_type}: ₹{amount} vs benchmark p90 ₹{p90}",
                "audit_probability": audit_rate + 5,  # +5% higher audit risk
                "percentile": 95
            }
        elif amount > median * 2:
            return {
                "flag": True,
                "risk_level": "MEDIUM",
                "reason": f"{deduction_type}: ₹{amount} is 2x median (₹{median})",
                "audit_probability": audit_rate + 2,
                "percentile": 75
            }
        elif amount > median:
            return {
                "flag": True,
                "risk_level": "LOW",
                "reason": f"{deduction_type}: ₹{amount} above median (₹{median})",
                "audit_probability": audit_rate,
                "percentile": 50
            }
        
        return {"flag": False, "risk_level": "LOW", "reason": None}

    def analyze_filing(self, filing_data):
        """Comprehensive audit risk analysis"""
        flags = []
        total_risk_score = 0
        audit_risk_sum = 0
        
        total_income = filing_data["total_income"]
        deductions = filing_data["matched_deductions"]
        
        # Check each deduction
        deduction_checks = {
            "80c": deductions.get("80c_investments", 0),
            "80d": deductions.get("80d_health_insurance", 0),
            "medical": filing_data.get("medical_expenses", 0),
            "donations": deductions.get("80g_donations", 0),
        }
        
        for deduction_type, amount in deduction_checks.items():
            result = self.check_deduction_anomaly(deduction_type, amount, total_income)
            if result["flag"]:
                flags.append({
                    "type": deduction_type,
                    "amount": amount,
                    "risk_level": result["risk_level"],
                    "reason": result["reason"],
                    "audit_probability": result["audit_probability"]
                })
                audit_risk_sum += result["audit_probability"]
        
        # Check income-to-deduction ratio
        total_deductions = sum(deductions.values())
        deduction_ratio = total_deductions / total_income if total_income > 0 else 0
        
        if deduction_ratio > 0.6:  # Deductions > 60% of income
            flags.append({
                "type": "high_deduction_ratio",
                "amount": total_deductions,
                "risk_level": "MEDIUM",
                "reason": f"Deductions are {deduction_ratio*100:.1f}% of income (benchmark: ~30-40%)",
                "audit_probability": 8
            })
            audit_risk_sum += 8
        
        # Check TDS consistency
        salary = filing_data.get("salary_reported", 0)
        tds = filing_data.get("tds_paid", 0)
        if salary > 0 and tds == 0:
            flags.append({
                "type": "no_tds_deducted",
                "amount": 0,
                "risk_level": "MEDIUM",
                "reason": f"No TDS deducted on ₹{salary} salary - unusual for salaried employees",
                "audit_probability": 5
            })
            audit_risk_sum += 5
        
        # Overall risk score (0-10)
        risk_score = min(10, audit_risk_sum / 20)  # Normalize
        
        risk_level_name = "RED" if risk_score > 7 else ("YELLOW" if risk_score > 4 else "GREEN")
        
        return {
            "audit_flags": flags,
            "overall_audit_risk_score": round(risk_score, 1),
            "risk_level": risk_level_name,
            "total_flags": len(flags),
            "estimated_audit_probability": min(50, audit_risk_sum),  # Cap at 50%
            "recommendations": self._generate_recommendations(flags, filing_data)
        }

    def _generate_recommendations(self, flags, filing_data):
        """Generate mitigation recommendations"""
        recommendations = []
        
        for flag in flags:
            if flag["type"] == "80c":
                recommendations.append({
                    "action": "Document 80C investments",
                    "details": "Keep all ELSS, PPF, LIC premium receipts and statements",
                    "priority": "HIGH" if flag["risk_level"] == "HIGH" else "MEDIUM"
                })
            elif flag["type"] == "80d":
                recommendations.append({
                    "action": "Document health insurance",
                    "details": "Keep policy documents and premium payment proofs",
                    "priority": "MEDIUM"
                })
            elif flag["type"] == "medical":
                recommendations.append({
                    "action": "Document medical expenses",
                    "details": "Keep medical bills, receipts, doctor prescriptions, and medical reports",
                    "priority": "HIGH"
                })
            elif flag["type"] == "donations":
                recommendations.append({
                    "action": "Verify donation receipts",
                    "details": "Ensure donations are to registered charities (80G certification)",
                    "priority": "HIGH" if flag["risk_level"] == "HIGH" else "MEDIUM"
                })
            elif flag["type"] == "tds_mismatch":
                recommendations.append({
                    "action": "Reconcile TDS",
                    "details": "Get Form 16 from employer and verify TDS amount matches ITR",
                    "priority": "HIGH"
                })
        
        if not recommendations:
            recommendations.append({
                "action": "Standard compliance",
                "details": "Keep all supporting documents for 6 years",
                "priority": "LOW"
            })
        
        return recommendations

    def calculate_penalty_if_audited(self, flags, income):
        """Calculate potential penalty if audited"""
        total_penalty = 0
        penalty_details = []
        
        for flag in flags:
            if flag["risk_level"] == "HIGH":
                # High risk: 50% of disallowed amount
                penalty = flag["amount"] * 0.5
                total_penalty += penalty
                penalty_details.append({
                    "reason": f"Disallowed {flag['type']}",
                    "disallowed_amount": flag["amount"],
                    "penalty_50_percent": penalty
                })
            elif flag["risk_level"] == "MEDIUM":
                # Medium risk: 25% of disallowed amount
                penalty = flag["amount"] * 0.25
                total_penalty += penalty
                penalty_details.append({
                    "reason": f"Partially disallowed {flag['type']}",
                    "disallowed_amount": flag["amount"],
                    "penalty_25_percent": penalty
                })
        
        return {
            "estimated_penalty": total_penalty,
            "penalty_details": penalty_details,
            "total_back_tax_and_penalty": total_penalty * 1.3  # Add 30% for interest
        }
