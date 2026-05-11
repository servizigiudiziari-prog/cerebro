"""Mode handler tests.

Real coverage lands with issue `[Phase 0] Four execution modes`.
"""

from __future__ import annotations

from cerebro.execution.modes import direct, planner_solve, planner_solve_critic, rag


def test_mode_handlers_exist() -> None:
    assert callable(direct.run_direct)
    assert callable(rag.run_rag)
    assert callable(planner_solve.run_planner_solve)
    assert callable(planner_solve_critic.run_planner_solve_critic)
