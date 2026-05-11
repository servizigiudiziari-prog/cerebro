# CEREBRO — Brief di Sviluppo per Claude Code
## Fase 0: Sistema Senza Training

**Destinatario:** Claude Code (agente di sviluppo autonomo)  
**Repository:** da creare come `cerebro` su GitHub  
**Durata stimata:** 2-3 settimane di lavoro  
**Linguaggio:** Codice e commenti in inglese, README/docs in italiano + inglese

---

## 0. COME LEGGERE QUESTO DOCUMENTO

Sei stato ingaggiato per implementare la Fase 0 di un sistema chiamato CEREBRO. La specifica architetturale completa è in `CEREBRO-v2-Specifica-Tecnica.md` (consegnata separatamente nel repo).

**Tu non devi implementare tutta la specifica.** Devi implementare solo la Fase 0, descritta qui sotto.

Se trovi ambiguità tra questo brief e la specifica tecnica, questo brief ha priorità. Se trovi un'ambiguità che blocca il lavoro, apri una issue con tag `clarification-needed` e prosegui sul resto.

---

## 1. MISSIONE DELLA FASE 0

Costruire una versione minima di CEREBRO che gira su Mac con Apple Silicon, **senza addestrare nulla**, e dimostra che l'orchestrazione modulare di un LLM locale produce risultati misurabilmente diversi da un LLM denso usato direttamente.

**Tesi della Fase 0:** un router euristico con 4 modalità di esecuzione (direct, RAG, planner-then-solve, planner-solve-critic) sopra un modello base locale produce un trade-off qualità/latenza/energia diverso (sperabilmente migliore) rispetto al modello base usato direttamente.

**Non stai dimostrando che CEREBRO è migliore di GPT-4.** Stai dimostrando che l'orchestrazione locale ha senso prima di investire in training di adapter.

---

## 2. SCOPE — COSA COSTRUIRE

### 2.1 Componenti obbligatori

1. **Trunk LLM locale** in MLX
   - Modello: Qwen2.5-1.5B-Instruct in formato MLX, quantizzato 4-bit
   - Caricamento da HuggingFace o conversione da safetensors
   - API uniforme: `generate(prompt, max_tokens, ...) -> output`

2. **Router euristico**
   - Input: query string + metadati
   - Output: `ExecutionMode` (enum: DIRECT, RAG, PLANNER_SOLVE, PLANNER_SOLVE_CRITIC)
   - Logica: regole esplicite basate su feature semplici (lunghezza query, parole chiave, presenza di codice, riferimenti temporali, complessità stimata)
   - Documentato: ogni regola del router deve essere ispezionabile e modificabile

3. **Memoria semantica (RAG)**
   - Database: LanceDB embedded
   - Embedding model: `BAAI/bge-small-en-v1.5` o equivalente, eseguito localmente
   - Corpus iniziale: Wikipedia IT (subset di 100k articoli) — fornire script di ingestion
   - API: `retrieve(query, top_k=5, filters=None) -> List[Chunk]`

4. **Quattro modalità di esecuzione**
   - `DIRECT`: query → trunk → output
   - `RAG`: query → retrieve → trunk(query + context) → output
   - `PLANNER_SOLVE`: query → trunk(planning prompt) → plan; trunk(plan + query) → output
   - `PLANNER_SOLVE_CRITIC`: come sopra + trunk(critic prompt su output) → output finale (oppure ciclo se critic identifica problemi, max 2 cicli)

5. **Orchestratore**
   - Riceve query, chiama router, esegue modalità selezionata, ritorna output strutturato con metadati (modalità usata, latenza, token, contesto recuperato)

6. **Suite di benchmark**
   - Implementare valutazione automatica su:
     - MMLU (subset 500 domande, multilingue se disponibile)
     - GSM8K (200 problemi)
     - HumanEval (100 problemi codice)
     - Suite custom IT: creare 50 domande che richiedono ragionamento in italiano (forniremo seed di 20 esempi, il resto da generare)
   - Per ogni benchmark, eseguire 4 configurazioni:
     - baseline 1: `DIRECT` sempre
     - baseline 2: `RAG` sempre
     - baseline 3: `PLANNER_SOLVE_CRITIC` sempre
     - candidato: router euristico decide

7. **Sistema di misurazione**
   - Per ogni esecuzione, loggare:
     - latenza TTFT (time to first token) in ms
     - throughput in tok/s
     - token totali generati
     - modalità selezionata dal router
     - chunk recuperati (se RAG)
     - cicli ricorsivi (se critic)
   - Utilizzo `powermetrics` (macOS) per stima energia. Wrapper Python da implementare.

