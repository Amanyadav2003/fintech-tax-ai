from app.models import Document, TaxFiling, User
from app.routes.tax_routes import _build_compliance_dashboard


def test_compliance_checklist_uses_document_types(db_session):
    user = User(id=1, email="compliance@example.com", pan="ABCDE1234F")
    filing = TaxFiling(user_id=1, status="analyzed", filing_year=2025, total_income=1000000, total_deductions=150000, tds_paid=100000, investments_80c=150000, health_insurance_80d=25000, home_loan_interest_80emi=200000)
    db_session.add_all([user, filing])
    db_session.commit()

    dashboard = _build_compliance_dashboard(user, filing, db_session)
    checklist = {item["id"]: item["completed"] for item in dashboard["checklist"]}
    assert checklist["form16"] is False
    assert checklist["proofs_80c"] is False
    assert checklist["proofs_80d"] is False
    assert checklist["home_loan"] is False
    assert checklist["forms"] is False

    db_session.add(Document(user_id=1, document_type="80c", file_path="/tmp/80c.pdf", original_filename="80c.pdf", extracted_data={}))
    db_session.commit()
    dashboard = _build_compliance_dashboard(user, filing, db_session)
    checklist = {item["id"]: item["completed"] for item in dashboard["checklist"]}
    assert checklist["proofs_80c"] is True
    assert checklist["proofs_80d"] is False