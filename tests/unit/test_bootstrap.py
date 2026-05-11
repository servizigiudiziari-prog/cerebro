"""Bootstrap-level tests: things that must hold true even with no logic wired yet.

These are *not* the real coverage of router/memory/modes — those will land
with their respective issues. They exist so that `pytest` returns 0 on a
fresh clone and CI has something green to verify.
"""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from cerebro import __version__
from cerebro.config import DEFAULT_CONFIG, CerebroConfig
from cerebro.execution.result import ExecutionResult
from cerebro.router.modes import ExecutionMode
from cerebro.telemetry.metrics import percentile, stopwatch


def test_version_string() -> None:
    assert isinstance(__version__, str)
    assert __version__.count(".") == 2


def test_default_config_is_immutable() -> None:
    # @dataclass(frozen=True) on every sub-config
    with pytest.raises(FrozenInstanceError):
        DEFAULT_CONFIG.trunk.max_tokens = 9999  # type: ignore[misc]


def test_default_config_round_trip_types() -> None:
    cfg = CerebroConfig()
    assert cfg.trunk.hf_model_id.startswith("Qwen/Qwen2.5")
    assert cfg.router.complexity_planner_solve_threshold > cfg.router.complexity_critic_threshold
    assert cfg.memory.rag_top_k > 0
    assert cfg.execution.critic_max_cycles == 2  # brief §2.1 #4: max 2 cycles


def test_execution_mode_values() -> None:
    # exactly four modes per brief §2.1 #4
    assert len(ExecutionMode) == 4
    assert {m.value for m in ExecutionMode} == {
        "direct",
        "rag",
        "planner_solve",
        "planner_solve_critic",
    }


def test_execution_mode_is_str_enum() -> None:
    # round-trip through JSON for telemetry / benchmark logs
    encoded = json.dumps({"mode": ExecutionMode.RAG})
    assert "rag" in encoded


def test_execution_result_dataclass() -> None:
    r = ExecutionResult(
        output="ok",
        mode=ExecutionMode.DIRECT,
        latency_ms=1.0,
        ttft_ms=0.5,
        tokens_generated=3,
    )
    assert r.retrieved == []
    assert r.critic_cycles == 0
    assert r.metadata == {}


def test_stopwatch_measures_elapsed() -> None:
    with stopwatch("noop") as s:
        pass
    assert s.label == "noop"
    assert s.wall_ms >= 0.0


def test_percentile_basic() -> None:
    assert percentile([1.0, 2.0, 3.0, 4.0], 50) == pytest.approx(2.5)
    assert percentile([], 50) == 0.0
    assert percentile([10.0], 90) == 10.0


def test_percentile_rejects_out_of_range() -> None:
    with pytest.raises(ValueError):
        percentile([1.0, 2.0], 150)


def test_custom_it_seed_file_present_and_well_formed() -> None:
    path = Path(__file__).resolve().parents[2] / "benchmarks" / "data" / "custom_it_seed.json"
    assert path.is_file(), f"missing seed: {path}"
    data = json.loads(path.read_text())
    assert "items" in data
    assert len(data["items"]) >= 20
    required = {"id", "question", "reference", "category", "expected_mode"}
    for item in data["items"]:
        assert required.issubset(item.keys()), f"missing keys in {item.get('id')}"
        assert item["expected_mode"] in {
            "direct",
            "rag",
            "planner_solve",
            "planner_solve_critic",
        }
