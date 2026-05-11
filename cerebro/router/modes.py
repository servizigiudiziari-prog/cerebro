"""Execution modes selectable by the router.

Per brief §2.1 #4, Phase 0 supports exactly four modes. Adding more requires
an architectural review (and likely Phase ≥ 1 anyway).
"""

from __future__ import annotations

from enum import Enum


class ExecutionMode(str, Enum):
    """One of four ways the orchestrator can answer a query.

    Inherits from `str` so it round-trips through JSON and YAML configs
    without extra serialization glue.

    Members:
        DIRECT: query → trunk → output (no retrieval, no planning).
        RAG: query → retrieve(top_k) → trunk(query + context) → output.
        PLANNER_SOLVE: trunk(plan) → trunk(plan + query) → output.
        PLANNER_SOLVE_CRITIC: PLANNER_SOLVE + trunk(critic) loop, max 2 cycles.
    """

    DIRECT = "direct"
    RAG = "rag"
    PLANNER_SOLVE = "planner_solve"
    PLANNER_SOLVE_CRITIC = "planner_solve_critic"
