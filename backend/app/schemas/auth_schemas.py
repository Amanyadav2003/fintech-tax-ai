"""
Updated schemas with enhanced validation and security
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional, Dict, List, Any
from datetime import datetime
from .tax_schemas import reject_pii_in_free_text


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., pattern=r"^\d{10}$", description="10-digit phone number")
    pan: str = Field(..., pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", description="Valid PAN format")
    age: int = Field(..., ge=18, le=100)
    state: str = "Maharashtra"
    employment_type: str = Field(default="Salaried", pattern=r"^(Salaried|Self-employed|Business)$")
    pan_aadhaar_linked: bool = False
    financial_year: str = "FY 2025-26 (AY 2026-27)"
    employer_name: Optional[str] = Field(default=None, max_length=150)
    email_reminders_enabled: bool = True

    @field_validator('employer_name')
    @classmethod
    def validate_employer_name(cls, value):
        return reject_pii_in_free_text(value)

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain digit')
        if not any(char in '!@#$%^&*' for char in v):
            raise ValueError('Password must contain special character')
        return v


class LoginOTPVerification(BaseModel):
    email: EmailStr
    otp: str = Field(..., pattern=r"^\d{6}$")


class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str

    @model_validator(mode='before')
    @classmethod
    def normalize_login_identity(cls, data: Any) -> Any:
        if isinstance(data, dict) and 'email' not in data and 'username' in data:
            username = data['username']
            if isinstance(username, str) and '@' in username:
                data['email'] = username
        return data

    @property
    def login_email(self) -> Optional[str]:
        return self.email or self.username


class OTPVerification(BaseModel):
    email: EmailStr
    otp: str = Field(..., pattern=r"^\d{6}$")


class OTPResend(BaseModel):
    email: EmailStr


class RegistrationResponse(BaseModel):
    email: EmailStr
    message: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    phone: str
    pan: str
    age: int
    state: str
    created_at: datetime
    employment_type: Optional[str] = None
    pan_aadhaar_linked: bool = False
    financial_year: str = "FY 2025-26 (AY 2026-27)"
    employer_name: Optional[str] = None
    email_reminders_enabled: bool = True
    profile_photo_url: Optional[str] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class IncomeData(BaseModel):
    salary: float = Field(ge=0, description="Must be non-negative")
    interest: float = Field(ge=0, description="Must be non-negative")
    dividend: float = Field(ge=0, description="Must be non-negative")
    rental_income: float = Field(ge=0, description="Must be non-negative")
    professional_fees: float = Field(ge=0, description="Must be non-negative")
    tds_deducted: float = Field(default=0, ge=0)
    hra_received: float = Field(default=0, ge=0)
    other_sources: float = Field(default=0, ge=0)
    short_term_capital_gains: float = Field(default=0, ge=0)
    long_term_capital_gains: float = Field(default=0, ge=0)


class NotificationPreferences(BaseModel):
    email_reminders_enabled: bool


class DeductionsData(BaseModel):
    investments: float = Field(ge=0, description="Recommended max ₹1.5L, but allowed higher for calculation")
    health_insurance: float = Field(ge=0, description="Max ₹25K-50K normally")
    education_loan_interest: float = Field(ge=0, description="No limit")
    home_loan_interest: float = Field(ge=0, description="No limit")
    donations: float = Field(ge=0, description="50% of income max")
    medical_expenses: float = Field(ge=0, description="For >60 years or >₹100K")
    other: float = Field(ge=0, description="Other deductions")


class TaxFilingCreate(BaseModel):
    filing_year: int = Field(..., ge=2020, le=2050)
    income_data: IncomeData
    deductions_data: DeductionsData
    tds_paid: float = Field(ge=0, description="TDS already paid")
    advance_tax_paid: float = Field(ge=0, description="Advance tax already paid")

    @field_validator('filing_year')
    @classmethod
    def validate_filing_year(cls, v):
        if v > 2025:
            raise ValueError("Cannot file for future years")
        return v


class TaxFilingAnalysis(BaseModel):
    filing_id: int
    total_income: float
    total_deductions: float
    taxable_income: float
    tax_old_regime: float
    tax_new_regime: float
    recommended_regime: str
    potential_savings: float
    audit_risk_score: float
    audit_risk_level: str
    missed_deductions: List[Dict]
    next_best_actions: List[Dict]


class TaxFilingResponse(BaseModel):
    id: int
    user_id: int
    filing_year: int
    status: str
    total_income: float
    total_deductions: float
    tax_old_regime: float
    tax_new_regime: float
    recommended_regime: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisResult(BaseModel):
    filing_id: int
    tax_agent_output: Dict
    risk_agent_output: Dict
    strategy_agent_output: Dict
    financial_health_score: int
    timestamp: datetime


class DashboardData(BaseModel):
    total_income: float
    total_tax_liability: float
    effective_tax_rate: float
    total_deductions: float
    audit_risk_level: str
    missed_opportunities: int
    estimated_savings: float
    financial_health_score: int


class ErrorResponse(BaseModel):
    detail: str
    error_code: str
    timestamp: datetime


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
