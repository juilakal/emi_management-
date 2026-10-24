import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List

TWO_PLACES = Decimal("0.01")


def round_curr(val: Decimal) -> Decimal:
    """Helper to round a Decimal value to 2 decimal places using standard ROUND_HALF_UP."""
    return val.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_emi(principal: Decimal, annual_rate: Decimal, tenure_months: int) -> Decimal:
    """
    Calculate the monthly Equated Monthly Instalment (EMI) using the reducing-balance formula.

    Formula:
        EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
        where:
            P = Principal loan amount
            r = Monthly interest rate as a decimal (annual_rate / (12 * 100))
            n = Total number of monthly instalments (tenure_months)

        If interest rate is 0:
            EMI = P / n
    """
    if principal <= Decimal("0"):
        raise ValueError("Principal amount must be greater than zero.")
    if annual_rate < Decimal("0"):
        raise ValueError("Annual interest rate cannot be negative.")
    if tenure_months <= 0:
        raise ValueError("Tenure must be at least 1 month.")

    P = principal
    n = tenure_months

    if annual_rate == Decimal("0"):
        emi = P / Decimal(str(n))
        return round_curr(emi)

    # Monthly interest rate
    r = (annual_rate / Decimal("100")) / Decimal("12")
    one_plus_r = Decimal("1") + r

    # (1 + r)^n
    pow_factor = one_plus_r ** Decimal(str(n))

    numerator = P * r * pow_factor
    denominator = pow_factor - Decimal("1")

    if denominator == Decimal("0"):
        return round_curr(P / Decimal(str(n)))

    emi = numerator / denominator
    return round_curr(emi)


def generate_amortization_schedule(
    principal: Decimal,
    annual_rate: Decimal,
    tenure_months: int,
    start_date: date
) -> List[Dict[str, Any]]:
    """
    Generate an itemized reducing-balance monthly amortization schedule.
    Handles exact penny reconciliation on the final instalment so that the sum
    of all principal components exactly equals the original principal amount.
    """
    if principal <= Decimal("0") or tenure_months <= 0 or annual_rate < Decimal("0"):
        raise ValueError("Invalid parameters for amortization schedule.")

    monthly_emi = calculate_emi(principal, annual_rate, tenure_months)
    r = (annual_rate / Decimal("100")) / Decimal("12") if annual_rate > Decimal("0") else Decimal("0")

    remaining_balance = principal
    schedule: List[Dict[str, Any]] = []

    for month_num in range(1, tenure_months + 1):
        # Calculate due date: each month from start_date
        # Month 1 is due one month after start_date, or on start_date + offset
        due_date = add_months(start_date, month_num)

        if annual_rate == Decimal("0"):
            interest_comp = Decimal("0.00")
        else:
            interest_comp = round_curr(remaining_balance * r)

        if month_num == tenure_months:
            # Final month adjustment: balance must zero out completely
            principal_comp = remaining_balance
            actual_emi = principal_comp + interest_comp
            remaining_balance = Decimal("0.00")
        else:
            principal_comp = monthly_emi - interest_comp
            if principal_comp > remaining_balance:
                principal_comp = remaining_balance
            actual_emi = principal_comp + interest_comp
            remaining_balance = round_curr(remaining_balance - principal_comp)

        schedule.append({
            "installment_number": month_num,
            "due_date": due_date,
            "principal_component": round_curr(principal_comp),
            "interest_component": round_curr(interest_comp),
            "emi_amount": round_curr(actual_emi),
            "remaining_balance": max(Decimal("0.00"), remaining_balance),
        })

    return schedule


def add_months(orig_date: date, months_to_add: int) -> date:
    """
    Add months to a date, correctly preserving the calendar day or snapping to the
    last day of the destination month for month-end dates (e.g. Jan 31 -> Feb 28/29).
    """
    total_months = orig_date.month + months_to_add - 1
    new_year = orig_date.year + total_months // 12
    new_month = total_months % 12 + 1
    max_day = calendar.monthrange(new_year, new_month)[1]
    new_day = min(orig_date.day, max_day)
    return date(new_year, new_month, new_day)


def get_loan_calculation_summary(
    principal: Decimal,
    annual_rate: Decimal,
    tenure_months: int,
    start_date: date = None
) -> Dict[str, Any]:
    """
    Get full summary containing standard EMI, total interest, total payable,
    and the amortized schedule with reconciled totals.
    """
    if start_date is None:
        start_date = date.today()

    schedule = generate_amortization_schedule(principal, annual_rate, tenure_months, start_date)
    
    total_principal_sum = sum(item["principal_component"] for item in schedule)
    total_interest_sum = sum(item["interest_component"] for item in schedule)
    total_payable_sum = sum(item["emi_amount"] for item in schedule)

    # Standard monthly EMI (as computed by formula before final penny reconciliation)
    standard_emi = calculate_emi(principal, annual_rate, tenure_months)

    return {
        "principal": round_curr(principal),
        "annual_interest_rate": round_curr(annual_rate),
        "tenure_months": tenure_months,
        "monthly_emi": standard_emi,
        "total_principal": round_curr(total_principal_sum),
        "total_interest": round_curr(total_interest_sum),
        "total_payable": round_curr(total_payable_sum),
        "schedule": schedule,
    }
