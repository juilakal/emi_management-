from datetime import date
from decimal import Decimal
import pytest
from services.emi_calculator import (
    calculate_emi,
    generate_amortization_schedule,
    get_loan_calculation_summary,
    add_months
)

def test_standard_emi_calculation():
    """
    Test standard reducing-balance loan calculation.
    Example:
    P = 100,000, Annual Rate = 12% (r = 1% per month = 0.01), Tenure = 12 months.
    Formula:
    EMI = 100000 * 0.01 * (1.01)^12 / ((1.01)^12 - 1) = 8884.88
    """
    principal = Decimal("100000.00")
    rate = Decimal("12.00")
    tenure = 12

    emi = calculate_emi(principal, rate, tenure)
    assert emi == Decimal("8884.88")


def test_zero_interest_loan_calculation():
    """
    Test zero-interest loan calculation: EMI = P / n.
    Example: P = 60,000, Rate = 0%, Tenure = 12 months -> EMI = 5000.00
    """
    principal = Decimal("60000.00")
    rate = Decimal("0.00")
    tenure = 12

    emi = calculate_emi(principal, rate, tenure)
    assert emi == Decimal("5000.00")


def test_invalid_calculator_inputs():
    """Test validation errors for zero/negative principal, negative rate, or zero tenure."""
    # Zero principal
    with pytest.raises(ValueError, match="greater than zero"):
        calculate_emi(Decimal("0.00"), Decimal("10.0"), 12)

    # Negative principal
    with pytest.raises(ValueError, match="greater than zero"):
        calculate_emi(Decimal("-5000.00"), Decimal("10.0"), 12)

    # Negative interest rate
    with pytest.raises(ValueError, match="cannot be negative"):
        calculate_emi(Decimal("100000.00"), Decimal("-2.5"), 12)

    # Zero tenure
    with pytest.raises(ValueError, match="at least 1 month"):
        calculate_emi(Decimal("100000.00"), Decimal("8.0"), 0)


def test_amortization_schedule_principal_reconciliation():
    """
    Requirement 8:
    Verify that the sum of all scheduled principal components reconciles
    EXACTLY to the original principal amount, with final month adjustment.
    """
    principal = Decimal("125000.00")
    rate = Decimal("10.50")
    tenure = 18
    start = date(2025, 1, 15)

    schedule = generate_amortization_schedule(principal, rate, tenure, start)
    assert len(schedule) == tenure

    # Sum of principal components
    sum_principal = sum(item["principal_component"] for item in schedule)
    assert sum_principal == principal

    # Final month remaining balance must be zero
    assert schedule[-1]["remaining_balance"] == Decimal("0.00")


def test_month_end_date_progression():
    """
    Requirement 8:
    Test monthly date generation for dates near the end of a month (e.g. Jan 31).
    Month 1: Jan 31 + 1 month = Feb 28 (or 29)
    Month 2: March 31
    Month 3: April 30
    """
    start = date(2024, 1, 31)  # 2024 was a leap year
    feb_due = add_months(start, 1)
    assert feb_due == date(2024, 2, 29)

    mar_due = add_months(start, 2)
    assert mar_due == date(2024, 3, 31)

    apr_due = add_months(start, 3)
    assert apr_due == date(2024, 4, 30)


def test_calculation_summary():
    """Test full calculation summary helper returns properly rounded totals."""
    summary = get_loan_calculation_summary(
        principal=Decimal("50000.00"),
        annual_rate=Decimal("12.00"),
        tenure_months=6,
        start_date=date(2025, 1, 1)
    )

    assert summary["principal"] == Decimal("50000.00")
    assert summary["tenure_months"] == 6
    assert summary["total_principal"] == Decimal("50000.00")
    assert summary["total_payable"] == summary["total_principal"] + summary["total_interest"]
