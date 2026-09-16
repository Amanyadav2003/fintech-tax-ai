from app.models import ChatHistory
from app.routes import tax_routes
from app.services.gemini_service import GeminiService, GeminiServiceError


def test_gemini_response_is_returned_and_saved(authenticated_client, db_session, monkeypatch):
    question = "My annual salary is 8 lakh. How should I calculate my income tax?"
    generated = (
        "Assuming FY 2025-26, I would compare taxable income under both regimes "
        "after the standard deduction and ask for your other income and deductions."
    )
    captured = {}

    monkeypatch.setenv("GEMINI_ENABLED", "true")
    monkeypatch.setenv("AI_PROVIDER", "gemini")

    def generate_response(message, recent_history=None, analysis_context=None, request_id=None):
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


def test_gemini_diagnostics_do_not_expose_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "secret-value-that-must-not-be-logged")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv("GEMINI_ENABLED", "true")
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    diagnostics = GeminiService().diagnostics()

    assert diagnostics["key_configured"] is True
    assert diagnostics["model"] == "gemini-2.5-flash"
    assert "secret-value" not in str(diagnostics)


def test_gemini_missing_key_is_classified(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    try:
        GeminiService().generate_response("What is TDS?")
    except GeminiServiceError as error:
        assert error.reason == "missing_api_key"
    else:
        raise AssertionError("expected missing API key error")


def test_gemini_provider_error_categories():
    cases = [
        (type("Error", (), {"code": 401})(), "invalid_api_key"),
        (type("Error", (), {"code": 404, "__str__": lambda self: "model not found"})(), "invalid_model"),
        (type("Error", (), {"code": 429})(), "rate_limited"),
        (TimeoutError("request timed out"), "timeout"),
        (RuntimeError("unsupported SDK method"), "sdk_api_compatibility"),
    ]

    for exception, expected in cases:
        assert GeminiService._classify_error(exception) == expected


def test_gemini_empty_response_is_rejected(monkeypatch):
    class EmptyModels:
        def generate_content(self, **kwargs):
            return type("Response", (), {"text": ""})()

    class EmptyClient:
        models = EmptyModels()

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    service = GeminiService()
    service._get_client = lambda: EmptyClient()

    try:
        service.generate_response("What is TDS?")
    except GeminiServiceError as error:
        assert error.reason == "empty_response"
    else:
        raise AssertionError("expected empty response error")


def test_gemini_response_parse_error_is_classified():
    class BrokenResponse:
        @property
        def text(self):
            raise ValueError("response candidates cannot be converted")

    try:
        GeminiService._extract_response_text(BrokenResponse())
    except GeminiServiceError as error:
        assert error.reason == "response_parse_error"
        assert "candidates" in error.detail
    else:
        raise AssertionError("expected response parsing error")


def test_gemini_safe_error_detail_redacts_secrets():
    error = RuntimeError("api-key=secret-value Authorization: Bearer token-value https://example.test/private")
    detail = GeminiService._safe_error_detail(error)

    assert "secret-value" not in detail
    assert "token-value" not in detail
    assert "example.test" not in detail