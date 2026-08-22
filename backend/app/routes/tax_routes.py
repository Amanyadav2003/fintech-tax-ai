from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
import json
from datetime import datetime

from ..models import User, TaxFiling, AuditFlag, ChatHistory
from ..schemas.tax_schemas import (
    UserCreate, UserResponse, TaxFilingCreate, TaxFilingResponse,
    TaxFilingAnalysis, IncomeData, DeductionsData,
    ChatQuery, ChatResponse, ReportRequest, ReportResponse,
    HistoryRequest, HistoryResponse, ScenarioRequest, ScenarioResponse,
    ChatMessage, ChatHistoryRequest, ChatHistoryResponse, ChatFeedback, ChatAnalytics
)
from ..agents.tax_agent import TaxAgent
from ..agents.risk_agent import RiskAgent
from ..agents.strategy_agent import StrategyAgent
from ..agents.chat_agent import ChatAgent
from ..agents.enhanced_chat_agent import EnhancedChatAgent, ConversationContext
from ..agents.report_agent import ReportAgent
from ..agents.history_agent import HistoryAgent
from ..agents.scenario_agent import ScenarioAgent
from ..utils.database import get_db
from ..utils.dependencies import get_current_user
from ..utils.logging_config import logger
from ..utils.middleware import limiter

router = APIRouter(prefix="/api/tax", tags=["tax"])

# Initialize agents
tax_agent = TaxAgent()
risk_agent = RiskAgent()
strategy_agent = StrategyAgent()


