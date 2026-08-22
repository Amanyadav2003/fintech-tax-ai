from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Dict, List
from datetime import datetime
import re


class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=10)
    pan: str = Field(..., min_length=10, max_length=10)
    age: int = Field(..., ge=18, le=120)
    state: str = Field(..., min_length=2, max_length=50)
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Validate 10-digit Indian phone number"""
        if not v.isdigit() or len(v) != 10:
            raise ValueError('Phone must be 10 digits')
        return v
    
    @field_validator('pan')
    @classmethod
    def validate_pan(cls, v):
        """Validate PAN format: AAAAA9999A (10 characters)"""
        pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
        if not re.match(pan_pattern, v):
            raise ValueError('PAN must be in format AAAAA9999A')
        return v.upper()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Ensure name contains only letters and spaces"""
        if not re.match(r'^[a-zA-Z\s]*$', v):
            raise ValueError('Name can only contain letters and spaces')
        return v


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    phone: str
    pan: str
    age: int
    state: str
    created_at: datetime

    class Config:
        from_attributes = True


class IncomeData(BaseModel):
    salary: float = Field(default=0, ge=0)
    interest: float = Field(default=0, ge=0)
    dividend: float = Field(default=0, ge=0)
    rental_income: float = Field(default=0, ge=0)
    professional_fees: float = Field(default=0, ge=0)
    tds_deducted: float = Field(default=0, ge=0)
    hra_received: float = Field(default=0, ge=0)
    other_sources: float = Field(default=0, ge=0)
    short_term_capital_gains: float = Field(default=0, ge=0)
    long_term_capital_gains: float = Field(default=0, ge=0)
    
    @field_validator('salary')
    @classmethod
    def validate_salary(cls, v):
        if v < 0:
            raise ValueError('Salary cannot be negative')
        return v


class DeductionsData(BaseModel):
    investments: float = Field(default=0, ge=0)
    health_insurance: float = Field(default=0, ge=0)
    education_loan_interest: float = Field(default=0, ge=0)
    home_loan_interest: float = Field(default=0, ge=0)
    donations: float = Field(default=0, ge=0)
    medical_expenses: float = Field(default=0, ge=0)
    other: float = Field(default=0, ge=0)


class TaxFilingCreate(BaseModel):
    filing_year: int = Field(default=2024, ge=2000, le=2100)  # Reasonable year range
    income_data: IncomeData
    deductions_data: DeductionsData
    tds_paid: float = Field(default=0, ge=0, le=100000000)
    advance_tax_paid: float = Field(default=0, ge=0, le=100000000)
    
    @field_validator('filing_year')
    @classmethod
    def validate_filing_year(cls, v):
        from datetime import datetime
        current_year = datetime.now().year
        if v > current_year + 1:
            raise ValueError('Filing year cannot be more than 1 year in future')
        if v < current_year - 10:
            raise ValueError('Filing year cannot be more than 10 years in past')
        return v


class TaxFilingAnalysis(BaseModel):
    """Complete tax analysis response matching frontend Results component"""
    tax_analysis: Dict
    risk_analysis: Dict
    strategy_analysis: Dict


class TaxFilingResponse(BaseModel):
    id: int
    user_id: int
    filing_year: int
    status: str
    total_income: float
    total_deductions: float
    tax_old_regime: float
    tax_new_regime: float
    recommended_regime: Optional[str] = None
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


# ============ NEW SCHEMAS FOR ENHANCED FEATURES ============

class ChatQuery(BaseModel):
    """Chat message input"""
    message: str = Field(..., min_length=1, max_length=1000)
    context: Optional[Dict] = None


class ChatResponse(BaseModel):
    """Chat message response"""
    response: str
    mode: Optional[str] = "unknown"  # training, execution, hybrid
    module: Optional[str] = "unknown"  # income_tax, gst, accounting
    response_type: Optional[str] = "general"  # lesson, guide, hybrid, general
    next_steps: Optional[List[str]] = []
    intent: Optional[str] = None  # For backward compatibility
    topic: Optional[str] = None
    suggestions: Optional[List[str]] = []  # For backward compatibility
    requires_context: bool = False


class ReportRequest(BaseModel):
    """Report generation request"""
    report_type: str = Field(default="summary")  # summary, ca_documentation, checklist
    filing_id: Optional[int] = None
    tax_data: Optional[Dict] = None
    risk_data: Optional[Dict] = None
    strategy_data: Optional[Dict] = None


class ReportResponse(BaseModel):
    """Report generation response"""
    report_content: str
    report_type: str
    format: str = "text"


class HistoryRequest(BaseModel):
    """History comparison request"""
    current_filing: Dict
    previous_filing: Optional[Dict] = None


class HistoryResponse(BaseModel):
    """History analysis response"""
    comparison_available: bool
    year_over_year: Optional[Dict] = None
    trend_analysis: Optional[Dict] = None
    insights: List[str] = []


class ScenarioRequest(BaseModel):
    """Scenario modeling request"""
    base_income: Dict
    scenarios: List[Dict] = []
    scenario_type: str = Field(default="investment")  # investment, salary, regime


class ScenarioResponse(BaseModel):
    """Scenario modeling response"""
    scenarios: List[Dict]
    optimal_scenario: Optional[Dict] = None
    recommendations: List[str] = []


# ============ CHAT HISTORY SCHEMAS ============

class ChatMessage(BaseModel):
    """Individual chat message"""
    id: int
    message_type: str  # "user" or "bot"
    message_content: str
    operating_mode: Optional[str] = None
    tax_module: Optional[str] = None
    response_type: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatSessionSummary(BaseModel):
    """Summary of a chat session"""
    session_id: str
    message_count: int
    modules_discussed: List[str]
    modes_used: List[str]
    first_message_time: datetime
    last_message_time: datetime
    topics: List[str]


class ChatHistoryRequest(BaseModel):
    """Request for chat history"""
    session_id: Optional[str] = None  # Specific session or all
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    module_filter: Optional[str] = None  # Filter by tax module


class ChatHistoryResponse(BaseModel):
    """Chat history response"""
    messages: List[ChatMessage]
    total_count: int
    session_summaries: Optional[List[ChatSessionSummary]] = []


class ChatFeedback(BaseModel):
    """User feedback on chat response"""
    message_id: int
    helpful: bool
    reason: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)


class ChatAnalytics(BaseModel):
    """Chat analytics data"""
    total_conversations: int
    total_messages: int
    average_response_length: float
    most_discussed_topics: List[str]
    popular_modules: List[str]
    user_engagement_score: float
    last_7_days_activity: List[Dict]
