import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote
from cryptography.fernet import Fernet
from flask import current_app


from backend.core.cache import cache


def _get_fernet() -> Fernet:
    """Instantiate a Fernet cipher derived from MFA_ENCRYPTION_KEY or application SECRET_KEY."""
    try:
        secret = (
            current_app.config.get("MFA_ENCRYPTION_KEY")
            or current_app.config.get("SECRET_KEY", "spaceloop-mfa-fallback-secret")
        )
    except RuntimeError:
        secret = "spaceloop-mfa-fallback-secret"
    key_bytes = hashlib.sha256(secret.encode("utf-8") if isinstance(secret, str) else secret).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def generate_totp_secret() -> str:
    """Generate a high-entropy 32-character Base32 TOTP secret."""
    raw_bytes = secrets.token_bytes(20)
    return base64.b32encode(raw_bytes).decode("utf-8").replace("=", "")


def encrypt_totp_secret(secret_b32: str) -> str:
    """Encrypt plain Base32 TOTP secret using Fernet (AES-128-CBC + HMAC)."""
    fernet = _get_fernet()
    encrypted = fernet.encrypt(secret_b32.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_totp_secret(encrypted_token: str) -> str:
    """Decrypt stored Fernet token to retrieve the original Base32 secret."""
    fernet = _get_fernet()
    decrypted = fernet.decrypt(encrypted_token.encode("utf-8"))
    return decrypted.decode("utf-8")


def generate_totp_code(secret_b32: str, for_time: int | None = None) -> str:
    """Compute the 6-digit TOTP code for a given timestamp according to RFC 6238."""
    if for_time is None:
        for_time = int(time.time())

    counter = for_time // 30
    # Normalize base32 padding
    clean_secret = secret_b32.strip().upper()
    missing_padding = len(clean_secret) % 8
    if missing_padding:
        clean_secret += "=" * (8 - missing_padding)

    key = base64.b32decode(clean_secret, casefold=True)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()

    offset = digest[19] & 0x0F
    truncated = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % 1000000
    return f"{truncated:06d}"


def verify_totp_code(
    secret_b32: str,
    code: str,
    window: int = 1,
    user_id: int | str | None = None,
    context: str = "general",
) -> bool:
    """Verify submitted TOTP code allowing for clock drift of +/- window steps (default: 30s drift).
    
    If user_id is provided, automatically enforces single-use replay protection across the drift window.
    """
    if not code or not isinstance(code, str):
        return False

    clean_code = code.strip()
    if len(clean_code) != 6 or not clean_code.isdigit():
        return False

    # Check replay cache if user_id is tracked
    if user_id is not None:
        replay_key = f"totp_replayed:{context}:{user_id}:{clean_code}"
        if cache.has(replay_key):
            return False

    now = int(time.time())

    for step in range(-window, window + 1):
        test_time = now + (step * 30)
        expected_code = generate_totp_code(secret_b32, for_time=test_time)
        if hmac.compare_digest(expected_code, clean_code):
            # Code is mathematically valid; mark it as used to prevent replay
            if user_id is not None:
                cache.set(f"totp_replayed:{context}:{user_id}:{clean_code}", True, ttl=90)
            return True

    return False


def generate_recovery_codes(count: int = 8) -> list[str]:
    """Generate human-readable, high-entropy alphanumeric backup recovery codes."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    codes = []
    for _ in range(count):
        part1 = "".join(secrets.choice(alphabet) for _ in range(5))
        part2 = "".join(secrets.choice(alphabet) for _ in range(5))
        codes.append(f"{part1}-{part2}")
    return codes


def hash_recovery_code(code: str) -> str:
    """Produce SHA-256 hex digest of a recovery code for database persistence."""
    normalized = code.strip().upper().replace(" ", "").replace("-", "")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_provisioning_uri(email: str, secret_b32: str, issuer: str = "SpaceLoop") -> str:
    """Construct an otpauth:// provisioning URI for QR code integration."""
    label = f"{issuer}:{quote(email)}"
    encoded_issuer = quote(issuer)
    return f"otpauth://totp/{label}?secret={secret_b32}&issuer={encoded_issuer}&algorithm=SHA1&digits=6&period=30"