### 2.2 Componenti FUORI SCOPE per Fase 0

**NON implementare:**

- Adapter LoRA o qualsiasi training (verranno in Fase 1)
- Selettore neurale (router solo euristico in questa fase)
- Memoria episodica o procedurale (solo semantica/RAG)
- Cognitive Execution Policy completa (solo enum `ExecutionMode`)
- Oracle routing (verrà in Fase 2)
- Modulo Arbiter completo (solo regole inline)
- Fusion modes degli adapter (non ci sono adapter)
- Sparse upcycling
- UI grafica (solo CLI)

Se ti accorgi di stare scivolando in uno di questi, **fermati e apri una issue**.

---

## 3. STRUTTURA DEL REPOSITORY

```
cerebro/
├── README.md                    # Bilingue IT/EN, descrizione e quickstart
├── LICENSE                      # MIT
├── pyproject.toml              # Poetry o uv
├── .gitignore
├── .github/
│   └── workflows/
│       ├── tests.yml           # CI su Mac runner se possibile
│       └── lint.yml
├── docs/
│   ├── architecture.md         # Riferimento a CEREBRO-v2-Specifica-Tecnica.md
│   ├── phase0-design.md        # Decisioni di design specifiche di Fase 0
│   └── benchmarks.md           # Come riprodurre i benchmark
├── cerebro/
│   ├── __init__.py
│   ├── trunk/
│   │   ├── __init__.py
│   │   ├── mlx_model.py        # Wrapper Qwen2.5 in MLX
│   │   └── prompts.py          # Template prompt per planner, critic, ecc.
│   ├── router/
│   │   ├── __init__.py
│   │   ├── heuristic.py        # Router euristico
│   │   ├── features.py         # Feature extraction dalla query
│   │   └── modes.py            # Enum ExecutionMode
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── semantic.py         # Wrapper LanceDB
│   │   ├── embeddings.py       # Embedding model wrapper
│   │   └── ingestion.py        # Script di caricamento Wikipedia
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── orchestrator.py     # Loop principale
│   │   ├── modes/
│   │   │   ├── direct.py
│   │   │   ├── rag.py
│   │   │   ├── planner_solve.py
│   │   │   └── planner_solve_critic.py
│   │   └── result.py           # Dataclass ExecutionResult
│   ├── telemetry/
│   │   ├── __init__.py
│   │   ├── metrics.py          # Latenza, throughput
│   │   ├── energy.py           # Wrapper powermetrics
│   │   └── logger.py           # Logging strutturato
│   └── cli.py                  # Entry point CLI
├── benchmarks/
│   ├── __init__.py
│   ├── mmlu.py
│   ├── gsm8k.py
│   ├── humaneval.py
│   ├── custom_it.py
│   ├── run_all.py              # Esegue tutte le baseline + candidato
│   └── data/
│       └── custom_it_seed.json # 20 esempi seed
├── tests/
│   ├── unit/
│   │   ├── test_router.py
│   │   ├── test_modes.py
│   │   └── test_memory.py
│   └── integration/
│       └── test_end_to_end.py
├── scripts/
│   ├── setup_environment.sh    # Setup Mac
│   ├── download_models.py      # Scarica e converte Qwen2.5
│   ├── ingest_wikipedia.py     # Popola LanceDB
│   └── run_phase0_report.py    # Genera report finale
└── results/                     # Output dei benchmark (gitignored eccetto README)
    └── README.md
```

---

## 4. VINCOLI TECNICI

### 4.1 Stack

- **Python:** 3.11+
- **Package manager:** `uv` (preferito) o Poetry
- **Framework ML:** `mlx` e `mlx-lm` ufficiali Apple
- **Database vettoriale:** `lancedb`
- **Embedding:** `sentence-transformers` con modello locale
- **Testing:** `pytest`, `pytest-asyncio` se necessario
- **Linting:** `ruff` per linting+formatting
- **Type checking:** `mypy` in modalità strict sui moduli core

### 4.2 Requisiti hardware del codice

Il codice deve girare su:
- macOS 14+
- Apple Silicon M2 o successivo
- 16GB RAM unificata minimo
- 50GB SSD liberi

Se ti accorgi che la configurazione minima non basta, documentalo e proponi modifiche, non aumentare i requisiti silenziosamente.

### 4.3 Vincoli di codice

