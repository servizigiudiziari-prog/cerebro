"""Central configuration for CEREBRO Phase 0.

All knobs (model paths, token limits, RAG top-k, router thresholds, telemetry
sampling) live here with sensible defaults. Runtime overrides may come from a
YAML file pointed to by `CEREBRO_CONFIG` env var (loader implemented in a
later issue).

Rationale: the brief requires that no constant be hardcoded across modules.
This file is the single source of truth. Anything else is a bug.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


# ---------- paths ----------

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
MODELS_DIR: Path = REPO_ROOT / "models"
DATA_DIR: Path = REPO_ROOT / "data"
RESULTS_DIR: Path = REPO_ROOT / "results"


# ---------- trunk (LLM) ----------

@dataclass(frozen=True)
class TrunkConfig:
    """Configuration for the local MLX-backed Qwen2.5 trunk."""

    hf_model_id: str = "Qwen/Qwen2.5-1.5B-Instruct"
    mlx_quantization: str = "q4"  # 4-bit per brief §2.1
    max_tokens: int = 512
    temperature: float = 0.2
    top_p: float = 0.95
    seed: int = 42


# ---------- router ----------

@dataclass(frozen=True)
class RouterConfig:
    """Thresholds for the heuristic router.

    Each rule in `router/heuristic.py` reads its threshold from here. Changing
    behaviour means editing this struct, not the routing code (per brief §5.2:
    rules must be ispezionabile e modificabile).
    """

    complexity_planner_solve_threshold: float = 0.7
    complexity_critic_threshold: float = 0.5
    short_query_token_cap: int = 12  # below this, default to DIRECT


# ---------- memory / RAG ----------

@dataclass(frozen=True)
class MemoryConfig:
    """LanceDB + sentence-transformers configuration for semantic recall."""

    lancedb_path: Path = field(default_factory=lambda: DATA_DIR / "lancedb")
    table_name: str = "wikipedia_it"
    embedding_model_id: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384
    rag_top_k: int = 5
    rag_min_score: float = 0.3  # below this, treat as no useful context


# ---------- execution ----------

@dataclass(frozen=True)
class ExecutionConfig:
    """Orchestrator-level limits."""

    critic_max_cycles: int = 2  # per brief §2.1 #4
    planner_max_tokens: int = 256


# ---------- telemetry ----------

@dataclass(frozen=True)
class TelemetryConfig:
    """Logging + energy-measurement knobs."""

    log_path: Path = field(default_factory=lambda: RESULTS_DIR / "runs.jsonl")
    powermetrics_enabled: bool = True
    powermetrics_sample_interval_ms: int = 500


# ---------- composite ----------

@dataclass(frozen=True)
class CerebroConfig:
    """Top-level configuration aggregating all module configs."""

    trunk: TrunkConfig = field(default_factory=TrunkConfig)
    router: RouterConfig = field(default_factory=RouterConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    telemetry: TelemetryConfig = field(default_factory=TelemetryConfig)


DEFAULT_CONFIG: CerebroConfig = CerebroConfig()
