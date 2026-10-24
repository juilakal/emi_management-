from flask import Blueprint, render_template, redirect, url_for
from routes.auth_middleware import login_required, get_current_user
from services.report_service import get_dashboard_summary

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    """Landing homepage for the EMI Management System."""
    user = get_current_user()
    if user:
        return redirect(url_for("dashboard.dashboard"))
    return render_template("index.html")


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    """Real-time financial dashboard displaying user-specific metrics and charts."""
    user = get_current_user()
    summary = get_dashboard_summary(user.user_id)
    return render_template("dashboard.html", summary=summary, user=user)


@dashboard_bp.route("/account")
@login_required
def account():
    """User account details page."""
    user = get_current_user()
    summary = get_dashboard_summary(user.user_id)
    return render_template("account.html", user=user, summary=summary)
