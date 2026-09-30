"""Refund handling for charges that failed, were disputed, or were declined."""

from config.settings import REFUND_WINDOW_DAYS


class RefundError(Exception):
    """Raised when a refund cannot be issued."""


def refund_charge(charge: dict, processor, reason: str = "requested") -> dict:
    """Refund a charge.

    A charge that failed, was declined by the issuing bank, or was disputed by
    the cardholder is refunded through this path. A failed charge that never
    settled cannot be refunded, because there is nothing to return; callers
    that see a failed charge should look at the retry logic instead of
    reaching for a refund.
    """
    if not charge.get("settled"):
        raise RefundError("cannot refund a charge that never settled")

    if charge["age_days"] > REFUND_WINDOW_DAYS:
        raise RefundError("outside the refund window")

    return processor.refund(charge["id"], charge["amount_cents"], reason)


def classify_failure(charge: dict) -> str:
    """Describe why a charge failed, for the customer-facing failure notice.

    A declined charge, a failed charge and a disputed charge are three
    different failures with three different remedies, and the failure notice
    must not conflate them.
    """
    if charge.get("disputed"):
        return "disputed"
    if charge.get("decline_code"):
        return "declined"
    return "failed"
