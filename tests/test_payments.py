from datetime import date
from decimal import Decimal
import pytest
from models import db, Loan, EMISchedule, Payment
from services.loan_service import create_loan
from services.payment_service import record_payment, get_payment_history
from services.report_service import get_dashboard_summary, generate_payments_csv

@pytest.fixture
def user_with_loan(app, registered_user):
    """Sets up a user with an active 6-month loan and returns the loan_id."""
    with app.app_context():
        loan, _ = create_loan(
            user_id=registered_user.user_id,
            loan_name="Personal Education Loan",
            lender_name="Bank of Baroda",
            principal=Decimal("60000.00"),
            annual_rate=Decimal("12.00"),
            tenure_months=6,
            start_date_val=date(2025, 1, 1)
        )
        return loan.loan_id


def test_successful_full_payment(app, registered_user, user_with_loan):
    """Test paying the exact remaining amount marks instalment as Paid."""
    with app.app_context():
        loan = db.session.get(Loan, user_with_loan)
        first_emi = loan.schedule[0]
        full_amount = first_emi.remaining_amount

        payment, err = record_payment(
            user_id=registered_user.user_id,
            emi_id=first_emi.emi_id,
            amount_paid=full_amount,
            payment_date_val=date(2025, 1, 15),
            payment_method="Bank Transfer",
            reference_number="NEFT12345"
        )

        assert err is None
        assert payment is not None
        assert payment.amount_paid == full_amount
        assert first_emi.remaining_amount == Decimal("0.00")
        assert first_emi.computed_status == "Paid"


def test_partial_payment(app, registered_user, user_with_loan):
    """Test paying less than full balance marks instalment as Partially Paid."""
    with app.app_context():
        loan = db.session.get(Loan, user_with_loan)
        first_emi = loan.schedule[0]
        partial_amount = Decimal("3000.00")

        payment, err = record_payment(
            user_id=registered_user.user_id,
            emi_id=first_emi.emi_id,
            amount_paid=partial_amount,
            payment_date_val=date(2025, 1, 10),
            payment_method="UPI",
            reference_number="UPI-PARTIAL-1"
        )

        assert err is None
        assert first_emi.amount_paid == partial_amount
        assert first_emi.remaining_amount == first_emi.emi_amount - partial_amount
        assert first_emi.computed_status in ("Partially Paid", "Overdue")


def test_multiple_payments_on_single_installment(app, registered_user, user_with_loan):
    """Test recording two successive partial payments against one instalment."""
    with app.app_context():
        loan = db.session.get(Loan, user_with_loan)
        first_emi = loan.schedule[0]
        
        # Payment 1: 2,000
        p1, err1 = record_payment(
            user_id=registered_user.user_id,
            emi_id=first_emi.emi_id,
            amount_paid=Decimal("2000.00"),
            payment_date_val=date(2025, 1, 5),
            payment_method="Cash"
        )
        assert err1 is None

        # Payment 2: 1,500
        p2, err2 = record_payment(
            user_id=registered_user.user_id,
            emi_id=first_emi.emi_id,
            amount_paid=Decimal("1500.00"),
            payment_date_val=date(2025, 1, 8),
            payment_method="UPI",
            reference_number="UPI-TR-2"
        )
        assert err2 is None

        # Verify cumulative amount
        assert first_emi.amount_paid == Decimal("3500.00")
        assert len(first_emi.payments) == 2


def test_excess_payment_rejection(app, registered_user, user_with_loan):
    """Test that paying more than the remaining balance is rejected."""
    with app.app_context():
        loan = db.session.get(Loan, user_with_loan)
        first_emi = loan.schedule[0]
        excess_amount = first_emi.remaining_amount + Decimal("500.00")

        payment, err = record_payment(
            user_id=registered_user.user_id,
            emi_id=first_emi.emi_id,
            amount_paid=excess_amount,
            payment_date_val=date(2025, 1, 10),
            payment_method="Bank Transfer"
        )

        assert payment is None
        assert "exceeds the remaining balance" in err.lower()


def test_zero_and_negative_payment_rejection(app, registered_user, user_with_loan):
    """Test that zero or negative payments are rejected."""
    with app.app_context():
        loan = db.session.get(Loan, user_with_loan)
        first_emi = loan.schedule[0]

        # Zero payment
        p_zero, err_zero = record_payment(
            user_id=registered_user.user_id,
            emi_id=first_emi.emi_id,
            amount_paid=Decimal("0.00"),
            payment_date_val=date(2025, 1, 10),
            payment_method="Cash"
        )
        assert p_zero is None
        assert "greater than zero" in err_zero.lower()

        # Negative payment
        p_neg, err_neg = record_payment(
            user_id=registered_user.user_id,
            emi_id=first_emi.emi_id,
            amount_paid=Decimal("-500.00"),
            payment_date_val=date(2025, 1, 10),
            payment_method="Cash"
        )
        assert p_neg is None
        assert "greater than zero" in err_neg.lower()


def test_cross_user_payment_prevention(app, registered_user, second_user, user_with_loan):
    """Test that User B cannot record a payment against User A's instalment."""
    with app.app_context():
        loan = db.session.get(Loan, user_with_loan)
        first_emi = loan.schedule[0]

        payment, err = record_payment(
            user_id=second_user.user_id,  # User B
            emi_id=first_emi.emi_id,      # Belongs to User A
            amount_paid=Decimal("1000.00"),
            payment_date_val=date(2025, 1, 10),
            payment_method="Cash"
        )

        assert payment is None
        assert "access denied" in err.lower()


def test_dashboard_totals_after_payment(app, registered_user, user_with_loan):
    """Test dashboard calculations accurately update after recording payments."""
    with app.app_context():
        loan = db.session.get(Loan, user_with_loan)
        first_emi = loan.schedule[0]
        pay_amount = Decimal("5000.00")
        record_payment(
            user_id=registered_user.user_id,
            emi_id=first_emi.emi_id,
            amount_paid=pay_amount,
            payment_date_val=date(2025, 1, 10),
            payment_method="Bank Transfer"
        )

        summary = get_dashboard_summary(registered_user.user_id)
        assert summary["total_amount_paid"] == pay_amount
        assert summary["total_active_loans"] == 1
        assert summary["total_original_principal"] == Decimal("60000.00")
        assert summary["total_outstanding_principal"] < Decimal("60000.00")


def test_csv_export_authorization(app, registered_user, second_user, user_with_loan):
    """Test CSV export only contains records of the authenticated user."""
    with app.app_context():
        loan = db.session.get(Loan, user_with_loan)
        first_emi = loan.schedule[0]
        record_payment(
            user_id=registered_user.user_id,
            emi_id=first_emi.emi_id,
            amount_paid=Decimal("4500.00"),
            payment_date_val=date(2025, 1, 15),
            payment_method="Bank Transfer",
            reference_number="REF-USER-1"
        )

        # Export for user 1
        csv_u1 = generate_payments_csv(registered_user.user_id)
        assert "REF-USER-1" in csv_u1
        assert "Personal Education Loan" in csv_u1

        # Export for user 2
        csv_u2 = generate_payments_csv(second_user.user_id)
        assert "REF-USER-1" not in csv_u2
        assert "Personal Education Loan" not in csv_u2
