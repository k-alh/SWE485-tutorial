# The lab queries

Six queries. One control, five engineered failures. Each names the mode it
triggers, the mechanism, and what a correct diagnosis sounds like.

> **Instructor copy.** Students get the queries in the notebook without the
> right-hand analysis. Keep this file out of the student fork, or accept that
> the diagnosis is being read rather than made.

---

## Q0 — control

> *How does login work?*

**Expect:** `auth/login.py` first by a wide margin; billing chunks far behind.

This is the section 3 worked trace, reproduced at 768 dimensions. Students
hand-computed cos ≈ 0.99 for auth and ≈ 0.44 for billing on toy 2-D vectors. The
absolute numbers here will differ — real embeddings are less extreme — but the
*ordering* and the size of the gap are the point. If Q0 does not rank auth over
billing cleanly, something is wrong with the setup, not with the lesson.

---

## Q1 — mode 1, bad chunking

> *How is the token signature verified?*

**Mechanism.** At 500 tokens / 50 overlap, `auth/tokens.py` splits into
`#L1-L68` and `#L61-L95`. `validate_token()` spans L43–L82, so the cut lands
*inside it*, at line 68 — between the expiry check (L64–67) and the signature
verification (L69–78).

Chunk 1 gets the function signature, the docstring, the imports and the expiry
check. Chunk 2 gets the HMAC comparison, orphaned from the `hmac` and `hashlib`
imports and from `TOKEN_SIGNING_KEY`, and opening mid-function.

This is the failure trace from section 4, made real rather than described.

**Correct diagnosis:** retrieval fault. Fix: AST-aware chunking (Part D ships a
working one — it puts `validate_token` in a single chunk, `#L43-L80`). Larger
overlap is a partial mitigation, not a fix.

**Watch for:** a student who says "the model didn't understand the code." It
understood the fragment it was given perfectly well.

---

## Q2 — mode 2, missed context

> *How does the second factor get checked?*

**Mechanism.** `auth/mfa.py` is listed in `.ragignore` and is never indexed. The
comment in that file dates the exclusion to a security review that was never
revisited — which is how this happens in practice.

**Expect:** top-k full of confident, irrelevant auth chunks. With the escape
hatch the model says `NOT IN CONTEXT`; without it, it invents a plausible MFA
flow.

**Correct diagnosis:** retrieval fault, and specifically one that no amount of
re-prompting can touch — the chunk does not exist in the index. Fix: remove the
exclusion and re-index.

**Watch for:** the student who reaches for `@file` before checking `.ragignore`.
Ask them how they would have known which file to `@`.

---

## Q3 — mode 3, stale source

> *How long does a session token last?*

**Mechanism.** Three sources disagree. `docs/README.md` says 24 hours,
`config/settings.py` says `TOKEN_TTL_SECONDS = 3600`, and
`docs/ADR-002-token-expiry.md` records the change and states plainly that the
README was not updated.

**The sharp question.** Is this a stale *index* or a stale *source*? It is a
stale **source**: the index is perfectly current, and faithfully retrieved a
document that is wrong. Re-indexing would change nothing.

This is the most valuable query in the set, because it is the one where the
correct answer is *not* "re-index." A student who reflexively says stale index
has pattern-matched the mode name without reading the evidence — push back once
and see whether they recover.

**Correct diagnosis:** retrieval worked; the corpus lied. Fix: fix the README,
or scope retrieval to authoritative sources. Note the general lesson: RAG
inherits the truthfulness of what you indexed.

---

## Q4 — mode 4, wrong retrieval

> *What happens when a charge fails?*

**Mechanism.** `billing/refund.py` is dense with *failed*, *declined*,
*disputed*, *failure* — it even contains a `classify_failure()` function. The
actual retry-and-lapse logic in `billing/charges.py` speaks a different dialect:
*settle*, *attempt*, *backoff*, *idempotent*. Lexical and semantic overlap pulls
the wrong file up.

**The thing to look at is the margin.** This one fails by a small gap, not a
large one, which is exactly the profile a re-ranker exists to fix. Have students
read the printed `margin between rank 1 and rank 2` out loud.

**Correct diagnosis:** retrieval fault, near-miss. Fix: a cross-encoder
re-ranker, or a narrower query. A larger `k` pulls the right chunk into context
but leaves it ranked below a distractor — it buries the problem rather than
solving it.

**⚠ Verify this one with a live key before the session.** Q1, Q2, Q3 and Q5 are
structural and cannot fail. Q4 depends on how the embedding model actually
scores two similar files, and it is the one query that may need its wording
adjusted after the first end-to-end run. If `charges.py` already wins, sharpen
the distractor vocabulary in `refund.py` rather than weakening `charges.py`.

---

## Q5 — mode 5, needle in a haystack

> *What happens to a user's active session when their subscription lapses
> mid-cycle?*

**Mechanism.** The answer requires three facts from three files:

1. `billing/charges.py` — `_enter_past_due()` sets the status field and
   explicitly does **not** touch sessions.
2. `auth/login.py` — `logout()` documents that tokens are stateless and cannot
   be revoked; login deliberately ignores billing status.
3. `config/settings.py` — `TOKEN_TTL_SECONDS = 3600`.

**The correct answer:** the user keeps working access for up to one hour after
the subscription lapses, because nothing revokes the token and it simply ages
out. `docs/ADR-002-token-expiry.md` states this consequence outright, which is
why a decomposed query finds it and a single broad query usually does not.

**Correct diagnosis:** a retrieval fault that a bigger context window does not
fix — the classic argument against "just use long context." Fix: decompose into
three grounded sub-questions and compose the answers.

**Watch for:** an answer that is confident about the hour but silent about *why*
the session survives. That student found `settings.py` and stopped.

---

## Summary

| Query | Mode | Fault | Fix | Robustness |
|---|---|---|---|---|
| Q0 | control | — | — | structural |
| Q1 | 1 bad chunking | retrieval | AST-aware chunking | structural |
| Q2 | 2 missed context | retrieval | un-ignore, re-index | structural |
| Q3 | 3 stale source | corpus | fix the source | structural |
| Q4 | 4 wrong retrieval | retrieval | re-rank / narrow | **verify with a live key** |
| Q5 | 5 needle | retrieval | decompose | structural |
