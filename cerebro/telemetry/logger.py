"""Structured logging configuration via `structlog`.

Per brief §4.3: no `print()` outside CLI/scripts; all events go through a
structured logger emitting one JSON object per line on stderr (and,
optionally, also to a file in `results/runs.jsonl`).
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog


def configure_logging(*, level: str = "INFO", json: bool = True) -> None:
    """Configure structlog + stdlib logging to a single JSON-line stream.

    Args:
        level: log level name (e.g. "DEBUG", "INFO"). Defaults to "INFO".
        json: emit JSON lines (production); set False for human-readable
            console output during local development.
    """
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=getattr(logging, level.upper(), logging.INFO),
    )

    renderers: list[Any]
    if json:
        renderers = [structlog.processors.JSONRenderer()]
    else:
        renderers = [structlog.dev.ConsoleRenderer(colors=True)]

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            *renderers,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a structlog bound logger.

    Args:
        name: optional logger name; included as a `logger=` field if set.

    Returns:
        Bound logger ready for `.info()`, `.warning()`, etc.
    """
    log = structlog.get_logger()
    if name:
        log = log.bind(logger=name)
    return log
