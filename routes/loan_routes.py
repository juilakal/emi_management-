from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from routes.auth_middleware import login_required, get_current_user
from services.loan_service import (
    validate_loan_input,
    create_loan,
    get_user_loans,
    get_loan_by_id,
    update_loan,
    delete_loan
)

loan_bp = Blueprint("loans", __name__, url_prefix="/loans")


@loan_bp.route("", methods=["GET"])
@login_required
def list_loans():
    """List all loans belonging strictly to the current user."""
    user = get_current_user()
    loans = get_user_loans(user.user_id)
    return render_template("loans.html", loans=loans)


@loan_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_loan():
    """Add a new loan with server-side validation and automatic schedule generation."""
    user = get_current_user()

    if request.method == "POST":
        loan_name = request.form.get("loan_name", "")
        lender_name = request.form.get("lender_name", "")
        principal_str = request.form.get("principal_amount", "")
        rate_str = request.form.get("annual_interest_rate", "")
        tenure_str = request.form.get("tenure_months", "")
        start_date_str = request.form.get("start_date", "")

        is_valid, error, parsed = validate_loan_input(
            loan_name, lender_name, principal_str, rate_str, tenure_str, start_date_str
        )

        if not is_valid:
            flash(error, "danger")
            return render_template(
                "loan_form.html",
                is_edit=False,
                loan_data=request.form,
                today=date.today().isoformat()
            )

        loan, err = create_loan(
            user_id=user.user_id,
            loan_name=parsed["loan_name"],
            lender_name=parsed["lender_name"],
            principal=parsed["principal_amount"],
            annual_rate=parsed["annual_interest_rate"],
            tenure_months=parsed["tenure_months"],
            start_date_val=parsed["start_date"]
        )

        if err:
            flash(err, "danger")
            return render_template(
                "loan_form.html",
                is_edit=False,
                loan_data=request.form,
                today=date.today().isoformat()
            )

        flash(f"Loan '{loan.loan_name}' created successfully with its complete EMI schedule!", "success")
        return redirect(url_for("loans.view_loan", loan_id=loan.loan_id))

    # Pre-fill from query params if navigated from the EMI calculator
    initial_data = {
        "loan_name": request.args.get("name", ""),
        "lender_name": request.args.get("lender", ""),
        "principal_amount": request.args.get("principal", ""),
        "annual_interest_rate": request.args.get("rate", ""),
        "tenure_months": request.args.get("tenure", ""),
        "start_date": request.args.get("start_date", date.today().isoformat()),
    }

    return render_template(
        "loan_form.html",
        is_edit=False,
        loan_data=initial_data,
        today=date.today().isoformat()
    )


@loan_bp.route("/<int:loan_id>", methods=["GET"])
@login_required
def view_loan(loan_id: int):
    """View details and repayment schedule for a single loan."""
    user = get_current_user()
    loan = get_loan_by_id(loan_id, user.user_id)

    if not loan:
        flash("Loan not found or you do not have permission to access it.", "danger")
        return redirect(url_for("loans.list_loans"))

    return render_template("loan_details.html", loan=loan)


@loan_bp.route("/<int:loan_id>/edit", methods=["GET", "POST"])
@login_required
def edit_loan(loan_id: int):
    """Edit loan details with safe edit policy enforcement."""
    user = get_current_user()
    loan = get_loan_by_id(loan_id, user.user_id)

    if not loan:
        flash("Loan not found or you do not have permission to edit it.", "danger")
        return redirect(url_for("loans.list_loans"))

    if request.method == "POST":
        loan_name = request.form.get("loan_name", "")
        lender_name = request.form.get("lender_name", "")
        principal_str = request.form.get("principal_amount", "")
        rate_str = request.form.get("annual_interest_rate", "")
        tenure_str = request.form.get("tenure_months", "")
        start_date_str = request.form.get("start_date", "")

        is_valid, error, parsed = validate_loan_input(
            loan_name, lender_name, principal_str, rate_str, tenure_str, start_date_str
        )

        if not is_valid:
            flash(error, "danger")
            return render_template(
                "loan_form.html",
                is_edit=True,
                loan=loan,
                loan_data=request.form,
                today=date.today().isoformat()
            )

        updated_loan, err = update_loan(
            loan_id=loan.loan_id,
            user_id=user.user_id,
            loan_name=parsed["loan_name"],
            lender_name=parsed["lender_name"],
            principal=parsed["principal_amount"],
            annual_rate=parsed["annual_interest_rate"],
            tenure_months=parsed["tenure_months"],
            start_date_val=parsed["start_date"]
        )

        if err:
            flash(err, "danger")
            return render_template(
                "loan_form.html",
                is_edit=True,
                loan=loan,
                loan_data=request.form,
                today=date.today().isoformat()
            )

        flash("Loan updated successfully!", "success")
        return redirect(url_for("loans.view_loan", loan_id=loan.loan_id))

    loan_data = {
        "loan_name": loan.loan_name,
        "lender_name": loan.lender_name,
        "principal_amount": str(loan.principal_amount),
        "annual_interest_rate": str(loan.annual_interest_rate),
        "tenure_months": str(loan.tenure_months),
        "start_date": loan.start_date.isoformat(),
    }

    return render_template(
        "loan_form.html",
        is_edit=True,
        loan=loan,
        loan_data=loan_data,
        today=date.today().isoformat()
    )


@loan_bp.route("/<int:loan_id>/delete", methods=["POST"])
@login_required
def remove_loan(loan_id: int):
    """Delete a loan with confirmation dialog validation and relationship cascading."""
    user = get_current_user()
    success, err = delete_loan(loan_id, user.user_id)

    if not success:
        flash(err or "Failed to delete loan.", "danger")
    else:
        flash("Loan and all associated schedules and payments were successfully deleted.", "success")

    return redirect(url_for("loans.list_loans"))
