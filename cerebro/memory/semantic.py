"""LanceDB-backed semantic store with a `retrieve()` API."""

from __future__ import annotations

from dataclasses import dataclass

from cerebro.config import MemoryConfig
from cerebro.memory.embeddings import LocalEmbedder


@dataclass(frozen=True)
class Chunk:
    """One retrieved chunk from the semantic store."""

    text: str
    score: float
    source_id: str
    source_title: str


class SemanticStore:
    """Read API over the LanceDB corpus indexed by `scripts/ingest_wikipedia.py`."""

    def __init__(self, config: MemoryConfig, embedder: LocalEmbedder) -> None:
        """Open the LanceDB table named `config.table_name`.

        Args:
            config: memory configuration with db path + table name.
            embedder: embedder used to vectorize queries at retrieve-time.

        Raises:
            NotImplementedError: tracked by issue `[Phase 0] LanceDB semantic memory`.
        """
        self.config = config
        self.embedder = embedder
        raise NotImplementedError(
            "SemanticStore opening not implemented yet (see GitHub issue: semantic memory)"
        )

    def retrieve(
        self,
        query: str,
        *,
        top_k: int | None = None,
        filters: dict[str, str] | None = None,
    ) -> list[Chunk]:
        """Retrieve the top-K most similar chunks for `query`.

        Args:
            query: natural-language query string.
            top_k: max chunks to return; falls back to `config.rag_top_k`.
            filters: optional metadata filters (e.g. `{"language": "it"}`).

        Returns:
            List of `Chunk`, ordered by descending score.

        Raises:
            NotImplementedError: tracked by issue `[Phase 0] LanceDB semantic memory`.
        """
        raise NotImplementedError(
            "retrieve() not implemented yet (see GitHub issue: semantic memory)"
        )
