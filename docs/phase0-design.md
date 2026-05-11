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

## D-009 — Powermetrics: opzione B (optional but structured)

**What:** energia non blocca Phase 0. Il report dichiara
`energy_status: measured | unavailable | skipped` esplicitamente, mai
omettendo. Default `TelemetryConfig.powermetrics_enabled = False`.

**Why:** brief Addendum I §8 lascia A/B. Antonio (2026-05-11) ha scelto
B con vincolo: il run finale deve dichiarare lo status in modo
strutturato. Una metrica omessa silenziosamente è peggio di una metrica
dichiarata mancante (rule of brief §9 #5 "onestà metrica").

**Alternatives:** A (sudoers NOPASSWD su powermetrics) — più rischioso
sul piano sicurezza, e fragile in CI.

---

## D-010 — Router rule disambiguation: Alternativa B

**What:** la regola
```
SE has_code_blocks OR has_math AND complexity > 0.5 → PSC
```
si legge come `(has_code_blocks OR has_math) AND complexity > 0.5 → PSC`
(Alt B), NON come `has_code_blocks OR (has_math AND complexity > 0.5)`
(Alt A).

**Why:** Addendum III §2.4 con default proposto B + clarification
Antonio 2026-05-11. Conservativa: non manda ogni query con codice nel
percorso più costoso. Si misura meglio il valore reale del critic.

**Implementation note:** `RouterConfig.log_triggering_features = True`
fa loggare la feature che ha attivato la rule in
`ExecutionResult.metadata["router_triggers"]` per audit.

---

## D-011 — Significatività: Wilson 95% CI + soglia magnitudine 5 pp

**What:** una differenza tra configurazioni è "significativa" se passa
**entrambe** queste soglie:
1. Wilson 95% CI dei due score non si sovrappongono (Addendum I §2);
2. Magnitudine della differenza ≥ 5 punti percentuali.

**Why:** la sola significatività statistica non basta su benchmark
piccoli (HumanEval 100 esempi: differenze sotto 5 problemi rischiano di
essere rumore strutturale anche se i CI non si toccano). La sola
magnitudine non basta su benchmark grandi (MMLU 500 esempi: una
differenza di 5 pp può essere rumore se il CI lo dice).

---

## D-012 — Soglie del criterio rivisto contro `best_fixed`

**What:** valori che decidono l'esito qualificato di Phase 0
(`modalities_insufficient` / `router_blind` / `router_partial` /
`success`):

| Soglia | Valore |
|--------|--------|
| `gain_available` significativo | ≥ 5 pp |
| `gain_ratio` per `success` | ≥ 0.5 |
| Latenza router vs DIRECT | ≤ 2.5× |
| Energia router vs DIRECT (se misurata) | ≤ 3× |
| Benchmark con vincoli rispettati per `success` | ≥ 3 su 5 |
| Almeno uno dei benchmark "success" deve essere non-MMLU | true |

**Why:** Addendum III §1 + clarification Antonio 2026-05-11. Pacchetto
coerente: il router deve catturare almeno metà del margine catturabile
sopra la migliore baseline fissa, con costo accettabile, su una
maggioranza di benchmark che includa task diversi da MMLU.

---

## D-013 — Self-confidence prompt: SICURO/NON_SICURO PRE-routing

**What:** la `router-confidence` configuration esegue **una chiamata
separata** al trunk prima di decidere la modalità, con un prompt che
chiede solo SICURO/NON_SICURO. NON usa "ANSWER + CONFIDENCE 0-1" in
single call.

**Why:** Addendum II §2 + clarification Antonio 2026-05-11. Lo schema
"ANSWER + CONFIDENCE single call" non è compatibile col flusso di
routing: se la risposta è già pronta quando arriva la confidence, non
posso più scegliere RAG dopo aver già risposto. Inoltre la confidence
post-hoc tende a essere over-confident (post-rationalization). La
formulazione binaria pre-routing è meno rumorosa.

**Future work:** una **sesta configurazione** "answer+confidence in
single call" può essere aggiunta dopo Phase 0 se interessa misurare
quella variante. Non blocca.

---

## D-014 — multi_turn_it benchmark incluso in Phase 0

**What:** quinto benchmark `benchmarks/multi_turn_it.py` con 20-30
conversazioni IT di 3-5 turni ciascuna. Eseguito con tutte e 5 le
configurazioni (DIRECT, RAG, PSC, router-heuristic, router-confidence)
+ oracle.

**Why:** Addendum II §3 + clarification Antonio 2026-05-11. Multi-turn
è la più predittiva dell'uso reale, pesa di più nelle raccomandazioni
Phase 1 anche se i numeri assoluti possono essere peggiori (è un task
più difficile per definizione). Costo: ~3-5 giorni aggiuntivi nello
scope di Phase 0, accettati esplicitamente.

**Implementation note:** generazione con LLM esterno + validazione di
Antonio. Valutazione tramite LLM-as-judge (Sonnet 4.6, vedi D-017).

---

## D-015 — Critic gold standard: 30 esempi gated on tool

**What:** validation accuratezza del critic con gold standard etichettato.
Target iniziale **30 esempi**, espansione a 50 se a 30 il segnale è
ambiguo (precision di una voce in `(0.65, 0.75)`).

L'etichettatura **NON inizia a mano libera**: prima si implementa
`scripts/validate_critic.py --annotate` (UI di etichettatura strutturata
con mini-calibrazione su 5 esempi). Poi Antonio etichetta 30 esempi in
**due sessioni di 75-90 minuti**.

Fino al completamento del gold standard: `PLANNER_SOLVE_CRITIC` resta
misurabile nei benchmark, ma **non è decision-grade per Phase 1**.

**Why:** Addendum IV §1 + clarification Antonio 2026-05-11. La
qualità del labeling crolla in sessioni lunghe. La calibrazione iniziale
allinea il valutatore (Antonio) ai criteri della rubrica prima del
labeling reale.

---

## D-016 — Soglie di fallimento per modalità individuali

**What:** criteri quantitativi per dichiarare una modalità `failed`
nella tabella "Validità delle modalità" del report finale:

| Modalità | Soglia |
|----------|--------|
| RAG | `retrieval_precision < 0.3` AND `RAG_score < DIRECT_score` |
| PLANNER_SOLVE | `improvement_rate < 0.4` (frazione esempi PS migliora DIRECT) |
| PLANNER_SOLVE_CRITIC | critic accuracy sotto D-015 OR `critic_corrections_helpful < 0.5` |
| DIRECT | non si dichiara fallita (è la baseline) |

**Why:** Addendum IV §2 + clarification Antonio 2026-05-11. Permette di
distinguere "tutto è fallito" da "una specifica modalità è fallita ma
le altre no" — informazione fondamentale per priorizzare Phase 1.

---

## D-017 — External models: un provider, ruoli separati, env+Keychain

**What:** Sonnet 4.6 di Anthropic come default per i 3 ruoli esterni
(`control_trunk_model`, `dataset_generator_model`, `judge_model`).
Credenziali risolte in ordine:
1. env var `ANTHROPIC_API_KEY`
2. macOS Keychain: service `cerebro.anthropic`, account `control-trunk`
3. assente → blocco SOLO al run finale Phase 0 (sviluppo router/FakeTrunk/
   test prosegue senza API). Senza API key al run finale, il report
   dichiara `capability_threshold: inconclusive`.

Judge: `temperature=0`, prompt rigido, output JSON/schema. Generation:
seed fisso, `temperature=0`. Il modello che ha generato e il modello che
ha giudicato sono **sempre loggati** in `runs.jsonl`.

**Why:** Addendum I §3 + §7, II §3, IV §1 + clarification Antonio
2026-05-11. Un solo provider in Phase 0 = meno credenziali, meno
attrito. Secondo provider / human spot-check riservati a claim
pubblici (paper), non blocco di Phase 0.

**No secrets in repo.** Mai `.env` committato. Solo `.env.example` con
i nomi delle var. Pre-commit hook di antonio-agent farà da rete (se
qualcuno fa qualcosa di simile in cerebro, il hook va portato qui).

---

## D-018 — Embedder: ONNX Runtime, non sentence-transformers

**What:** embedder per RAG è `BAAI/bge-small-en-v1.5` in formato ONNX
caricato via `onnxruntime` + tokenizers Rust-backed. **No `torch`** come
default. `MemoryConfig.embedding_backend = "onnx"`.

**Why:** brief §4.3 vieta `torch` come default. `sentence-transformers`
trascina `torch` (~700 MB) violando lo spirito del vincolo, anche se
il brief stesso cita ST in §4.1 (tensione interna al brief). Antonio
2026-05-11: «no torch nel path principale, MLX-native se fattibile
subito altrimenti ONNX per embeddings».

**Trade-off**: MLX-native sarebbe l'ideale (zero deps non-Apple) ma al
2026-05-11 non esistono port MLX maturi di BGE-small. Il porting custom
sarebbe 2-3 giorni. ONNX Runtime + tokenizers = ~50 MB di deps e modello
ONNX scaricabile da HF hub. MLX-native port resta come optimization
future se ONNX diventa bottleneck (probabilmente no: l'embedder gira
una volta per chunk + una per query).

**Alternative considerate**:
- `sentence-transformers` con `torch` accettato → respinto, viola la
  filosofia local-first lightweight del progetto.
- `torch` come adapter opzionale solo per dev → possibile in futuro,
  non default.

---

## D-019 — Slice strategy di implementazione

**What:** l'ordine di implementazione delle issue Phase 0 è:

1. Issue **#2** (router + feature extraction) — puro Python, niente
   modelli.
2. Issue **#4** (4 modes) contro un `FakeTrunk` che implementa
   l'interfaccia `MlxTrunk.generate()` ritornando stringhe canned dal
   test. Permette di testare orchestratore, fallback, critic loop in
   modo deterministico senza dipendenze pesanti.
3. Issue **#1** (trunk MLX reale) — integrato dietro la stessa
   interfaccia.
4. Issue **#3** (LanceDB + ONNX embedder) — in parallelo a #1, il
   router gira già senza retrieval.
5. Tutto il resto (#5 telemetria, #6..#9 brief base, #11..#18
   addendum extension) — segue secondo dipendenze.

**Why:** review esterna Codex 2026-05-11 + clarification Antonio.
L'ordine foundational del brief §7.2 (Trunk MLX prima) è l'ordine di
consegna del valore. Questo è l'ordine di implementazione testabile:
sistema osservabile dal giorno 2-3 senza GPU. Il brief §7.3 esclude
esplicitamente da `clarification-needed` le scelte di ordine di
implementazione.

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
