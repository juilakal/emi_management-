from datetime import date
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, jsonify, flash
from routes.auth_middleware import login_required, get_current_user
from services.emi_calculator import get_loan_calculation_summary
from services.loan_service import get_user_loans
from services.emi_schedule_service import get_all_installments_for_user

emi_bp = Blueprint("emi", __name__)


@emi_bp.route("/calculator", methods=["GET", "POST"])
def calculator():
    """Interactive EMI calculator page supporting both standard POST and interactive preview."""
    result = None
    errors = []

    # Default initial values
    principal_val = "500000"
    rate_val = "8.5"
    tenure_val = "24"
    tenure_unit = "months"

    if request.method == "POST":
        principal_val = request.form.get("principal", "").strip()
        rate_val = request.form.get("rate", "").strip()
        tenure_val = request.form.get("tenure", "").strip()
        tenure_unit = request.form.get("tenure_unit", "months").strip()

        try:
            P = Decimal(principal_val)
            if P <= Decimal("0"):
                errors.append("Principal amount must be greater than zero.")
        except (ValueError, InvalidOperation):
            errors.append("Principal amount must be a valid positive number.")
            P = None

        try:
            R = Decimal(rate_val)
            if R < Decimal("0"):
                errors.append("Annual interest rate cannot be negative.")
            elif R > Decimal("100"):
                errors.append("Annual interest rate must be 100% or less.")
        except (ValueError, InvalidOperation):
            errors.append("Interest rate must be a valid number.")
            R = None

        try:
            T = int(tenure_val)
            if T <= 0:
                errors.append("Tenure must be at least 1.")
            elif tenure_unit == "years":
                T = T * 12
            if T > 360:
                errors.append("Tenure cannot exceed 360 months (30 years).")
        except (ValueError, TypeError):
            errors.append("Tenure must be a valid whole number.")
            T = None

        if not errors and P is not None and R is not None and T is not None:
            try:
                result = get_loan_calculation_summary(
                    principal=P,
                    annual_rate=R,
                    tenure_months=T,
                    start_date=date.today()
                )
            except Exception as e:
                errors.append(f"Calculation error: {str(e)}")

        for err in errors:
            flash(err, "danger")

    return render_template(
        "emi_calculator.html",
        result=result,
        principal=principal_val,
        rate=rate_val,
        tenure=tenure_val,
        tenure_unit=tenure_unit
    )


@emi_bp.route("/calculator/api", methods=["POST"])
def calculator_api():
    """AJAX endpoint for real-time recalculations from JavaScript."""
    data = request.get_json(silent=True) or request.form

    try:
        principal = Decimal(str(data.get("principal", "0")).strip())
        rate = Decimal(str(data.get("rate", "0")).strip())
        tenure = int(str(data.get("tenure", "0")).strip())
        tenure_unit = str(data.get("tenure_unit", "months")).strip()

        if tenure_unit == "years":
            tenure = tenure * 12

        if principal <= Decimal("0") or rate < Decimal("0") or tenure <= 0 or tenure > 360:
            return jsonify({"error": "Invalid inputs. Ensure positive principal, non-negative rate, and valid tenure (1-360 months)."}), 400

        summary = get_loan_calculation_summary(principal, rate, tenure, date.today())
        
        # Format for JSON response
        response_payload = {
            "principal": str(summary["principal"]),
            "rate": str(summary["annual_interest_rate"]),
            "tenure_months": summary["tenure_months"],
            "monthly_emi": str(summary["monthly_emi"]),
            "total_interest": str(summary["total_interest"]),
            "total_payable": str(summary["total_payable"]),
            "schedule": [
                {
                    "installment_number": item["installment_number"],
                    "due_date": item["due_date"].isoformat(),
                    "principal_component": str(item["principal_component"]),
                    "interest_component": str(item["interest_component"]),
                    "emi_amount": str(item["emi_amount"]),
                    "remaining_balance": str(item["remaining_balance"]),
                }
                for item in summary["schedule"]
            ]
        }
        return jsonify(response_payload)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@emi_bp.route("/schedule")
@login_required
def schedule():
    """Display EMI schedule across all user loans or filtered by loan and status."""
    user = get_current_user()
    loan_id = request.args.get("loan_id", type=int)
    status_filter = request.args.get("status", "")

    loans = get_user_loans(user.user_id)
    installments = get_all_installments_for_user(
        user_id=user.user_id,
        loan_id=loan_id,
        status_filter=status_filter
    )

    return render_template(
        "emi_schedule.html",
        loans=loans,
        installments=installments,
        selected_loan_id=loan_id,
        selected_status=status_filter
    )
