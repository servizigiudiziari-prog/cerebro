"""macOS `powermetrics` wrapper for rough energy estimates.

`powermetrics` requires sudo on macOS, which makes CI integration awkward.
Phase 0 design: wrapper exposes a `measure(callable)` API that records
joules-per-token; if powermetrics is unavailable (no sudo, non-Mac), the
wrapper returns `None` for the energy field and the orchestrator carries
on without it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EnergySample:
    """Average power draw over a measured interval."""

    cpu_power_mw: float
    gpu_power_mw: float
    ane_power_mw: float
    duration_ms: float
    joules_total: float


def measure_powermetrics_supported() -> bool:
    """Return True if `powermetrics` is callable on this host.

    Phase 0 stub: hardware check + sudo capability check tracked by issue
    `[Phase 0] Telemetry and energy measurement`.

    Returns:
        Always False until the issue lands.
    """
    return False


def measure_window_ms(duration_ms: int) -> EnergySample | None:
    """Sample `powermetrics` for `duration_ms` and return averaged power.

    Args:
        duration_ms: sampling window length.

    Returns:
        `EnergySample`, or None if measurement is not available.

    Raises:
        NotImplementedError: tracked by issue `[Phase 0] Telemetry and energy`.
    """
    raise NotImplementedError(
        "powermetrics wrapper not implemented yet (see GitHub issue: telemetry)"
    )
