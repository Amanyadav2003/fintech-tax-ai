from app.agents.tax_agent import TaxAgent


def test_fy2025_new_regime_rebate_cases():
    agent = TaxAgent()
    for taxable_income, slab_tax, expected_rebate in ((900000, 30000, 30000), (1200000, 60000, 60000)):
        result = agent.calculate_tax_new_regime(taxable_income + agent.standard_deduction_new)
        assert result["tax_before_cess"] == slab_tax
        assert result["rebate_87a"] == expected_rebate
        assert result["total_tax"] == 0


def test_fy2025_new_regime_13l_no_marginal_relief_needed():
    result = TaxAgent().calculate_tax_new_regime(1300000 + 75000)
    assert result["taxable_income"] == 1300000
    assert result["tax_before_cess"] == 75000
    assert result["rebate_87a"] == 0
    assert result["marginal_relief"] == 0
    assert result["health_education_cess"] == 3000
    assert result["total_tax"] == 78000


def test_old_regime_87a_threshold_and_cap():
    agent = TaxAgent()
    at_threshold = agent.calculate_tax_old_regime(550000, 0)
    above_threshold = agent.calculate_tax_old_regime(560000, 0)
    assert at_threshold["taxable_income"] == 500000
    assert at_threshold["rebate_87a"] == 12500
    assert at_threshold["total_tax"] == 0
    assert above_threshold["rebate_87a"] == 0
    assert above_threshold["total_tax"] == 15080