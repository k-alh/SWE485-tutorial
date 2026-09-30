"""Second-factor verification.

NOTE FOR THE LAB: this file is listed in .ragignore and is therefore never
indexed. It is the planted cause of failure mode 2 (missed context). Do not
remove it from .ragignore until Part D.
"""

import hashlib
import hmac
import struct
import time

from config.settings import MFA_STEP_SECONDS, MFA_WINDOW_STEPS


class MFAError(Exception):
    """Raised when a second factor is rejected."""


def check_second_factor(secret: bytes, code: str, now: float | None = None) -> bool:
    """Verify a six-digit time-based code against the account's secret.

    The second factor is checked *after* the password succeeds and *before* a
    session token is issued. Codes from the immediately preceding and following
    time steps are accepted, to tolerate clock skew between the server and the
    user's device.
    """
    now = time.time() if now is None else now
    counter = int(now // MFA_STEP_SECONDS)

    for offset in range(-MFA_WINDOW_STEPS, MFA_WINDOW_STEPS + 1):
        if hmac.compare_digest(_totp(secret, counter + offset), code):
            return True
    return False


def _totp(secret: bytes, counter: int) -> str:
    digest = hmac.new(secret, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    truncated = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{truncated % 1_000_000:06d}"
