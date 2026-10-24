from datetime import date
from decimal import Decimal
import pytest
from models import Loan, EMISchedule, Payment, db
from services.loan_service import create_loan, update_loan, delete_loan, get_loan_by_id
from services.payment_service import record_payment

def test_loan_creation_and_schedule_generation(app, registered_user):
    """Test creating a loan saves it to the database and generates the schedule."""
    with app.app_context():
        loan, err = create_loan(
            user_id=registered_user.user_id,
            loan_name="Car Loan",
            lender_name="HDFC Bank",
            principal=Decimal("300000.00"),
            annual_rate=Decimal("9.00"),
            tenure_months=12,
            start_date_val=date(2025, 1, 10)
        )

        assert err is None
        assert loan is not None
        assert loan.loan_id is not None
        assert loan.user_id == registered_user.user_id
        assert loan.emi_amount > 0

        # Verify schedule was generated
        schedules = EMISchedule.query.filter_by(loan_id=loan.loan_id).all()
        assert len(schedules) == 12
        assert schedules[0].installment_number == 1
        assert schedules[-1].installment_number == 12


def test_loan_ownership_isolation(app, registered_user, second_user):
    """Test that a user cannot access another user's loan."""
    with app.app_context():
        # User 1 creates a loan
        loan, _ = create_loan(
            user_id=registered_user.user_id,
            loan_name="Private Loan",
            lender_name="SBI",
            principal=Decimal("100000.00"),
            annual_rate=Decimal("10.00"),
            tenure_months=6,
            start_date_val=date(2025, 2, 1)
        )

        # User 2 attempts to query User 1's loan
        retrieved = get_loan_by_id(loan.loan_id, user_id=second_user.user_id)
        assert retrieved is None

        # User 2 attempts to delete User 1's loan
        success, err = delete_loan(loan.loan_id, user_id=second_user.user_id)
        assert success is False
        assert "access denied" in err.lower()


def test_safe_edit_policy_before_payments(app, registered_user):
    """Test modifying a loan before payments regenerates the schedule."""
    with app.app_context():
        loan, _ = create_loan(
            user_id=registered_user.user_id,
            loan_name="Laptop Loan",
            lender_name="Bajaj Finance",
            principal=Decimal("50000.00"),
            annual_rate=Decimal("12.00"),
            tenure_months=6,
            start_date_val=date(2025, 3, 1)
        )

        # Update tenure to 12 months
        updated, err = update_loan(
            loan_id=loan.loan_id,
            user_id=registered_user.user_id,
            loan_name="Laptop Loan Updated",
            lender_name="Bajaj Finance",
            principal=Decimal("50000.00"),
            annual_rate=Decimal("12.00"),
            tenure_months=12,
            start_date_val=date(2025, 3, 1)
        )

        assert err is None
        assert updated.tenure_months == 12
        assert updated.loan_name == "Laptop Loan Updated"
        # Schedule count must now be 12
        assert len(updated.schedule) == 12


def test_safe_edit_policy_after_payments(app, registered_user):
    """Test modifying financial terms after payments begin is strictly blocked."""
    with app.app_context():
        loan, _ = create_loan(
            user_id=registered_user.user_id,
            loan_name="Home Renovation",
            lender_name="Axis Bank",
            principal=Decimal("200000.00"),
            annual_rate=Decimal("8.50"),
            tenure_months=12,
            start_date_val=date(2025, 1, 1)
        )

        # Record a payment on instalment #1
        first_emi = loan.schedule[0]
        pay, p_err = record_payment(
            user_id=registered_user.user_id,
            emi_id=first_emi.emi_id,
            amount_paid=first_emi.emi_amount,
            payment_date_val=date(2025, 2, 1),
            payment_method="UPI"
        )
        assert p_err is None

        # Attempt to change principal or tenure
        updated, err = update_loan(
            loan_id=loan.loan_id,
            user_id=registered_user.user_id,
            loan_name="Home Renovation",
            lender_name="Axis Bank",
            principal=Decimal("250000.00"),  # Altered principal!
            annual_rate=Decimal("8.50"),
            tenure_months=12,
            start_date_val=date(2025, 1, 1)
        )

        assert updated is None
        assert "cannot be altered after payments have been recorded" in err


def test_loan_deletion_cascades_safely(app, registered_user):
    """Test deleting a loan removes all its schedules and payments cleanly."""
    with app.app_context():
        loan, _ = create_loan(
            user_id=registered_user.user_id,
            loan_name="Temporary Loan",
            lender_name="ICICI",
            principal=Decimal("50000.00"),
            annual_rate=Decimal("10.00"),
            tenure_months=6,
            start_date_val=date(2025, 1, 1)
        )

        loan_id = loan.loan_id
        emi_id = loan.schedule[0].emi_id

        # Record a payment
        record_payment(
            user_id=registered_user.user_id,
            emi_id=emi_id,
            amount_paid=Decimal("500.00"),
            payment_date_val=date(2025, 1, 15),
            payment_method="Cash"
        )

        # Delete the loan
        success, err = delete_loan(loan_id, registered_user.user_id)
        assert success is True

        # Verify nothing remains orphaned
        assert db.session.get(Loan, loan_id) is None
        assert EMISchedule.query.filter_by(loan_id=loan_id).count() == 0
        assert Payment.query.filter_by(emi_id=emi_id).count() == 0
