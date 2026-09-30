# minibank

A very small account service: authentication on one side, subscription billing
on the other.

> **A note for the SWE 485 lab.** Parts of this README are **wrong on purpose**,
> in the way real READMEs go wrong — they were true once. Do not fix them. They
> are the corpus for failure mode 3.

## Sessions

Logging in returns a session token. The token is stateless: it is signed, but
it is not stored server side, so there is no session table to look a token up
in.

**Session tokens expire after 24 hours.** After that the user must log in
again. Because tokens are not tracked, logging out does not invalidate a token
that has already been handed out — it simply stops the client presenting it.

## Billing

Each account is charged once per billing cycle. If the payment processor does
not settle the charge, the service retries a small number of times and then
marks the account past due.

## Layout

| Package | What lives there |
|---|---|
| `auth/` | Login, password hashing, session tokens, second factor |
| `billing/` | Charges, retries, refunds, invoices |
| `config/` | Every runtime tunable, on one page |
| `docs/` | This file and the architecture decision records |
