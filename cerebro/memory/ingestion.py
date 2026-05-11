"""Helpers to ingest a corpus into the LanceDB semantic store.

Wikipedia IT subset (100k articles) is the Phase 0 default; see
`scripts/ingest_wikipedia.py` for the CLI driver.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class IngestedDocument:
    """One source document before chunking."""

    source_id: str
    title: str
    text: str
    language: str


def chunk_document(doc: IngestedDocument, *, target_tokens: int = 256) -> list[str]:
    """Split a document into ~`target_tokens`-sized chunks.

    Strategy is paragraph-aware with hard-cap fallback. Implementation
    tracked by issue `[Phase 0] LanceDB semantic memory`.

    Args:
        doc: source document.
        target_tokens: soft target chunk size in whitespace-tokens.

    Returns:
        List of chunk texts (non-overlapping in Phase 0).

    Raises:
        NotImplementedError: tracked by GitHub issue.
    """
    raise NotImplementedError(
        "chunk_document() not implemented yet (see GitHub issue: semantic memory)"
    )


def ingest_corpus(docs: Iterable[IngestedDocument]) -> int:
    """Embed + write a stream of documents to LanceDB.

    Args:
        docs: iterable of source documents.

    Returns:
        Number of chunks written.

    Raises:
        NotImplementedError: tracked by GitHub issue.
    """
    raise NotImplementedError(
        "ingest_corpus() not implemented yet (see GitHub issue: semantic memory)"
    )
