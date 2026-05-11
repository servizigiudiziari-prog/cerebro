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


def test_benchmark_defaults_aligned_with_addendum_I() -> None:
    # Addendum I §2: rigore statistico = temperature 0.0, top_p 1.0, seed.
    # Addendum I §5: rag_min_score default 0.5.
    cfg = CerebroConfig()
    assert cfg.trunk.temperature == 0.0, "Addendum I §2 requires temperature=0.0 by default"
    assert cfg.trunk.top_p == 1.0, "Addendum I §2 requires top_p=1.0 by default"
    assert cfg.trunk.seed > 0, "seed must be set and recorded"
    assert cfg.memory.rag_min_score == 0.5, "Addendum I §5 default rag_min_score is 0.5"


def test_confirmed_decisions_d009_to_d019() -> None:
    """Pin-na le 11 decisioni cumulative confermate da Antonio 2026-05-11.

    Se uno di questi assert fallisce, una delle decisioni in
    docs/phase0-design.md § D-009..D-019 è stata silenziosamente
    rovesciata. Da fixare o aggiornare il design doc esplicitamente.
    """
    cfg = CerebroConfig()

    # D-009: powermetrics opzione B (energy optional, default disabled).
    assert cfg.telemetry.powermetrics_enabled is False

    # D-010: router rule Alternativa B + log feature triggers.
    assert cfg.router.rule_alternative == "B"
    assert cfg.router.log_triggering_features is True

    # D-011: Wilson 95% CI + magnitude threshold 5pp.
    assert cfg.evaluation.statistical.confidence_level == 0.95
    assert cfg.evaluation.statistical.magnitude_threshold_pp == 5.0

    # D-012: criterio rivisto contro best_fixed.
    f = cfg.evaluation.falsifiability
    assert f.gain_available_significance_pp == 5.0
    assert f.gain_ratio_success_min == 0.5
    assert f.latency_max_ratio_vs_direct == 2.5
    assert f.energy_max_ratio_vs_direct == 3.0
    assert f.benchmarks_required_for_success == 3
    assert f.require_non_mmlu_benchmark is True

    # D-013: confidence prompt è SICURO/NON_SICURO (binario pre-routing).
    assert "SICURO" in cfg.router.confidence_prompt
    assert "NON_SICURO" in cfg.router.confidence_prompt

    # D-015: critic validation soglie.
    cv = cfg.evaluation.critic_validation
    assert cv.gold_standard_size_initial == 30
    assert cv.precision_min == 0.7
    assert cv.recall_min == 0.6
    assert cv.rubric_voices_passing_min == 3
    assert cv.calibration_set_size == 5
    assert cv.session_duration_minutes_max == 90

    # D-016: soglie modalità individuali.
    mf = cfg.evaluation.mode_failure
    assert mf.rag_retrieval_precision_min == 0.3
    assert mf.planner_solve_improvement_rate_min == 0.4
    assert mf.critic_corrections_helpful_min == 0.5

    # D-017: external models = single provider Sonnet 4.6, block at final run.
    em = cfg.external_models
    assert em.control_trunk_model == "claude-sonnet-4-6"
    assert em.dataset_generator_model == "claude-sonnet-4-6"
    assert em.judge_model == "claude-sonnet-4-6"
    assert em.judge_temperature == 0.0
    assert em.generation_temperature == 0.0
    assert em.block_if_missing_at_final_run is True
    assert em.keychain_service == "cerebro.anthropic"

    # D-018: embedder backend = onnx (no torch / no sentence-transformers).
    assert cfg.memory.embedding_backend == "onnx"


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
        selected_mode=ExecutionMode.DIRECT,
        executed_mode=ExecutionMode.DIRECT,
        latency_ms=1.0,
        ttft_ms=0.5,
        tokens_generated=3,
    )
    assert r.retrieved == []
    assert r.critic_cycles == 0
    assert r.metadata == {}
    assert r.routing_override_reason is None
    assert r.routing_was_overridden is False
    # mode alias still works for back-compat
    assert r.mode == ExecutionMode.DIRECT


def test_execution_result_routing_override() -> None:
    # Addendum III §2.1: selected_mode and executed_mode may differ when
    # a runtime override fires (e.g. low_confidence_retrieval).
    r = ExecutionResult(
        output="answered without context",
        selected_mode=ExecutionMode.RAG,
        executed_mode=ExecutionMode.DIRECT,
        routing_override_reason="low_confidence_retrieval",
        latency_ms=1.0,
        ttft_ms=0.5,
        tokens_generated=3,
    )
    assert r.routing_was_overridden is True
    assert r.mode == ExecutionMode.DIRECT  # alias returns executed_mode


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
