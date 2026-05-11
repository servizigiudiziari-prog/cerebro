"""Main `ask()` entry point: query → ExecutionResult.

The orchestrator is intentionally thin: it owns wiring (trunk, memory,
router, mode handlers) but no business logic. The interesting decisions
live in the mode implementations.
"""

from __future__ import annotations

from cerebro.config import CerebroConfig
from cerebro.execution.result import ExecutionResult
from cerebro.memory.semantic import SemanticStore
from cerebro.trunk.mlx_model import MlxTrunk


class Orchestrator:
    """Wires the trunk, memory, router, and mode handlers together."""

    def __init__(
        self,
        config: CerebroConfig,
        trunk: MlxTrunk,
        memory: SemanticStore,
    ) -> None:
        """Store collaborators. No side effects in `__init__`.

        Args:
            config: full CerebroConfig.
            trunk: loaded MLX trunk.
            memory: opened semantic store.
        """
        self.config = config
        self.trunk = trunk
        self.memory = memory

    def ask(self, query: str) -> ExecutionResult:
        """Answer a query end-to-end.

        Steps (tracked by issue `[Phase 0] Four execution modes`):
            1. extract features from `query`
            2. route to an `ExecutionMode`
            3. dispatch to the matching mode handler
            4. wrap the handler output in an `ExecutionResult`

        Args:
            query: raw user query.

        Returns:
            Populated `ExecutionResult`.

        Raises:
            NotImplementedError: tracked by GitHub issue.
        """
        raise NotImplementedError(
            "Orchestrator.ask() not implemented yet (see GitHub issue: execution modes)"
        )
