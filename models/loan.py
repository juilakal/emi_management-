from datetime import datetime, date
from decimal import Decimal
from models import db

class Loan(db.Model):
    """Loan model representing an individual loan taken by a user."""
    __tablename__ = "loans"

    loan_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    loan_name = db.Column(db.String(100), nullable=False)
    lender_name = db.Column(db.String(100), nullable=False)
    principal_amount = db.Column(db.Numeric(12, 2), nullable=False)
    annual_interest_rate = db.Column(db.Numeric(5, 2), nullable=False)
    tenure_months = db.Column(db.Integer, nullable=False)
    emi_amount = db.Column(db.Numeric(12, 2), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="Active", nullable=False)  # Active, Closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    schedule = db.relationship(
        "EMISchedule",
        backref="loan",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="EMISchedule.installment_number"
    )

    @property
    def total_paid(self) -> Decimal:
        """Total payments recorded across all instalments of this loan."""
        total = Decimal("0.00")
        for item in self.schedule:
            total += item.amount_paid
        return total.quantize(Decimal("0.01"))

    @property
    def total_scheduled_amount(self) -> Decimal:
        """Total scheduled repayment amount across all instalments."""
        total = Decimal("0.00")
        for item in self.schedule:
            total += Decimal(str(item.emi_amount))
        return total.quantize(Decimal("0.01"))

    @property
    def total_interest_payable(self) -> Decimal:
        """Total interest payable across the scheduled instalments."""
        total = Decimal("0.00")
        for item in self.schedule:
            total += Decimal(str(item.interest_component))
        return total.quantize(Decimal("0.01"))

    @property
    def outstanding_principal(self) -> Decimal:
        """
        Calculates remaining outstanding principal based on unpaid principal components.
        For partial payments on an installment, credit is applied towards principal proportionally or sequentially.
        Here we calculate: Sum of (principal_component * (remaining / emi_amount)) for unpaid/partial installments.
        """
        remaining_principal = Decimal("0.00")
        for item in self.schedule:
            emi_val = Decimal(str(item.emi_amount))
            paid_val = item.amount_paid
            if paid_val >= emi_val:
                continue
            princ_val = Decimal(str(item.principal_component))
            unpaid_ratio = (emi_val - paid_val) / emi_val if emi_val > 0 else Decimal("0")
            remaining_principal += princ_val * unpaid_ratio

        rounded = remaining_principal.quantize(Decimal("0.01"))
        return max(Decimal("0.00"), rounded)

    @property
    def remaining_total_amount(self) -> Decimal:
        """Total remaining payable amount across all installments."""
        rem = Decimal("0.00")
        for item in self.schedule:
            rem += item.remaining_amount
        return rem.quantize(Decimal("0.01"))

    @property
    def repayment_progress_percentage(self) -> float:
        """Percentage of total scheduled loan amount paid."""
        total = self.total_scheduled_amount
        if total <= 0:
            return 0.0
        pct = (self.total_paid / total) * Decimal("100.0")
        return min(100.0, float(round(pct, 1)))

    @property
    def paid_installments_count(self) -> int:
        """Count of fully paid instalments."""
        return sum(1 for item in self.schedule if item.amount_paid >= Decimal(str(item.emi_amount)))

    @property
    def pending_installments_count(self) -> int:
        """Count of not yet fully paid instalments."""
        return len(self.schedule) - self.paid_installments_count

    @property
    def has_payments(self) -> bool:
        """Payment transactions are not part of the EMI tracker."""
        return False

    @property
    def is_editable(self) -> bool:
        """Loan details remain editable because no payment ledger is maintained."""
        return True

    def __repr__(self) -> str:
        return f"<Loan {self.loan_id}: {self.loan_name} (User {self.user_id})>"
