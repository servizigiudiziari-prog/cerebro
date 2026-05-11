"""Driver that runs every benchmark in every configuration.

Per brief §2.1 #6, for each benchmark we run four configurations:
    - baseline 1: DIRECT always
    - baseline 2: RAG always
    - baseline 3: PLANNER_SOLVE_CRITIC always
    - candidate:  heuristic router decides

Implementation tracked by issue `[Phase 0] Benchmark suite`.
"""

from __future__ import annotations


def main() -> int:
    """Run every benchmark in every configuration."""
    raise NotImplementedError("run_all not implemented yet")


if __name__ == "__main__":
    raise SystemExit(main())
