from flask import Blueprint, render_template, Response
from routes.auth_middleware import login_required, get_current_user
from services.report_service import get_reports_data, generate_payments_csv

report_bp = Blueprint("reports", __name__, url_prefix="/reports")


@report_bp.route("", methods=["GET"])
@login_required
def reports():
    """Display comprehensive financial reports, loan summaries, and charts."""
    user = get_current_user()
    data = get_reports_data(user.user_id)
    return render_template("reports.html", data=data)


@report_bp.route("/export-csv", methods=["GET"])
@login_required
def export_csv():
    """
    Download a CSV file containing the authenticated user's payment history.
    Strictly restricted to the current user's records.
    """
    user = get_current_user()
    csv_content = generate_payments_csv(user.user_id)

    response = Response(
        csv_content,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=payment_history_user_{user.user_id}.csv",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )
    return response
