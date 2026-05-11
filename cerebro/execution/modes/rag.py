"""RAG mode: query → retrieve(top_k) → trunk(query + context) → output."""

from __future__ import annotations

from cerebro.execution.result import ExecutionResult
from cerebro.memory.semantic import SemanticStore
from cerebro.trunk.mlx_model import MlxTrunk


def run_rag(query: str, trunk: MlxTrunk, memory: SemanticStore) -> ExecutionResult:
    """Execute the RAG mode end-to-end.

    Args:
        query: raw user query.
        trunk: loaded MLX trunk.
        memory: opened semantic store.

    Returns:
        `ExecutionResult` with `mode=RAG` and `retrieved` populated.

    Raises:
        NotImplementedError: tracked by issue `[Phase 0] Four execution modes`.
    """
    raise NotImplementedError("RAG mode not implemented yet (see GitHub issue: execution modes)")
