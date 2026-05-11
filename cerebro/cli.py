"""Command-line entry point for CEREBRO.

Usage:
    cerebro ask "domanda"

Output is a JSON object printed to stdout containing the answer plus
metadata (mode, latency, tokens, retrieved chunk count, critic cycles).
"""

from __future__ import annotations

import json
import sys
from typing import NoReturn

import typer

from cerebro import __version__

app = typer.Typer(
    help="CEREBRO Phase 0 — heuristic-routed orchestration of a local MLX LLM.",
    no_args_is_help=True,
    add_completion=False,
)


@app.command()
def ask(
    query: str = typer.Argument(..., help="Question to answer."),
    json_output: bool = typer.Option(
        True, "--json/--text", help="Emit a JSON envelope (default) or plain text."
    ),
) -> None:
    """Run one query end-to-end and print the answer plus metadata."""
    # Wired up by the orchestrator issue. For bootstrap we fail loudly so the
    # user never thinks "no output" means "success".
    raise typer.Exit(
        code=_die(
            "cerebro.ask is not wired yet: see GitHub issue "
            "`[Phase 0] End-to-end integration and CLI`. "
            f"Stub returned for query={query!r}, json_output={json_output}."
        )
    )


@app.command()
def version() -> None:
    """Print the package version and exit."""
    typer.echo(json.dumps({"name": "cerebro", "version": __version__}))


def _die(msg: str) -> int:
    typer.echo(msg, err=True)
    return 1


def main() -> NoReturn:
    """Entry point referenced by `[project.scripts]` in pyproject.toml."""
    app()
    sys.exit(0)


if __name__ == "__main__":
    main()
