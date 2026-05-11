# Review esterna — Codex (2026-05-11)

> Recensione del bootstrap CEREBRO al commit `69e54d1` da parte di Codex,
> agente di review esterno usato da Antonio in parallelo a antonio-agent.
> Registrata qui perché:
> 1. è materiale di progetto a tutti gli effetti (review esterne
>    riducono il rischio di cecità del maintainer);
> 2. la roadmap (Stage I, asse visibilità) prevede pubblicazione futura
>    del repo e le review esterne sono parte della catena di evidenze;
> 3. uno dei punti sollevati (tensione `torch` via `sentence-transformers`
>    vs vincolo brief §4.3 "no torch") è azionabile e richiede una
>    decisione esplicita di prodotto.

---

## Riassunto del feedback

**Stato letto**: `origin/main` `69e54d1`, worktree pulito, nessuna
modifica fatta da Codex (review-only).

**Giudizio strategico**: progetto «molto serio come impostazione», ma al
2026-05-11 è **bootstrap/skeleton**, non un agente funzionante. La parte
forte dichiarata: governance (`README.md`, `ROADMAP.md`, `docs/_brief/`,
`docs/phase0-design.md`). Tesi descritta come buona, anti-hype,
falsificabile (small LLM locale MLX + router/modi + benchmark onesti
contro `best_fixed` / `oracle` / `gain_ratio`).

**Stato reale del codice secondo Codex**:
- Core quasi tutto stub: trunk MLX, router, RAG, orchestrator, 4 modes,
  benchmark e report sollevano `NotImplementedError`.
- Funzionano: config frozen, enum `ExecutionMode`, `ExecutionResult`,
  prompt template, logging, stopwatch/percentili.
- Test attuali = shape tests, non funzionali.
- `compileall` passa (sintassi OK).
- Non ha eseguito `pytest/ruff/mypy` per limite ambiente (uv DNS fail
  + `.venv` vuota). Su CI GitHub Actions invece i test passano.

**Punto architetturale segnalato**:
> Nel brief c'è un vincolo "no torch / no transformers", ma
> `pyproject.toml` dipende da `sentence-transformers`, che trascina
> `torch`. Non è per forza un bug, perché il brief stesso cita
> `sentence-transformers` per embedding, ma è una tensione architetturale
> da chiarire presto: o accetti Torch solo per embedding, o cambi
> embedder.

**Proposta operativa di Codex**:
> Il prossimo passo migliore è implementare una **slice piccola ma
> completa e testabile**: router feature extraction + heuristic route +
> test reali, poi mode handlers con `FakeTrunk`, e solo dopo MLX/LanceDB
> pesanti. Così la tesi inizia a vivere prima di affogare nel setup
> modelli.

---

## Risposta tecnica

### Sul giudizio strategico

Accettato. Il bootstrap stesso è stato presentato come tale (commit
message `d55baa6`: "bootstrap Phase 0 skeleton (no logic, all
NotImplementedError stubs)") e la ROADMAP §1 Phase 0 lo dichiara
in corso. Nessun overclaim da correggere.

### Sulla tensione `torch` via `sentence-transformers`

**Conferma**: il punto è reale ed era già noto. Documentato in:
- `docs/phase0-design.md` § D-004 ("Open questions" finale):
  *"Multilingual embedder swap. Should we switch from `bge-small-en`
  to an IT-tuned model before the first benchmark run?"* — non copre
  esattamente il punto di Codex (`torch` vs no-`torch`), ma è collegato.
- GitHub issue #3 (`[Phase 0] LanceDB semantic memory`) sezione
  "Open question": *"Brief §4.1 names sentence-transformers but §4.3
  forbids torch. ST has torch as a hard dep. For Phase 0 we accept
  torch (CPU) since ST is explicitly required."*

**Azione di follow-up** (eseguita contestualmente a questa review):
aperta issue GitHub dedicata `clarification-needed: torch via
sentence-transformers vs brief §4.3` con tre opzioni:
1. Accettare `torch` come transitive dep di `sentence-transformers`
   (status quo del bootstrap).
2. Sostituire `sentence-transformers` con un wrapper MLX-native dell'
   embedder (lavoro non banale, allinea al vincolo brief).
3. Sostituire l'embedder con uno via `huggingface-hub` senza `torch`
   (es. via ONNX-runtime).

La decisione spetta ad Antonio e va presa prima di Phase 1.

### Sulla slice strategy

**Accettata e promossa nella ROADMAP**. Codex ha ragione che l'ordine
foundational del brief §7.2 (Trunk MLX come prima issue) è il **migliore
ordine di consegna del valore**, ma non è il **migliore ordine di
implementazione testabile**. La slice proposta — router + heuristic +
test reali → modes con `FakeTrunk` → MLX/LanceDB — produce un sistema
osservabile end-to-end molto prima.

Il brief §7.3 esplicitamente esclude da `clarification-needed` le
"scelte di implementazione interne ai moduli" e gli "ordini di
operazioni". Quindi cambiare ordine di implementazione delle issue è
una scelta che il maintainer può fare senza chiedere.

**Azione**: aggiornata ROADMAP §1 Phase 0 con la sotto-sezione "Strategia
di implementazione: slice testabile prima del setup modelli".

### Sui limiti dell'ambiente di Codex

Notato che `uv sync` fallisce su DNS in quell'ambiente. Non azionabile
da qui — è un fatto della sua infrastruttura di review, non del progetto.
La CI GitHub Actions Linux (ubuntu-latest) è autoritativa per i test.

---

## Take-away per il maintainer prossimo

1. Prima di Phase 1 risolvere l'issue `clarification-needed` su `torch`.
2. Quando si parte con l'implementazione, seguire la slice strategy:
   - **Issue #2** (router + features) come prima implementazione.
   - **Issue #4** (4 modes) implementata contro un `FakeTrunk` che simula
     `MlxTrunk.generate()` senza scaricare modelli. Test deterministici
     senza GPU.
   - **Issue #1** (trunk MLX reale) come terza, integrata dietro la
     stessa interfaccia.
   - **Issue #3** (LanceDB RAG) in parallelo a #1 ma comunque dopo #2 e
     #4 — il router funziona già senza retrieval.
3. Lo `_brief/` resta la fonte normativa; questa review è materiale
   secondario, registrata per tracciabilità.

---

*Review attribuita a: Codex (agente esterno di Antonio).*
*Registrata da: antonio-agent main session 2026-05-11 22:14 Europe/Rome.*
