from datetime import date
from decimal import Decimal
from models import db

class EMISchedule(db.Model):
    """EMISchedule model representing each individual monthly instalment for a loan."""
    __tablename__ = "emi_schedule"

    emi_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    loan_id = db.Column(db.Integer, db.ForeignKey("loans.loan_id", ondelete="CASCADE"), nullable=False, index=True)
    installment_number = db.Column(db.Integer, nullable=False)
    due_date = db.Column(db.Date, nullable=False, index=True)
    principal_component = db.Column(db.Numeric(12, 2), nullable=False)
    interest_component = db.Column(db.Numeric(12, 2), nullable=False)
    emi_amount = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(20), default="Pending", nullable=False)

    __table_args__ = (
        db.UniqueConstraint("loan_id", "installment_number", name="uq_loan_installment"),
    )

    # Relationship to Payments
    payments = db.relationship(
        "Payment",
        backref="emi",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="Payment.payment_date.desc(), Payment.payment_id.desc()"
    )

    @property
    def amount_paid(self) -> Decimal:
        """Sum of all recorded payments against this instalment, or full EMI if marked Paid."""
        total = Decimal("0.00")
        for p in self.payments:
            total += Decimal(str(p.amount_paid))
        if total == Decimal("0.00") and self.status == "Paid":
            return Decimal(str(self.emi_amount)).quantize(Decimal("0.01"))
        return total.quantize(Decimal("0.01"))

    @property
    def remaining_amount(self) -> Decimal:
        """Outstanding balance left on this instalment."""
        if self.status == "Paid":
            return Decimal("0.00")
        rem = Decimal(str(self.emi_amount)) - self.amount_paid
        return max(Decimal("0.00"), rem.quantize(Decimal("0.01")))

    @property
    def computed_status(self) -> str:
        """
        Payment status:
        - Paid: If marked Paid or remaining is 0.
        - Overdue: If due date has passed and remaining > 0.
        - Partially Paid: If some amount paid.
        - Pending: Not paid and due date not passed.
        """
        if self.status == "Paid" or self.remaining_amount <= Decimal("0.00"):
            return "Paid"
        today = date.today()
        if self.due_date < today:
            return "Overdue"
        if self.amount_paid > Decimal("0.00"):
            return "Partially Paid"
        return "Pending"

    @property
    def status_badge_class(self) -> str:
        """Bootstrap badge color class matching status."""
        status = self.computed_status
        if status == "Paid":
            return "badge-paid"
        if status == "Overdue":
            return "badge-overdue"
        if status == "Partially Paid":
            return "badge-partial"
        return "badge-pending"

    def __repr__(self) -> str:
        return f"<EMISchedule {self.emi_id}: Loan {self.loan_id} #{self.installment_number}>"