- **No dipendenze pesanti inutili.** No torch, no tensorflow, no transformers (usa mlx-lm direttamente).
- **Async dove ha senso**, non per default. RAG retrieval e generazione possono essere sync nella Fase 0.
- **Type hints ovunque.** Niente `Any` se non strettamente necessario.
- **Docstring in inglese**, formato Google style.
- **Errori espliciti.** No `except Exception: pass`. Ogni errore deve avere un significato.
- **Logging strutturato** con `structlog` o equivalente. No `print()` se non in CLI/scripts.
- **Config via file YAML/TOML**, non hardcoded. Tutte le costanti (top_k, max_tokens, soglie) in `cerebro/config.py` con default sensati.

---

## 5. COMPORTAMENTO DEL ROUTER EURISTICO

Questo è il pezzo più delicato della Fase 0. Specifiche dettagliate:

### 5.1 Feature estratte dalla query

```python
@dataclass
class QueryFeatures:
    length_tokens: int
    has_code_blocks: bool          # presenza di ``` o pattern di codice
    has_math: bool                  # presenza di formule, numeri, simboli matematici
    has_question_words: bool        # chi/cosa/quando/perché/come
    references_past: bool           # "ricordi", "prima", "ieri", "l'altra volta"
    references_facts: bool          # "qual è", "quando è nato", "definizione di"
    estimated_complexity: float     # 0-1, basato su lunghezza + struttura
    language: Literal["it", "en", "mixed"]
```

### 5.2 Regole del router

```
SE references_facts AND NOT has_code_blocks:
    → RAG

SE has_code_blocks OR has_math AND estimated_complexity > 0.5:
    → PLANNER_SOLVE_CRITIC

SE estimated_complexity > 0.7:
    → PLANNER_SOLVE

ALTRIMENTI:
    → DIRECT
```

**Importante:** queste regole sono il punto di partenza, non il punto finale. Documenta nel codice **perché** ogni regola esiste, e rendi facile modificarle.

### 5.3 Test del router

Per ogni regola, scrivere almeno 3 test:
- caso che dovrebbe attivare la regola
- caso al confine
- caso che NON dovrebbe attivare la regola

---

## 6. CRITERI DI ACCETTAZIONE

La Fase 0 è considerata completa quando **tutti** questi criteri sono soddisfatti:

### 6.1 Funzionali

- [ ] CLI funzionante: `cerebro ask "domanda"` produce output con metadati
- [ ] Tutte e 4 le modalità di esecuzione funzionano end-to-end
- [ ] Router seleziona modalità coerenti con le regole documentate
- [ ] RAG recupera chunk pertinenti dal corpus Wikipedia
- [ ] PLANNER_SOLVE_CRITIC esegue fino a 2 cicli e si ferma quando il critic approva

### 6.2 Test

- [ ] Test unitari per ogni modulo core (coverage > 70% su `cerebro/router`, `cerebro/execution`, `cerebro/memory`)
- [ ] Test di integrazione end-to-end per ciascuna modalità
- [ ] CI verde su PR

### 6.3 Benchmark

- [ ] Script `run_all.py` esegue tutti e 4 i benchmark con tutte e 4 le configurazioni
- [ ] Report generato automaticamente in `results/phase0_report.md` con:
  - Tabella qualità per benchmark × configurazione
  - Tabella latenza per benchmark × configurazione
  - Distribuzione delle modalità selezionate dal router
  - Confronto energetico (joule/token) se misurabile

### 6.4 Documentazione

- [ ] README con quickstart riproducibile in <10 minuti
- [ ] `docs/phase0-design.md` con tutte le decisioni di design e i loro perché
- [ ] `docs/benchmarks.md` con istruzioni per riprodurre ogni benchmark
- [ ] Ogni funzione pubblica ha docstring

### 6.5 Riproducibilità

- [ ] Setup completo via `scripts/setup_environment.sh`
- [ ] Download e conversione modello via `scripts/download_models.py`
- [ ] Ingestion Wikipedia via `scripts/ingest_wikipedia.py`
- [ ] Tutti gli script con `--help` informativo

---

## 7. WORKFLOW DI SVILUPPO

### 7.1 Git workflow

- Branch `main` protetto, no push diretti
- Feature branch: `feat/router-heuristic`, `feat/rag-pipeline`, etc.
- Pull request per ogni branch, anche se è solo per te stesso (audit trail)
- Commit message in inglese, formato Conventional Commits
- Squash merge in main

### 7.2 Issue tracking

Creare issue per ogni componente principale:
- `[Phase 0] Trunk integration with MLX`
- `[Phase 0] Heuristic router with feature extraction`
- `[Phase 0] LanceDB semantic memory`
- `[Phase 0] Four execution modes`
- `[Phase 0] Telemetry and energy measurement`
- `[Phase 0] Benchmark suite`
- `[Phase 0] Custom IT benchmark generation`
- `[Phase 0] End-to-end integration and CLI`
- `[Phase 0] Documentation and reproducibility`

Lavorare un'issue alla volta. Chiuderla con il PR di merge.

### 7.3 Quando chiedere chiarimenti

Apri una issue con tag `clarification-needed` se:
- Una specifica è ambigua e una scelta avrebbe conseguenze su altre parti
- Trovi un blocco tecnico che richiede una decisione di prodotto
- Stai per aggiungere una dipendenza non listata in sezione 4.1
- Stai per cambiare la struttura del repo
- Il tempo stimato per un componente è raddoppiato rispetto alle stime

**Non chiedere chiarimenti per:**
- Scelte di implementazione interne ai moduli
- Naming di funzioni private
- Ottimizzazioni di codice
- Stile (segui ruff)

---

## 8. REPORT FINALE

Alla fine della Fase 0, generare `results/phase0_report.md` con questo schema:

```markdown
# CEREBRO Phase 0 — Report Tecnico

