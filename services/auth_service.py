import re
from typing import Tuple, Optional
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
    except Exception as e:
        db.session.rollback()
        err_msg = str(e)
        if "Can't connect to MySQL" in err_msg or "2003" in err_msg or "Operation not permitted" in err_msg:
            return None, "Cannot connect to MySQL database at 127.0.0.1:3306. Please start your MySQL Server (e.g., via macOS System Settings -> MySQL -> Start MySQL Server)."
        return None, f"Database error during registration: {err_msg}"


def authenticate_user(email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
    """
    Authenticates a user by email and password using secure hash verification.
    """
    if not email or not password:
        return None, "Both email and password are required."

    clean_email = email.strip().lower()
    try:
        user = User.query.filter_by(email=clean_email).first()
    except Exception as e:
        err_msg = str(e)
        if "Can't connect to MySQL" in err_msg or "2003" in err_msg:
            return None, "Cannot connect to MySQL database at 127.0.0.1:3306. Please start your MySQL Server (e.g., via macOS System Settings -> MySQL -> Start MySQL Server)."
        return None, f"Database error during authentication: {err_msg}"

    if not user or not user.check_password(password):
        return None, "Invalid email or password. Please try again."

    return user, None


def get_user_by_id(user_id: int) -> Optional[User]:
    """Retrieve user by primary key."""
    if not user_id:
        return None
    return db.session.get(User, user_id)
