"""Populate LanceDB with a 100k-article subset of Wikipedia IT.

Usage:
    python scripts/ingest_wikipedia.py [--limit N] [--lang it]

Implementation tracked by issue `[Phase 0] LanceDB semantic memory`.
"""

from __future__ import annotations

import argparse
import sys


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Return parsed CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Ingest a Wikipedia subset into LanceDB.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100_000,
        help="Number of articles to ingest (default: 100000).",
    )
    parser.add_argument(
        "--lang",
        default="it",
        help="Wikipedia language code (default: it).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns an exit code (0 = success)."""
    args = parse_args(argv)
    raise NotImplementedError(
        f"ingest_wikipedia.py not implemented yet (limit={args.limit}, lang={args.lang})"
    )


if __name__ == "__main__":
    sys.exit(main())
