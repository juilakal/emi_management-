from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from models import db

class User(db.Model):
    """User model representing registered system accounts."""
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships: Deleting a user deletes all their loans (and cascades to schedules/payments)
    loans = db.relationship("Loan", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        """Hash and store the password using Werkzeug's secure PBKDF2 SHA-256 hashing."""
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password: str) -> bool:
        """Verify the password against the stored password hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.user_id}: {self.email}>"
