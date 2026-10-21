from uuid import uuid4

import pytest

from app.models import User
from app.routes import auth_routes
from app.utils.security import SecurityManager


def _mock_google_claims(monkeypatch, claims):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-google-client-id")
    monkeypatch.setattr(
        auth_routes.id_token,
        "verify_oauth2_token",
        lambda credential, request, audience: claims,
    )


def _post_google(client, credential="mock-google-id-token"):
    return client.post("/api/auth/google", json={"credential": credential})


@pytest.fixture(autouse=True)
def cleanup_google_auth_test_users(db_session):
    yield
    db_session.query(User).filter(User.email.like("%@google-auth.example")).delete(synchronize_session=False)
    db_session.commit()


def _user(db_session, email, **overrides):
    user = User(
        email=email,
        name="Existing User",
        password_hash=SecurityManager.hash_password("OldPassword123!"),
        phone="9876543210",
        pan=uuid4().hex,
        age=30,
        state="Maharashtra",
        is_active=overrides.pop("is_active", True),
        is_verified=True,
        email_verified=overrides.pop("email_verified", True),
        **overrides,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_google_login_returns_503_when_not_configured(client, monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)

    response = _post_google(client)

    assert response.status_code == 503
    assert response.json() == {"detail": "Google sign-in is not configured"}


def test_google_login_rejects_invalid_token(client, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-google-client-id")

    def reject_token(*args, **kwargs):
        raise ValueError("invalid token")

    monkeypatch.setattr(auth_routes.id_token, "verify_oauth2_token", reject_token)

    response = _post_google(client)

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid Google credential"}


def test_google_login_rejects_unverified_email(client, monkeypatch):
    _mock_google_claims(monkeypatch, {"email": "person@example.com", "email_verified": False})

    response = _post_google(client)

    assert response.status_code == 401


def test_google_login_creates_incomplete_user_and_issues_login_response(client, db_session, monkeypatch):
    _mock_google_claims(
        monkeypatch,
        {"email": "New.Person@Google-Auth.Example", "email_verified": True, "name": "New Person"},
    )

    response = _post_google(client)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "new.person@google-auth.example"
    assert body["user"] == {"id": body["id"], "email": body["email"], "name": "New Person"}
    user = db_session.query(User).filter(User.email == "new.person@google-auth.example").one()
    assert user.email_verified is True
    assert user.phone is None
    assert user.pan is None
    assert user.age is None
    assert user.state == "Maharashtra"
    assert user.employment_type == "Salaried"

    _user(db_session, "shape@google-auth.example")
    login_response = client.post(
        "/api/auth/login",
        json={"username": "shape@google-auth.example", "password": "OldPassword123!"},
    )
    assert set(body) == set(login_response.json())


def test_google_login_uses_email_local_part_when_name_is_missing(client, db_session, monkeypatch):
    _mock_google_claims(
        monkeypatch,
        {"email": "fallback@google-auth.example", "email_verified": True},
    )

    response = _post_google(client)

    assert response.status_code == 200
    assert db_session.query(User).filter(User.email == "fallback@google-auth.example").one().name == "fallback"


def test_google_login_accepts_existing_verified_user(client, db_session, monkeypatch):
    _user(db_session, "verified@google-auth.example")
    _mock_google_claims(
        monkeypatch,
        {"email": "VERIFIED@Google-Auth.Example", "email_verified": True, "name": "Google Name"},
    )

    response = _post_google(client)

    assert response.status_code == 200
    assert response.json()["email"] == "verified@google-auth.example"


def test_google_login_verifies_existing_unverified_user_and_replaces_password(client, db_session, monkeypatch):
    user = _user(db_session, "unverified@google-auth.example", email_verified=False)
    old_password_hash = user.password_hash
    _mock_google_claims(
        monkeypatch,
        {"email": "unverified@google-auth.example", "email_verified": True},
    )

    response = _post_google(client)
    old_password_login = client.post(
        "/api/auth/login",
        json={"username": "unverified@google-auth.example", "password": "OldPassword123!"},
    )

    assert response.status_code == 200
    assert old_password_login.status_code == 401
    db_session.refresh(user)
    assert user.email_verified is True
    assert user.password_hash != old_password_hash


def test_google_login_rejects_disabled_user(client, db_session, monkeypatch):
    _user(db_session, "disabled@google-auth.example", is_active=False)
    _mock_google_claims(
        monkeypatch,
        {"email": "disabled@google-auth.example", "email_verified": True},
    )

    response = _post_google(client)

    assert response.status_code == 403
    assert response.json() == {"detail": "User account is disabled"}
