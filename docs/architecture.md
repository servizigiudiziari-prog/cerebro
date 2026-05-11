# Architecture — Phase 0

This document is **intentionally short**. The complete architectural
specification lives in `CEREBRO-v2-Specifica-Tecnica.md` (handed over
separately by the project owner). Phase 0 is a subset; if a question is
not answered here, defer to the brief `CEREBRO-Brief-Claude-Code.md`.

---

## What Phase 0 builds

```
┌──────────────────────────────────────────────────────────────────┐
│                           cerebro.cli                            │
│             "cerebro ask 'qual è la capitale...?'"               │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│                  cerebro.execution.Orchestrator                  │
│                                                                  │
│   1. features = router.features.extract_features(query)          │
│   2. mode     = router.heuristic.route(features, config)         │
│   3. result   = dispatch(mode)                                   │
│   4. return ExecutionResult(...)                                 │
└────────┬────────────────────────────────────────────────────────┬┘
         │                                                        │
         ▼                                                        ▼
┌─────────────────────────────────┐    ┌──────────────────────────┐
│   cerebro.execution.modes.*     │    │  cerebro.telemetry.*     │
│   ┌─────────────────────────┐   │    │  - stopwatch / percentile│
│   │ DIRECT                  │   │    │  - powermetrics wrapper  │
│   │ RAG                     │   │    │  - structlog JSON logs   │
│   │ PLANNER_SOLVE           │   │    └──────────────────────────┘
│   │ PLANNER_SOLVE_CRITIC    │   │
│   └────────┬──────────┬─────┘   │
└────────────┼──────────┼─────────┘
             │          │
             ▼          ▼
┌─────────────────┐   ┌─────────────────────────────────────────┐
│ cerebro.trunk   │   │ cerebro.memory                          │
│ MlxTrunk        │   │ SemanticStore (LanceDB) + LocalEmbedder │
│ Qwen2.5-1.5B q4 │   │ Wikipedia IT 100k chunks                │
└─────────────────┘   └─────────────────────────────────────────┘
```

---

## What Phase 0 does **not** build

Per brief §2.2:

- LoRA / training of any kind (Phase 1)
- Neural selector (Phase 1+)
- Episodic or procedural memory (Phase 1+)
- Complete Cognitive Execution Policy (only the `ExecutionMode` enum)
- Oracle routing (Phase 2)
- Complete Arbiter module
- Adapter fusion modes
- Sparse upcycling
- Any GUI

If you find yourself drifting into one of the above while implementing
Phase 0, **stop and open an issue**.

---

## Module map

| Module                          | Responsibility                                              |
|---------------------------------|-------------------------------------------------------------|
| `cerebro.config`                | Single source of truth for all defaults / thresholds.       |
| `cerebro.trunk.mlx_model`       | MLX-backed Qwen2.5 wrapper. `generate(prompt) -> result`.   |
| `cerebro.trunk.prompts`         | Planner / solver / critic / RAG prompt templates.           |
| `cerebro.router.features`       | `extract_features(query) -> QueryFeatures`.                 |
| `cerebro.router.heuristic`      | `route(features, config) -> ExecutionMode`.                 |
| `cerebro.router.modes`          | `ExecutionMode` enum (exactly four values).                 |
| `cerebro.memory.embeddings`     | Local sentence-transformers wrapper.                        |
| `cerebro.memory.semantic`       | LanceDB read API (`SemanticStore.retrieve`).                |
| `cerebro.memory.ingestion`      | Document chunking + ingestion helpers.                      |
| `cerebro.execution.orchestrator`| `Orchestrator.ask(query) -> ExecutionResult`.               |
| `cerebro.execution.modes.*`     | One file per mode handler.                                  |
| `cerebro.execution.result`      | `ExecutionResult` dataclass.                                |
| `cerebro.telemetry.metrics`     | Stopwatch + percentile helpers.                             |
| `cerebro.telemetry.energy`      | `powermetrics` wrapper (best-effort, may be unavailable).   |
| `cerebro.telemetry.logger`      | `structlog` config + `get_logger()`.                        |
| `cerebro.cli`                   | `typer`-based CLI entry point.                              |

---

## Reading order for new contributors

1. `CEREBRO-Brief-Claude-Code.md` — what we are building and why
2. `docs/phase0-design.md` — design decisions and their rationale
3. `cerebro/config.py` — every knob lives here
4. `cerebro/router/modes.py` + `cerebro/execution/result.py` — the data
   shapes that flow through the system
5. `docs/benchmarks.md` — how to reproduce the report
