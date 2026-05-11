"""Download and (if needed) convert the Qwen2.5-1.5B-Instruct trunk to MLX format.

Usage:
    python scripts/download_models.py [--force]

Implementation tracked by issue `[Phase 0] Trunk MLX integration`.
"""

from __future__ import annotations

import argparse
import sys


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Return parsed CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Download Qwen2.5-1.5B-Instruct and convert to MLX 4-bit.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if the local cache already has the model.",
    )
    parser.add_argument(
        "--target-dir",
        default="models/qwen2.5-1.5b-instruct-mlx-q4",
        help="Where to place the converted MLX weights.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns an exit code (0 = success)."""
    args = parse_args(argv)
    raise NotImplementedError(
        f"download_models.py not implemented yet (target={args.target_dir}, force={args.force})"
    )


if __name__ == "__main__":
    sys.exit(main())
