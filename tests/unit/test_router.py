"""Router tests.

Real coverage lands with issue `[Phase 0] Heuristic router with feature extraction`.
This file pins the public surface so renames break loudly.
"""

from __future__ import annotations

import inspect

from cerebro.router import features, heuristic, modes


def test_public_surface_router() -> None:
    assert hasattr(modes, "ExecutionMode")
    assert hasattr(features, "QueryFeatures")
    assert hasattr(features, "extract_features")
    assert hasattr(heuristic, "route")


def test_extract_features_signature() -> None:
    sig = inspect.signature(features.extract_features)
    assert list(sig.parameters) == ["query"]


def test_route_signature() -> None:
    sig = inspect.signature(heuristic.route)
    assert list(sig.parameters) == ["features", "config"]
