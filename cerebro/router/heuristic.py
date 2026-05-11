"""Heuristic router that maps a query to one `ExecutionMode`.

Rules (brief §5.2):

    IF references_facts AND NOT has_code_blocks:        → RAG
    IF (has_code_blocks OR has_math)
       AND estimated_complexity > critic_threshold:     → PLANNER_SOLVE_CRITIC
    IF estimated_complexity > planner_solve_threshold:  → PLANNER_SOLVE
    ELSE:                                               → DIRECT

Every threshold lives in `cerebro.config.RouterConfig`, not here.
Implementation tracked by issue `[Phase 0] Heuristic router with feature extraction`.
"""

from __future__ import annotations

from cerebro.config import RouterConfig
from cerebro.router.features import QueryFeatures
from cerebro.router.modes import ExecutionMode


def route(features: QueryFeatures, config: RouterConfig) -> ExecutionMode:
    """Apply the heuristic routing rules.

    Args:
        features: structured features extracted from the query.
        config: thresholds used by the rules.

    Returns:
        The selected execution mode.

    Raises:
        NotImplementedError: implementation tracked by GitHub issue.
    """
    raise NotImplementedError(
        "routing rules not implemented yet (see GitHub issue: heuristic router)"
    )
