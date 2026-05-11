"""Generate the final Phase-0 report from benchmark output.

Usage:
    python scripts/run_phase0_report.py [--out results/phase0_report.md]

Implementation tracked by issue `[Phase 0] Documentation and reproducibility`.
"""

from __future__ import annotations

import argparse
import sys


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Return parsed CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Generate Phase-0 report from benchmark output.",
    )
    parser.add_argument(
        "--out",
        default="results/phase0_report.md",
        help="Output path for the report.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns an exit code (0 = success)."""
    args = parse_args(argv)
    raise NotImplementedError(f"run_phase0_report.py not implemented yet (out={args.out})")


if __name__ == "__main__":
    sys.exit(main())
