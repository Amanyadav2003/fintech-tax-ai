from app.models import ChatHistory
from app.routes import tax_routes
from app.services.gemini_service import GeminiService, GeminiServiceError


def test_gemini_response_is_returned_and_saved(authenticated_client, db_session, monkeypatch):
    question = (
        "My annual salary is ₹8 lakh. Please calculate my estimated income tax under both the "
        "Old Regime and New Regime. Clearly mention assumptions, standard deduction, taxable "
        "income, rebate and cess. Use the applicable FY/AY and mention if the calculation may "
        "change based on the assessment year."
    )
    generated = (
        "Assumptions: FY 2025-26, gross salary ₹8,00,000, no other income. "
        "Gross salary, standard deduction, taxable income, Old Regime, New Regime, "
        "rebate and 4% cess are shown; actual tax depends on your details."
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
    assert "Assumptions" in response.json()["response"]
    assert "Gross salary" in response.json()["response"]
    assert "standard deduction" in response.json()["response"]
    assert "taxable income" in response.json()["response"]
    assert "Old Regime" in response.json()["response"]
    assert "New Regime" in response.json()["response"]
    assert "rebate" in response.json()["response"]
    assert "cess" in response.json()["response"]

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
    assert "Section 80C" in body["response"]
    assert "Section 80D" in body["response"]
    assert "Comprehensive Income Tax Guidance" not in body["response"]
    assert "Deduction Planning" not in body["response"]


def test_max_tokens_uses_complete_local_salary_fallback(authenticated_client, monkeypatch):
    monkeypatch.setenv("GEMINI_ENABLED", "true")
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setattr(
        tax_routes.gemini_service,
        "generate_response",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            GeminiServiceError("max_output_tokens", detail="finish_reason=MAX_TOKENS", usable_text=True)
        ),
    )

    response = authenticated_client.post(
        "/api/tax/chat",
        json={
            "message": "My annual salary is ₹8 lakh. Please calculate my estimated income tax under both the Old Regime and New Regime. Clearly mention assumptions, standard deduction, taxable income, rebate and cess.",
            "context": {"session_id": "max-token-session"},
        },
    )

    body = response.json()
    fallback_text = body["response"].lower()
    assert response.status_code == 200
    assert body["provider"] == "local_fallback"
    assert "assumptions" in fallback_text
    assert "gross salary" in fallback_text
    assert "standard deduction" in fallback_text
    assert "taxable income" in fallback_text
    assert "old regime" in fallback_text
    assert "new regime" in fallback_text
    assert "87a" in fallback_text
    assert "cess" in fallback_text


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


def test_gemini_environment_defaults_are_bounded(monkeypatch):
    monkeypatch.delenv("GEMINI_TIMEOUT_MS", raising=False)
    monkeypatch.delenv("GEMINI_MAX_OUTPUT_TOKENS", raising=False)

    diagnostics = GeminiService().diagnostics()

    assert diagnostics["timeout_ms"] == 30000
    assert diagnostics["max_output_tokens"] == 2048


def test_gemini_invalid_environment_values_use_defaults(monkeypatch):
    monkeypatch.setenv("GEMINI_TIMEOUT_MS", "not-a-number")
    monkeypatch.setenv("GEMINI_MAX_OUTPUT_TOKENS", "-1")

    diagnostics = GeminiService().diagnostics()

    assert diagnostics["timeout_ms"] == 30000
    assert diagnostics["max_output_tokens"] == 512


def test_gemini_thinking_config_is_disabled(monkeypatch):
    captured = {}

    class Models:
        def generate_content(self, **kwargs):
            captured["config"] = kwargs["config"]
            return type("Response", (), {"text": "complete answer"})()

    class Client:
        models = Models()

    service = GeminiService()
    service._get_client = lambda: Client()
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    assert service.generate_response("What is TDS?") == "complete answer"
    assert captured["config"].thinking_config.thinking_budget == 0
    assert captured["config"].thinking_config.include_thoughts is False


def test_gemini_max_tokens_response_with_text_is_classified_as_partial(monkeypatch):
    class Candidate:
        finish_reason = "FinishReason.MAX_TOKENS"

    class Models:
        def generate_content(self, **kwargs):
            return type("Response", (), {"text": "partial answer", "candidates": [Candidate()]})()

    class Client:
        models = Models()

    service = GeminiService()
    service._get_client = lambda: Client()
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    try:
        service.generate_response("Calculate tax for salary of 8 lakh")
    except GeminiServiceError as error:
        assert error.reason == "max_output_tokens"
        assert error.usable_text is True
    else:
        raise AssertionError("expected partial completion classification")


def test_gemini_stop_response_is_returned(monkeypatch):
    class Models:
        def generate_content(self, **kwargs):
            return type("Response", (), {"text": "complete answer", "candidates": [type("Candidate", (), {"finish_reason": "STOP"})()]})()

    class Client:
        models = Models()

    service = GeminiService()
    service._get_client = lambda: Client()
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    assert service.generate_response("What is TDS?") == "complete answer"


def test_gemini_candidate_parts_are_used_when_response_text_is_empty(monkeypatch):
    class Part:
        text = "candidate answer"

    class Content:
        parts = [Part()]

    class Candidate:
        content = Content()
        finish_reason = "STOP"

    class Models:
        def generate_content(self, **kwargs):
            return type("Response", (), {"text": "", "candidates": [Candidate()]})()

    class Client:
        models = Models()

    service = GeminiService()
    service._get_client = lambda: Client()
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    assert service.generate_response("What is TDS?") == "candidate answer"


def test_gemini_max_tokens_without_text_uses_fallback(monkeypatch):
    class Models:
        def generate_content(self, **kwargs):
            return type("Response", (), {"text": "", "candidates": [type("Candidate", (), {"finish_reason": "MAX_TOKENS"})()]})()

    class Client:
        models = Models()

    service = GeminiService()
    service._get_client = lambda: Client()
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    try:
        service.generate_response("What is TDS?")
    except GeminiServiceError as error:
        assert error.reason == "empty_response"
    else:
        raise AssertionError("expected empty response error")


def test_gemini_blocked_response_uses_fallback(monkeypatch):
    class Models:
        def generate_content(self, **kwargs):
            return type("Response", (), {"text": "", "candidates": [type("Candidate", (), {"finish_reason": "SAFETY"})()]})()

    class Client:
        models = Models()

    service = GeminiService()
    service._get_client = lambda: Client()
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    try:
        service.generate_response("What is TDS?")
    except GeminiServiceError as error:
        assert error.reason == "blocked_response"
    else:
        raise AssertionError("expected blocked response error")


def test_gemini_limits_history_and_context(monkeypatch):
    captured = {}

    class Models:
        def generate_content(self, **kwargs):
            captured["prompt"] = kwargs["contents"]
            return type("Response", (), {"text": "bounded answer"})()

    class Client:
        models = Models()

    service = GeminiService()
    service._get_client = lambda: Client()
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    history = [
        {"message_type": "user", "message_content": "old " + ("x" * 2000)}
        for _ in range(8)
    ]

    assert service.generate_response("What is TDS?", history, {"analysis": "y" * 5000}) == "bounded answer"
    assert len(captured["prompt"]) <= 6000 + 3000 + 1000 + 500


def test_gemini_oversized_message_is_rejected(monkeypatch):
    service = GeminiService()
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    try:
        service.generate_response("x" * 4001)
    except GeminiServiceError as error:
        assert error.reason == "message_too_long"
    else:
        raise AssertionError("expected oversized message error")