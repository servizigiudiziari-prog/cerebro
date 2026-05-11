"""PLANNER_SOLVE mode: trunk(plan) → trunk(plan + query) → output."""

from __future__ import annotations

from cerebro.execution.result import ExecutionResult
from cerebro.trunk.mlx_model import MlxTrunk


def run_planner_solve(query: str, trunk: MlxTrunk) -> ExecutionResult:
    """Execute the PLANNER_SOLVE mode end-to-end.

    Args:
        query: raw user query.
        trunk: loaded MLX trunk.

    Returns:
        `ExecutionResult` with `mode=PLANNER_SOLVE`.

    Raises:
        NotImplementedError: tracked by issue `[Phase 0] Four execution modes`.
    """
    raise NotImplementedError(
        "PLANNER_SOLVE mode not implemented yet (see GitHub issue: execution modes)"
    )
