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
        g.current_user = db.session.get(User, user_id)
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


def validate_csrf():
    """Validates CSRF token for state-changing HTTP methods."""
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        # Check header first, then form field
        token = request.headers.get("X-CSRFToken") or request.form.get("csrf_token")
        expected = session.get("_csrf_token")
        if not expected or not token or not secrets.compare_digest(expected, token):
            flash("Invalid or expired session security token. Please try again.", "danger")
            abort(400, description="CSRF token validation failed.")
