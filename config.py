"""Pinned configuration for the SWE 485 Week 5 RAG lab.

Everything in this file is perishable. It is collected here so that the annual
refresh described in PERISHABLE_FIGURES.md is a one-file edit rather than a
hunt through two notebooks.
"""

# --- Models ---------------------------------------------------------------
# gemini-embedding-001 is chosen deliberately over gemini-embedding-2:
#   * it accepts the explicit `task_type` field, which is easier to see and to
#     grade than the prompt-instruction format the newer model requires;
#   * it returns UN-NORMALIZED vectors below 3072 dimensions, which forces the
#     normalization step the study material's section 3 asks about.
# If -001 is retired, switch to gemini-embedding-2 and rewrite prepare_query()
# and prepare_document() below to use the prompt-instruction format. See
# https://ai.google.dev/gemini-api/docs/embeddings

EMBED_MODEL = "gemini-embedding-001"
CHAT_MODEL = "gemini-3.6-flash"

EMBED_DIM = 768                      # 3072 is the default; 768/1536/3072 advised
NEEDS_MANUAL_NORMALIZATION = True    # True for -001 below 3072; False for -2

DOC_TASK_TYPE = "RETRIEVAL_DOCUMENT"
QUERY_TASK_TYPE = "CODE_RETRIEVAL_QUERY"   # try "RETRIEVAL_QUERY" and compare

# --- Retrieval ------------------------------------------------------------

K = 4
CHUNK_TOKENS = 500
OVERLAP_TOKENS = 50

# --- Corpus ---------------------------------------------------------------

CORPUS_DIR = "minibank"
INDEXABLE_SUFFIXES = (".py", ".md")

# --- Offline mode ---------------------------------------------------------
# True loads embeddings.npz instead of calling the embedding API. Chunking,
# scoring, ranking and every Part B failure still run. Only generation needs
# the network. Set this before an assessed demo on an unreliable connection.

OFFLINE = False


# --- Task-type seam -------------------------------------------------------
# These are pass-throughs for gemini-embedding-001, which carries the task in
# a field rather than in the text. They exist so that a migration to
# gemini-embedding-2 is a two-function edit rather than a rewrite.

def prepare_document(content: str, title: str = "none") -> str:
    # gemini-embedding-2 would need: f"title: {title} | text: {content}"
    return content


def prepare_query(query: str) -> str:
    # gemini-embedding-2 would need: f"task: code retrieval | query: {query}"
    return query
