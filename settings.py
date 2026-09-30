"""Service configuration.

Every tunable the service reads at runtime lives here, so that a reviewer can
see the whole operational surface of the system on one page.
"""

# --- Authentication -------------------------------------------------------

TOKEN_SIGNING_KEY = "development-key-do-not-ship"

# How long a session token remains valid, in seconds. Changed from 86400 to
# 3600 in ADR-002; see docs/ADR-002-token-expiry.md.
TOKEN_TTL_SECONDS = 3600

MAX_LOGIN_ATTEMPTS = 5
PBKDF2_ITERATIONS = 240_000

MFA_STEP_SECONDS = 30
MFA_WINDOW_STEPS = 1

# --- Billing --------------------------------------------------------------

RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 2
SUBSCRIPTION_GRACE_HOURS = 72
REFUND_WINDOW_DAYS = 30

CURRENCY = "SAR"
VAT_RATE = 0.15
