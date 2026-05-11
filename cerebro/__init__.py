"""CEREBRO — Phase 0 modular orchestration of a local MLX LLM.

This package implements the Phase 0 spec from `CEREBRO-Brief-Claude-Code.md`:
a heuristic router on top of Qwen2.5-1.5B (MLX, 4-bit) selecting one of four
execution modes (DIRECT, RAG, PLANNER_SOLVE, PLANNER_SOLVE_CRITIC). No training.
"""

__version__ = "0.0.1"
