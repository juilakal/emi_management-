import pytest
from models import User
from services.auth_service import register_user, authenticate_user

def test_user_registration(app):
    """Test standard user registration succeeds and hashes password."""
    with app.app_context():
        user, err = register_user(
            full_name="Aarav Kumar",
            email="aarav@example.com",
            password="StrongPassword123",
            confirm_password="StrongPassword123"
        )
        assert err is None
        assert user is not None
        assert user.user_id is not None
        assert user.email == "aarav@example.com"
        assert user.password_hash != "StrongPassword123"
        assert user.check_password("StrongPassword123") is True
        assert user.check_password("WrongPassword") is False


def test_duplicate_email_rejection(app, registered_user):
    """Test registering with an existing email is rejected."""
    with app.app_context():
        user, err = register_user(
            full_name="Another Person",
            email="rajesh@example.com",  # Already registered
            password="Password789",
            confirm_password="Password789"
        )
        assert user is None
        assert "already exists" in err.lower()


def test_password_mismatch_rejection(app):
    """Test mismatched passwords return a validation error."""
    with app.app_context():
        user, err = register_user(
            full_name="Test User",
            email="testuser@example.com",
            password="Password123",
            confirm_password="PasswordMismatch"
        )
        assert user is None
        assert "passwords do not match" in err.lower()


def test_successful_login(app, registered_user):
    """Test authenticating with valid credentials returns user."""
    with app.app_context():
        user, err = authenticate_user("rajesh@example.com", "SecurePass123!")
        assert err is None
        assert user is not None
        assert user.user_id == registered_user.user_id


def test_invalid_login(app, registered_user):
    """Test authenticating with incorrect password or wrong email fails."""
    with app.app_context():
        # Wrong password
        user, err = authenticate_user("rajesh@example.com", "IncorrectPassword")
        assert user is None
        assert "invalid email or password" in err.lower()

        # Non-existent user
        user, err = authenticate_user("unknown@example.com", "SomePassword")
        assert user is None
        assert "invalid email or password" in err.lower()


def test_protected_routes_redirect_unauthenticated(client):
    """Test accessing protected pages without authentication redirects to login."""
    protected_urls = [
        "/dashboard",
        "/loans",
        "/loans/add",
        "/schedule",
        "/payments/history",
        "/reports",
        "/account",
    ]
    for url in protected_urls:
        response = client.get(url, follow_redirects=False)
        assert response.status_code in (302, 401)
        assert "/login" in response.headers["Location"]


def test_client_registration_creates_account_and_logs_in(client, app):
    """Registering via the form should create the user and open the dashboard."""
    get_resp = client.get("/register")
    assert get_resp.status_code == 200

    with client.session_transaction() as sess:
        csrf = sess.get("_csrf_token")

    response = client.post("/register", data={
        "csrf_token": csrf,
        "full_name": "New User",
        "email": "newuser@example.com",
        "password": "secret123",
        "confirm_password": "secret123",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Financial Overview" in response.data
    with app.app_context():
        assert User.query.filter_by(email="newuser@example.com").first() is not None


def test_client_login_and_logout_flow(client, registered_user):
    """Test logging in via HTTP sets session, and logging out clears it."""
    # Post login
    login_resp = client.post("/login", data={
        "email": "rajesh@example.com",
        "password": "SecurePass123!"
    }, follow_redirects=True)
    assert login_resp.status_code == 200
    assert b"Financial Overview" in login_resp.data

    # Now accessing /dashboard succeeds
    dash_resp = client.get("/dashboard")
    assert dash_resp.status_code == 200

    # Logout
    logout_resp = client.post("/logout", follow_redirects=True)
    assert logout_resp.status_code == 200
    assert b"logged out" in logout_resp.data.lower()

    # Accessing /dashboard now redirects
    dash_resp_after = client.get("/dashboard", follow_redirects=False)
    assert dash_resp_after.status_code == 302
