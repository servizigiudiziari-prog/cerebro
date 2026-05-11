"""DIRECT mode: query → trunk → output. No retrieval, no planning."""

from __future__ import annotations

from cerebro.execution.result import ExecutionResult
from cerebro.trunk.mlx_model import MlxTrunk


def run_direct(query: str, trunk: MlxTrunk) -> ExecutionResult:
    """Execute the DIRECT mode end-to-end.

    Args:
        query: raw user query.
        trunk: loaded MLX trunk.

    Returns:
        `ExecutionResult` with `mode=DIRECT` and `retrieved=[]`.

    Raises:
        NotImplementedError: tracked by issue `[Phase 0] Four execution modes`.
    """
    raise NotImplementedError("DIRECT mode not implemented yet (see GitHub issue: execution modes)")
