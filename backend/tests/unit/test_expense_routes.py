from datetime import datetime

from app.models import Expense


def test_expenses_are_filtered_by_requested_month(authenticated_client, db_session):
    current_user_id = authenticated_client.get("/api/auth/me").json()["id"]
    db_session.add_all([
        Expense(user_id=current_user_id, amount=4500, category="Rent", description="August", date=datetime(2026, 8, 25)),
        Expense(user_id=current_user_id, amount=3000, category="Rent", description="July", date=datetime(2026, 7, 25)),
    ])
    db_session.commit()

    august = authenticated_client.get("/api/expenses?month=2026-08")
    july = authenticated_client.get("/api/expenses?month=2026-07")

    assert august.status_code == 200
    assert [expense["description"] for expense in august.json()] == ["August"]
    assert [expense["description"] for expense in july.json()] == ["July"]


def test_invalid_expense_month_is_rejected(authenticated_client):
    response = authenticated_client.get("/api/expenses?month=2026-13")

    assert response.status_code == 422


def test_expense_records_remain_after_month_queries(authenticated_client, db_session):
    current_user_id = authenticated_client.get("/api/auth/me").json()["id"]
    expense = Expense(user_id=current_user_id, amount=4500, category="Rent", description="Keep me", date=datetime(2026, 8, 25))
    db_session.add(expense)
    db_session.commit()
    expense_id = expense.id

    response = authenticated_client.get("/api/expenses?month=2026-08")

    assert response.status_code == 200
    assert db_session.query(Expense).filter(Expense.id == expense_id).count() == 1