## Setup
- Modello: Qwen2.5-1.5B-Instruct 4bit
- Hardware: [specifica esatta]
- Data esecuzione: [timestamp]
- Commit: [hash]

## Risultati Qualità
[Tabella per benchmark con 4 configurazioni]

## Risultati Latenza
[Tabella TTFT, tok/s, latenza totale media]

## Routing
- Distribuzione modalità selezionate
- Casi in cui il router ha probabilmente sbagliato (esempi)

## Energia
[Se misurata]

## Conclusioni
- Il router euristico batte le baseline su quali metriche?
- Quali modalità sono effettivamente utili?
- Cosa è emerso che non era previsto?
- Cosa NON funziona e perché?

## Raccomandazioni per Fase 1
- Quali adapter sembrano più promettenti dai pattern osservati?
- Quali debolezze del router suggeriscono priorità per il Selettore neurale?
```

**Il report deve essere onesto.** Se le baseline battono il router, dirlo chiaramente. Il valore della Fase 0 è la conoscenza prodotta, non il risultato positivo.

---

## 9. PRINCIPI DI LAVORO

1. **Niente magia.** Ogni decisione automatica deve essere ispezionabile. Niente "il modello sceglie", sempre "il router applica regola X".

2. **Misura prima di ottimizzare.** Non ottimizzare codice che non è stato profilato. Le ottimizzazioni premature in Fase 0 sono perdita di tempo.

3. **Fallisci visibile.** Se una modalità non funziona su un benchmark, il report lo deve mostrare chiaramente. Non nascondere fallimenti dietro medie.

4. **Documenta il "perché", non solo il "cosa".** Il codice spiega cosa fa. I commenti e i docs spiegano perché.

5. **Onestà metrica.** Non usare metriche aggregate quando una distribuzione direbbe di più. Riportare p50, p90, p99 oltre alla media per le latenze.

6. **Riproducibilità totale.** Chi clona il repo deve poter rigirare tutto in meno di un'ora di setup + tempo di esecuzione benchmark.

---

## 10. FUORI SCOPE: COSE DA NON FARE

- Non aggiungere altri modelli oltre a Qwen2.5-1.5B in Fase 0
- Non tentare fine-tuning anche se sembra "facile"
- Non implementare interfacce web o GUI
- Non aggiungere supporto a Linux/Windows (Mac-first, gli altri vengono dopo)
- Non scrivere wrapper per modelli cloud (OpenAI, Anthropic, etc.)
- Non implementare streaming dell'output (sync è OK per Fase 0)
- Non costruire un sistema di plugin estensibile (YAGNI)
- Non scrivere il paper (verrà nelle fasi finali)

---

## 11. CRITERI DI USCITA — QUANDO FERMARSI

La Fase 0 si chiude quando:

- Tutti i criteri di accettazione (sezione 6) sono verdi
- Il report finale è generato
- Il repo ha un tag `v0.1.0-phase0`
- È stata aperta una issue `phase-1-planning` con le raccomandazioni del report

**Non procedere oltre alla Fase 1 senza esplicita autorizzazione del committente** (Antonio).

---

## 12. CONTATTO

Committente: **Antonio**  
Direzione architetturale: Antonio + Claude (modello Anthropic)  
Tu (Claude Code): esecutore tecnico autonomo della Fase 0.

Se questo brief contiene errori o lacune, **dillo prima di iniziare**, non dopo aver scritto 5000 righe di codice nella direzione sbagliata.

Inizia aprendo il repo, leggendo la specifica completa `CEREBRO-v2-Specifica-Tecnica.md`, e creando le issue elencate in sezione 7.2. Poi inizia dalla più foundational (trunk MLX integration).

Buona costruzione.

---

*Brief versione 1.0 — Maggio 2026*
