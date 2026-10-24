from datetime import datetime
from decimal import Decimal
from models import db

class Payment(db.Model):
    """Payment model representing a recorded payment transaction against an EMI instalment."""
    __tablename__ = "payments"

    payment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    emi_id = db.Column(db.Integer, db.ForeignKey("emi_schedule.emi_id", ondelete="CASCADE"), nullable=False, index=True)
    amount_paid = db.Column(db.Numeric(12, 2), nullable=False)
    payment_date = db.Column(db.Date, nullable=False, index=True)
    payment_method = db.Column(db.String(50), nullable=False)  # 'Bank Transfer', 'UPI', 'Cash', 'Other'
    reference_number = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def formatted_amount(self) -> str:
        """Formatted currency string for amount paid."""
        return f"₹{Decimal(str(self.amount_paid)):,.2f}"

    def __repr__(self) -> str:
        return f"<Payment {self.payment_id}: ₹{self.amount_paid} for EMI {self.emi_id}>"
