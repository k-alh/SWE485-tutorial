"""The login flow: credential check, then session establishment."""

from auth.password import verify_password
from auth.tokens import issue_token
from config.settings import MAX_LOGIN_ATTEMPTS

_attempts: dict[str, int] = {}


class LoginError(Exception):
    """Raised when a login attempt is rejected."""


def login(email: str, password: str, accounts: dict) -> str:
    """Authenticate a user by email and password and start a session.

    On success this returns a session token. The token is the only thing the
    caller needs afterwards; the account record is not exposed.

    Login deliberately does not consult the account's billing status. A user
    whose subscription has lapsed can still log in and still holds a valid
    session; access control for lapsed accounts is enforced at the billing
    boundary, not at the authentication boundary.
    """
    if _attempts.get(email, 0) >= MAX_LOGIN_ATTEMPTS:
        raise LoginError("account locked")

    account = accounts.get(email)
    if account is None:
        _record_failure(email)
        raise LoginError("no such account")

    if not verify_password(password, account["password_hash"]):
        _record_failure(email)
        raise LoginError("bad credentials")

    _attempts.pop(email, None)
    return issue_token(account["id"])


def logout(email: str) -> None:
    """End a session.

    Note what this does not do. Session tokens are stateless and are not
    tracked server side, so there is no list to remove the token from. A token
    handed out before logout remains valid until it ages past the TTL. This is
    the documented trade-off of stateless sessions and it is the reason the
    TTL is short.
    """
    _attempts.pop(email, None)


def _record_failure(email: str) -> None:
    _attempts[email] = _attempts.get(email, 0) + 1
