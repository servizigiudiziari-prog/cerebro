"""Central configuration for CEREBRO Phase 0.

All knobs (model paths, token limits, RAG top-k, router thresholds,
evaluation thresholds, external models, telemetry sampling) live here
with sensible defaults. Runtime overrides may come from a YAML file
pointed to by `CEREBRO_CONFIG` env var (loader implemented in a later
issue).

Rationale: the brief requires that no constant be hardcoded across
modules. This file is the single source of truth. Anything else is a
bug.

All defaults below are aligned with `docs/_brief/` (brief base + four
addenda) and with the cumulative pre-implementation decisions confirmed
by Antonio on 2026-05-11 (see `docs/phase0-design.md` § D-009..D-019).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# ---------- paths ----------

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
MODELS_DIR: Path = REPO_ROOT / "models"
DATA_DIR: Path = REPO_ROOT / "data"
RESULTS_DIR: Path = REPO_ROOT / "results"


# ---------- enums / status types ----------

# D-009: powermetrics is optional. The report always carries an explicit
# status, never silently omits. The values are checked at the boundary
# (telemetry/energy.py) and serialized to the runs.jsonl + report.
EnergyStatus = Literal["measured", "unavailable", "skipped"]


# ---------- trunk (LLM) ----------


@dataclass(frozen=True)
class TrunkConfig:
    """Configuration for the local MLX-backed Qwen2.5 trunk."""

    hf_model_id: str = "Qwen/Qwen2.5-1.5B-Instruct"
    mlx_quantization: str = "q4"  # 4-bit per brief §2.1
    max_tokens: int = 512
    # Addendum I §2: benchmark deve girare a temperature=0.0, top_p=1.0,
    # seed fisso. Eccezioni esplicite e documentate.
    temperature: float = 0.0
    top_p: float = 1.0
    seed: int = 42


# ---------- router ----------


@dataclass(frozen=True)
class RouterConfig:
    """Thresholds for the heuristic router.

    Each rule in `router/heuristic.py` reads its threshold from here.
    Changing behaviour means editing this struct, not the routing code
    (per brief §5.2: rules must be ispezionabile e modificabile).
    """

    complexity_planner_solve_threshold: float = 0.7
    complexity_critic_threshold: float = 0.5
    short_query_token_cap: int = 12  # below this, default to DIRECT
    # Addendum III §2.4 disambiguation (D-010 in phase0-design.md):
    # ALT_B = "(has_code_blocks OR has_math) AND complexity > 0.5"
    # → PLANNER_SOLVE_CRITIC. Conservativa, evita di mandare ogni query
    # con codice nel percorso più costoso.
    rule_alternative: Literal["A", "B"] = "B"
    # When the heuristic fires a rule, the trigger feature is stored in
    # ExecutionResult.metadata["router_triggers"] for telemetry / audit.
    log_triggering_features: bool = True

    # Addendum II §2: prompt esatto della router-confidence
    # configuration (D-013: SICURO/NON_SICURO PRE-routing, NON
    # answer+confidence in single call — quest'ultima opzione è una
    # sesta configurazione che si valuterà solo dopo i risultati di
    # Phase 0).
    confidence_prompt: str = (
        "Domanda: {query}\n"
        "\n"
        "Sei in grado di rispondere correttamente a questa domanda al "
        "primo tentativo, senza aiuti esterni? Rispondi solo con una di "
        "queste due parole:\n"
        "SICURO\n"
        "NON_SICURO"
    )


# ---------- memory / RAG ----------


@dataclass(frozen=True)
class MemoryConfig:
    """LanceDB + ONNX-runtime sentence embedder configuration for RAG.

    Embedder backend: ONNX Runtime con `BAAI/bge-small-en-v1.5` in
    formato ONNX. Decisione D-018 (`docs/phase0-design.md`):
    `sentence-transformers` trascina `torch` (~700 MB) violando lo
    spirito del brief §4.3 "no torch". ONNX Runtime + tokenizers
    Rust-backed = ~50 MB e stesso modello.
    """

    lancedb_path: Path = field(default_factory=lambda: DATA_DIR / "lancedb")
    table_name: str = "wikipedia_it"
    embedding_model_id: str = "BAAI/bge-small-en-v1.5"
    embedding_backend: Literal["onnx", "mlx", "sentence_transformers"] = "onnx"
    embedding_dim: int = 384
    rag_top_k: int = 5
    # Addendum I §5: soglia di confidence per RAG, default 0.5.
    # Sotto soglia: low_confidence_retrieval=True e fallback a DIRECT
    # solo per le configurazioni di routing (NON per la baseline
    # RAG-sempre, vedi Addendum III §2.2 — asimmetria fallback).
    rag_min_score: float = 0.5


# ---------- execution ----------


@dataclass(frozen=True)
class ExecutionConfig:
    """Orchestrator-level limits."""

    critic_max_cycles: int = 2  # per brief §2.1 #4
    planner_max_tokens: int = 256


# ---------- telemetry ----------


@dataclass(frozen=True)
class TelemetryConfig:
    """Logging + energy-measurement knobs.

    Powermetrics: D-009 = Opzione B (Addendum I §8). Energia opzionale.
    Il report dichiara esplicitamente lo status (`measured`,
    `unavailable`, `skipped`), non lo omette. Default
    `powermetrics_enabled = False`: chi vuole attivarla deve farlo
    esplicitamente dopo aver configurato `sudoers`.
    """

    log_path: Path = field(default_factory=lambda: RESULTS_DIR / "runs.jsonl")
    powermetrics_enabled: bool = False
    powermetrics_sample_interval_ms: int = 500


# ---------- external models (control trunk, dataset generator, judge) ----------


@dataclass(frozen=True)
class ExternalModelConfig:
    """External-API models used for control, dataset generation, judging.

    D-017 (Addendum I §3 + §7, II §3, IV §1 + clarification Antonio
    2026-05-11): un solo provider in Phase 0 per ridurre attrito
    credenziali, ma ruoli separati in config e nel logging. Sonnet 4.6
    di Anthropic come default. Un secondo provider o uno human
    spot-check sarà introdotto solo per claim pubblici / paper, NON come
    blocco di Phase 0.

    Credential resolution (in ordine di priorità):
        1. env var `ANTHROPIC_API_KEY`
        2. macOS Keychain: service=`cerebro.anthropic`,
           account=`control-trunk`
        3. nothing → behaviour controlled by
           `block_if_missing_at_final_run` (see below)
    """

    control_trunk_model: str = "claude-sonnet-4-6"
    dataset_generator_model: str = "claude-sonnet-4-6"
    judge_model: str = "claude-sonnet-4-6"

    # Judge: deterministic, rigid prompt, JSON output. Generation:
    # determinism + seed where supported by the API.
    judge_temperature: float = 0.0
    generation_temperature: float = 0.0
    generation_seed: int = 42

    # D-017: senza API key si può sviluppare (router, FakeTrunk, test).
    # Il run FINALE di Phase 0 invece DEVE avere control trunk, oppure
    # il report dichiara `capability_threshold: inconclusive` (Addendum
    # IV §4) e Phase 0 non si chiude come pienamente valida.
    block_if_missing_at_final_run: bool = True

    # Keychain identifiers (logica resolve in cerebro.trunk.api_control,
    # non in questo config).
    keychain_service: str = "cerebro.anthropic"
    keychain_account: str = "control-trunk"


# ---------- evaluation (criterio falsificazione, validation critic, soglie modalità) ----------


@dataclass(frozen=True)
class StatisticalConfig:
    """Significatività statistica delle differenze tra configurazioni.

    D-011 (Addendum I §2 + clarification Antonio 2026-05-11):
    significatività primaria = Wilson 95% CI non sovrapposti; soglia
    secondaria di magnitudine pratica = `≥ 5 pp`. Una differenza è
    "significativa" se passa entrambe.
    """

    confidence_level: float = 0.95
    bootstrap_samples: int = 1000  # per metriche non-binarie (Addendum I §2)
    magnitude_threshold_pp: float = 5.0  # punti percentuali


@dataclass(frozen=True)
class FalsifiabilityConfig:
    """Criterio di falsificazione rivisto Phase 0.

    D-012 (Addendum III §1 + valori confermati Antonio 2026-05-11).
    Quattro esiti possibili: `modalities_insufficient`, `router_blind`,
    `router_partial`, `success`. Più dimensione incrociata
    `capability_threshold` (Addendum III §3, IV §4).
    """

    gain_available_significance_pp: float = 5.0  # vedi anche StatisticalConfig
    gain_ratio_success_min: float = 0.5  # router deve catturare ≥ 50% del margine
    latency_max_ratio_vs_direct: float = 2.5
    energy_max_ratio_vs_direct: float = 3.0
    benchmarks_required_for_success: int = 3  # su 5 totali
    require_non_mmlu_benchmark: bool = True  # almeno uno non-MMLU


@dataclass(frozen=True)
class CriticValidationConfig:
    """Soglie validation critic con gold standard etichettato.

    D-015 (Addendum IV §1 + clarification Antonio 2026-05-11).
    Etichettatura dipende dal tool `validate_critic.py --annotate`: NON
    si chiede ad Antonio di labelare a mano libera. Una volta che il
    tool è pronto, target iniziale 30 esempi in due sessioni di 75-90
    minuti, con mini-calibrazione su 5 esempi prima del labeling reale.
    """

    gold_standard_size_initial: int = 30
    gold_standard_size_expansion: int = 50
    calibration_set_size: int = 5
    session_duration_minutes_max: int = 90
    precision_min: float = 0.7
    recall_min: float = 0.6
    rubric_voices_passing_min: int = 3  # su 4 voci
    # Espandi a `gold_standard_size_expansion` se a 30 esempi la
    # precision di una voce cade nella banda di incertezza:
    expansion_trigger_precision_band: tuple[float, float] = (0.65, 0.75)


@dataclass(frozen=True)
class ModeFailureConfig:
    """Soglie quantitative di fallimento per modalità individuali.

    D-016 (Addendum IV §2 + valori confermati Antonio 2026-05-11). Una
    modalità si dichiara `failed` se le sue soglie non sono rispettate;
    resta nel benchmark ma non guida decisioni Phase 1.
    """

    # RAG fails if retrieval_precision < X AND RAG_score < DIRECT_score
    rag_retrieval_precision_min: float = 0.3
    # PLANNER_SOLVE fails if frazione esempi PS_score > DIRECT_score < Y
    planner_solve_improvement_rate_min: float = 0.4
    # PLANNER_SOLVE_CRITIC fails if critic accuracy sotto soglia OR
    # frazione revisioni che migliorano l'output < Z
    critic_corrections_helpful_min: float = 0.5


@dataclass(frozen=True)
class EvaluationConfig:
    """Container per tutte le soglie di valutazione Phase 0."""

    statistical: StatisticalConfig = field(default_factory=StatisticalConfig)
    falsifiability: FalsifiabilityConfig = field(default_factory=FalsifiabilityConfig)
    critic_validation: CriticValidationConfig = field(default_factory=CriticValidationConfig)
    mode_failure: ModeFailureConfig = field(default_factory=ModeFailureConfig)


# ---------- composite ----------


@dataclass(frozen=True)
class CerebroConfig:
    """Top-level configuration aggregating all module configs."""

    trunk: TrunkConfig = field(default_factory=TrunkConfig)
    router: RouterConfig = field(default_factory=RouterConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    telemetry: TelemetryConfig = field(default_factory=TelemetryConfig)
    external_models: ExternalModelConfig = field(default_factory=ExternalModelConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)


DEFAULT_CONFIG: CerebroConfig = CerebroConfig()
