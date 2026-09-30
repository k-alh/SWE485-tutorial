"""Session token issue and validation.

Tokens are opaque to clients. Internally a token is three base64url segments
joined by dots:

    <header>.<payload>.<signature>

The payload carries the account id and the issue time. Expiry is *not* stored
in the token itself; it is derived at validation time from the configured TTL,
so that changing the TTL takes effect immediately for tokens already in the
wild. See docs/ADR-002-token-expiry.md for why that decision was made.
"""

import base64
import hashlib
import hmac
import json
import time

from config.settings import TOKEN_SIGNING_KEY, TOKEN_TTL_SECONDS


class TokenError(Exception):
    """Raised when a token cannot be validated. Never carries detail."""


def _b64url_decode(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _split_token(token: str) -> tuple[str, str, str]:
    parts = token.split(".")
    if len(parts) != 3:
        raise TokenError("malformed token")
    return parts[0], parts[1], parts[2]


def validate_token(token: str, now: float | None = None) -> dict:
    """Validate a session token and return its decoded payload.

    Two independent checks must both pass: the token must not have aged past
    the configured TTL, and its signature must verify against the signing key.
    Either failure raises TokenError with no detail, so that a caller cannot
    distinguish an expired token from a forged one by the error message.
    """
    now = time.time() if now is None else now
    header_b64, payload_b64, signature_b64 = _split_token(token)

    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except (ValueError, json.JSONDecodeError) as exc:
        raise TokenError("unreadable payload") from exc

    issued_at = payload.get("iat")
    if not isinstance(issued_at, (int, float)):
        raise TokenError("missing issue time")

    age = now - issued_at
    if age < 0:
        raise TokenError("token issued in the future")
    if age > TOKEN_TTL_SECONDS:
        raise TokenError("expired")

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected = hmac.new(
        TOKEN_SIGNING_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()

    presented = _b64url_decode(signature_b64)
    if not hmac.compare_digest(expected, presented):
        raise TokenError("bad signature")

    return payload


def issue_token(account_id: str, now: float | None = None) -> str:
    """Mint a fresh session token for an account."""
    now = time.time() if now is None else now
    header_b64 = _b64url_encode(json.dumps({"alg": "HS256"}).encode())
    payload_b64 = _b64url_encode(
        json.dumps({"sub": account_id, "iat": int(now)}).encode()
    )
    signature = hmac.new(
        TOKEN_SIGNING_KEY.encode("utf-8"),
        f"{header_b64}.{payload_b64}".encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{header_b64}.{payload_b64}.{_b64url_encode(signature)}"
