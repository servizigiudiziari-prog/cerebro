#!/usr/bin/env bash
# Phase 0 environment bootstrap: create venv via uv and install dependencies.
# Idempotent: safe to run multiple times.

set -euo pipefail

# Verify we are on macOS Apple Silicon (brief §4.2).
if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "ERROR: macOS required (brief §4.2). Detected: $(uname -s)" >&2
    exit 1
fi
if [[ "$(uname -m)" != "arm64" ]]; then
    echo "ERROR: Apple Silicon (arm64) required. Detected: $(uname -m)" >&2
    exit 1
fi

# Verify uv is installed.
if ! command -v uv >/dev/null 2>&1; then
    echo "ERROR: 'uv' not found. Install with: brew install uv" >&2
    exit 1
fi

# Resolve repo root regardless of where the script is invoked from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo ">>> Creating .venv with Python 3.12 (if absent)..."
uv venv --python 3.12 .venv

echo ">>> Installing dependencies (incl. dev + apple/mlx extras)..."
uv sync --extra dev --extra apple

echo ">>> Verifying mlx works on this machine..."
uv run python -c "import mlx.core as mx; a = mx.array([1.0, 2.0]); print('mlx OK,', a.sum().item())"

echo ">>> Done. Activate with: source .venv/bin/activate"
