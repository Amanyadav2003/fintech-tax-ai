from app.models import ChatHistory
from app.routes import tax_routes
from app.services.gemini_service import GeminiServiceError


def test_gemini_response_is_returned_and_saved(authenticated_client, db_session, monkeypatch):
    question = "My annual salary is 8 lakh. How should I calculate my income tax?"
    generated = (
        "Assuming FY 2025-26, I would compare taxable income under both regimes "
        "after the standard deduction and ask for your other income and deductions."
    )
    captured = {}

    monkeypatch.setenv("GEMINI_ENABLED", "true")
    monkeypatch.setenv("AI_PROVIDER", "gemini")

    def generate_response(message, recent_history=None, analysis_context=None):
        captured["message"] = message
        return generated

    monkeypatch.setattr(tax_routes.gemini_service, "generate_response", generate_response)

    user_id = authenticated_client.get("/api/auth/me").json()["id"]
    response = authenticated_client.post(
        "/api/tax/chat",
        json={"message": question, "context": {"session_id": "gemini-session"}},
    )

    assert response.status_code == 200
    assert captured["message"] == question
    assert response.json()["response"] == generated
    assert response.json()["provider"] == "gemini"
    assert response.json()["session_id"] == "gemini-session"

    saved = db_session.query(ChatHistory).filter(
        ChatHistory.user_id == user_id,
        ChatHistory.session_id == "gemini-session",
        ChatHistory.message_type == "bot",
    ).one()
    assert saved.message_content == generated


def test_gemini_failure_returns_marked_fallback_without_feature_menu(
    authenticated_client,
    monkeypatch,
):
    monkeypatch.setenv("GEMINI_ENABLED", "true")
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setattr(
        tax_routes.gemini_service,
        "generate_response",
        lambda *args, **kwargs: (_ for _ in ()).throw(GeminiServiceError("timeout")),
    )

    response = authenticated_client.post(
        "/api/tax/chat",
        json={
            "message": "What tax deductions can a salaried employee claim in India?",
            "context": {"session_id": "fallback-session"},
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["provider"] == "local_fallback"
    assert body["response_type"] == "temporary_error"
    assert "temporarily unable" in body["response"]
    assert "Comprehensive Income Tax Guidance" not in body["response"]
    assert "Deduction Planning" not in body["response"]