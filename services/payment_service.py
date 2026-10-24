from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple, Dict, Any, List
from models import db, Payment, EMISchedule, Loan
from services.emi_calculator import round_curr

VALID_PAYMENT_METHODS = ["Bank Transfer", "UPI", "Cash", "Other"]


def validate_payment_input(
    emi_id_str: str,
    amount_str: str,
    payment_date_str: str,
    payment_method: str,
    reference_number: Optional[str] = None
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """Validate payment form fields."""
    parsed: Dict[str, Any] = {}

    try:
        emi_id = int(str(emi_id_str).strip())
        parsed["emi_id"] = emi_id
    except (ValueError, TypeError):
        return False, "Invalid instalment selected.", parsed

    try:
        amount = Decimal(str(amount_str).strip())
        if amount <= Decimal("0"):
            return False, "Payment amount must be greater than zero.", parsed
        parsed["amount_paid"] = round_curr(amount)
    except (ValueError, InvalidOperation, TypeError):
        return False, "Please enter a valid numeric payment amount.", parsed

    try:
        if isinstance(payment_date_str, date):
            parsed["payment_date"] = payment_date_str
        else:
            parsed["payment_date"] = date.fromisoformat(str(payment_date_str).strip())
    except (ValueError, TypeError):
        return False, "Please enter a valid payment date (YYYY-MM-DD).", parsed

    clean_method = (payment_method or "").strip()
    if clean_method not in VALID_PAYMENT_METHODS:
        return False, f"Invalid payment method. Allowed methods: {', '.join(VALID_PAYMENT_METHODS)}.", parsed
    parsed["payment_method"] = clean_method

    clean_ref = (reference_number or "").strip()
    parsed["reference_number"] = clean_ref if clean_ref else None

    return True, None, parsed


def record_payment(
    user_id: int,
    emi_id: int,
    amount_paid: Decimal,
    payment_date_val: date,
    payment_method: str,
    reference_number: Optional[str] = None
) -> Tuple[Optional[Payment], Optional[str]]:
    """
    Records a payment against an instalment inside an atomic transaction.
    Verifies ownership, validates amount against remaining balance,
    updates instalment status, and closes the loan if all instalments are satisfied.
    """
    # Verify installment ownership
    installment = EMISchedule.query.join(Loan).filter(
        EMISchedule.emi_id == emi_id,
        Loan.user_id == user_id
    ).first()

    if not installment:
        return None, "Instalment not found or access denied."

    # Validate amount
    amt = round_curr(amount_paid)
    if amt <= Decimal("0"):
        return None, "Payment amount must be greater than zero."

    remaining = installment.remaining_amount
    if amt > remaining:
        return None, f"Payment amount (₹{amt}) exceeds the remaining balance of ₹{remaining}."

    # Optional duplicate check by reference number on the same day if reference provided
    if reference_number and reference_number.strip():
        existing_ref = Payment.query.join(EMISchedule).join(Loan).filter(
            Loan.user_id == user_id,
            Payment.reference_number == reference_number.strip(),
            Payment.payment_date == payment_date_val
        ).first()
        if existing_ref:
            return None, f"A payment with reference number '{reference_number.strip()}' on this date has already been recorded."

    try:
        # Create payment record
        payment = Payment(
            emi_id=installment.emi_id,
            amount_paid=amt,
            payment_date=payment_date_val,
            payment_method=payment_method,
            reference_number=reference_number.strip() if reference_number else None
        )
        db.session.add(payment)
        db.session.flush()

        # Update installment status
        # Note: after adding this payment, new remaining balance will be:
        new_remaining = remaining - amt
        if new_remaining <= Decimal("0.00"):
            installment.status = "Paid"
        else:
            installment.status = "Partially Paid"

        # Check if the whole loan is now fully paid
        loan = installment.loan
        all_paid = True
        for sch in loan.schedule:
            # sch.remaining_amount will reflect the newly flushed payment
            if sch.remaining_amount > Decimal("0.00"):
                all_paid = False
                break

        if all_paid:
            loan.status = "Closed"
        else:
            loan.status = "Active"

        db.session.commit()
        return payment, None
    except Exception as e:
        db.session.rollback()
        return None, f"Failed to record payment: {str(e)}"


def get_payment_history(
    user_id: int,
    loan_id: Optional[int] = None,
    start_date_val: Optional[date] = None,
    end_date_val: Optional[date] = None,
    search_query: Optional[str] = None
) -> Tuple[List[Payment], Decimal]:
    """
    Retrieve payment history belonging strictly to user_id,
    with filtering by loan, date range, and search text.
    Returns (payments_list, total_filtered_amount).
    """
    query = Payment.query.join(EMISchedule).join(Loan).filter(Loan.user_id == user_id)

    if loan_id:
        query = query.filter(Loan.loan_id == loan_id)

    if start_date_val:
        query = query.filter(Payment.payment_date >= start_date_val)

    if end_date_val:
        query = query.filter(Payment.payment_date <= end_date_val)

    if search_query and search_query.strip():
        term = f"%{search_query.strip()}%"
        query = query.filter(
            db.or_(
                Loan.loan_name.ilike(term),
                Payment.reference_number.ilike(term),
                Payment.payment_method.ilike(term)
            )
        )

    payments = query.order_by(Payment.payment_date.desc(), Payment.created_at.desc()).all()
    total_amount = sum((Decimal(str(p.amount_paid)) for p in payments), Decimal("0.00"))

    return payments, round_curr(total_amount)
