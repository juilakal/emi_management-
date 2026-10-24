import csv
import io
from datetime import date
from decimal import Decimal
from typing import Dict, Any, List
from models import db, Loan, EMISchedule, Payment
from services.emi_calculator import round_curr


def get_dashboard_summary(user_id: int) -> Dict[str, Any]:
    """
    Computes real-time dashboard aggregates for the authenticated user.
    All figures are derived directly from database records without hardcoding.
    """
    loans = Loan.query.filter_by(user_id=user_id).all()
    active_loans = [l for l in loans if l.status == "Active"]

    total_active_loans = len(active_loans)
    total_original_principal = sum((Decimal(str(l.principal_amount)) for l in loans), Decimal("0.00"))
    total_outstanding_principal = sum((l.outstanding_principal for l in loans), Decimal("0.00"))
    total_monthly_emi = sum((Decimal(str(l.emi_amount)) for l in active_loans), Decimal("0.00"))
    total_amount_paid = sum((l.total_paid for l in loans), Decimal("0.00"))

    # Instalment level counts
    all_installments = EMISchedule.query.join(Loan).filter(Loan.user_id == user_id).all()
    today = date.today()

    paid_installments_count = 0
    pending_installments_count = 0
    overdue_installments_count = 0

    for item in all_installments:
        status = item.computed_status
        if status == "Paid":
            paid_installments_count += 1
        elif status == "Overdue":
            overdue_installments_count += 1
            pending_installments_count += 1
        else:  # Pending or Partially Paid
            pending_installments_count += 1

    # Upcoming EMI payments (next 5 not fully paid, sorted by due_date)
    upcoming_installments = sorted(
        [item for item in all_installments if item.remaining_amount > Decimal("0.00")],
        key=lambda x: x.due_date
    )[:5]

    # Recent payments (latest 5)
    recent_payments = Payment.query.join(EMISchedule).join(Loan).filter(
        Loan.user_id == user_id
    ).order_by(Payment.payment_date.desc(), Payment.created_at.desc()).limit(5).all()

    # Loan repayment progress
    loan_progress_list = []
    for l in loans:
        loan_progress_list.append({
            "loan_id": l.loan_id,
            "loan_name": l.loan_name,
            "lender_name": l.lender_name,
            "principal": l.principal_amount,
            "total_paid": l.total_paid,
            "outstanding": l.outstanding_principal,
            "progress_pct": l.repayment_progress_percentage,
            "status": l.status,
        })

    # Chart data: distribution by loan outstanding
    loan_names_chart = [l.loan_name for l in active_loans]
    loan_balances_chart = [float(l.outstanding_principal) for l in active_loans]

    return {
        "total_active_loans": total_active_loans,
        "total_original_principal": round_curr(total_original_principal),
        "total_outstanding_principal": round_curr(total_outstanding_principal),
        "total_monthly_emi": round_curr(total_monthly_emi),
        "total_amount_paid": round_curr(total_amount_paid),
        "pending_installments_count": pending_installments_count,
        "overdue_installments_count": overdue_installments_count,
        "paid_installments_count": paid_installments_count,
        "upcoming_installments": upcoming_installments,
        "recent_payments": recent_payments,
        "loan_progress_list": loan_progress_list,
        "chart_data": {
            "paid_count": paid_installments_count,
            "pending_count": pending_installments_count,
            "overdue_count": overdue_installments_count,
            "loan_names": loan_names_chart,
            "loan_balances": loan_balances_chart,
        }
    }


def get_reports_data(user_id: int) -> Dict[str, Any]:
    """
    Computes comprehensive financial reporting data for the Reports page.
    """
    loans = Loan.query.filter_by(user_id=user_id).all()
    all_installments = EMISchedule.query.join(Loan).filter(Loan.user_id == user_id).all()
    payments = Payment.query.join(EMISchedule).join(Loan).filter(Loan.user_id == user_id).all()

    total_amount_paid = sum((Decimal(str(p.amount_paid)) for p in payments), Decimal("0.00"))
    total_original_principal = sum((Decimal(str(l.principal_amount)) for l in loans), Decimal("0.00"))
    total_outstanding_principal = sum((l.outstanding_principal for l in loans), Decimal("0.00"))
    total_scheduled_amount = sum((l.total_scheduled_amount for l in loans), Decimal("0.00"))
    remaining_scheduled_payments = sum((item.remaining_amount for item in all_installments), Decimal("0.00"))

    # Loan-wise breakdown
    loan_summaries = []
    for l in loans:
        loan_summaries.append({
            "loan_id": l.loan_id,
            "loan_name": l.loan_name,
            "lender_name": l.lender_name,
            "principal": l.principal_amount,
            "annual_rate": l.annual_interest_rate,
            "tenure": l.tenure_months,
            "emi": l.emi_amount,
            "total_paid": l.total_paid,
            "outstanding": l.outstanding_principal,
            "remaining_total": l.remaining_total_amount,
            "progress_pct": l.repayment_progress_percentage,
            "status": l.status,
            "paid_installments": l.paid_installments_count,
            "total_installments": len(l.schedule),
        })

    # Monthly payment breakdown
    monthly_payments_map: Dict[str, Decimal] = {}
    for p in payments:
        month_key = p.payment_date.strftime("%Y-%m")
        monthly_payments_map[month_key] = monthly_payments_map.get(month_key, Decimal("0.00")) + Decimal(str(p.amount_paid))

    sorted_months = sorted(monthly_payments_map.keys())
    monthly_breakdown = [
        {"month": m, "total": round_curr(monthly_payments_map[m])}
        for m in sorted_months
    ]

    return {
        "total_amount_paid": round_curr(total_amount_paid),
        "total_original_principal": round_curr(total_original_principal),
        "total_outstanding_principal": round_curr(total_outstanding_principal),
        "total_scheduled_amount": round_curr(total_scheduled_amount),
        "remaining_scheduled_payments": round_curr(remaining_scheduled_payments),
        "loan_summaries": loan_summaries,
        "monthly_breakdown": monthly_breakdown,
        "monthly_labels": sorted_months,
        "monthly_values": [float(monthly_payments_map[m]) for m in sorted_months],
    }


def generate_payments_csv(user_id: int) -> str:
    """
    Exports the authenticated user's payment history into a CSV string.
    Properly escapes fields and strictly filters by user_id to prevent data leakage.
    """
    payments = Payment.query.join(EMISchedule).join(Loan).filter(
        Loan.user_id == user_id
    ).order_by(Payment.payment_date.desc(), Payment.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Header
    writer.writerow([
        "Payment ID",
        "Payment Date",
        "Loan Name",
        "Lender",
        "Instalment Number",
        "Amount Paid (INR)",
        "Payment Method",
        "Reference Number",
        "Recorded At"
    ])

    for p in payments:
        writer.writerow([
            p.payment_id,
            p.payment_date.strftime("%Y-%m-%d"),
            p.emi.loan.loan_name,
            p.emi.loan.lender_name,
            p.emi.installment_number,
            f"{p.amount_paid:.2f}",
            p.payment_method,
            p.reference_number or "N/A",
            p.created_at.strftime("%Y-%m-%d %H:%M:%S")
        ])

    return output.getvalue()
