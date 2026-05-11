"""Structured result returned by the orchestrator for one query."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cerebro.memory.semantic import Chunk
from cerebro.router.modes import ExecutionMode


@dataclass(frozen=True)
class ExecutionResult:
    """Everything the caller needs from a single CEREBRO run.

    The orchestrator returns this object; CLI and benchmark suite consume it.
    Adding fields is acceptable; removing fields breaks downstream code and
    requires a deprecation cycle.

    Attributes:
        output: final natural-language answer.
        mode: which `ExecutionMode` the router selected.
        latency_ms: wall-clock total from `ask()` entry to return.
        ttft_ms: time-to-first-token of the final generation.
        tokens_generated: total tokens produced across all trunk calls.
        retrieved: chunks fetched by RAG, empty for non-RAG modes.
        critic_cycles: number of critic iterations actually run.
        metadata: free-form bag for telemetry / debugging.
    """

    output: str
    mode: ExecutionMode
    latency_ms: float
    ttft_ms: float
    tokens_generated: int
    retrieved: list[Chunk] = field(default_factory=list)
    critic_cycles: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
