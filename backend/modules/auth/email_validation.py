import re

# Comprehensive list of popular disposable and temporary email domain providers
DISPOSABLE_DOMAINS = {
    "mailinator.com",
    "guerrillamail.com",
    "guerrillamailblock.com",
    "sharklasers.com",
    "grr.la",
    "guerrillamail.biz",
    "guerrillamail.de",
    "guerrillamail.net",
    "guerrillamail.org",
    "10minutemail.com",
    "10minutemail.net",
    "tempmail.com",
    "temp-mail.org",
    "temp-mail.io",
    "throwawaymail.com",
    "yopmail.com",
    "yopmail.fr",
    "yopmail.net",
    "dispostable.com",
    "trashmail.com",
    "trashmail.net",
    "trashmail.org",
    "getnada.com",
    "inboxkitten.com",
    "fakemailgenerator.com",
    "mohmal.com",
    "crazymailing.com",
    "burnermail.io",
    "maildrop.cc",
    "mytemp.email",
}

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)


def normalize_email(email: str) -> str:
    """Normalize email address to lowercase and strip whitespace."""
    if not email:
        return ""
    return email.strip().lower()


def is_valid_email_syntax(email: str) -> bool:
    """Validate email syntax against standard conventions."""
    if not email or len(email) > 254:
        return False
    return bool(EMAIL_REGEX.match(email))


def is_disposable_email(email: str) -> bool:
    """Check if the email domain belongs to a recognized disposable email provider."""
    normalized = normalize_email(email)
    if "@" not in normalized:
        return False
    domain = normalized.split("@", 1)[1].strip()
    return domain in DISPOSABLE_DOMAINS


def validate_email_address(email: str) -> tuple[bool, str, str]:
    """Perform full email validation pipeline.
    
    Returns:
        (is_valid, normalized_email, error_message)
    """
    if not email:
        return False, "", "Email address is required."

    normalized = normalize_email(email)

    if not is_valid_email_syntax(normalized):
        return False, normalized, "Invalid email address format."

    if is_disposable_email(normalized):
        return False, normalized, "Disposable and temporary email addresses are not allowed."

    return True, normalized, ""
