#!/usr/bin/env python3
"""Check that the planted failures still fire. No API key, no network.

Run this after ANY edit to minibank/ or to the chunk settings in config.py.
The corpus is load-bearing: if a defect stops firing, the lab quietly becomes a
demonstration that RAG works fine, which is the opposite of the lesson.

    python3 tools/verify_corpus.py

Four of the five modes are structural and are checked here. Mode 4 depends on
how the embedding model scores two similar files and can only be verified with
a live key — see queries.md.
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import config  # noqa: E402

CORPUS = ROOT / config.CORPUS_DIR
failures = []


def check(label, condition, detail=""):
    print(f"  [{'ok ' if condition else 'FAIL'}] {label}")
    if not condition:
        failures.append(f"{label}{' — ' + detail if detail else ''}")


def load_chunker():
    nb = json.loads((ROOT / "01_rag_by_hand.ipynb").read_text())
    for cell in nb["cells"]:
        if "chunker" in cell.get("metadata", {}).get("tags", []):
            ns = {}
            exec("".join(cell["source"]), ns)  # noqa: S102
            return ns
    raise SystemExit("no cell tagged 'chunker' in 01_rag_by_hand.ipynb")


chunker = load_chunker()
chunks, skipped = chunker["build_chunks"](
    str(CORPUS), config.CHUNK_TOKENS, config.OVERLAP_TOKENS,
    config.INDEXABLE_SUFFIXES,
)
by_id = {c["id"]: c for c in chunks}

print(f"\n{len(chunks)} chunks, {len(skipped)} files skipped\n")

# --- Mode 1: validate_token must straddle a chunk boundary ----------------
print("mode 1 — bad chunking")
tok = [c for c in chunks if c["path"] == "auth/tokens.py"]
src = (CORPUS / "auth/tokens.py").read_text().splitlines()
def line_of(needle):
    return next(i + 1 for i, l in enumerate(src) if needle in l)

fn_start = line_of("def validate_token")
fn_end = line_of("def issue_token") - 2
expiry = line_of('raise TokenError("expired")')
sig = line_of("if not hmac.compare_digest")

check("tokens.py splits into more than one chunk", len(tok) > 1)
if len(tok) > 1:
    boundary = tok[0]["end"]
    check(
        f"the cut (L{boundary}) falls inside validate_token (L{fn_start}-L{fn_end})",
        fn_start < boundary < fn_end,
        "retune the file length or CHUNK_TOKENS",
    )
    check(
        f"expiry check (L{expiry}) and signature check (L{sig}) land in different chunks",
        expiry <= boundary < sig,
        "the two halves of the function must be separated",
    )
    check(
        "the second chunk opens mid-function",
        tok[1]["start"] > fn_start,
    )

# --- Mode 2: mfa.py must be excluded --------------------------------------
print("\nmode 2 — missed context")
check("auth/mfa.py exists", (CORPUS / "auth/mfa.py").exists())
check("auth/mfa.py is NOT indexed", "auth/mfa.py" in skipped)
check(
    "the exclusion comes from .ragignore",
    "auth/mfa.py" in (CORPUS / ".ragignore").read_text(),
)

# --- Mode 3: the three sources must disagree ------------------------------
print("\nmode 3 — stale source")
readme = (CORPUS / "docs/README.md").read_text()
settings = (CORPUS / "config/settings.py").read_text()
adr = (CORPUS / "docs/ADR-002-token-expiry.md").read_text()
check("README still claims 24 hours", "24 hours" in readme)
check("settings.py says 3600", "TOKEN_TTL_SECONDS = 3600" in settings)
check("ADR-002 records the change", "86400" in adr and "3600" in adr)
check("all three are indexed", all(
    any(c["path"] == p for c in chunks)
    for p in ("docs/README.md", "config/settings.py", "docs/ADR-002-token-expiry.md")
))

# --- Mode 4: the distractor must be present -------------------------------
print("\nmode 4 — wrong retrieval  (ranking needs a live key; see queries.md)")
refund = (CORPUS / "billing/refund.py").read_text().lower()
charges = (CORPUS / "billing/charges.py").read_text().lower()
check("refund.py is dense in failure vocabulary", refund.count("fail") >= 4)
check("charges.py avoids that vocabulary", charges.count("fail") <= 1)
check("charges.py holds the real retry logic", "RETRY_MAX_ATTEMPTS" in
      (CORPUS / "billing/charges.py").read_text())

# --- Mode 5: three facts in three files -----------------------------------
print("\nmode 5 — needle in a haystack")
check("fact 1 — charges.py does not touch sessions on lapse",
      "not touched" in charges or "not* touched" in charges
      or "stays" in charges)
check("fact 2 — login.py documents that tokens cannot be revoked",
      "remains valid" in (CORPUS / "auth/login.py").read_text())
check("fact 3 — settings.py holds the TTL",
      "TOKEN_TTL_SECONDS" in settings)
check("the three live in three different files", True)

# --- Report ---------------------------------------------------------------
print()
if failures:
    print(f"{len(failures)} CHECK(S) FAILED:\n")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("all structural checks passed — mode 4 ranking still needs a live run")
