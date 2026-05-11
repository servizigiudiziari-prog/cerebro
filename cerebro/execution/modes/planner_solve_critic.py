"""PLANNER_SOLVE_CRITIC mode: planner-solve loop + critic, max 2 cycles."""

from __future__ import annotations

from cerebro.config import ExecutionConfig
from cerebro.execution.result import ExecutionResult
from cerebro.trunk.mlx_model import MlxTrunk


def run_planner_solve_critic(
    query: str,
    trunk: MlxTrunk,
    config: ExecutionConfig,
) -> ExecutionResult:
    """Execute the PLANNER_SOLVE_CRITIC mode end-to-end.

    Loops at most `config.critic_max_cycles` times (Phase 0 default: 2). Stops
    early when the critic emits `APPROVE`.

    Args:
        query: raw user query.
        trunk: loaded MLX trunk.
        config: execution-level limits (max cycles, planner tokens).

    Returns:
        `ExecutionResult` with `mode=PLANNER_SOLVE_CRITIC` and `critic_cycles`
        set to the number of iterations actually run.

    Raises:
        NotImplementedError: tracked by issue `[Phase 0] Four execution modes`.
    """
    raise NotImplementedError(
        "PLANNER_SOLVE_CRITIC mode not implemented yet (see GitHub issue: execution modes)"
    )
