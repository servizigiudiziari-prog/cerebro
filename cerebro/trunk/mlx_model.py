"""Thin wrapper around mlx-lm exposing a stable `generate()` API.

Goal: the rest of the codebase never imports `mlx_lm` directly. Swapping
model backends in later phases (sparse upcycling, LoRA-adapted variants) is
a one-file change here.
"""

from __future__ import annotations

from dataclasses import dataclass

from cerebro.config import TrunkConfig


@dataclass
class GenerationResult:
    """Output of a single trunk generation."""

    text: str
    tokens_generated: int
    ttft_ms: float
    throughput_tok_per_s: float


class MlxTrunk:
    """Local Qwen2.5-1.5B-Instruct trunk loaded once at process start."""

    def __init__(self, config: TrunkConfig) -> None:
        """Load the MLX model + tokenizer described by `config`.

        Args:
            config: trunk configuration (model id, quantization, decoding).

        Raises:
            NotImplementedError: tracked by issue `[Phase 0] Trunk MLX`.
        """
        self.config = config
        raise NotImplementedError(
            "MLX trunk loading not implemented yet (see GitHub issue: trunk integration)"
        )

    def generate(
        self,
        prompt: str,
        *,
        max_tokens: int | None = None,
    ) -> GenerationResult:
        """Run a single decode pass.

        Args:
            prompt: full prompt text (already formatted with chat template).
            max_tokens: hard cap on emitted tokens; falls back to config.

        Returns:
            `GenerationResult` with text and timing metadata.

        Raises:
            NotImplementedError: tracked by issue `[Phase 0] Trunk MLX`.
        """
        raise NotImplementedError(
            "generate() not implemented yet (see GitHub issue: trunk integration)"
        )
