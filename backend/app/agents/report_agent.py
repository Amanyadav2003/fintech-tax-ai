"""
REPORT AGENT - PDF Report Generation
Generates downloadable tax summary reports, ITR forms, and documentation
"""

import io
import json
from datetime import datetime
from typing import Dict, List, Optional
from typing import Any


class ReportAgent:
    """Agent for generating tax reports and documents"""

    def __init__(self):
        self.company_name = "TaxAI - Smart Tax Filing"
        self.company_tagline = "Your AI Tax Assistant"

    def generate_tax_summary_report(
        self,
        tax_result: Dict,
        risk_result: Dict,
        strategy_result: Dict,
        user_profile: Optional[Dict] = None
    ) -> str:
        """Generate comprehensive tax summary as formatted text (can convert to PDF)"""
        
        report_lines = []
        
        # Header
        report_lines.append("=" * 60)
        report_lines.append(f"{self.company_name:^60}")
        report_lines.append(f"{self.company_tagline:^60}")
        report_lines.append("=" * 60)
        report_lines.append(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Income Section
        report_lines.append("-" * 60)
        report_lines.append("INCOME DETAILS")
        report_lines.append("-" * 60)
        
        income = tax_result.get("tax_analysis", {})
        report_lines.append(f"Gross Total Income:    ₹{income.get('gross_income', 0):,.0f}")
        report_lines.append(f"Total Deductions:      ₹{income.get('total_deductions', 0):,.0f}")
        report_lines.append(f"Taxable Income:         ₹{income.get('taxable_income', 0):,.0f}")
        report_lines.append("")
        
        # Tax Comparison
        report_lines.append("-" * 60)
        report_lines.append("TAX CALCULATION")
        report_lines.append("-" * 60)
        
        old_regime = income.get("old_regime_tax", 0)
        new_regime = income.get("new_regime_tax", 0)
        recommended = income.get("recommended_regime", "new")
        
        report_lines.append(f"Old Regime Tax:         ₹{old_regime:,.0f}")
        report_lines.append(f"New Regime Tax:         ₹{new_regime:,.0f}")
        
        savings = income.get("potential_savings", 0)
        if savings > 0:
            report_lines.append(f"Potential Savings:    ₹{savings:,.0f}")
        
        report_lines.append(f"✓ Recommended Regime:  {recommended.upper()}")
        report_lines.append("")
        
        # Risk Analysis
        report_lines.append("-" * 60)
        report_lines.append("AUDIT RISK ANALYSIS")
        report_lines.append("-" * 60)
        
        risk = risk_result.get("risk_analysis", {})
        risk_level = risk.get("risk_level", "GREEN")
        audit_score = risk.get("audit_risk_score", 0)
        
        report_lines.append(f"Risk Level:            {risk_level}")
        report_lines.append(f"Audit Risk Score:      {audit_score}/10")
        
        flags = risk.get("flags", [])
        if flags:
            report_lines.append("⚠️  Flags:")
            for flag in flags:
                report_lines.append(f"   • {flag}")
        
        penalty = risk.get("penalty_if_audited", 0)
        if penalty > 0:
            report_lines.append(f"Penalty if Audited:    ₹{penalty:,.0f}")
        
        report_lines.append("")
        
        # Strategy & Recommendations
        report_lines.append("-" * 60)
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("-" * 60)
        
        strategy = strategy_result.get("strategy_analysis", {})
        financial_score = strategy.get("financial_health_score", 0)
        
        report_lines.append(f"Financial Health Score: {financial_score}/100")
        
        actions = strategy_result.get("recommended_actions", [])
        if actions:
            report_lines.append("")
            report_lines.append("Next Best Actions:")
            for i, action in enumerate(actions[:5], 1):
                report_lines.append(f"   {i}. {action}")
        
        missed = strategy.get("missed_opportunities", [])
        if missed:
            report_lines.append("")
            report_lines.append("Missed Opportunities:")
            for m in missed:
                report_lines.append(f"   • {m}")
        
        # Footer
        report_lines.append("")
        report_lines.append("=" * 60)
        report_lines.append("This is an AI-generated summary. Consult a CA for final filing.")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)

    def generate_ca_documentation(
        self,
        tax_result: Dict,
        risk_result: Dict,
        user_profile: Dict
    ) -> str:
        """Generate CA-ready documentation package"""
        
        doc_lines = []
        
        # Header
        doc_lines.append("=" * 70)
        doc_lines.append("TAX FILING DOCUMENTATION PACKAGE")
        doc_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d')}")
        doc_lines.append("=" * 70)
        doc_lines.append("")
        
        # Client Details
        doc_lines.append("CLIENT DETAILS")
        doc_lines.append("-" * 70)
        doc_lines.append(f"Name: {user_profile.get('name', 'N/A')}")
        doc_lines.append(f"PAN: {user_profile.get('pan', 'N/A')}")
        doc_lines.append(f"Age: {user_profile.get('age', 'N/A')}")
        doc_lines.append("")
        
        # Income Breakdown
        income = tax_result.get("tax_analysis", {})
        doc_lines.append("INCOME BREAKDOWN")
        doc_lines.append("-" * 70)
        doc_lines.append(f"Salary Income:          ₹{income.get('gross_income', 0):,.0f}")
        doc_lines.append(f"Interest Income:       ₹{income.get('interest_income', 0):,.0f}")
        doc_lines.append(f"Other Income:           ₹{income.get('other_income', 0):,.0f}")
        doc_lines.append(f"Gross Total:           ₹{income.get('gross_income', 0):,.0f}")
        doc_lines.append("")
        
        # Deductions Claimed
        doc_lines.append("DEDUCTIONS CLAIMED")
        doc_lines.append("-" * 70)
        
        deductions = tax_result.get("deductions", {}).get("matched_deductions", {})
        for section, amount in deductions.items():
            doc_lines.append(f"{section.upper()}:              ₹{amount:,.0f}")
        
        doc_lines.append(f"TOTAL DEDUCTIONS:       ₹{income.get('total_deductions', 0):,.0f}")
        doc_lines.append("")
        
        # Tax Computation
        doc_lines.append("TAX COMPUTATION")
        doc_lines.append("-" * 70)
        doc_lines.append(f"Taxable Income:        ₹{income.get('taxable_income', 0):,.0f}")
        doc_lines.append(f"Old Regime Tax:        ₹{income.get('old_regime_tax', 0):,.0f}")
        doc_lines.append(f"New Regime Tax:        ₹{income.get('new_regime_tax', 0):,.0f}")
        doc_lines.append(f"Recommended:           {income.get('recommended_regime', 'N/A').upper()} REGIME")
        doc_lines.append("")
        
        # Risk Flags
        doc_lines.append("AUDIT RISK ASSESSMENT")
        doc_lines.append("-" * 70)
        
        risk = risk_result.get("risk_analysis", {})
        doc_lines.append(f"Risk Level:            {risk.get('risk_level', 'N/A')}")
        doc_lines.append(f"Audit Score:          {risk.get('audit_risk_score', 0)}/10")
        
        flags = risk.get("flags", [])
        if flags:
            doc_lines.append("Flags Raised:")
            for flag in flags:
                doc_lines.append(f"  - {flag}")
        else:
            doc_lines.append("No significant flags raised.")
        
        doc_lines.append("")
        
        # Required Documents Checklist
        doc_lines.append("DOCUMENT CHECKLIST")
        doc_lines.append("-" * 70)
        doc_lines.append("☐ Form 16 (TDS Certificate)")
        doc_lines.append("☐ Bank Interest Certificates")
        doc_lines.append("☐ Investment Proofs (80C)")
        doc_lines.append("☐ Health Insurance Premium Receipt (80D)")
        doc_lines.append("☐ Home Loan Interest Certificate (80EMI)")
        doc_lines.append("☐ Donation Receipts (80G)")
        doc_lines.append("☐ Previous Year ITR Copy")
        doc_lines.append("")
        
        # Signature
        doc_lines.append("=" * 70)
        doc_lines.append("Prepared by TaxAI")
        doc_lines.append("For professional use, verify with a certified CA")
        doc_lines.append("=" * 70)
        
        return "\n".join(doc_lines)

    def generate_compliance_checklist(
        self,
        filing_data: Dict,
        deadline: str = "July 31, 2025"
    ) -> str:
        """Generate compliance checklist"""
        
        checklist = []
        
        checklist.append("=" * 50)
        checklist.append("TAX COMPLIANCE CHECKLIST")
        checklist.append(f"Due Date: {deadline}")
        checklist.append("=" * 50)
        checklist.append("")
        
        # Pre-filing items
        checklist.append("PRE-FILING ITEMS")
        checklist.append("-" * 50)
        checklist.append("☐ Gather all Form 16/16A")
        checklist.append("☐ Collect bank interest certificates")
        checklist.append("☐ Get home loan interest certificate")
        checklist.append("☐ Verify 80C investment receipts")
        checklist.append("☐ Collect health insurance premium receipts")
        checklist.append("☐ Get donation receipts (80G certified)")
        checklist.append("☐ Download Form 26AS")
        checklist.append("")
        
        # Verification
        checklist.append("VERIFICATION")
        checklist.append("-" * 50)
        checklist.append("☐ Verify personal details (name, PAN, Aadhaar)")
        checklist.append("☐ Confirm bank details for refund")
        checklist.append("☐ Check TDS credits match Form 26AS")
        checklist.append("☐ Verify income from all sources")
        checklist.append("☐ Cross-check deductions claimed")
        checklist.append("")
        
        # Regime selection
        checklist.append("REGIME SELECTION")
        checklist.append("-" * 50)
        checklist.append("☐ Calculate tax under old regime")
        checklist.append("☐ Calculate tax under new regime")
        checklist.append("☐ Compare and select optimal regime")
        checklist.append("")
        
        # Filing
        checklist.append("FILING STEPS")
        checklist.append("-" * 50)
        checklist.append("☐ Login to e-filing portal")
        checklist.append("☐ Select correct ITR form")
        checklist.append("☐ Fill income details")
        checklist.append("☐ Claim deductions")
        checklist.append("☐ Verify tax calculation")
        checklist.append("☐ Pay balance tax (if any)")
        checklist.append("☐ Submit ITR")
        checklist.append("☐ Verify via Aadhaar OTP")
        checklist.append("")
        
        # Post-filing
        checklist.append("POST-FILING")
        checklist.append("-" * 50)
        checklist.append("☐ Save ITR-V receipt")
        checklist.append("☐ Verify refund status")
        checklist.append("☐ Keep documents for 6 years")
        checklist.append("")
        
        checklist.append("=" * 50)
        checklist.append("TIPS FOR SMOOTH FILING")
        checklist.append("=" * 50)
        checklist.append("• File early to avoid last-minute issues")
        checklist.append("• Verify all TDS credits before filing")
        checklist.append("• Choose old regime if high deductions")
        checklist.append("• Keep digital copies of all documents")
        checklist.append("• E-verify within 30 days")
        
        return "\n".join(checklist)

    def generate_csv_export(self, filing_data: Dict) -> str:
        """Generate CSV data for tax filing data export"""
        
        rows = []
        
        # Header row
        rows.append("Category,Section,Amount,Notes")
        
        # Income rows
        income = filing_data.get("income_data", {})
        for key, amount in income.items():
            if amount and amount > 0:
                rows.append(f"Income,{key},{amount},")
        
        # Deduction rows
        deductions = filing_data.get("deductions_data", {})
        section_map = {
            "investments": "80C",
            "health_insurance": "80D",
            "education_loan_interest": "80E",
            "home_loan_interest": "80EMI",
            "donations": "80G"
        }
        for key, section in section_map.items():
            amount = deductions.get(key, 0)
            if amount and amount > 0:
                rows.append(f"Deduction,{section},{amount},")
        
        return "\n".join(rows)

    def get_supported_formats(self) -> List[str]:
        """Return supported export formats"""
        return ["txt", "csv", "json"]

    def generate_report(
        self,
        report_type: str,
        data: Dict,
        user_profile: Optional[Dict] = None
    ) -> str:
        """Main method to generate reports"""
        
        tax_result = data.get("tax_result", {})
        risk_result = data.get("risk_result", {})
        strategy_result = data.get("strategy_result", {})
        
        if report_type == "summary":
            return self.generate_tax_summary_report(
                tax_result, risk_result, strategy_result, user_profile
            )
        elif report_type == "ca_documentation":
            return self.generate_ca_documentation(
                tax_result, risk_result, user_profile or {}
            )
        elif report_type == "checklist":
            return self.generate_compliance_checklist(data.get("filing_data", {}))
        elif report_type == "csv":
            return self.generate_csv_export(data.get("filing_data", {}))
        else:
            return self.generate_tax_summary_report(
                tax_result, risk_result, strategy_result, user_profile
            )
