"""Structured result returned by the orchestrator for one query."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cerebro.memory.semantic import Chunk
from cerebro.router.modes import ExecutionMode


@dataclass(frozen=True)
class ExecutionResult:
    """Everything the caller needs from a single CEREBRO run.

    The orchestrator returns this object; CLI and benchmark suite consume
    it.  Adding fields is acceptable; removing fields breaks downstream
    code and requires a deprecation cycle.

    Routing fields (per docs/_brief/03-addendum-III.md §2.1):

        selected_mode: which `ExecutionMode` the router CHOSE before
            execution started, based purely on `QueryFeatures`.
        executed_mode: which `ExecutionMode` was ACTUALLY run after any
            runtime override (e.g. `low_confidence_retrieval` triggers
            the RAG→DIRECT fallback documented in addendum I §5).
        routing_override_reason: short identifier for why
            `selected_mode != executed_mode`, e.g.
            "low_confidence_retrieval". `None` if no override happened.

    All telemetry tables that report "mode distribution" must report
    BOTH selected and executed distributions, and flag rows where they
    differ — attributing to the router decisions the system overrode
    produces misleading statistics.

    Attributes:
        output: final natural-language answer.
        selected_mode: see routing fields above.
        executed_mode: see routing fields above.
        routing_override_reason: see routing fields above.
        latency_ms: wall-clock total from `ask()` entry to return.
        ttft_ms: time-to-first-token of the final generation. Measured
            internally to the trunk wrapper without exposing streaming
            to the caller (addendum III §2.3).
        tokens_generated: total tokens produced across all trunk calls.
        retrieved: chunks fetched by RAG, empty for non-RAG modes.
        critic_cycles: number of critic iterations actually run.
        critic_unresolved: True if the critic still flagged problems at
            the maximum number of cycles (addendum I §4).
        contradiction_signals: post-hoc signals registered for analysis
            in phase 2 (addendum I §9). Free-form dict; default fields:
            "unused_chunks", "unused_plan_steps", "critic_cycles".
        metadata: free-form bag for telemetry / debugging.
    """

    output: str
    selected_mode: ExecutionMode
    executed_mode: ExecutionMode
    latency_ms: float
    ttft_ms: float
    tokens_generated: int
    routing_override_reason: str | None = None
    retrieved: list[Chunk] = field(default_factory=list)
    critic_cycles: int = 0
    critic_unresolved: bool = False
    contradiction_signals: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def routing_was_overridden(self) -> bool:
        """True iff the router's selection was overridden at runtime."""
        return self.selected_mode != self.executed_mode

    @property
    def mode(self) -> ExecutionMode:
        """Back-compat alias for the executed mode.

        New code should use `selected_mode` or `executed_mode` explicitly.
        This alias exists to keep the bootstrap test suite working during
        the addendum-III alignment commit.
        """
        return self.executed_mode
