"""End-to-end integration test.

Skipped in bootstrap: requires Qwen2.5 weights + populated LanceDB. Will be
re-enabled when issue `[Phase 0] End-to-end integration and CLI` lands.
"""

from __future__ import annotations

import pytest


@pytest.mark.requires_model
@pytest.mark.requires_lancedb
@pytest.mark.slow
def test_ask_round_trip() -> None:
    pytest.skip("end-to-end harness not implemented yet (see GitHub issue)")
