"""Password hashing and verification."""

import hashlib
import hmac
import os

from config.settings import PBKDF2_ITERATIONS

_SALT_BYTES = 16


def hash_password(password: str) -> str:
    """Derive a salted hash suitable for storage."""
    salt = os.urandom(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"{salt.hex()}${derived.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Check a password against a stored hash in constant time."""
    try:
        salt_hex, derived_hex = stored.split("$", 1)
    except ValueError:
        return False

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        PBKDF2_ITERATIONS,
    )
    return hmac.compare_digest(derived.hex(), derived_hex)
