#!/usr/bin/env python3
"""Regenerate embeddings.npz — the offline fallback for the Week 5 lab.

Run this once at build time, and again whenever the corpus, the chunk settings
or EMBED_MODEL change. If you do not, the offline path silently diverges from
the online one and two teams get different score tables from the same corpus.

    export GEMINI_API_KEY=...
    python3 tools/build_embeddings.py

The chunker is not reimplemented here. It is extracted from
01_rag_by_hand.ipynb, so there is exactly one definition of chunking in this
repository and it is the one the students read.
"""

import json
import os
import pathlib
import sys

import numpy as np
from google import genai
from google.genai import types

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import config  # noqa: E402


def load_chunker():
    """Exec the cell tagged `chunker` from the student notebook."""
    nb = json.loads((ROOT / "01_rag_by_hand.ipynb").read_text())
    for cell in nb["cells"]:
        if "chunker" in cell.get("metadata", {}).get("tags", []):
            namespace = {}
            exec("".join(cell["source"]), namespace)  # noqa: S102
            return namespace
    raise SystemExit("no cell tagged 'chunker' in 01_rag_by_hand.ipynb")


def main():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("set GEMINI_API_KEY first")

    chunker = load_chunker()
    chunks, skipped = chunker["build_chunks"](
        str(ROOT / config.CORPUS_DIR),
        config.CHUNK_TOKENS,
        config.OVERLAP_TOKENS,
        config.INDEXABLE_SUFFIXES,
    )
    print(f"{len(chunks)} chunks, {len(skipped)} files skipped")

    client = genai.Client(api_key=key)
    result = client.models.embed_content(
        model=config.EMBED_MODEL,
        contents=[config.prepare_document(c["text"]) for c in chunks],
        config=types.EmbedContentConfig(
            task_type=config.DOC_TASK_TYPE,
            output_dimensionality=config.EMBED_DIM,
        ),
    )

    vectors = np.stack([
        np.asarray(e.values, dtype=np.float32)
        / np.linalg.norm(np.asarray(e.values, dtype=np.float32))
        for e in result.embeddings
    ])

    out = ROOT / "embeddings.npz"
    np.savez(
        out,
        vectors=vectors,
        ids=np.array([c["id"] for c in chunks]),
        model=config.EMBED_MODEL,
        dim=config.EMBED_DIM,
        chunk_tokens=config.CHUNK_TOKENS,
        overlap_tokens=config.OVERLAP_TOKENS,
    )
    print(f"wrote {out} — {vectors.shape}, model={config.EMBED_MODEL}")


if __name__ == "__main__":
    main()
