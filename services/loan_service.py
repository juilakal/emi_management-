from datetime import date
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple, Dict, Any
from models import db, Loan, EMISchedule
from services.emi_calculator import calculate_emi, generate_amortization_schedule, round_curr


def validate_loan_input(
    loan_name: str,
    lender_name: str,
    principal_str: str,
    interest_rate_str: str,
    tenure_str: str,
    start_date_str: str
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """Validate and parse user-submitted loan form inputs."""
    parsed: Dict[str, Any] = {}

    if not loan_name or not loan_name.strip():
        return False, "Loan name/purpose is required.", parsed
    parsed["loan_name"] = loan_name.strip()

    if not lender_name or not lender_name.strip():
        return False, "Lender name is required.", parsed
    parsed["lender_name"] = lender_name.strip()

    # Principal amount
    try:
        principal = Decimal(str(principal_str).strip())
        if principal <= Decimal("0"):
            return False, "Loan principal amount must be greater than zero.", parsed
        parsed["principal_amount"] = round_curr(principal)
    except (ValueError, InvalidOperation, TypeError):
        return False, "Please enter a valid numeric principal amount.", parsed

    # Annual interest rate
    try:
        interest_rate = Decimal(str(interest_rate_str).strip())
        if interest_rate < Decimal("0"):
            return False, "Annual interest rate cannot be negative.", parsed
        if interest_rate > Decimal("100.0"):
            return False, "Annual interest rate must be 100% or less.", parsed
        parsed["annual_interest_rate"] = round_curr(interest_rate)
    except (ValueError, InvalidOperation, TypeError):
        return False, "Please enter a valid numeric interest rate.", parsed

    # Tenure months
    try:
        tenure = int(str(tenure_str).strip())
        if tenure < 1 or tenure > 360:
            return False, "Loan tenure must be between 1 and 360 months (30 years).", parsed
        parsed["tenure_months"] = tenure
    except (ValueError, TypeError):
        return False, "Please enter an integer number of months for tenure.", parsed

    # Start date
    try:
        if isinstance(start_date_str, date):
            parsed["start_date"] = start_date_str
        else:
            parsed["start_date"] = date.fromisoformat(str(start_date_str).strip())
    except (ValueError, TypeError):
        return False, "Please select a valid start date (YYYY-MM-DD).", parsed

    return True, None, parsed


def create_loan(
    user_id: int,
    loan_name: str,
    lender_name: str,
    principal: Decimal,
    annual_rate: Decimal,
    tenure_months: int,
    start_date_val: date
) -> Tuple[Optional[Loan], Optional[str]]:
    """
    Creates a new loan record, recalculates the EMI server-side,
    and generates the complete monthly repayment schedule inside an atomic transaction.
    """
    try:
        # Server-side authoritative EMI calculation
        emi_val = calculate_emi(principal, annual_rate, tenure_months)

        loan = Loan(
            user_id=user_id,
            loan_name=loan_name,
            lender_name=lender_name,
            principal_amount=round_curr(principal),
            annual_interest_rate=round_curr(annual_rate),
            tenure_months=tenure_months,
            emi_amount=emi_val,
            start_date=start_date_val,
            status="Active"
        )
        db.session.add(loan)
        db.session.flush()  # Assigns loan.loan_id

        # Generate amortization schedule
        schedule_items = generate_amortization_schedule(
            principal=principal,
            annual_rate=annual_rate,
            tenure_months=tenure_months,
            start_date=start_date_val
        )

        for item in schedule_items:
            emi_record = EMISchedule(
                loan_id=loan.loan_id,
                installment_number=item["installment_number"],
                due_date=item["due_date"],
                principal_component=item["principal_component"],
                interest_component=item["interest_component"],
                emi_amount=item["emi_amount"],
                status="Pending"
            )
            db.session.add(emi_record)

        db.session.commit()
        return loan, None
    except Exception as e:
        db.session.rollback()
        return None, f"Failed to create loan and schedule: {str(e)}"


def get_user_loans(user_id: int) -> List[Loan]:
    """Retrieve all loans belonging strictly to the specified user."""
    return Loan.query.filter_by(user_id=user_id).order_by(Loan.created_at.desc()).all()


def get_loan_by_id(loan_id: int, user_id: int) -> Optional[Loan]:
    """
    Retrieve loan by ID, strictly enforcing user ownership.
    Returns None if loan does not exist or belongs to another user.
    """
    return Loan.query.filter_by(loan_id=loan_id, user_id=user_id).first()


def update_loan(
    loan_id: int,
    user_id: int,
    loan_name: str,
    lender_name: str,
    principal: Decimal,
    annual_rate: Decimal,
    tenure_months: int,
    start_date_val: date
) -> Tuple[Optional[Loan], Optional[str]]:
    """
    Updates loan details with a safe edit policy:
    If payments have already been recorded, prevents overwriting schedule to preserve financial integrity.
    If no payments exist, recalculates EMI and regenerates the schedule.
    """
    loan = get_loan_by_id(loan_id, user_id)
    if not loan:
        return None, "Loan not found or access denied."

    # Safe edit policy: check for existing payments
    if loan.has_payments:
        # If user only changed non-financial metadata (loan name, lender name), we can allow it safely
        is_terms_changed = (
            round_curr(loan.principal_amount) != round_curr(principal) or
            round_curr(loan.annual_interest_rate) != round_curr(annual_rate) or
            loan.tenure_months != tenure_months or
            loan.start_date != start_date_val
        )
        if is_terms_changed:
            return None, "Financial terms (principal, rate, tenure, start date) cannot be altered after payments have been recorded. You may only edit the loan title and lender name."

        try:
            loan.loan_name = loan_name
            loan.lender_name = lender_name
            db.session.commit()
            return loan, None
        except Exception as e:
            db.session.rollback()
            return None, f"Failed to update loan details: {str(e)}"

    # If no payments recorded yet, we can fully update and regenerate schedule
    try:
        new_emi = calculate_emi(principal, annual_rate, tenure_months)

        loan.loan_name = loan_name
        loan.lender_name = lender_name
        loan.principal_amount = round_curr(principal)
        loan.annual_interest_rate = round_curr(annual_rate)
        loan.tenure_months = tenure_months
        loan.emi_amount = new_emi
        loan.start_date = start_date_val

        # Clear existing un-paid schedule
        EMISchedule.query.filter_by(loan_id=loan.loan_id).delete()

        # Generate fresh schedule
        schedule_items = generate_amortization_schedule(
            principal=principal,
            annual_rate=annual_rate,
            tenure_months=tenure_months,
            start_date=start_date_val
        )

        for item in schedule_items:
            emi_record = EMISchedule(
                loan_id=loan.loan_id,
                installment_number=item["installment_number"],
                due_date=item["due_date"],
                principal_component=item["principal_component"],
                interest_component=item["interest_component"],
                emi_amount=item["emi_amount"],
                status="Pending"
            )
            db.session.add(emi_record)

        db.session.commit()
        return loan, None
    except Exception as e:
        db.session.rollback()
        return None, f"Failed to update loan: {str(e)}"


def delete_loan(loan_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
    """
    Deletes a loan and cascades to its schedules and payments.
    Strictly verifies ownership before deletion.
    """
    loan = get_loan_by_id(loan_id, user_id)
    if not loan:
        return False, "Loan not found or access denied."

    try:
        db.session.delete(loan)
        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to delete loan: {str(e)}"