@router.post("/filings", response_model=TaxFilingResponse)
@limiter.limit("10/minute")
def create_tax_filing(
    request: Request,
    filing: TaxFilingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new tax filing (authenticated users only)"""
    
    try:
        # Create filing record
        db_filing = TaxFiling(
            user_id=current_user.id,
            filing_year=filing.filing_year,
            status="draft",
            salary=filing.income_data.salary,
            interest=filing.income_data.interest,
            dividend=filing.income_data.dividend,
            rental_income=filing.income_data.rental_income,
            professional_fees=filing.income_data.professional_fees,
            investments_80c=filing.deductions_data.investments,
            health_insurance_80d=filing.deductions_data.health_insurance,
            education_loan_80e=filing.deductions_data.education_loan_interest,
            home_loan_interest_80emi=filing.deductions_data.home_loan_interest,
            donations_80g=filing.deductions_data.donations,
            tds_paid=filing.tds_paid,
            advance_tax_paid=filing.advance_tax_paid
        )
        
        db.add(db_filing)
        db.commit()
        db.refresh(db_filing)
        
        logger.info(f"Tax filing created: user={current_user.id}, filing_id={db_filing.id}, year={filing.filing_year}")
        
        return db_filing
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating tax filing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating tax filing"
        )


@router.post("/analyze", response_model=TaxFilingAnalysis)
@limiter.limit("5/minute")
def analyze_direct(
    request: Request,
    filing_data: TaxFilingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Direct tax analysis without creating a filing first (for frontend)"""
    
    try:
        # Prepare data for agents
        income_data = {
            "salary": filing_data.income_data.salary or 0,
            "interest": filing_data.income_data.interest or 0,
            "dividend": filing_data.income_data.dividend or 0,
            "rental_income": filing_data.income_data.rental_income or 0,
            "professional_fees": filing_data.income_data.professional_fees or 0,
            "tds_deducted": filing_data.income_data.tds_deducted or 0,
            "hra_received": filing_data.income_data.hra_received or 0,
            "other_sources": filing_data.income_data.other_sources or 0,
            "short_term_capital_gains": filing_data.income_data.short_term_capital_gains or 0,
            "long_term_capital_gains": filing_data.income_data.long_term_capital_gains or 0,
            "age": current_user.age or 30,
            "total_income": (
                (filing_data.income_data.salary or 0) +
                (filing_data.income_data.interest or 0) +
                (filing_data.income_data.dividend or 0) +
                (filing_data.income_data.rental_income or 0) +
                (filing_data.income_data.professional_fees or 0)
            ),
        }
        
        deductions_data = {
            "investments": filing_data.deductions_data.investments or 0,
            "health_insurance": filing_data.deductions_data.health_insurance or 0,
            "education_loan_interest": filing_data.deductions_data.education_loan_interest or 0,
            "home_loan_interest": filing_data.deductions_data.home_loan_interest or 0,
            "donations": filing_data.deductions_data.donations or 0,
            "medical_expenses": filing_data.deductions_data.medical_expenses or 0,
            "other": filing_data.deductions_data.other or 0,
        }
        
        # Run TAX AGENT
        tax_result = tax_agent.process_filing(income_data, deductions_data)
        logger.info(f"Direct tax analysis completed: user={current_user.id}")
        
        # Run RISK AGENT
        filing_data_for_risk = {
            "total_income": income_data["total_income"],
            "matched_deductions": tax_result["deductions"]["matched_deductions"],
            "tds_paid": filing_data.tds_paid or 0,
            "salary_reported": filing_data.income_data.salary or 0,
        }
        risk_result = risk_agent.analyze_filing(filing_data_for_risk)
        logger.info(f"Risk analysis completed: user={current_user.id}, risk_level={risk_result['risk_level']}")
        
        # Run STRATEGY AGENT
        filing_data_for_strategy = {
            "total_income": income_data["total_income"],
            "80d_claimed": filing_data.deductions_data.health_insurance or 0,
            "80e_claimed": filing_data.deductions_data.education_loan_interest or 0,
            "80emi_claimed": filing_data.deductions_data.home_loan_interest or 0,
            "80g_claimed": filing_data.deductions_data.donations or 0,
            "tax_liability": float(tax_result["recommendation"]["tax_new_regime"] or 0),
            "deduction_ratio": float(
                tax_result["deductions"]["total_deductions"] / income_data["total_income"]
                if income_data["total_income"] > 0 else 0
            ),
            "effective_tax_rate": float(
                (tax_result["recommendation"]["tax_new_regime"] or 0) / (income_data["total_income"] or 1)
                if income_data["total_income"] > 0 else 0
            ),
        }
        strategy_result = strategy_agent.get_next_best_actions({}, filing_data_for_strategy, risk_result)
        missed_deductions = strategy_agent.identify_missed_deductions({}, filing_data_for_strategy)
        financial_health_score = strategy_agent.score_financial_health({}, filing_data_for_strategy)
        logger.info(f"Strategy analysis completed: user={current_user.id}")
        
        # Calculate penalty if audited
        penalty_calc = risk_agent.calculate_penalty_if_audited(
            risk_result["audit_flags"],
            income_data["total_income"]
        )
        
        # Persist the completed analysis for the home and history views.
        saved_filing = TaxFiling(
            user_id=current_user.id,
            filing_year=filing_data.filing_year,
            status="analyzed",
            salary=filing_data.income_data.salary,
            interest=filing_data.income_data.interest,
            dividend=filing_data.income_data.dividend,
            rental_income=filing_data.income_data.rental_income,
            professional_fees=filing_data.income_data.professional_fees,
            total_income=income_data["total_income"],
            investments_80c=filing_data.deductions_data.investments,
            health_insurance_80d=filing_data.deductions_data.health_insurance,
            education_loan_80e=filing_data.deductions_data.education_loan_interest,
            home_loan_interest_80emi=filing_data.deductions_data.home_loan_interest,
            donations_80g=filing_data.deductions_data.donations,
            total_deductions=tax_result["deductions"]["total_deductions"],
            taxable_income=tax_result["tax_old_regime"]["taxable_income"],
            tax_old_regime=tax_result["tax_old_regime"]["total_tax"],
            tax_new_regime=tax_result["tax_new_regime"]["total_tax"],
            recommended_regime=tax_result["recommendation"]["recommended_regime"],
            tax_agent_output=json.dumps(tax_result),
            risk_agent_output=json.dumps(risk_result),
            strategy_agent_output=json.dumps({"next_actions": strategy_result, "missed_deductions": missed_deductions}),
        )
        db.add(saved_filing)
        db.commit()

        # Return response in format that matches Results.js expectations
        return {
            "tax_analysis": {
                "recommended_regime": tax_result["recommendation"]["recommended_regime"],
                "potential_savings": tax_result["recommendation"]["potential_savings"],
                "gross_income": income_data["total_income"],
                "total_deductions": tax_result["deductions"]["total_deductions"],
                "taxable_income": tax_result["tax_old_regime"]["taxable_income"],
                "old_regime_tax": tax_result["tax_old_regime"]["total_tax"],
                "new_regime_tax": tax_result["tax_new_regime"]["total_tax"],
            },
            "risk_analysis": {
                "audit_risk_score": risk_result["overall_audit_risk_score"],
                "risk_level": risk_result["risk_level"],
                "flags": [flag["reason"] for flag in risk_result["audit_flags"]],
                "penalty_if_audited": penalty_calc["estimated_penalty"],
            },
            "strategy_analysis": {
                "financial_health_score": financial_health_score,
                "missed_opportunities": [d.get("description", "") for d in missed_deductions],
                "recommended_actions": [a.get("action", "") for a in strategy_result],
            },
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Error during direct analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during analysis: {str(e)}"
        )


@router.get("/history")
@limiter.limit("20/minute")
def get_analysis_history(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    filings = db.query(TaxFiling).filter(TaxFiling.user_id == current_user.id).order_by(TaxFiling.created_at.desc()).all()
    return [{
        "filing_id": filing.id,
        "created_at": filing.created_at,
        "gross_income": filing.total_income,
        "total_deductions": filing.total_deductions,
        "recommended_regime": filing.recommended_regime,
        "tax_old_regime": filing.tax_old_regime,
        "tax_new_regime": filing.tax_new_regime,
        "potential_savings": abs(filing.tax_old_regime - filing.tax_new_regime),
        "audit_risk_score": (json.loads(filing.risk_agent_output).get("overall_audit_risk_score", 0) if filing.risk_agent_output else 0),
    } for filing in filings]


@router.post("/analyze/{filing_id}", response_model=TaxFilingAnalysis)
@limiter.limit("5/minute")
def analyze_filing(
    request: Request,
    filing_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run all 3 agents on a filing (authenticated users only)"""
    
    try:
        # Get filing
        filing = db.query(TaxFiling).filter(TaxFiling.id == filing_id).first()
        if not filing:
            raise HTTPException(status_code=404, detail="Filing not found")
        
        # Check ownership
        if filing.user_id != current_user.id:
            logger.warning(f"Unauthorized access attempt: user={current_user.id}, filing={filing_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this filing"
            )
        
        # Prepare data for agents
        income_data = {
            "salary": filing.salary,
            "interest": filing.interest,
            "dividend": filing.dividend,
            "rental_income": filing.rental_income,
            "professional_fees": filing.professional_fees,
            "age": current_user.age,
            "total_income": filing.salary + filing.interest + filing.dividend + filing.rental_income + filing.professional_fees,
        }
        
        deductions_data = {
            "investments": filing.investments_80c,
            "health_insurance": filing.health_insurance_80d,
            "education_loan_interest": filing.education_loan_80e,
            "home_loan_interest": filing.home_loan_interest_80emi,
            "donations": filing.donations_80g,
        }
        
        # Run TAX AGENT
        tax_agent = TaxAgent()
        tax_result = tax_agent.process_filing(income_data, deductions_data)
        logger.info(f"Tax analysis completed: user={current_user.id}, filing={filing_id}")
        
        # Run RISK AGENT
        filing_data_for_risk = {
            "total_income": income_data["total_income"],
            "matched_deductions": tax_result["deductions"]["matched_deductions"],
            "tds_paid": filing.tds_paid,
            "salary_reported": filing.salary,
        }
        risk_agent = RiskAgent()
        risk_result = risk_agent.analyze_filing(filing_data_for_risk)
        logger.info(f"Risk analysis completed: user={current_user.id}, filing={filing_id}, risk_level={risk_result['risk_level']}")
        
        # Run STRATEGY AGENT
        strategy_agent = StrategyAgent()
        filing_data_for_strategy = {
            "total_income": income_data["total_income"],
            "80d_claimed": filing.health_insurance_80d,
            "80e_claimed": filing.education_loan_80e,
            "80emi_claimed": filing.home_loan_interest_80emi,
            "80g_claimed": filing.donations_80g,
            "tax_liability": tax_result["recommendation"]["tax_new_regime"] if tax_result["recommendation"]["recommended_regime"] == "new" else tax_result["recommendation"]["tax_old_regime"],
        }
        strategy_result = strategy_agent.get_next_best_actions({}, filing_data_for_strategy, risk_result)
        missed_deductions = strategy_agent.identify_missed_deductions({}, filing_data_for_strategy)
        financial_health_score = strategy_agent.score_financial_health({}, filing_data_for_strategy)
        logger.info(f"Strategy analysis completed: user={current_user.id}, filing={filing_id}")
        
        # Calculate penalty if audited
        penalty_calc = risk_agent.calculate_penalty_if_audited(risk_result["audit_flags"], income_data["total_income"])
        
        # Update filing with results
        filing.tax_agent_output = json.dumps(tax_result)
        filing.risk_agent_output = json.dumps(risk_result)
        filing.strategy_agent_output = json.dumps({"next_actions": strategy_result, "missed_deductions": missed_deductions})
        filing.tax_old_regime = tax_result["tax_old_regime"]["total_tax"]
        filing.tax_new_regime = tax_result["tax_new_regime"]["total_tax"]
        filing.recommended_regime = tax_result["recommendation"]["recommended_regime"]
        filing.total_income = income_data["total_income"]
        filing.total_deductions = tax_result["deductions"]["total_deductions"]
        filing.taxable_income = tax_result[f"tax_{tax_result['recommendation']['recommended_regime']}_regime"]["taxable_income"]
        filing.status = "analyzed"
        db.commit()
        db.refresh(filing)
        
        # Format audit flags as simple strings for frontend
        audit_flag_strings = [f"{flag['reason']}" for flag in risk_result["audit_flags"]]
        
        return {
            "filing_id": filing_id,
            "total_income": income_data["total_income"],
            "total_deductions": tax_result["deductions"]["total_deductions"],
            "taxable_income": filing.taxable_income,
            "tax_old_regime": tax_result["tax_old_regime"]["total_tax"],
            "tax_new_regime": tax_result["tax_new_regime"]["total_tax"],
            "recommended_regime": tax_result["recommendation"]["recommended_regime"],
            "potential_savings": tax_result["recommendation"]["potential_savings"],
            "audit_risk_score": risk_result["overall_audit_risk_score"],
            "audit_risk_level": risk_result["risk_level"],
            "audit_flags": audit_flag_strings,
            "potential_penalty": penalty_calc["estimated_penalty"],
            "missed_deductions": [f"{d.get('deduction', 'Deduction')} - {d.get('description', '')}" for d in missed_deductions],
            "financial_health_score": financial_health_score,
            "next_best_actions": [f"{a.get('priority', 0)}. {a.get('action', '')}" for a in strategy_result[:3]],
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Error during analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during analysis"
        )


@router.get("/results/{filing_id}")
@limiter.limit("20/minute")
def get_analysis_results(
    request: Request,
    filing_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analysis results for a filing"""
    
    try:
        filing = db.query(TaxFiling).filter(TaxFiling.id == filing_id).first()
        if not filing:
            raise HTTPException(status_code=404, detail="Filing not found")
        
        # Check ownership
        if filing.user_id != current_user.id:
            logger.warning(f"Unauthorized access attempt: user={current_user.id}, filing={filing_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this filing"
            )
        
        return {
            "filing_id": filing.id,
            "status": filing.status,
            "total_income": filing.total_income,
            "total_deductions": filing.total_deductions,
            "tax_old_regime": filing.tax_old_regime,
            "tax_new_regime": filing.tax_new_regime,
            "recommended_regime": filing.recommended_regime,
            "tax_agent_output": json.loads(filing.tax_agent_output) if filing.tax_agent_output else None,
            "risk_agent_output": json.loads(filing.risk_agent_output) if filing.risk_agent_output else None,
            "strategy_agent_output": json.loads(filing.strategy_agent_output) if filing.strategy_agent_output else None,
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving results"
        )


@router.get("/dashboard")
@limiter.limit("20/minute")
def get_dashboard(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's tax dashboard"""
    
    try:
        # Get latest filing
        latest_filing = db.query(TaxFiling).filter(
            TaxFiling.user_id == current_user.id
        ).order_by(TaxFiling.created_at.desc()).first()

        if not latest_filing:
            return {
                "message": "No filings found",
                "compliance_dashboard": _build_default_compliance_dashboard(current_user)
            }

        effective_tax_rate = (latest_filing.tax_old_regime / latest_filing.total_income * 100) if latest_filing.total_income > 0 else 0
        total_tax_liability = latest_filing.tax_new_regime if latest_filing.recommended_regime == "new" else latest_filing.tax_old_regime
        compliance_dashboard = _build_compliance_dashboard(current_user, latest_filing)

        return {
            "user_id": current_user.id,
            "total_income": latest_filing.total_income,
            "total_tax_liability": total_tax_liability,
            "effective_tax_rate": effective_tax_rate,
            "total_deductions": latest_filing.total_deductions,
            "recommended_regime": latest_filing.recommended_regime,
            "potential_savings": abs(latest_filing.tax_old_regime - latest_filing.tax_new_regime),
            "last_updated": latest_filing.updated_at,
            "compliance_dashboard": compliance_dashboard,
        }
    
    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving dashboard"
        )


def _build_default_compliance_dashboard(current_user: User) -> dict:
    """Build a default compliance dashboard for users without filings."""

    return {
        "filing_status": {
            "status": "not_started",
            "label": "Not started",
            "next_action": "Start a tax analysis to generate compliance guidance",
            "steps": [
                {"name": "Draft", "completed": False},
                {"name": "Ready to File", "completed": False},
                {"name": "Filed", "completed": False},
                {"name": "Verified", "completed": False},
            ],
        },
        "reminders": [
            {
                "id": "itr",
                "title": "ITR filing",
                "due_date": "31 July",
                "status": "upcoming",
                "description": "Prepare and submit your income tax return before the due date.",
            },
            {
                "id": "advance_tax",
                "title": "Advance tax",
                "due_date": "15 Jun / 15 Sep / 15 Dec / 15 Mar",
                "status": "ongoing",
                "description": "Review quarterly advance tax installments and avoid interest under 234B/234C.",
            },
            {
                "id": "tds",
                "title": "TDS verification",
                "due_date": "Before e-filing",
                "status": "upcoming",
                "description": "Reconcile Form 16, Form 26AS, AIS, and TIS before filing.",
            },
        ],
        "checklist": [
            {"id": "personal_details", "label": "Verify PAN, Aadhaar, and bank details", "completed": bool(current_user.pan)},
            {"id": "form16", "label": "Collect Form 16 / 16A", "completed": False},
            {"id": "forms", "label": "Check Form 26AS, AIS, and TIS", "completed": False},
            {"id": "proofs", "label": "Gather deduction proofs", "completed": False},
            {"id": "verify", "label": "E-verify the return after filing", "completed": False},
        ],
        "documents": [
            {"id": "form16", "name": "Form 16 / 16A", "required": True, "reason": "TDS reconciliation"},
            {"id": "pan", "name": "PAN and Aadhaar", "required": True, "reason": "Identity verification"},
            {"id": "bank", "name": "Bank account proof", "required": True, "reason": "Refund credit"},
            {"id": "proofs", "name": "Deduction receipts", "required": False, "reason": "80C / 80D / 80G claims"},
            {"id": "home_loan", "name": "Home loan interest certificate", "required": False, "reason": "House property deductions"},
            {"id": "form26as", "name": "Form 26AS / AIS / TIS", "required": True, "reason": "Tax credit matching"},
        ],
    }


def _build_compliance_dashboard(current_user: User, latest_filing: TaxFiling) -> dict:
    """Build a compliance dashboard from the latest filing data."""

    status = (latest_filing.status or "draft").lower()

    if status in {"filed", "verified"}:
        filing_stage = "filed"
        filing_label = "Filed"
        next_action = "E-verify the return and keep proof of filing"
    elif status in {"analyzed", "completed"}:
        filing_stage = "ready_to_file"
        filing_label = "Ready to file"
        next_action = "Review disclosures, upload proofs, and e-file the return"
    else:
        filing_stage = "draft"
        filing_label = "Draft"
        next_action = "Complete income and deduction details"

    reminders = [
        {
            "id": "itr",
            "title": "ITR filing",
            "due_date": f"31 July {latest_filing.filing_year + 1}",
            "status": "upcoming" if filing_stage != "filed" else "completed",
            "description": "File the return before the CBDT due date for the assessment year.",
        },
        {
            "id": "advance_tax",
            "title": "Advance tax",
            "due_date": "15 Jun / 15 Sep / 15 Dec / 15 Mar",
            "status": "ongoing" if latest_filing.advance_tax_paid >= 0 else "upcoming",
            "description": "Review estimated liability and keep quarterly installments on track.",
        },
        {
            "id": "tds",
            "title": "TDS verification",
            "due_date": "Before e-filing / within verification window",
            "status": "attention" if latest_filing.tds_paid > 0 else "upcoming",
            "description": "Match TDS against Form 16, Form 26AS, AIS, and TIS.",
        },
    ]

    checklist = [
        {
            "id": "form16",
            "label": "Collect Form 16 / 16A",
            "completed": latest_filing.tds_paid > 0,
            "detail": "Use it to verify salary TDS and interest TDS.",
        },
        {
            "id": "forms",
            "label": "Cross-check Form 26AS, AIS, and TIS",
            "completed": latest_filing.total_income > 0,
            "detail": "Reconcile all reported tax credits before filing.",
        },
        {
            "id": "proofs_80c",
            "label": "Upload 80C investment proofs",
            "completed": latest_filing.investments_80c > 0,
            "detail": "PPF, ELSS, LIC, EPF, and tuition fee receipts.",
        },
        {
            "id": "proofs_80d",
            "label": "Upload 80D health insurance receipts",
            "completed": latest_filing.health_insurance_80d > 0,
            "detail": "Premium receipts for self, family, and parents.",
        },
        {
            "id": "home_loan",
            "label": "Upload home loan interest certificate",
            "completed": latest_filing.home_loan_interest_80emi > 0,
            "detail": "Needed for Section 24(b) claims.",
        },
        {
            "id": "verify",
            "label": "E-verify the return after filing",
            "completed": filing_stage == "filed",
            "detail": "Choose Aadhaar OTP, net banking, or other permitted methods.",
        },
    ]

    documents = [
        {
            "id": "form16",
            "name": "Form 16 / 16A",
            "required": True,
            "reason": "TDS reconciliation",
            "uploaded": latest_filing.tds_paid > 0,
        },
        {
            "id": "bank",
            "name": "Bank account proof",
            "required": True,
            "reason": "Refund credit",
            "uploaded": filing_stage == "filed",
        },
        {
            "id": "proofs",
            "name": "Deduction receipts",
            "required": False,
            "reason": "80C / 80D / 80G claims",
            "uploaded": latest_filing.total_deductions > 0,
        },
        {
            "id": "home_loan",
            "name": "Home loan certificate",
            "required": False,
            "reason": "House property deduction",
            "uploaded": latest_filing.home_loan_interest_80emi > 0,
        },
        {
            "id": "form26as",
            "name": "Form 26AS / AIS / TIS",
            "required": True,
            "reason": "Tax credit matching",
            "uploaded": latest_filing.total_income > 0,
        },
    ]

    steps = [
        {"name": "Draft", "completed": filing_stage in {"draft", "ready_to_file", "filed"}},
        {"name": "Ready to File", "completed": filing_stage in {"ready_to_file", "filed"}},
        {"name": "Filed", "completed": filing_stage == "filed"},
        {"name": "Verified", "completed": latest_filing.status.lower() == "verified" if latest_filing.status else False},
    ]

    completion_count = sum(1 for item in checklist if item["completed"])
    completion_percent = round((completion_count / len(checklist)) * 100) if checklist else 0

    uploaded_count = sum(1 for item in documents if item["uploaded"])

    return {
        "filing_status": {
            "status": filing_stage,
            "label": filing_label,
            "next_action": next_action,
            "steps": steps,
        },
        "reminders": reminders,
        "checklist": checklist,
        "documents": documents,
        "tracking": {
            "completion_percent": completion_percent,
            "completed_items": completion_count,
            "total_items": len(checklist),
            "uploaded_documents": uploaded_count,
            "required_documents": sum(1 for item in documents if item["required"]),
        },
    }


# ============ NEW API ROUTES FOR ENHANCED FEATURES ============

# Initialize new agents
enhanced_chat_agent = EnhancedChatAgent()
report_agent = ReportAgent()
history_agent = HistoryAgent()
scenario_agent = ScenarioAgent()


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
def chat(
    request: Request,
    query: ChatQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI Chat Assistant - Ask tax questions with history tracking"""

    try:
        # Generate session ID from user (or could be passed in query)
        session_id = query.context.get("session_id", f"session_{current_user.id}_{datetime.now().timestamp()}") if query.context else f"session_{current_user.id}_{datetime.now().timestamp()}"
        
        # Create conversation context for user
        conversation = ConversationContext(str(current_user.id))
        
        # Use EnhancedChatAgent
        result = enhanced_chat_agent.generate_response(query.message, conversation)
        
        # Ensure result is a dict
        if isinstance(result, str):
            result = {
                "response": result,
                "mode": "unknown",
                "module": "unknown",
                "response_type": "general",
                "next_steps": []
            }
        
        # Clean up response to remove non-serializable objects
        response_data = {
            "response": result.get("response", ""),
            "mode": result.get("mode", "unknown"),
            "module": result.get("module", "unknown"),
            "response_type": result.get("response_type", "general"),
            "next_steps": result.get("next_steps", []),
        }
        
        # Save user message to chat history
        try:
            user_message_db = ChatHistory(
                user_id=current_user.id,
                session_id=session_id,
                message_type="user",
                message_content=query.message,
                operating_mode=None,
                tax_module=None,
                response_type=None
            )
            db.add(user_message_db)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to save user message to history: {str(e)}")
            db.rollback()
        
        # Save bot response to chat history
        try:
            bot_message_db = ChatHistory(
                user_id=current_user.id,
                session_id=session_id,
                message_type="bot",
                message_content=response_data.get("response", ""),
                operating_mode=response_data.get("mode"),
                tax_module=response_data.get("module"),
                response_type=response_data.get("response_type"),
                next_steps=response_data.get("next_steps"),
                confidence_score=0.95  # Can be improved with actual confidence metrics
            )
            db.add(bot_message_db)
            db.commit()
            
            # Return session ID with response for frontend tracking
            response_data["session_id"] = session_id
        except Exception as e:
            logger.warning(f"Failed to save bot message to history: {str(e)}")
            db.rollback()
        
        logger.info(f"Chat request processed: user={current_user.id}, mode={result.get('mode')}, module={result.get('module')}")
        return response_data

    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing chat request"
        )



@router.post("/report", response_model=ReportResponse)
@limiter.limit("10/minute")
def generate_report(
    request: Request,
    report_req: ReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate tax reports"""

    try:
        result = report_agent.generate_report(
            report_req.report_type,
            {
                "tax_result": report_req.tax_data or {},
                "risk_result": report_req.risk_data or {},
                "strategy_result": report_req.strategy_data or {},
                "filing_data": {}
            }
        )

        logger.info(f"Report generated: user={current_user.id}, type={report_req.report_type}")
        return {
            "report_content": result,
            "report_type": report_req.report_type,
            "format": "text"
        }

    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating report"
        )


@router.post("/history/compare", response_model=HistoryResponse)
@limiter.limit("10/minute")
def compare_history(
    request: Request,
    history_req: HistoryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compare current year vs previous year"""

    try:
        result = history_agent.compare_with_previous_year(
            history_req.current_filing,
            history_req.previous_filing
        )
        logger.info(f"History comparison: user={current_user.id}")
        return result

    except Exception as e:
        logger.error(f"Error in history comparison: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error comparing history"
        )


@router.post("/scenario/model", response_model=ScenarioResponse)
@limiter.limit("10/minute")
def model_scenario(
    request: Request,
    scenario_req: ScenarioRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """What-if scenario modeling"""

    try:
        if scenario_req.scenario_type == "investment":
            result = scenario_agent.model_investment_scenario(
                scenario_req.base_income,
                {s.get("name", ""): s.get("amount", 0) for s in scenario_req.scenarios},
                {})
        elif scenario_req.scenario_type == "regime":
            result = scenario_agent.model_regime_comparison(
                scenario_req.base_income,
                {})
        else:
            result = {"scenarios": scenario_req.scenarios, "recommendations": []}

        logger.info(f"Scenario modeled: user={current_user.id}, type={scenario_req.scenario_type}")
        return result

    except Exception as e:
        logger.error(f"Error in scenario modeling: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error modeling scenario"
        )
