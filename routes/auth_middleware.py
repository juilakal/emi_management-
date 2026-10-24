import secrets
from functools import wraps
from flask import session, request, redirect, url_for, flash, abort, g
from models import db, User


def get_current_user():
    """Returns the authenticated User object from session user_id, or None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    if not hasattr(g, "current_user"):
        try:
            g.current_user = db.session.get(User, user_id)
        except Exception:
            g.current_user = None
    return g.current_user


def login_required(view_func):
    """Decorator requiring an authenticated session to access the route."""
    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        if "user_id" not in session or not get_current_user():
            session.clear()
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view_func(*args, **kwargs)
    return decorated_view


def generate_csrf_token() -> str:
    """Generates or retrieves the session's CSRF protection token."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(24)
    return session["_csrf_token"]


def _tokens_match(expected: str, token: str) -> bool:
    """Constant-time compare that never raises on length mismatch."""
    if not expected or not token or len(expected) != len(token):
        return False
    return secrets.compare_digest(expected, token)


def validate_csrf():
    """Validates CSRF token for state-changing HTTP methods."""
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        token = request.headers.get("X-CSRFToken") or request.form.get("csrf_token")
        expected = session.get("_csrf_token")
        if not _tokens_match(expected, token):
            flash("Your session expired. Please try again.", "warning")
            if request.endpoint == "auth.register":
                return redirect(url_for("auth.register"))
            if request.endpoint == "auth.login":
                return redirect(url_for("auth.login"))
            if request.referrer:
                return redirect(request.referrer)
            abort(400, description="Your session expired. Please try again.")
