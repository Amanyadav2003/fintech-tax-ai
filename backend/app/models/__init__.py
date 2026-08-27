from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    phone = Column(String)
    pan = Column(String, unique=True, index=True)  # Encrypted in production
    password_hash = Column(String)  # Hashed password
    age = Column(Integer)
    state = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    otp_code = Column(String, nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    employment_type = Column(String, nullable=True)
    pan_aadhaar_linked = Column(Boolean, default=False, nullable=False)
    financial_year = Column(String, default="FY 2025-26 (AY 2026-27)", nullable=False)
    employer_name = Column(String, nullable=True)
    email_reminders_enabled = Column(Boolean, default=True, nullable=False)
    profile_photo_url = Column(String, nullable=True)
    verification_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    document_type = Column(String, index=True, nullable=False)
    file_path = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    extracted_data = Column(JSON, nullable=False, default=dict)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TaxFiling(Base):
    __tablename__ = "tax_filings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    filing_year = Column(Integer)
    status = Column(String)  # draft, completed, filed
    
    # Income details
    salary = Column(Float, default=0)
    interest = Column(Float, default=0)
    dividend = Column(Float, default=0)
    rental_income = Column(Float, default=0)
    professional_fees = Column(Float, default=0)
    total_income = Column(Float, default=0)
    
    # Deductions
    investments_80c = Column(Float, default=0)
    health_insurance_80d = Column(Float, default=0)
    education_loan_80e = Column(Float, default=0)
    home_loan_interest_80emi = Column(Float, default=0)
    donations_80g = Column(Float, default=0)
    other_deductions = Column(Float, default=0)
    total_deductions = Column(Float, default=0)
    
    # Tax calculation
    taxable_income = Column(Float, default=0)
    tax_old_regime = Column(Float, default=0)
    tax_new_regime = Column(Float, default=0)
    recommended_regime = Column(String)  # old or new
    tds_paid = Column(Float, default=0)
    advance_tax_paid = Column(Float, default=0)
    
    # Agent outputs (JSON)
    tax_agent_output = Column(JSON)
    risk_agent_output = Column(JSON)
    strategy_agent_output = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    description = Column(String, nullable=True)
    date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AuditFlag(Base):
    __tablename__ = "audit_flags"

    id = Column(Integer, primary_key=True, index=True)
    filing_id = Column(Integer, index=True, nullable=False)
    flag_type = Column(String)  # high_deduction, missing_deduction, duplicate_claim, etc.
    severity = Column(String)  # low, medium, high
    description = Column(String)
    recommendation = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class BenchmarkData(Base):
    __tablename__ = "benchmark_data"

    id = Column(Integer, primary_key=True, index=True)
    income_bracket_min = Column(Float)
    income_bracket_max = Column(Float)
    deduction_type = Column(String)  # 80c, 80d, etc.
    median_amount = Column(Float)
    mean_amount = Column(Float)
    percentile_75 = Column(Float)
    percentile_90 = Column(Float)
    audit_risk_percentage = Column(Float)
    year = Column(Integer)


class TokenBlacklist(Base):
    """Stores revoked tokens to prevent reuse after logout"""
    __tablename__ = "token_blacklist"
    
    id = Column(Integer, primary_key=True, index=True)
    token_jti = Column(String, unique=True, index=True)  # JWT ID claim for revocation
    user_id = Column(Integer, index=True)
    blacklisted_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime)  # When to delete this entry
    
    def __repr__(self):
        return f"<TokenBlacklist(user_id={self.user_id}, jti={self.token_jti[:8] if self.token_jti else 'N/A'})>"


class ChatHistory(Base):
    """Stores chat conversation history for users"""
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    session_id = Column(String, index=True)  # Group related messages
    message_type = Column(String)  # "user" or "bot"
    message_content = Column(String)  # The actual message text
    
    # Context information
    operating_mode = Column(String)  # training, execution, hybrid
    tax_module = Column(String)  # income_tax, gst, accounting, general
    sub_module = Column(String, nullable=True)  # Specific topic
    
    # Response metadata
    response_type = Column(String, nullable=True)  # educational, procedural, calculation, etc.
    next_steps = Column(JSON, nullable=True)  # Suggested follow-up topics
    confidence_score = Column(Float, nullable=True)  # How confident was the response
    
    # Interaction tracking
    tokens_used = Column(Integer, default=0)
    response_time_ms = Column(Integer, default=0)
    helpful = Column(Boolean, nullable=True)  # User feedback
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ChatHistory(user_id={self.user_id}, mode={self.operating_mode}, module={self.tax_module})>"
