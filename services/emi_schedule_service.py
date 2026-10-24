from decimal import Decimal
from typing import List, Optional, Tuple
from models import db, EMISchedule, Loan


def get_schedule_for_loan(loan_id: int, user_id: int) -> Optional[List[EMISchedule]]:
    """Retrieve all EMI instalments for a loan, verifying user ownership."""
    loan = Loan.query.filter_by(loan_id=loan_id, user_id=user_id).first()
    if not loan:
        return None
    return loan.schedule


def get_installment_by_id(emi_id: int, user_id: int) -> Optional[EMISchedule]:
    """
    Retrieve a specific EMI instalment by emi_id,
    verifying ownership through the relationship chain: emi -> loan -> user.
    """
    return EMISchedule.query.join(Loan).filter(
        EMISchedule.emi_id == emi_id,
        Loan.user_id == user_id
    ).first()


def get_upcoming_installments(user_id: int, limit: int = 5) -> List[EMISchedule]:
    """
    Retrieve next upcoming pending or partially paid instalments for a user,
    ordered chronologically by due date.
    """
    all_installments = EMISchedule.query.join(Loan).filter(
        Loan.user_id == user_id,
        Loan.status == "Active"
    ).order_by(EMISchedule.due_date.asc()).all()

    # Filter to only those with remaining balance
    upcoming = [item for item in all_installments if item.remaining_amount > 0]
    return upcoming[:limit]


def get_all_installments_for_user(
    user_id: int,
    loan_id: Optional[int] = None,
    status_filter: Optional[str] = None
) -> List[EMISchedule]:
    """
    Retrieve all instalments for a user with optional loan filter and status filter.
    Returns the manually maintained EMI status.
    """
    query = EMISchedule.query.join(Loan).filter(Loan.user_id == user_id)

    if loan_id:
        query = query.filter(EMISchedule.loan_id == loan_id)

    installments = query.order_by(Loan.loan_name.asc(), EMISchedule.installment_number.asc()).all()

    if status_filter and status_filter.strip():
        req_status = status_filter.strip().lower()
        installments = [item for item in installments if item.computed_status.lower() == req_status]

    return installments


def update_installment_status(
    user_id: int,
    emi_id: int,
    new_status: str,
    amount_paid: Optional[Decimal] = None
) -> Tuple[bool, Optional[str]]:
    """
    Directly updates the status and repayment balance of an EMI instalment.
    Supports setting status to 'Paid', 'Pending', or 'Partially Paid'.
    """
    installment = get_installment_by_id(emi_id, user_id)
    if not installment:
        return False, "Instalment not found or access denied."

    clean_status = (new_status or "Pending").strip()
    if clean_status not in ["Paid", "Pending", "Partially Paid"]:
        return False, f"Invalid status: {clean_status}"

    try:
        if clean_status == "Paid":
            installment.status = "Paid"
        elif clean_status == "Pending":
            installment.status = "Pending"

        elif clean_status == "Partially Paid":
            installment.status = "Partially Paid"

        # Check if entire loan is now fully satisfied
        loan = installment.loan
        db.session.flush()
        all_settled = all(item.remaining_amount <= 0 or item.status == "Paid" for item in loan.schedule)
        loan.status = "Closed" if all_settled else "Active"

        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        return False, f"Error updating instalment: {str(e)}"
