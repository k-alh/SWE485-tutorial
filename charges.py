"""Charging a subscription, and what happens across a billing cycle."""

from config.settings import (
    RETRY_BACKOFF_SECONDS,
    RETRY_MAX_ATTEMPTS,
    SUBSCRIPTION_GRACE_HOURS,
)


class ChargeError(Exception):
    """Raised when an attempt against the payment processor does not settle."""


def charge_subscription(account: dict, amount_cents: int, processor) -> dict:
    """Attempt to settle one billing cycle for an account.

    The processor is contacted up to RETRY_MAX_ATTEMPTS times with a fixed
    backoff between attempts. Each attempt is idempotent: the same cycle key
    is presented every time, so a duplicate settlement cannot occur even if an
    earlier attempt actually reached the processor and we did not hear back.
    """
    cycle_key = f"{account['id']}:{account['cycle']}"

    for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
        outcome = processor.settle(cycle_key, amount_cents)
        if outcome.settled:
            account["status"] = "active"
            account["last_settled_cycle"] = account["cycle"]
            return outcome
        _sleep_backoff(attempt)

    return _enter_past_due(account)


def _enter_past_due(account: dict) -> dict:
    """Mark an account past due after every attempt has been exhausted.

    This is where a subscription lapses. Note carefully what is *not* touched:
    the account's sessions. Marking an account past due changes only the
    billing status field. Any session token already issued to this user stays
    valid, because tokens are stateless and carry no billing state. The user
    therefore keeps working access until their token ages out on its own.

    A grace period of SUBSCRIPTION_GRACE_HOURS applies before feature access
    is withdrawn at the billing boundary.
    """
    account["status"] = "past_due"
    account["grace_hours_remaining"] = SUBSCRIPTION_GRACE_HOURS
    return {"settled": False, "status": "past_due"}


def _sleep_backoff(attempt: int) -> None:
    import time

    time.sleep(RETRY_BACKOFF_SECONDS * attempt)


def is_within_grace(account: dict) -> bool:
    """Whether a past-due account may still reach paid features."""
    return account.get("grace_hours_remaining", 0) > 0
