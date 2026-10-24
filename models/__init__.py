from flask_sqlalchemy import SQLAlchemy

# Initialize shared SQLAlchemy extension instance
db = SQLAlchemy()

from models.user import User
from models.loan import Loan
from models.emi import EMISchedule
from models.payment import Payment

__all__ = ["db", "User", "Loan", "EMISchedule", "Payment"]
