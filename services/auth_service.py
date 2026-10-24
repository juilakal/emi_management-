import re
from typing import Tuple, Optional
from sqlalchemy.exc import IntegrityError, OperationalError
from models import db, User

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_registration_input(
    full_name: str,
    email: str,
    password: str,
    confirm_password: str
) -> Tuple[bool, Optional[str]]:
    """Validate user registration fields."""
    if not full_name or not full_name.strip():
        return False, "Full Name is required."
    if len(full_name.strip()) < 2:
        return False, "Full Name must be at least 2 characters long."

    if not email or not email.strip():
        return False, "Email address is required."
    clean_email = email.strip().lower()
    if not EMAIL_REGEX.match(clean_email):
        return False, "Please provide a valid email address (e.g., user@example.com)."

    if not password:
        return False, "Password is required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."

    if password != confirm_password:
        return False, "Passwords do not match."

    return True, None


def register_user(
    full_name: str,
    email: str,
    password: str,
    confirm_password: str
) -> Tuple[Optional[User], Optional[str]]:
    """
    Registers a new user after validation and checks for unique email.
    Never stores plain-text passwords.
    """
    is_valid, error = validate_registration_input(full_name, email, password, confirm_password)
    if not is_valid:
        return None, error

    try:
        clean_email = email.strip().lower()
        existing_user = User.query.filter_by(email=clean_email).first()
        if existing_user:
            return None, "An account with this email address already exists. Please log in."

        user = User(
            full_name=full_name.strip(),
            email=clean_email
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user, None
    except IntegrityError:
        db.session.rollback()
        return None, "An account with this email address already exists. Please log in."
    except OperationalError:
        db.session.rollback()
        return None, "Could not save your account right now. Please try again."
    except Exception:
        db.session.rollback()
        return None, "Could not create your account. Please try again."


def authenticate_user(email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
    """
    Authenticates a user by email and password using secure hash verification.
    """
    if not email or not password:
        return None, "Both email and password are required."

    clean_email = email.strip().lower()
    try:
        user = User.query.filter_by(email=clean_email).first()
    except Exception:
        return None, "Could not sign you in right now. Please try again."

    if not user or not user.check_password(password):
        return None, "Invalid email or password. Please try again."

    return user, None


def get_user_by_id(user_id: int) -> Optional[User]:
    """Retrieve user by primary key."""
    if not user_id:
        return None
    return db.session.get(User, user_id)
