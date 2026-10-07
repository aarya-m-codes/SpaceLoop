import re
from werkzeug.security import check_password_hash, generate_password_hash


def hash_user_password(password: str) -> str:
    """Securely hash a password using Werkzeug's scrypt implementation."""
    if not password:
        raise ValueError("Password cannot be empty.")
    return generate_password_hash(password, method="scrypt")


def verify_user_password(password: str, password_hash: str) -> bool:
    """Verify a plain-text password against a stored secure password hash."""
    if not password or not password_hash:
        return False
    return check_password_hash(password_hash, password)


def check_password_complexity(password: str) -> tuple[bool, str]:
    """Ensure password meets production security criteria."""
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one numeric digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+[\]~`]", password):
        return False, "Password must contain at least one special character."
    return True, "Password complexity verified."
