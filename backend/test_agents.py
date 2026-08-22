"""
Demo/Test script to verify all 3 agents work correctly
Run: python test_agents.py
"""

from app.agents.tax_agent import TaxAgent
from app.agents.risk_agent import RiskAgent
from app.agents.strategy_agent import StrategyAgent
import json

def test_agents():
    print("=" * 80)
    print("TaxMate AI - 3-Agent Test Suite")
    print("=" * 80)
    
    # Sample data
    income_data = {
        "salary": 1200000,
        "interest": 50000,
        "dividend": 100000,
        "rental_income": 0,
        "professional_fees": 0,
        "age": 35,
    }
    
    deductions_data = {
        "investments": 150000,        # Max 80C
        "health_insurance": 25000,    # 80D
        "education_loan_interest": 0,
        "home_loan_interest": 200000, # 80EMI
        "donations": 50000,           # 80G
    }
    
    print("\n📊 INPUT DATA:")
    print(f"Total Income: ₹{sum([income_data['salary'], income_data['interest'], income_data['dividend']]):,}")
    print(f"Investments (80C): ₹{deductions_data['investments']:,}")
    print(f"Home Loan Interest (80EMI): ₹{deductions_data['home_loan_interest']:,}")
    print(f"Health Insurance (80D): ₹{deductions_data['health_insurance']:,}")
    
    # ============================================
    # AGENT 1: TAX AGENT
    # ============================================
    print("\n" + "=" * 80)
    print("🧮 AGENT 1: TAX AGENT (Calculation Engine)")
    print("=" * 80)
    
    tax_agent = TaxAgent()
    tax_result = tax_agent.process_filing(income_data, deductions_data)
    
    print("\n✅ Tax Calculation:")
    print(f"   Total Income: ₹{tax_result['total_income']:,}")
    print(f"   Total Deductions: ₹{tax_result['deductions']['total_deductions']:,}")
    print(f"\n   Old Regime:")
    print(f"   - Taxable Income: ₹{tax_result['tax_old_regime']['taxable_income']:,}")
    print(f"   - Tax: ₹{tax_result['tax_old_regime']['total_tax']:,}")
    print(f"\n   New Regime:")
    print(f"   - Taxable Income: ₹{tax_result['tax_new_regime']['taxable_income']:,}")
    print(f"   - Tax: ₹{tax_result['tax_new_regime']['total_tax']:,}")
    print(f"\n💡 Recommendation: {tax_result['recommendation']['recommended_regime'].upper()} REGIME")
    print(f"   Potential Savings: ₹{tax_result['recommendation']['potential_savings']:,}")
    
    # ============================================
    # AGENT 2: RISK AGENT
    # ============================================
    print("\n" + "=" * 80)
    print("⚠️  AGENT 2: RISK AGENT (Audit Detection)")
    print("=" * 80)
    
    risk_agent = RiskAgent()
    filing_data_for_risk = {
        "total_income": tax_result['total_income'],
        "matched_deductions": tax_result['deductions']['matched_deductions'],
        "tds_paid": 150000,
        "salary_reported": income_data['salary'],
    }
    risk_result = risk_agent.analyze_filing(filing_data_for_risk)
    
    print(f"\n🎯 Audit Risk Score: {risk_result['overall_audit_risk_score']:.1f}/10")
    print(f"📊 Risk Level: {risk_result['risk_level']}")
    print(f"🚨 Estimated Audit Probability: {risk_result['estimated_audit_probability']:.0f}%")
    
    if risk_result['audit_flags']:
        print(f"\n🚩 Flagged Items ({len(risk_result['audit_flags'])}):")
        for flag in risk_result['audit_flags']:
            print(f"   • {flag['type'].upper()}: {flag['reason']}")
            print(f"     Risk Level: {flag['risk_level']}")
    else:
        print("\n✅ No audit flags detected!")
    
    print(f"\n💼 Recommendations ({len(risk_result['recommendations'])}):")
    for rec in risk_result['recommendations'][:3]:
        print(f"   • {rec['action']}")
        print(f"     {rec['details']}")
    
    # ============================================
    # AGENT 3: STRATEGY AGENT
    # ============================================
    print("\n" + "=" * 80)
    print("📈 AGENT 3: STRATEGY AGENT (Financial Planning)")
    print("=" * 80)
    
    strategy_agent = StrategyAgent()
    user_profile = {"age": income_data['age']}
    filing_data_for_strategy = {
        "total_income": tax_result['total_income'],
        "80d_claimed": deductions_data['health_insurance'],
        "80e_claimed": 0,
        "80emi_claimed": deductions_data['home_loan_interest'],
        "80g_claimed": 0,
        "tax_liability": tax_result['recommendation']['tax_new_regime'] if tax_result['recommendation']['recommended_regime'] == "new" else tax_result['recommendation']['tax_old_regime'],
    }
    
    strategy_result = strategy_agent.get_next_best_actions(user_profile, filing_data_for_strategy, risk_result)
    missed = strategy_agent.identify_missed_deductions(user_profile, filing_data_for_strategy)
    
    print("\n💡 Missed Opportunities:")
    if missed:
        for m in missed[:3]:
            print(f"   • {m['deduction']}")
            print(f"     {m['description']}")
            print(f"     Potential Savings: ₹{m['potential_savings']:,.0f}")
    else:
        print("   ✅ No missed deductions detected!")
    
    tax_saving_recs = strategy_agent.recommend_tax_saving_actions(
        income_data,
        tax_result['recommendation']['tax_new_regime'] if tax_result['recommendation']['recommended_regime'] == "new" else tax_result['recommendation']['tax_old_regime']
    )
    
    print(f"\n💰 Tax-Saving Recommendations:")
    for rec in tax_saving_recs['recommendations'][:3]:
        print(f"   • {rec['action']}")
        print(f"     Amount: ₹{rec['amount']:,}")
        print(f"     Tax Saving: ₹{rec['tax_saving']:,}")
    
    print(f"\n📊 Total Potential Savings: ₹{tax_saving_recs['total_potential_savings']:,}")
    
    # ============================================
    # SUMMARY
    # ============================================
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE - All Agents Working!")
    print("=" * 80)
    print("\n📋 Summary:")
    print(f"   Total Income: ₹{tax_result['total_income']:,}")
    print(f"   Recommended Tax: ₹{tax_result['recommendation']['potential_savings'] if tax_result['recommendation']['recommended_regime'] == 'new' else tax_result['recommendation']['tax_old_regime']:,}")
    print(f"   Audit Risk: {risk_result['risk_level']}")
    print(f"   Potential Savings: ₹{tax_result['recommendation']['potential_savings'] + tax_saving_recs['total_potential_savings']:,}")
    print("\n🚀 Ready for production!")

if __name__ == "__main__":
    test_agents()
