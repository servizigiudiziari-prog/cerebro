# Phase 0 — Design Decisions

Reasoned decisions made during Phase 0 bootstrap. Each entry follows the
"what / why / alternatives considered" pattern. The bar is high enough to
write something down here: if a choice can be reversed by editing a single
constant, it doesn't belong here.

---

## D-001 — Single source of truth for configuration

**What:** All defaults (model id, thresholds, top-k, max tokens, paths) live
in `cerebro/config.py` as frozen dataclasses. Other modules accept a config
in their constructor; no module reads constants from elsewhere.

**Why:** Brief §4.3 explicitly forbids hardcoded constants. Centralising
them also makes the router thresholds (the most likely thing to tune) a
one-file edit.

**Alternatives:** Pydantic settings + YAML overlay (heavier dependency,
defer to a later issue); env-vars (poor type discoverability).

---

## D-002 — `ExecutionMode` is a `str`-Enum

**What:** The four execution modes are members of an `Enum` that also
inherits from `str`, so `ExecutionMode.RAG == "rag"` and JSON serialization
of `{"mode": ExecutionMode.RAG}` produces `{"mode": "rag"}` natively.

**Why:** Telemetry logs (`results/runs.jsonl`) and benchmark output files
need string identifiers. Avoids a custom encoder.

**Alternatives:** Plain `str` constants (no exhaustiveness check at type
level); separate `to_json()` helpers (extra surface).

---

## D-003 — Heuristic router is rule-driven, not learned

**What:** `cerebro/router/heuristic.py` is a small chain of `if` statements
keyed off `QueryFeatures`. Thresholds come from `RouterConfig`.

**Why:** Brief §9 #1: "niente magia". Phase 0 must be inspectable. A
learned router is exactly the Phase 1 selector and would prejudice that
work. Brief §5.2 mandates a specific rule set; this implementation
follows it byte-for-byte and documents *why* each rule exists.

**Alternatives:** Embedding-based nearest-neighbour router (would require
training data we don't have); LLM-as-judge router (defeats the point of
Phase 0 — we'd be measuring the trunk twice).

---

## D-004 — RAG embedding model: `BAAI/bge-small-en-v1.5`

**What:** Default embedder is `BAAI/bge-small-en-v1.5` (384-dim), runs on
CPU/MPS via sentence-transformers.

**Why:** Brief §2.1 #3 names it as the default. Small enough to load
quickly, multilingual-enough for the IT-heavy corpus (BGE-M3 would be
nicer but adds weight; defer to a later evaluation).

**Alternatives:** `intfloat/multilingual-e5-small` (similar size, better
on IT — track as a potential swap in the benchmark report). `BGE-M3`
(heavier).

---

## D-005 — Telemetry uses `structlog`, not stdlib `logging` directly

**What:** All non-CLI/script output flows through a configured `structlog`
logger emitting JSON lines on stderr.

**Why:** Brief §4.3 demands structured logging; downstream analysis of
benchmark runs benefits from one-event-per-line JSON.

**Alternatives:** Plain `logging.Formatter` (works but loses key=value
ergonomics); `loguru` (less neutral as a JSON sink).

---

## D-006 — Critic loop cap = 2 cycles

**What:** `PLANNER_SOLVE_CRITIC` runs at most two critic cycles (i.e. one
initial answer + up to one revision). Cap lives in
`ExecutionConfig.critic_max_cycles`.

**Why:** Brief §2.1 #4 mandates "max 2 cycles". Higher caps would inflate
latency and energy without an obvious quality justification at Phase 0.

**Alternatives:** Dynamic budget based on residual uncertainty (out of
scope for Phase 0 — needs telemetry data we will only have after the
first benchmark run).

---

## D-007 — CI: a single consolidated test job + `paths-ignore`

**What:** `.github/workflows/tests.yml` runs all tests in **one** job, not
one job per module. `paths-ignore` excludes docs and results from
triggering the workflow.

**Why:** GitHub Actions bills a one-minute minimum per job. The `cerebro`
repo doesn't yet have many tests, but the lesson from `antonio-agent`
(2026-05-11) was clear: an over-fragmented test workflow burns budget
fast. We start economical and split only when wall-clock matters.

**Alternatives:** Matrix over Python versions (defer — Phase 0 pins
Python 3.11+, two CI cells = double the cost for no signal).

---

## D-008 — Bootstrap allows stubs to raise `NotImplementedError`

**What:** Module surface is created in the bootstrap PR; bodies raise
`NotImplementedError("... see GitHub issue ...")`. The bootstrap test
suite asserts the *shape* (public functions exist, signatures match,
enum has exactly four values, dataclass fields are present).

**Why:** Want to merge a stable repository skeleton before any one
component is finished. Issues can then proceed in parallel without
constant rebases.

**Alternatives:** Land each module's first version inside its own issue
(harder to bootstrap CI without something to lint/test).

---

## Open questions (move to issues as they become blocking)

- **Multilingual embedder swap.** Should we switch from `bge-small-en` to
  an IT-tuned model before the first benchmark run? Decision deferred to
  after first run on the Italian custom benchmark.
- **Streaming output.** Brief §10 forbids streaming in Phase 0, but the
  telemetry layer needs a way to record TTFT distinct from total latency.
  Track in the trunk-MLX issue.
- **`powermetrics` and sudo.** `powermetrics` requires sudo, which makes
  unattended runs awkward. May need a `sudoers` snippet documented in
  `docs/benchmarks.md`. Track in the telemetry issue.
