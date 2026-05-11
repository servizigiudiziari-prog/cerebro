"""Latency / throughput measurement primitives."""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator


@dataclass
class TimingSample:
    """One stopwatch sample with named label."""

    label: str
    wall_ms: float


@contextmanager
def stopwatch(label: str) -> Iterator[TimingSample]:
    """Context manager that records elapsed wall time in ms.

    Usage:
        with stopwatch("trunk.generate") as s:
            ...
        print(s.wall_ms)

    Args:
        label: human-readable name for the timed region.

    Yields:
        `TimingSample` whose `wall_ms` field is populated on exit.
    """
    sample = TimingSample(label=label, wall_ms=0.0)
    start = time.perf_counter()
    try:
        yield sample
    finally:
        sample.wall_ms = (time.perf_counter() - start) * 1000.0


def percentile(values: list[float], p: float) -> float:
    """Pure-Python percentile (linear interpolation).

    Args:
        values: list of samples, sorted or unsorted.
        p: percentile in [0, 100].

    Returns:
        Interpolated percentile value. Empty input returns 0.0.
    """
    if not values:
        return 0.0
    if not 0 <= p <= 100:
        raise ValueError(f"percentile {p} out of range [0, 100]")
    s = sorted(values)
    k = (len(s) - 1) * (p / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    frac = k - lo
    return s[lo] * (1 - frac) + s[hi] * frac
