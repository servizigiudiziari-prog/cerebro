"""Wrapper around a local sentence-transformers embedder.

Default model is `BAAI/bge-small-en-v1.5` (384 dim). The model is loaded
once and pinned in memory for the lifetime of the process.
"""

from __future__ import annotations

from collections.abc import Sequence

from cerebro.config import MemoryConfig


class LocalEmbedder:
    """Local CPU/MPS embedder for query and document vectors."""

    def __init__(self, config: MemoryConfig) -> None:
        """Load the embedding model named in `config.embedding_model_id`.

        Args:
            config: memory configuration including model id and dim.

        Raises:
            NotImplementedError: tracked by issue `[Phase 0] LanceDB semantic memory`.
        """
        self.config = config
        raise NotImplementedError(
            "LocalEmbedder loading not implemented yet (see GitHub issue: semantic memory)"
        )

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed a batch of texts.

        Args:
            texts: sequence of strings to embed.

        Returns:
            One vector per input, each of length `config.embedding_dim`.

        Raises:
            NotImplementedError: tracked by issue `[Phase 0] LanceDB semantic memory`.
        """
        raise NotImplementedError("embed() not implemented yet (see GitHub issue: semantic memory)")
