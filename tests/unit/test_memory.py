"""Memory module surface test.

Real coverage lands with issue `[Phase 0] LanceDB semantic memory`.
"""

from __future__ import annotations

from cerebro.memory import embeddings, ingestion, semantic


def test_memory_public_surface() -> None:
    assert hasattr(embeddings, "LocalEmbedder")
    assert hasattr(semantic, "SemanticStore")
    assert hasattr(semantic, "Chunk")
    assert hasattr(ingestion, "IngestedDocument")
    assert hasattr(ingestion, "chunk_document")
    assert hasattr(ingestion, "ingest_corpus")
