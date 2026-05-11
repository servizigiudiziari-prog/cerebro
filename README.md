# CEREBRO

> **Fase 0 — Sistema senza training.** Versione minima dimostrativa di un'orchestrazione modulare di un LLM locale su Mac con Apple Silicon. Non addestra nulla: dimostra che un router euristico con 4 modalità di esecuzione sopra Qwen2.5-1.5B (MLX, 4-bit) produce un trade-off qualità/latenza/energia diverso dal modello base usato direttamente.

> **Phase 0 — System without training.** A minimal demonstration of modular orchestration of a local LLM on Apple Silicon Macs. No training: shows that a heuristic router with 4 execution modes on top of Qwen2.5-1.5B (MLX, 4-bit) produces a different quality/latency/energy trade-off than the base model used directly.

---

## 🇮🇹 Quickstart (italiano)

### Requisiti

- macOS 14+ (testato su macOS 26)
- Apple Silicon M2 o successivo
- 16GB RAM unificata minimo
- 50GB SSD liberi
- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) (gestore pacchetti)

### Setup (target: <10 minuti)

```bash
git clone https://github.com/servizigiudiziari-prog/cerebro.git
cd cerebro
bash scripts/setup_environment.sh         # crea venv + installa deps
uv run python scripts/download_models.py  # scarica Qwen2.5-1.5B-Instruct 4bit
uv run python scripts/ingest_wikipedia.py # popola LanceDB con corpus Wikipedia IT
uv run cerebro ask "Qual è la capitale dell'Italia?"
```

### Comandi principali

```bash
uv run cerebro ask "<domanda>"                    # query singola
uv run python benchmarks/run_all.py               # tutti i benchmark
uv run python scripts/run_phase0_report.py        # genera report finale
uv run pytest                                     # esegue test suite
uv run ruff check . && uv run ruff format .       # lint + format
uv run mypy cerebro                                # type check
```

### Struttura

- `cerebro/trunk/` — Wrapper Qwen2.5 in MLX, prompt template
- `cerebro/router/` — Router euristico (feature extraction + regole esplicite)
- `cerebro/memory/` — RAG con LanceDB + embedding locali
- `cerebro/execution/` — Orchestratore + 4 modalità (`DIRECT`, `RAG`, `PLANNER_SOLVE`, `PLANNER_SOLVE_CRITIC`)
- `cerebro/telemetry/` — Latenza, throughput, energia (powermetrics)
- `benchmarks/` — MMLU, GSM8K, HumanEval, custom IT
- `docs/` — Decisioni di design e riproducibilità benchmark

---

## 🇬🇧 Quickstart (English)

### Requirements

- macOS 14+ (tested on macOS 26)
- Apple Silicon M2 or later
- 16GB unified RAM minimum
- 50GB free SSD
- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) package manager

### Setup (target: <10 minutes)

```bash
git clone https://github.com/servizigiudiziari-prog/cerebro.git
cd cerebro
bash scripts/setup_environment.sh         # create venv + install deps
uv run python scripts/download_models.py  # download Qwen2.5-1.5B-Instruct 4bit
uv run python scripts/ingest_wikipedia.py # populate LanceDB with IT Wikipedia corpus
uv run cerebro ask "What is the capital of Italy?"
```

### Main commands

```bash
uv run cerebro ask "<question>"                   # single query
uv run python benchmarks/run_all.py               # run all benchmarks
uv run python scripts/run_phase0_report.py        # generate final report
uv run pytest                                     # run test suite
uv run ruff check . && uv run ruff format .       # lint + format
uv run mypy cerebro                                # type check
```

### Layout

- `cerebro/trunk/` — Qwen2.5 wrapper in MLX, prompt templates
- `cerebro/router/` — Heuristic router (feature extraction + explicit rules)
- `cerebro/memory/` — RAG with LanceDB + local embeddings
- `cerebro/execution/` — Orchestrator + 4 modes (`DIRECT`, `RAG`, `PLANNER_SOLVE`, `PLANNER_SOLVE_CRITIC`)
- `cerebro/telemetry/` — Latency, throughput, energy (powermetrics)
- `benchmarks/` — MMLU, GSM8K, HumanEval, custom IT
- `docs/` — Design decisions and benchmark reproducibility

---

## Status / Stato

**Fase 0 in costruzione.** Le issue aperte tracciano i componenti in lavorazione. Quando i criteri di accettazione (vedi `docs/phase0-design.md`) sono tutti verdi e `results/phase0_report.md` è generato, viene taggato `v0.1.0-phase0`.

**Phase 0 in progress.** Open issues track components under development. When all acceptance criteria (see `docs/phase0-design.md`) are green and `results/phase0_report.md` is generated, the tag `v0.1.0-phase0` is cut.

## License

MIT — see [LICENSE](LICENSE).
