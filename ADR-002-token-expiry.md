# ADR-002 — Shorten the session token TTL from 24 hours to 1 hour

- **Status:** Accepted
- **Date:** 2026-02-11
- **Supersedes:** the 24-hour TTL described in the README
- **Related:** `config/settings.py` (`TOKEN_TTL_SECONDS`), `auth/tokens.py`

## Context

Session tokens are stateless. They are signed and self-describing, and the
server keeps no record of which tokens it has issued. That buys us a service
that scales horizontally with no shared session store, and it costs us the
ability to revoke an individual token. Once a token is out, it is valid until
it ages out.

The consequence had been under-appreciated. With a 24-hour TTL, a token stolen
from a client — or simply left behind on a shared machine — remained usable for
up to a full day, and nothing in the system could stop it. Logging out did not
help; `auth.login.logout()` clears the failed-attempt counter and nothing else.

The same property has a billing consequence. When a subscription lapses,
`billing.charges._enter_past_due()` changes the account's status field and does
not touch sessions, because there are no sessions to touch. A user whose
subscription lapsed mid-cycle therefore kept full access for whatever remained
of their token's lifetime.

## Decision

Reduce `TOKEN_TTL_SECONDS` from `86400` to `3600`.

Expiry is derived at validation time from the configured TTL rather than being
stamped into the token at issue time. This means the change takes effect
immediately for tokens already in circulation, rather than only for tokens
issued after the deploy. `auth.tokens.validate_token()` computes the token's
age from its `iat` claim and compares it against the current TTL.

## Consequences

- The exposure window for a leaked token drops from 24 hours to 1 hour.
- The exposure window for a lapsed subscription drops correspondingly: a
  past-due account retains working access for at most one hour, not one day.
- Users on long sessions re-authenticate more often. Accepted.
- **The README was not updated and still states 24 hours.** Recorded here
  deliberately.
