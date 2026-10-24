from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from routes.auth_middleware import login_required, get_current_user
from services.payment_service import (
    validate_payment_input,
    record_payment,
    get_payment_history,
    VALID_PAYMENT_METHODS
)
from services.emi_schedule_service import get_installment_by_id
from services.loan_service import get_user_loans

payment_bp = Blueprint("payments", __name__, url_prefix="/payments")


@payment_bp.route("/record/<int:emi_id>", methods=["GET", "POST"])
@login_required
def record_installment_payment(emi_id: int):
    """Record a full or partial payment against a specific instalment."""
    user = get_current_user()
    installment = get_installment_by_id(emi_id, user.user_id)

    if not installment:
        flash("Instalment not found or you do not have permission to access it.", "danger")
        return redirect(url_for("loans.list_loans"))

    # If instalment is already fully settled
    if installment.remaining_amount <= 0:
        flash(f"Instalment #{installment.installment_number} has already been fully paid.", "info")
        return redirect(url_for("loans.view_loan", loan_id=installment.loan_id))

    if request.method == "POST":
        amount_str = request.form.get("amount_paid", "")
        payment_date_str = request.form.get("payment_date", "")
        payment_method = request.form.get("payment_method", "")
        reference_number = request.form.get("reference_number", "")

        is_valid, error, parsed = validate_payment_input(
            emi_id_str=str(emi_id),
            amount_str=amount_str,
            payment_date_str=payment_date_str,
            payment_method=payment_method,
            reference_number=reference_number
        )

        if not is_valid:
            flash(error, "danger")
            return render_template(
                "payment_form.html",
                installment=installment,
                methods=VALID_PAYMENT_METHODS,
                today=date.today().isoformat(),
                form_data=request.form
            )

        payment, err = record_payment(
            user_id=user.user_id,
            emi_id=installment.emi_id,
            amount_paid=parsed["amount_paid"],
            payment_date_val=parsed["payment_date"],
            payment_method=parsed["payment_method"],
            reference_number=parsed["reference_number"]
        )

        if err:
            flash(err, "danger")
            return render_template(
                "payment_form.html",
                installment=installment,
                methods=VALID_PAYMENT_METHODS,
                today=date.today().isoformat(),
                form_data=request.form
            )

        flash(
            f"Payment of ₹{payment.amount_paid:.2f} successfully recorded for instalment #{installment.installment_number}!",
            "success"
        )
        return redirect(url_for("loans.view_loan", loan_id=installment.loan_id))

    # Pre-fill form with remaining amount and current date
    initial_data = {
        "amount_paid": str(installment.remaining_amount),
        "payment_date": date.today().isoformat(),
        "payment_method": "Bank Transfer",
        "reference_number": ""
    }

    return render_template(
        "payment_form.html",
        installment=installment,
        methods=VALID_PAYMENT_METHODS,
        today=date.today().isoformat(),
        form_data=initial_data
    )


@payment_bp.route("/history", methods=["GET"])
@login_required
def history():
    """Display payment history with filtering and search."""
    user = get_current_user()
    loan_id = request.args.get("loan_id", type=int)
    start_date_str = request.args.get("start_date", "").strip()
    end_date_str = request.args.get("end_date", "").strip()
    search_query = request.args.get("search", "").strip()

    start_date_val = None
    end_date_val = None

    if start_date_str:
        try:
            start_date_val = date.fromisoformat(start_date_str)
        except ValueError:
            pass

    if end_date_str:
        try:
            end_date_val = date.fromisoformat(end_date_str)
        except ValueError:
            pass

    payments, total_amount = get_payment_history(
        user_id=user.user_id,
        loan_id=loan_id,
        start_date_val=start_date_val,
        end_date_val=end_date_val,
        search_query=search_query
    )

    loans = get_user_loans(user.user_id)

    return render_template(
        "payment_history.html",
        payments=payments,
        total_amount=total_amount,
        loans=loans,
        selected_loan_id=loan_id,
        start_date=start_date_str,
        end_date=end_date_str,
        search_query=search_query
    )
