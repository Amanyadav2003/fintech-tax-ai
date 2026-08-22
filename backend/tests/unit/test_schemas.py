"""
Unit tests for request schema validation
"""

import pytest
from pydantic import ValidationError
from app.schemas.tax_schemas import (
    UserCreate,
    IncomeData,
    DeductionsData,
    TaxFilingCreate
)


class TestUserValidation:
    """Test UserCreate schema validation"""
    
    def test_valid_user_creation(self, test_user_data):
        """Test creating valid user"""
        user = UserCreate(**test_user_data)
        assert user.email == test_user_data["email"]
        assert user.name == test_user_data["name"]
        assert user.age == test_user_data["age"]
    
    def test_invalid_email(self, test_user_data):
        """Test invalid email validation"""
        invalid_data = {**test_user_data, "email": "invalid_email"}
        
        with pytest.raises(ValidationError):
            UserCreate(**invalid_data)
    
    def test_invalid_phone_format(self, test_user_data):
        """Test invalid phone format"""
        # Too short
        with pytest.raises(ValidationError):
            UserCreate(**{**test_user_data, "phone": "123456789"})
        
        # Non-numeric
        with pytest.raises(ValidationError):
            UserCreate(**{**test_user_data, "phone": "987654321a"})
    
    def test_invalid_pan_format(self, test_user_data):
        """Test invalid PAN format"""
        # Wrong format
        with pytest.raises(ValidationError):
            UserCreate(**{**test_user_data, "pan": "INVALID"})
    
    def test_pan_case_insensitive(self, test_user_data):
        """Test PAN is converted to uppercase"""
        user_data = {**test_user_data, "pan": "abcde1234f"}
        user = UserCreate(**user_data)
        assert user.pan == "ABCDE1234F"
    
    def test_age_validation(self, test_user_data):
        """Test age validation"""
        # Too young
        with pytest.raises(ValidationError):
            UserCreate(**{**test_user_data, "age": 17})
        
        # Too old
        with pytest.raises(ValidationError):
            UserCreate(**{**test_user_data, "age": 121})
    
    def test_name_validation(self, test_user_data):
        """Test name validation (letters and spaces only)"""
        # Invalid characters
        with pytest.raises(ValidationError):
            UserCreate(**{**test_user_data, "name": "Test123"})
        
        with pytest.raises(ValidationError):
            UserCreate(**{**test_user_data, "name": "Test@User"})
    
    def test_name_length_validation(self, test_user_data):
        """Test name length validation"""
        # Too short
        with pytest.raises(ValidationError):
            UserCreate(**{**test_user_data, "name": "A"})
        
        # Too long
        long_name = "A" * 101
        with pytest.raises(ValidationError):
            UserCreate(**{**test_user_data, "name": long_name})


class TestIncomeValidation:
    """Test IncomeData schema validation"""
    
    def test_valid_income(self):
        """Test valid income data"""
        income = IncomeData(
            salary=1000000,
            interest=50000,
            dividend=100000
        )
        assert income.salary == 1000000
        assert income.interest == 50000
    
    def test_negative_income_validation(self):
        """Test negative income validation"""
        with pytest.raises(ValidationError):
            IncomeData(salary=-100000)
    
    def test_income_max_limits(self):
        """Test income maximum limits"""
        # Salary max 100 crore
        with pytest.raises(ValidationError):
            IncomeData(salary=100000001)
        
        # Interest max 50 lakh
        with pytest.raises(ValidationError):
            IncomeData(interest=5000001)
    
    def test_income_defaults(self):
        """Test income defaults to 0"""
        income = IncomeData()
        assert income.salary == 0
        assert income.interest == 0
        assert income.dividend == 0


class TestDeductionsValidation:
    """Test DeductionsData schema validation"""
    
    def test_valid_deductions(self):
        """Test valid deductions data"""
        deductions = DeductionsData(
            investments=150000,  # 80C max 1.5L
            health_insurance=25000,  # 80D max 5L
            home_loan_interest=200000  # 80EMI max 20L
        )
        assert deductions.investments == 150000
    
    def test_80c_limit(self):
        """Test 80C limit (max 1.5L)"""
        with pytest.raises(ValidationError):
            DeductionsData(investments=1500001)
    
    def test_80d_limit(self):
        """Test 80D limit (max 5L)"""
        with pytest.raises(ValidationError):
            DeductionsData(health_insurance=500001)
    
    def test_80emi_limit(self):
        """Test 80EMI limit (max 20L)"""
        with pytest.raises(ValidationError):
            DeductionsData(home_loan_interest=2000001)
    
    def test_negative_deductions_validation(self):
        """Test negative deductions validation"""
        with pytest.raises(ValidationError):
            DeductionsData(investments=-10000)


class TestTaxFilingValidation:
    """Test TaxFilingCreate schema validation"""
    
    def test_valid_tax_filing(self, test_tax_filing_data):
        """Test valid tax filing"""
        filing = TaxFilingCreate(
            user_id=1,
            filing_year=2024,
            income_data=IncomeData(**test_tax_filing_data["income_data"]),
            deductions_data=DeductionsData(**test_tax_filing_data["deductions_data"])
        )
        assert filing.user_id == 1
        assert filing.filing_year == 2024
    
    def test_invalid_user_id(self, test_tax_filing_data):
        """Test invalid user ID (must be > 0)"""
        with pytest.raises(ValidationError):
            TaxFilingCreate(
                user_id=-1,
                filing_year=2024,
                income_data=IncomeData(**test_tax_filing_data["income_data"]),
                deductions_data=DeductionsData(**test_tax_filing_data["deductions_data"])
            )
    
    def test_invalid_filing_year(self, test_tax_filing_data):
        """Test invalid filing year"""
        # Too far in future
        with pytest.raises(ValidationError):
            TaxFilingCreate(
                user_id=1,
                filing_year=2030,
                income_data=IncomeData(**test_tax_filing_data["income_data"]),
                deductions_data=DeductionsData(**test_tax_filing_data["deductions_data"])
            )
        
        # Too far in past
        with pytest.raises(ValidationError):
            TaxFilingCreate(
                user_id=1,
                filing_year=2000,
                income_data=IncomeData(**test_tax_filing_data["income_data"]),
                deductions_data=DeductionsData(**test_tax_filing_data["deductions_data"])
            )
    
    def test_filing_year_range(self, test_tax_filing_data):
        """Test filing year valid range"""
        # Should accept current year
        from datetime import datetime
        current_year = datetime.now().year
        
        filing = TaxFilingCreate(
            user_id=1,
            filing_year=current_year,
            income_data=IncomeData(**test_tax_filing_data["income_data"]),
            deductions_data=DeductionsData(**test_tax_filing_data["deductions_data"])
        )
        assert filing.filing_year == current_year
