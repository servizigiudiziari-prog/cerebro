# CEREBRO Phase 0 — Authoritative Material (concatenated)

Generated from `docs/_brief/`. Read order: brief base → I → II → III → IV.
Precedence rules in `docs/_brief/README.md`.

---


# === 00-brief ===

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

---

# === 01-addendum-I ===

# CEREBRO Phase 0 — Addendum Tecnico al Brief

**Destinatario:** Claude Code
**Rapporto col brief principale:** integra `CEREBRO-Brief-Claude-Code.md`. In caso di conflitto tra i due documenti, **questo addendum prevale**.
**Stato:** vincolante. Da applicare prima di iniziare l'implementazione.

---

## 0. PERCHÉ QUESTO ADDENDUM

Il brief originale specifica bene **cosa costruire**. Questo addendum specifica **come misurarlo onestamente**. Senza queste integrazioni, la Fase 0 rischia di produrre codice funzionante ma report non azionabili: differenze nei numeri che possono essere rumore statistico, conclusioni che confondono limiti del trunk con limiti dell'orchestrazione, baseline incomplete che mascherano il vero margine di miglioramento.

Le modifiche sono nove, più una sezione di priorità di esecuzione e criteri di accettazione aggiuntivi.

---

## 1. ORACLE BOUND — quinta configurazione di benchmark

Modifica sezione 2.1 punto 6 e sezione 6.3 del brief.

Aggiungere una **quinta configurazione** alle quattro elencate:

- **oracle:** per ogni esempio del benchmark, eseguire tutte e 4 le modalità e selezionare ex-post la risposta col punteggio più alto.

L'oracle non è una baseline realistica — è il **massimo raggiungibile** con il set di modalità disponibili. Il delta tra router euristico e oracle è la metrica più importante della Fase 0: misura quanto margine c'è per il Selettore neurale di Fase 1.

Senza questa configurazione, un risultato come "router 65% / DIRECT 60%" sembra un successo, ma se l'oracle raggiunge l'85% il router sta sprecando il 90% del margine disponibile. È un'informazione che cambia completamente le priorità di Fase 1.

L'oracle va riportato nel report finale (sezione 8 del brief) accanto alle altre quattro configurazioni, in tutte le tabelle di qualità.

---

## 2. RIGORE STATISTICO

Modifica sezione 8 del brief.

Tutte le esecuzioni di benchmark devono usare:

- `temperature = 0.0` di default. Eccezioni esplicite, documentate e giustificate.
- `top_p = 1.0`, `seed` fissato e riportato nel log di ogni esecuzione.
- **Intervallo di confidenza al 95%** calcolato per ogni metrica di qualità: Wilson score per le accuracy binarie, bootstrap (n=1000) per metriche più complesse.
- **Soglia di significatività dichiarata ex-ante**: due configurazioni si considerano effettivamente differenti solo se gli intervalli di confidenza non si sovrappongono. Differenze sotto soglia vanno riportate come "non significative" senza interpretazione narrativa.

Le sezioni `Conclusioni` e `Raccomandazioni per Fase 1` del report devono attenersi rigorosamente a questa regola. Niente formulazioni del tipo "il router sembra migliorare di X" se X è dentro l'intervallo di rumore. Meglio scrivere "differenza non significativa" che produrre conclusioni che il rumore stesso giustifica.

---

## 3. CONTROLLO CON TRUNK PIÙ CAPACE

Nuovo requisito. Non sostituisce nulla del brief, lo integra.

Su un sottoinsieme di **50 esempi per ciascun benchmark** (selezione casuale con seed riportato), eseguire le quattro modalità anche con un trunk diverso e più capace, accessibile via API esterna. Modello di riferimento: Claude Sonnet 4.6 via API Anthropic, oppure equivalente disponibile.

**Scopo:** distinguere "modalità inutile in sé" da "modalità inutile perché Qwen2.5-1.5B non è abbastanza capace per usarla".

Se PLANNER_SOLVE peggiora la qualità con Qwen2.5-1.5B ma la migliora con il trunk di controllo, la conclusione cambia radicalmente per la Fase 1: il problema non è la modalità, è la capacità minima del trunk per attivarla utilmente.

Costo stimato API: trascurabile (≈50 × 4 modalità × 4 benchmark = 800 chiamate, una tantum).

Implementare un wrapper minimale `cerebro.trunk.api_control` con la stessa interfaccia di `mlx_model.py`. Non integrarlo nel router. Solo per il controllo benchmark.

---

## 4. CRITIC CON RUBRICA ESPLICITA

Modifica sezione 2.1 punto 4 del brief (modalità `PLANNER_SOLVE_CRITIC`).

Il prompt del critic deve usare una rubrica strutturata, non un giudizio generico. Voci minime:

1. **Aderenza alla domanda** — la risposta affronta direttamente ciò che è stato chiesto? (sì/no)
2. **Coerenza interna** — la risposta contiene contraddizioni interne? (sì/no)
3. **Uso del contesto** — se è stato fornito contesto retrieved, la risposta lo usa correttamente o lo ignora/contraddice? (sì/no/non applicabile)
4. **Completezza minima** — ci sono parti della domanda lasciate senza risposta? (sì/no)

Il critic ritorna l'output rivisto **solo se** almeno una delle voci ha rilevato un problema. Altrimenti ritorna l'output originale invariato. Questo evita il fenomeno noto della "critica cosmetica" che con modelli piccoli spesso degrada l'output invece di migliorarlo.

Aggiungere un test che verifica la consistenza del critic: 3 esecuzioni indipendenti sullo stesso input (con `temperature=0`) devono produrre giudizi identici sulle 4 voci. Se non lo fanno, il critic non è affidabile e va sistemato prima di entrare nel benchmark.

Comportamento al ciclo 2 se il critic continua a rilevare problemi: ritornare l'output dell'ultimo passaggio con flag `critic_unresolved: true` nei metadati. Non perdere l'output, ma marcarlo.

---

## 5. RAG CON SOGLIA E FALLBACK

Modifica sezione 2.1 punto 3 e sezione 5.2 del brief.

Il modulo RAG deve:

- Calcolare la similarità coseno di ciascun chunk recuperato.
- Scartare chunk sotto soglia configurabile (default: `0.5`, da calibrare empiricamente).
- Se **nessun chunk supera la soglia**, segnalare `low_confidence_retrieval = True`.

Modifica corrispondente al router (sezione 5.2 del brief). La regola

```
SE references_facts AND NOT has_code_blocks: → RAG
```

diventa:

```
SE references_facts AND NOT has_code_blocks:
    → RAG, con fallback a DIRECT se low_confidence_retrieval
```

Il fallback va loggato come metadato dell'esecuzione: `routing_overridden: true`, `original_mode: RAG`, `final_mode: DIRECT`, `reason: low_confidence_retrieval`.

**Motivazione:** un contesto irrilevante fornito al modello produce confabulazione condizionata dal contesto, peggiore del DIRECT puro. Senza soglia, il router sceglierà RAG per ogni query fattuale, anche su argomenti non coperti dal corpus Wikipedia IT 100k (cioè la maggior parte delle query specifiche), producendo danni invece di vantaggi.

---

## 6. ANALISI PER CATEGORIA

Modifica sezione 8 del brief.

Il report finale deve includere, oltre alle tabelle aggregate per benchmark:

- Performance per **categoria semantica** quando il benchmark è eterogeneo. MMLU ha 57 categorie; aggregarle nasconde pattern critici. Riportare almeno le 10 categorie con maggior delta tra configurazioni.
- Custom IT: tassonomia minima — fattuale, ragionamento, linguistico, culturale — e performance per categoria.

**Motivazione:** il router euristico potrebbe risultare neutro nell'aggregato pur migliorando dell'8% su alcune categorie e peggiorando del 6% su altre. Questo dato è incomparabilmente più informativo del numero medio per orientare la Fase 1. Wikipedia IT aiuterà alcune categorie MMLU e quasi tutte le custom IT; non aiuterà HumanEval. Mostrarlo è il punto.

---

## 7. CUSTOM IT BENCHMARK — PROTOCOLLO DI GENERAZIONE

Modifica sezione 2.1 punto 6 del brief.

Per le 30 domande non-seed:

- **Non generarle con Qwen2.5-1.5B** (il trunk del sistema). Bias di favoritismo: il modello tende a generare domande che sa risolvere, gonfiando artificialmente i risultati.
- Usare un modello esterno via API per la generazione (Claude Sonnet 4.6 o equivalente di classe GPT-4).
- Ground truth di ciascuna domanda **va validata** prima dell'inclusione. Implementare `scripts/validate_custom_it.py` che presenta le domande generate e attende conferma esplicita di Antonio prima del run definitivo.
- Tenere **5 delle 20 seed come held-out di calibrazione**: mai usate in fase di sviluppo, mai mostrate al router in fase di tuning, riservate al run finale del report.

---

## 8. POWERMETRICS — DECISIONE BINARIA

Modifica sezione 2.1 punto 7 del brief.

`powermetrics` su macOS richiede `sudo`, complicando CI e esecuzioni automatiche. Due opzioni:

- **A** — Energia è metrica core. `scripts/setup_environment.sh` configura `/etc/sudoers.d/cerebro` con `NOPASSWD` limitato al solo comando `powermetrics`. Documentare il rischio di sicurezza e richiedere conferma esplicita all'utente al primo setup.
- **B** — Energia è metrica opzionale. Se l'utente non ha eseguito setup privilegiato, il report dichiara "energia non misurata in questa esecuzione" e il benchmark non fallisce.

**Decisione:** **opzione B**, salvo diversa indicazione di Antonio. Aprire issue `clarification-needed` solo se l'opzione B presenta complicazioni tecniche impreviste non risolvibili autonomamente.

---

## 9. CONTRADICTION PRESSURE — metrica, non modulo

Nuovo requisito, basso costo, alto valore per Fase 1.

Aggiungere al logging strutturato di ogni esecuzione (sezione 2.1 punto 7) un campo `contradiction_signals` calcolato a posteriori:

- Per modalità con RAG: numero di chunk recuperati presenti nel prompt ma non riferiti/usati nell'output finale (proxy di "contesto ignorato").
- Per modalità con planner: numero di passi del piano non eseguiti o non riflessi nell'output finale.
- Per modalità con critic: numero di cicli necessari prima dell'approvazione (1 o 2).

**Non implementare logica di reazione a questo segnale in Fase 0.** Solo registrarlo nei log. Se nei benchmark questi segnali correlano con bassa qualità, è materiale immediato per Fase 1.

Aprire issue `phase-2-research: contradiction pressure correlation analysis` da tenere aperta per la Fase successiva.

---

## 10. PRIORITÀ DI ESECUZIONE — risolvere PRIMA del trunk MLX

Prima di iniziare l'implementazione del trunk MLX (issue foundational del brief), risolvere o confermare:

1. **Powermetrics:** confermare opzione B (sezione 8 di questo addendum) o chiedere conferma ad Antonio se serve diversa configurazione.
2. **API key disponibile per il trunk di controllo** (sezione 3 di questo addendum). Se non disponibile, aprire issue `clarification-needed: external API access for control trunk`.
3. **Modello esterno per generazione custom IT** (sezione 7 di questo addendum). Stesso processo del punto 2 se non disponibile.

Aprire issue `clarification-needed` per ciascun punto irrisolto. Non procedere oltre il setup environment senza risposta.

---

## 11. CRITERI DI ACCETTAZIONE AGGIUNTIVI

Aggiungere ai criteri di sezione 6 del brief:

- [ ] Configurazione **oracle** eseguita su tutti i benchmark e riportata nel report finale.
- [ ] Intervalli di confidenza al 95% riportati su ogni metrica di qualità.
- [ ] Sottoinsieme di controllo con trunk esterno eseguito su 50 esempi per benchmark.
- [ ] Critic con rubrica strutturata implementato e testato per consistenza tra esecuzioni.
- [ ] RAG con soglia di confidence e fallback automatico a DIRECT implementato.
- [ ] Report finale include analisi per categoria semantica (MMLU e custom IT).
- [ ] Custom IT validate prima del run definitivo e held-out di 5 domande separato.
- [ ] Decisione powermetrics dichiarata esplicitamente nel report.
- [ ] Campo `contradiction_signals` presente nei log di ogni esecuzione.

---

## 12. PRINCIPIO GENERALE

Il brief originale è scritto come specifica di **costruzione**. Questo addendum lo riorienta verso specifica di **conoscenza prodotta**.

Costruire codice pulito che gira è un risultato strumentale. Il risultato finale della Fase 0 deve essere un report che permette decisioni difendibili per la Fase 1. Le otto integrazioni sopra servono a questo. Se un'integrazione entra in conflitto con la fattibilità nei tempi (sezione 1 del brief: 2-3 settimane), aprire issue `clarification-needed: scope vs timeline` invece di tagliare silenziosamente.

---

*Addendum versione 1.0 — Maggio 2026*
*In caso di conflitto col brief principale, questo addendum prevale.*

---

# === 02-addendum-II ===

# CEREBRO Phase 0 — Addendum II

**Destinatario:** Claude Code
**Rapporto con i documenti precedenti:** integra `CEREBRO-Brief-Claude-Code.md` e `CEREBRO-Brief-Addendum.md` (Addendum I). In caso di conflitto tra documenti, la **sezione 1 di questo Addendum II prevale su tutto**. Le sezioni 2-5 si applicano congiuntamente al brief originale e all'Addendum I.
**Stato:** vincolante. Da applicare prima di iniziare l'implementazione.

---

## 0. PERCHÉ QUESTO SECONDO ADDENDUM

L'Addendum I ha rafforzato il rigore di misurazione del progetto, ma ha lasciato intatto un problema più profondo: la **formulazione stessa della tesi di Fase 0 non è falsificabile come scritta**, e il set di modalità + benchmark scelti non può produrre osservazioni inattese — solo conferme o smentite di ipotesi note. Questo Addendum II affronta entrambi i punti, più tre integrazioni che il primo addendum non copriva.

Le cinque sezioni che seguono sono indipendenti tra loro ma cumulative. La sezione 1 deve essere risolta da Antonio (decisione di prodotto) prima che Claude Code scriva codice.

---

## 1. CRITERIO DI FALSIFICAZIONE DELLA FASE 0 — decisione da prendere PRIMA del codice

**Questa sezione non è implementabile autonomamente da Claude Code. Richiede una decisione esplicita di Antonio prima di qualsiasi altra attività.**

Il brief originale dichiara come tesi di Fase 0: *"un router euristico con 4 modalità […] produce un trade-off qualità/latenza/energia diverso (sperabilmente migliore) rispetto al modello base usato direttamente."*

Il termine "diverso" rende la tesi tecnicamente non-falsificabile: anche se il router peggiora la qualità su tutti i benchmark, il trade-off è comunque "diverso", quindi la tesi è confermata. Il "sperabilmente migliore" tra parentesi è una cautela retorica, non un criterio.

Una Fase 0 onesta richiede di dichiarare **ex ante** una soglia di successo concreta. Schema decisionale richiesto:

> La Fase 0 si considera **successo** se e solo se il router euristico (configurazione `router-heuristic`):
>
> - batte la baseline `DIRECT` su almeno **N benchmark su 4**, con differenza statisticamente significativa (intervalli di confidenza non sovrapposti, vedi Addendum I §2)
> - non supera la baseline `DIRECT` in latenza media per più di un fattore **L**
> - non supera la baseline `DIRECT` in energia per token (se misurata) per più di un fattore **E**

I tre valori `N`, `L`, `E` devono essere fissati da Antonio prima dell'inizio dell'implementazione. Valori suggeriti come punto di partenza ragionevole, soggetti a modifica:

- `N = 2` (almeno metà dei benchmark)
- `L = 2.5` (latenza fino a 2.5× la baseline accettabile)
- `E = 3` (energia fino a 3× la baseline accettabile)

Esiti possibili del report finale, dato il criterio dichiarato:

| Esito | Significato |
|---|---|
| `success` | I tre vincoli sono rispettati |
| `partial_success` | Vincolo qualità rispettato, vincoli costo no |
| `failure` | Vincolo qualità non rispettato |

**Conseguenza operativa:** il report finale (sezione 8 del brief) deve riportare l'esito **come prima riga del documento**, non come paragrafo interpretativo nelle conclusioni. Niente narrativa positiva su un esito `failure`.

**Apri issue `clarification-needed: fase 0 success criteria` con i valori proposti, in attesa di conferma o modifica da Antonio.** Non procedere all'implementazione del trunk MLX senza risposta.

---

## 2. ROUTER SELF-CONFIDENCE — quinta configurazione di benchmark

Integra sezione 2.1 punto 6 del brief e sezione 1 dell'Addendum I (configurazione `oracle`).

Il router euristico previsto dal brief decide la modalità basandosi su feature sintattiche della query (`length_tokens`, `has_code_blocks`, `has_math`, ecc.). Queste sono proxy deboli per il **tipo di computazione effettivamente necessaria**: misurano la forma dell'input, non la difficoltà del task per il modello.

Esiste una sorgente di informazione che il router euristico non usa: **l'autovalutazione di confidence del modello stesso**. Aggiungere una **quinta configurazione di benchmark** chiamata `router-confidence` che procede così:

1. Per ogni query, prima di selezionare la modalità, eseguire una chiamata aggiuntiva al trunk con il seguente prompt strutturato:

   ```
   Domanda: {query}

   Sei in grado di rispondere correttamente a questa domanda al primo tentativo, senza aiuti esterni? Rispondi solo con una di queste due parole:
   SICURO
   NON_SICURO
   ```

2. Parsing dell'output (case-insensitive, prima parola riconosciuta).

3. Selezione modalità:

   ```
   SE confidence == NON_SICURO AND references_facts AND NOT has_code_blocks:
       → RAG (con fallback DIRECT da Addendum I §5 se low_confidence_retrieval)
   SE confidence == NON_SICURO AND (has_code_blocks OR has_math OR estimated_complexity > 0.5):
       → PLANNER_SOLVE
   SE confidence == NON_SICURO:
       → PLANNER_SOLVE
   SE confidence == SICURO:
       → DIRECT
   ```

4. Loggare il valore di confidence riportato dal modello in ogni esecuzione.

Implementazione: aggiungere `cerebro/router/confidence.py` con classe `ConfidenceRouter` che eredita o componene `HeuristicRouter`. Non sostituire il router euristico — è una configurazione aggiuntiva, non sostitutiva.

Costo: una chiamata extra al trunk per query (~50-100 token output). Sostenibile nel benchmark.

**Valore atteso:** se `router-confidence` batte sia `router-heuristic` che le baseline, è il risultato più importante della Fase 0 — suggerisce che il modello ha conoscenza implicita di quando ha bisogno di aiuto, materiale diretto per il Selettore neurale di Fase 1.

Riportare nel report finale accanto alle altre cinque configurazioni (DIRECT, RAG, PLANNER_SOLVE_CRITIC, router-heuristic, oracle).

---

## 3. BENCHMARK MULTI-TURN — colmare l'assenza più grossa

Integra sezione 2.1 punto 6 del brief.

I quattro benchmark previsti (MMLU, GSM8K, HumanEval, custom IT) misurano esclusivamente task **one-shot**: una query, una risposta. Nessuno misura la capacità del sistema in conversazione multi-turn.

Se CEREBRO ambisce a essere un sistema reale e non un solver di benchmark di letteratura, l'uso reale dominante è multi-turn. Una valutazione che lo ignora misura il sottoinsieme più facile e prevedibile degli usi possibili.

**Aggiungere un quinto benchmark:** `multi_turn_it`.

Specifiche minime:

- 20-30 conversazioni in italiano, ciascuna di 3-5 turni
- Mix di task: continuazione di task tecnico (debug iterativo), riformulazione di richiesta, contraddizione esplicita dell'utente, cambio di argomento e ritorno
- Ground truth: per ogni turno, criteri di accettazione strutturati (la risposta riconosce il contesto precedente? mantiene coerenza con i fatti stabiliti? evita di reintrodurre informazioni già fornite?)
- Generazione: come per custom IT (Addendum I §7), con modello esterno + validazione di Antonio prima del run
- Valutazione: rubrica strutturata applicata turno per turno, con possibilità di **LLM-as-judge** esterno (Claude Sonnet 4.6 via API) per la valutazione di coerenza tra turni — l'autovalutazione locale qui è inaffidabile per i motivi della sezione 4 Addendum I

Eseguire le **cinque configurazioni** (incluse oracle e router-confidence) anche su questo benchmark.

Implementare `benchmarks/multi_turn_it.py` con dataset in `benchmarks/data/multi_turn_it_seed.json` (10 esempi seed forniti, 10-20 generati con protocollo validazione).

**Motivazione esplicita nel report:** dichiarare che la performance multi-turn è la più predittiva dell'uso reale, e quindi pesa di più nelle raccomandazioni per Fase 1, anche se i numeri assoluti possono essere peggiori (è un task più difficile).

---

## 4. REGISTRO DI ANOMALIE QUALITATIVE — canale per le scoperte inattese

Integra sezione 2.1 punto 7 e sezione 8 del brief.

Per come è strutturato il brief (anche con tutte le modifiche degli addendum), la Fase 0 può solo confermare o smentire ipotesi già definite. Tutto ciò che misura è metrica aggregata su categorie pre-classificate. Le osservazioni qualitative — i casi anomali, i fallimenti sorprendenti, le coincidenze sospette — vengono cancellate dalla media.

**Aggiungere salvataggio automatico di anomalie selezionate** durante l'esecuzione dei benchmark, in un file `results/anomalies.jsonl`.

Criteri di selezione automatica (un esempio viene salvato se almeno uno dei criteri è soddisfatto):

1. **Convergenza errata:** tutte e 4 le modalità producono risposte semanticamente equivalenti **ma sbagliate** rispetto al ground truth. Segnale di bias condiviso del trunk.
2. **Divergenza massima:** le 4 modalità producono 4 risposte semanticamente diverse, e oracle ≠ router-heuristic ≠ router-confidence. Segnale di alta sensibilità del task alla scelta di modalità.
3. **Critic-failure visibile:** la modalità `PLANNER_SOLVE_CRITIC` approva una risposta che il benchmark valuta come scorretta. Segnale che la rubrica del critic non cattura la dimensione di errore rilevante.
4. **Router-confidence calibration miss:** il modello dice `SICURO` ma sbaglia, oppure dice `NON_SICURO` ma DIRECT sarebbe stato sufficiente. Salvare entrambi i casi separatamente.
5. **Outlier di latenza:** esecuzioni con latenza > 3 deviazioni standard sopra la media della stessa configurazione.

Ogni record salvato include: query, ground truth, output di tutte le configurazioni eseguite, metadati (modalità, confidence, retrieval chunks, cicli critic), criterio di anomalia attivato.

**Nel report finale aggiungere sezione "Anomalie qualitative":** non un'analisi automatica, ma il riferimento al file `anomalies.jsonl` e l'indicazione che la sua ispezione manuale da parte di Antonio è materiale critico per le decisioni di Fase 1.

Costo implementativo: bassissimo (filtri durante il logging già strutturato). Valore epistemico: alto.

---

## 5. NOTA INTERPRETATIVA — la cecità sintattica del router euristico

Integra sezione 9 del brief (`docs/phase0-design.md`) e sezione 8 (report finale).

Aggiungere nel documento di design e nel report finale la seguente nota esplicita, non come scusa ma come quadro interpretativo:

> Il router euristico decide la modalità di esecuzione sulla base di feature sintattiche estratte dalla query: lunghezza, presenza di blocchi di codice, presenza di simboli matematici, parole-chiave fattuali, complessità stimata. Queste feature misurano la **forma dell'input**, non la difficoltà reale del task per il modello.
>
> La correlazione tra forma sintattica della query e tipo di computazione cognitivamente utile è debole. Un calcolo banale e una dimostrazione difficile possono entrambi avere `has_math = true`. Una richiesta di sintesi superficiale e una di analisi profonda possono avere la stessa `length_tokens`.
>
> Pertanto, se il router euristico migliora solo marginalmente sulle baseline, la spiegazione naturale **non è** "le euristiche sono mal calibrate". È: "le euristiche guardano nel posto sbagliato". Il dato veramente predittivo del bisogno di orchestrazione è la **confidence del modello sul task**, non la sintassi della domanda. La configurazione `router-confidence` (sezione 2 di questo addendum) testa esattamente questa ipotesi alternativa.
>
> Questa nota deve essere richiamata esplicitamente nella sezione "Raccomandazioni per Fase 1" del report: il Selettore neurale di Fase 1 non dovrebbe imitare il router euristico raffinandolo, ma sostituirlo con un meccanismo che usa rappresentazioni semantiche o segnali interni del modello.

Lo scopo di questa nota è impedire la lettura sbagliata del report. Una sezione "Conclusioni" che dice *"il router euristico ha performato sotto le attese, suggerendo che serve un router più sofisticato"* è banale e non azionabile. La conclusione corretta è *"il router euristico ha confermato il limite strutturale delle euristiche sintattiche; la direzione di Fase 1 va su segnali semantici o auto-introspettivi"*. Questa è una raccomandazione di prodotto.

---

## 6. PRIORITÀ DI ESECUZIONE — cosa va deciso da Antonio prima del codice

In aggiunta alle priorità della sezione 10 dell'Addendum I:

1. **Criterio di falsificazione** (sezione 1 di questo addendum): Antonio deve dichiarare i valori di `N`, `L`, `E`. Conferma dei valori suggeriti o sostituzione esplicita.
2. **Approvazione del benchmark multi-turn** (sezione 3): Antonio deve confermare che il benchmark vale lo sforzo di implementazione (~3-5 giorni aggiuntivi al timeline) o esplicitamente declassarlo a `phase-1-deferred`.
3. **Conferma del prompt di self-confidence** (sezione 2): Antonio deve approvare il prompt esatto, o proporne uno alternativo. Il prompt non è cosmetico — cambia la calibrazione della configurazione.

Aprire una **issue cumulativa** `clarification-needed: addendum-ii decisions required` che elenca i tre punti. Non procedere oltre il setup environment senza risposte.

---

## 7. CRITERI DI ACCETTAZIONE AGGIUNTIVI

In aggiunta ai criteri della sezione 11 dell'Addendum I:

- [ ] Criterio di falsificazione dichiarato e visibile come prima riga del report finale, con esito (`success` / `partial_success` / `failure`).
- [ ] Configurazione `router-confidence` implementata e benchmarked su tutti i benchmark, accanto a `oracle` e alle altre tre.
- [ ] Benchmark `multi_turn_it` implementato, dataset validato, eseguito con tutte e cinque le configurazioni.
- [ ] File `results/anomalies.jsonl` generato con criteri di selezione automatica funzionanti.
- [ ] Nota interpretativa della sezione 5 presente in `docs/phase0-design.md` e richiamata nel report finale.

---

## 8. PRINCIPIO

L'Addendum I ha trasformato il brief da specifica di costruzione a specifica di conoscenza prodotta. L'Addendum II fa un passo ulteriore: trasforma la conoscenza prodotta in **conoscenza decidibile**.

Un report di Fase 0 che produce numeri non azionabili è inutile anche se è preciso. Un report che dichiara prima l'asticella, poi misura onestamente se l'ha superata, e in più registra le anomalie che la metrica aggregata cancella, è la base su cui si può decidere se andare in Fase 1, come, e con quali priorità.

Se questa onestà preventiva produce un esito `failure`, **è un esito utile**. Significa che si è scoperto qualcosa: che l'orchestrazione locale del modello specificato, con i benchmark specificati, non basta. Quello è materiale di valore. La narrativa positiva su un esperimento mal definito non lo è.

---

*Addendum II versione 1.0 — Maggio 2026*
*La sezione 1 prevale su tutti i documenti precedenti. Le sezioni 2-5 si integrano con essi.*

---

# === 03-addendum-III ===

# CEREBRO Phase 0 — Addendum III

**Destinatario:** Claude Code
**Rapporto con i documenti precedenti:** integra `CEREBRO-Brief-Claude-Code.md`, `CEREBRO-Brief-Addendum.md` (Addendum I) e `CEREBRO-Brief-Addendum-II.md` (Addendum II).
**Sostituzione esplicita:** la **sezione 1 di questo Addendum III sostituisce integralmente la sezione 1 dell'Addendum II**. Il criterio di falsificazione precedente è ritirato. Tutto il resto degli Addendum I e II resta in vigore.
**Stato:** vincolante.

---

## 0. PERCHÉ QUESTO TERZO ADDENDUM

L'Addendum II ha introdotto un criterio di falsificazione contro la baseline `DIRECT`. Quel criterio era insufficiente: dichiarare successo perché il router batte DIRECT mentre una qualsiasi delle altre baseline fisse fa meglio sarebbe stato un risultato auto-indulgente. Un risultato vero richiede di confrontarsi con la migliore baseline fissa disponibile, non con la più debole.

Questo addendum corregge il criterio, formalizza quattro tensioni operative del brief che produrrebbero ambiguità nei log e nel report, e introduce uno schema interpretativo strutturato per la lettura del risultato finale.

---

## 1. CRITERIO DI FALSIFICAZIONE RIVISTO — contro `best_fixed`, non contro `DIRECT`

**Sostituisce integralmente la sezione 1 dell'Addendum II.**

Definizioni operative, da calcolare per ciascun benchmark e per ciascuna categoria semantica rilevante:

- `best_fixed` = max(`DIRECT_score`, `RAG_sempre_score`, `PLANNER_SOLVE_CRITIC_sempre_score`). La migliore tra le tre baseline fisse.
- `gain_available` = `oracle_score` − `best_fixed`. Quanto margine esiste per il selettore, sopra la migliore politica fissa.
- `gain_captured` = `router_score` − `best_fixed`. Quanto il router cattura (può essere negativo).
- `gain_ratio` = `gain_captured` / `gain_available`, definito solo se `gain_available` > soglia di significatività.

Quattro esiti possibili del confronto, di cui solo uno è successo:

| Esito | Condizione | Significato |
|---|---|---|
| **`modalities_insufficient`** | `gain_available` ≤ soglia di significatività su tutti i benchmark | Le modalità non differenziano abbastanza. Il router è irrilevante per costruzione. |
| **`router_blind`** | `gain_available` alto **e** `gain_ratio` basso (≤ 0) | Le modalità servono, le euristiche sintattiche non sanno sceglierle. |
| **`router_partial`** | `gain_available` alto **e** 0 < `gain_ratio` < soglia di cattura | Il router cattura qualcosa ma non abbastanza per giustificarsi. |
| **`success`** | `gain_available` alto **e** `gain_ratio` ≥ soglia di cattura **e** vincoli costo rispettati | Il router cattura una quota significativa del margine catturabile a costo accettabile. |

Soglie suggerite, da confermare da Antonio:

- **Soglia di significatività di `gain_available`:** 5 punti percentuali (differenze sotto questa soglia rendono il router strutturalmente irrilevante in quel benchmark).
- **Soglia di cattura `gain_ratio`:** ≥ 0.5 (il router deve catturare almeno metà del margine catturabile).
- **Vincolo latenza:** latenza media router ≤ 2.5 × `DIRECT`.
- **Vincolo energia (se misurata):** energia/token router ≤ 3 × `DIRECT`.
- **Requisito di estensione:** condizioni soddisfatte su almeno 3 benchmark su 5 (inclusi multi-turn), con almeno uno di esso non MMLU.

Conseguenza operativa: il report finale deve dichiarare **come prima riga del documento** l'esito qualificato — uno tra `modalities_insufficient`, `router_blind`, `router_partial`, `success` — accompagnato dai valori numerici di `gain_available` e `gain_ratio` per ciascun benchmark.

**Esiti diversi da `success` non sono fallimenti del progetto. Sono diagnosi diverse, ciascuna azionabile in modo diverso per la Fase 1.** Vedere sezione 3 di questo addendum.

**Apri issue `clarification-needed: revised falsifiability criteria` con i valori proposti.** Non procedere all'implementazione del trunk MLX senza risposta. Sostituisce l'omologa issue dell'Addendum II.

---

## 2. TENSIONI OPERATIVE — quattro fix al brief

Quattro punti ambigui nel brief originale che, se non risolti prima, produrrebbero log inconsistenti e report ambigui.

### 2.1 — `selected_mode` vs `executed_mode`

Modifica `cerebro/execution/result.py`.

La dataclass `ExecutionResult` deve avere **tre** campi distinti per il routing:

```python
@dataclass
class ExecutionResult:
    selected_mode: ExecutionMode          # modalità scelta dal router PRIMA dell'esecuzione
    executed_mode: ExecutionMode          # modalità effettivamente eseguita
    routing_override_reason: Optional[str]  # se diverse, motivo (es. "low_confidence_retrieval")
    # ... altri campi ...
```

Tutte le tabelle del report che riportano "distribuzione modalità selezionate" devono riportare **entrambe** le distribuzioni (selected ed executed) e segnalare quando differiscono.

Motivazione: il fallback RAG→DIRECT introdotto dall'Addendum I §5 fa sì che la decisione finale non sia più puramente del router. Senza distinguere i due campi, attribuire al router decisioni che il sistema ha sovrascritto produce statistiche fuorvianti.

### 2.2 — Fallback nelle baseline fisse: decisione di asimmetria

Decisione esplicita da incorporare in `cerebro/execution/orchestrator.py`:

**Il fallback automatico (RAG → DIRECT su `low_confidence_retrieval`) si applica esclusivamente alle configurazioni di routing (`router-heuristic`, `router-confidence`). NON si applica alle baseline fisse.**

Conseguenze:

- La baseline `RAG sempre` esegue RAG anche su query con retrieval di bassa qualità, producendo prevedibilmente alcuni risultati peggiori. Questo è voluto: misura il costo di non avere fallback.
- Non si applica per simmetria nemmeno alla baseline `PLANNER_SOLVE_CRITIC sempre` — opera con i suoi parametri pieni in tutti i casi.

Motivazione: le baseline devono essere politiche pure per essere comparabili. Una baseline che applica fallback contestuali non è più una baseline ma un'altra strategia di routing, e perde la sua funzione di riferimento.

Questa decisione va documentata in `docs/phase0-design.md` con motivazione esplicita.

### 2.3 — TTFT senza streaming esposto

Modifica `cerebro/trunk/mlx_model.py`.

TTFT (time to first token) è osservabile internamente al wrapper MLX anche senza esporre streaming all'utente o all'API. Implementazione:

```python
def generate(self, prompt: str, max_tokens: int, measure_ttft: bool = True) -> GenerationResult:
    t_start = time.perf_counter()
    # invocazione iterativa del modello
    for i, token in enumerate(self._stream_internally(prompt, max_tokens)):
        if i == 0 and measure_ttft:
            ttft_ms = (time.perf_counter() - t_start) * 1000
        # ... accumulo tokens ...
    # output finale come stringa unica (no streaming esterno)
```

Cioè: il wrapper internamente itera sui token, ma ritorna solo la stringa completa. TTFT viene misurato all'interno dell'iterazione, non viene mai esposto come stream.

Aggiungere al `GenerationResult` il campo `ttft_ms: float`.

Documentare nel codice che lo streaming è disponibile internamente per la sola telemetria, non come API pubblica.

### 2.4 — Ambiguità degli operatori nelle regole del router

Le regole del router come scritte nel brief (sezione 5.2) sono ambigue sulla precedenza:

```
SE has_code_blocks OR has_math AND estimated_complexity > 0.5: → PLANNER_SOLVE_CRITIC
```

In Python questa espressione, per precedenza di `and`/`or`, viene letta come `has_code_blocks OR (has_math AND estimated_complexity > 0.5)` — cioè il codice attiva sempre PLANNER_SOLVE_CRITIC, la matematica solo sopra soglia. Probabilmente non era l'intenzione.

**Decisione da prendere — due alternative:**

**Alternativa A — Codice attiva sempre il critic:**

```
SE references_facts AND NOT has_code_blocks:
    → RAG
SE has_code_blocks:
    → PLANNER_SOLVE_CRITIC
SE has_math AND estimated_complexity > 0.5:
    → PLANNER_SOLVE_CRITIC
SE estimated_complexity > 0.7:
    → PLANNER_SOLVE
ALTRIMENTI:
    → DIRECT
```

**Alternativa B — Codice attiva il critic solo sopra soglia:**

```
SE references_facts AND NOT has_code_blocks:
    → RAG
SE (has_code_blocks OR has_math) AND estimated_complexity > 0.5:
    → PLANNER_SOLVE_CRITIC
SE estimated_complexity > 0.7:
    → PLANNER_SOLVE
ALTRIMENTI:
    → DIRECT
```

Antonio deve scegliere. **Suggerimento di chi scrive:** Alternativa B è più conservativa e produce log più puliti (meno query in PLANNER_SOLVE_CRITIC, meno overhead). Alternativa A è più aggressiva sulla qualità del codice generato a costo di latenza.

In assenza di decisione esplicita, **default Alternativa B** e issue `clarification-needed: router rule disambiguation` aperta.

---

## 3. SCHEMA INTERPRETATIVO DEL REPORT FINALE

Integra sezione 8 del brief originale e sezione 5 dell'Addendum II.

La sezione "Conclusioni" del report finale deve essere strutturata come **lettura esplicita di uno dei quattro esiti** della sezione 1 di questo addendum, ciascuno con raccomandazioni specifiche per la Fase 1.

### Esito `modalities_insufficient`

- Numeri osservati: `gain_available` ≤ soglia su tutti o quasi tutti i benchmark. Oracle ≈ best_fixed ≈ DIRECT.
- Lettura: l'orchestrazione delle quattro modalità non aggiunge capacità sopra il modello diretto. Le modalità sono ridondanti per questo trunk e questi task.
- Raccomandazione Fase 1: **non investire nel Selettore neurale.** Ripensare il set di modalità. Considerare modalità qualitativamente diverse (es. tool use, function calling esterno) invece di varianti di orchestrazione interna.

### Esito `router_blind`

- Numeri osservati: `gain_available` alto, `gain_ratio` ≤ 0 (il router peggiora o pareggia best_fixed).
- Lettura: il margine c'è ma le euristiche sintattiche non sanno catturarlo. Le modalità funzionano, il selettore no.
- Raccomandazione Fase 1: **priorità massima al Selettore neurale.** Non un router euristico raffinato — un selettore che usa segnali semantici o auto-introspettivi (vedi configurazione `router-confidence` dell'Addendum II §2 per il segnale più immediatamente promettente).

### Esito `router_partial`

- Numeri osservati: `gain_available` alto, 0 < `gain_ratio` < soglia di cattura.
- Lettura: il router euristico cattura qualcosa ma non abbastanza per giustificarsi sopra le baseline fisse. Esiste un sottoinsieme di feature predittive ma è insufficiente.
- Raccomandazione Fase 1: **analizzare il file `anomalies.jsonl` e i pattern di routing del file di log** per identificare le categorie di query dove il router funziona vs dove fallisce. Il Selettore neurale di Fase 1 va addestrato proprio sulle categorie dove l'euristica fallisce.

### Esito `success`

- Numeri osservati: tutti i vincoli rispettati.
- Lettura: l'orchestrazione locale produce un trade-off favorevole, anche con un router euristico. Il caso più ottimistico.
- Raccomandazione Fase 1: **investire in adapter sui pattern dove il router già funziona bene**, per amplificarli. Il Selettore neurale diventa secondario rispetto allo specializzare le modalità.

### Esito speciale: `capability_threshold` (incrociato con trunk di controllo)

Indipendentemente dall'esito principale, se il sottoinsieme di controllo con trunk esterno (Addendum I §3) mostra che la stessa modalità ha gain positivo sul trunk grosso e gain negativo sul trunk locale Qwen2.5-1.5B, dichiarare nel report:

> Le modalità sono sensibili alla capacità del trunk. La premessa "orchestrazione locale utile a 1.5B" è invalidata; la premessa più generale "orchestrazione utile sopra capacità soglia" resta viva.

Raccomandazione corrispondente: **prima di investire in Selettore o adapter, ripetere la Fase 0 con un trunk leggermente più grande (Qwen2.5-3B o 7B in 4-bit)** per identificare empiricamente la soglia di capacità sotto cui l'orchestrazione è controproducente.

---

## 4. PRIORITÀ DI ESECUZIONE — aggiornate

In aggiunta alle priorità delle sezioni 10 dell'Addendum I e 6 dell'Addendum II, da risolvere prima del codice:

1. **Criterio rivisto** (sezione 1 di questo addendum): Antonio conferma valori di `gain_ratio ≥ 0.5`, soglia significatività `gain_available = 5 pp`, vincoli L=2.5, E=3, requisito di estensione su 3 benchmark su 5. Modifica o conferma.
2. **Disambiguazione operatori router** (sezione 2.4): Antonio sceglie Alternativa A o B.
3. **Conferma asimmetria fallback** (sezione 2.2): conferma che il fallback non si applica alle baseline fisse.

Le priorità degli addendum precedenti restano in piedi. Apri **un'unica issue cumulativa** `clarification-needed: pre-implementation decisions` che elenca tutti i punti aperti dei tre addendum. Non procedere oltre il setup environment senza risposte complete.

---

## 5. CRITERI DI ACCETTAZIONE AGGIUNTIVI

In sostituzione del criterio Addendum II §11 punto 1, e in aggiunta agli altri:

- [ ] Criterio rivisto contro `best_fixed` implementato. Esito qualificato (`modalities_insufficient` / `router_blind` / `router_partial` / `success`) come prima riga del report finale.
- [ ] `ExecutionResult` con campi `selected_mode`, `executed_mode`, `routing_override_reason` distinti e popolati in tutti i logging.
- [ ] Tabelle del report che riportano distribuzione modalità includono entrambe le viste (selected ed executed).
- [ ] Fallback RAG→DIRECT applicato solo a configurazioni di routing, non a baseline fisse. Documentato in `docs/phase0-design.md`.
- [ ] TTFT misurato internamente al wrapper MLX, senza streaming esposto come API pubblica.
- [ ] Regole router scritte con parentesi esplicite, scelta Alternativa A o B documentata.
- [ ] Sezione "Conclusioni" del report struttura la lettura come uno dei cinque scenari della sezione 3 (quattro principali + `capability_threshold`).
- [ ] Issue cumulativa pre-implementazione chiusa con tutte le risposte di Antonio prima del primo PR di codice.

---

## 6. PRINCIPIO — perché questo addendum esiste

Il criterio di falsificazione dell'Addendum II era difendibile ma cedevole. Permetteva di chiamare successo un router che battesse la baseline più debole, anche se una baseline fissa banale avrebbe fatto meglio. Era la formulazione di chi vuole proteggere il proprio progetto dall'insuccesso.

Il criterio rivisto di questo addendum è il contrario: misura il router contro il meglio che si può ottenere senza router. Se il router non batte una regola banale del tipo "usa sempre la modalità X", il router non si giustifica. Lo schema dei quattro esiti (cinque con `capability_threshold`) impone al report di dichiarare esplicitamente quale dei casi si è verificato, evitando la narrativa positiva su qualunque risultato.

Questo è il minimo livello di onestà sperimentale a cui un progetto di ricerca dovrebbe puntare. L'Addendum II ci era arrivato a metà strada. L'Addendum III lo porta a termine.

---

*Addendum III versione 1.0 — Maggio 2026*
*La sezione 1 sostituisce integralmente la sezione 1 dell'Addendum II.*
*Tutto il resto degli Addendum I e II resta in vigore.*

---

# === 04-addendum-IV ===

# CEREBRO Phase 0 — Addendum IV

**Destinatario:** Claude Code
**Rapporto con i documenti precedenti:** integra `CEREBRO-Brief-Claude-Code.md`, `CEREBRO-Brief-Addendum.md` (Addendum I), `CEREBRO-Brief-Addendum-II.md` (Addendum II), `CEREBRO-Brief-Addendum-III.md` (Addendum III). Nessuna sostituzione di precedenti: questo addendum aggiunge tre fix e due chiarimenti.
**Stato:** vincolante.

---

## 0. PERCHÉ QUESTO QUARTO ADDENDUM

Gli addendum precedenti hanno coperto: rigore di misurazione, espansione del campo di osservazione, criterio decisionale comparativo. Restano tre buchi:

1. La consistenza del critic è misurata, ma non la sua **accuratezza** rispetto a un giudizio esterno di verità.
2. I criteri di esito si applicano al router, **non alle singole modalità** — manca un test che dichiari una modalità individuale come fallita.
3. Il progetto costruisce un router prima di sapere se il problema del routing ha una soluzione catturabile. Manca una **diagnosi strutturale del problema** indipendente dalla soluzione proposta.

Più due chiarimenti minori: visibilità dell'esito `capability_threshold` nel report e tensione concettuale sul principio di trasparenza dichiarato nel brief.

---

## 1. TEST DI ACCURATEZZA DEL CRITIC — gold standard etichettato

Integra Addendum I §4 (rubrica del critic).

L'Addendum I richiede che il critic produca giudizi consistenti su tre esecuzioni indipendenti a `temperature=0`. Questo misura **stabilità**, non **accuratezza**: un critic sistematicamente sbagliato passerà il test producendo lo stesso errore in modo riproducibile. Senza ancoraggio a un giudizio esterno, la rubrica è una pseudo-misura di se stessa.

**Aggiungere un test di accuratezza basato su gold standard etichettato manualmente.**

Procedura:

1. **Costruire un set di valutazione del critic** di 30-50 coppie `(output, ground_truth_judgment)`, dove:
   - L'output proviene da esecuzioni reali della modalità `PLANNER_SOLVE` su esempi dei benchmark (campionati casualmente con seed riportato).
   - Il `ground_truth_judgment` è prodotto da Antonio (o da un valutatore esterno qualificato) come giudizio binario sulle quattro voci della rubrica (aderenza, coerenza, uso del contesto, completezza).
   - Stratificato: includere esempi sia chiaramente corretti, sia chiaramente errati, sia ambigui. Indicativamente 40% corretti, 40% errati, 20% ambigui.

2. **Eseguire il critic** sul set di valutazione e calcolare per ogni voce della rubrica:
   - **Precision:** frazione delle critiche del critic che concordano col giudizio umano quando il critic dice "problema presente"
   - **Recall:** frazione dei problemi reali (per giudizio umano) effettivamente identificati dal critic
   - **F1** come media armonica delle due

3. **Soglia di accettabilità del critic** (da confermare da Antonio):
   - Precision ≥ 0.7 e Recall ≥ 0.6 su almeno 3 voci su 4
   - Se sotto soglia, il critic si dichiara **non affidabile** per la Fase 0, e la modalità `PLANNER_SOLVE_CRITIC` va annotata nel report come "critic accuracy below threshold", con esecuzione comunque condotta a fini di confronto ma senza valore decisionale per Fase 1.

4. **Output:** sezione dedicata nel report finale, "Validazione del critic", con tabella delle metriche per voce della rubrica e dichiarazione esplicita di affidabilità.

Implementare `scripts/validate_critic.py` con flag `--annotate` per la fase di etichettatura manuale e `--evaluate` per il calcolo delle metriche. Salvare il dataset in `benchmarks/data/critic_validation.json`.

**Costo:** 30-50 esempi etichettati manualmente = 2-3 ore di lavoro di Antonio. Più 1-2 giorni di implementazione. Significativo, ma il critic senza questo test è inutile per le decisioni di Fase 1.

---

## 2. CRITERI DI FALLIMENTO PER LE MODALITÀ INDIVIDUALI

Integra Addendum III §1 (criterio di falsificazione contro `best_fixed`).

I criteri dell'Addendum III misurano il router contro `best_fixed`. Non c'è alcun criterio per dichiarare una **modalità individuale** come fallita. La conseguenza è che la Fase 1 può scartare modalità solo sulla base di interpretazione qualitativa dei numeri aggregati.

**Aggiungere quattro criteri quantitativi, uno per modalità.** Da calcolare per ogni benchmark e riportare nel report finale come tabella separata "Validità delle modalità".

### RAG

- `retrieval_precision`: frazione di chunk recuperati con similarità sopra soglia che il modello effettivamente cita o usa nell'output (misurato come overlap di n-gram tra chunk e output, escluse stop word).
- **Soglia di fallimento:** `retrieval_precision < 0.3` e `RAG_score < DIRECT_score` significa che il modello ignora il contesto recuperato. Modalità RAG dichiarata **non efficace per questo trunk**.

### PLANNER_SOLVE

- `improvement_rate`: frazione di esempi su cui `PLANNER_SOLVE_score > DIRECT_score`, calcolata per esempio (non aggregata).
- **Soglia di fallimento:** `improvement_rate < 0.4` significa che il piano peggiora più spesso di quanto migliori. Modalità PLANNER_SOLVE dichiarata **strutturalmente controproducente per questo trunk**.

### PLANNER_SOLVE_CRITIC

- Due condizioni congiunte:
  - Test di accuratezza del critic (sezione 1 di questo addendum) sopra soglia.
  - `critic_corrections_helpful`: frazione delle revisioni del critic che migliorano effettivamente l'output (misurato confrontando lo score della risposta pre-critic con quello post-critic, per esempio).
- **Soglia di fallimento:** critic accuracy sotto soglia OR `critic_corrections_helpful < 0.5` (il critic corregge in modo neutro o peggiorativo più della metà delle volte). Modalità dichiarata **fallita**.

### DIRECT

Non si dichiara fallita. È la baseline di riferimento. Le altre modalità si dichiarano fallite **relativamente a DIRECT** per il trunk in uso.

### Conseguenze per il report

Sezione "Validità delle modalità" deve dichiarare per ciascuna modalità uno tra:
- `valid` — soglie rispettate
- `failed` — soglie non rispettate
- `untested` — se la modalità non è valutabile per ragioni tecniche (es. RAG su benchmark senza copertura nel corpus)

E nella sezione "Raccomandazioni per Fase 1" del report:
- Modalità `failed` non vengono portate in Fase 1 senza giustificazione esplicita
- Modalità `valid` ma non catturate dal router → priorità per il Selettore neurale di Fase 1

---

## 3. ANALISI DI CLUSTERING DELLE PERFORMANCE — diagnosi strutturale del problema

Nuovo requisito.

Il progetto costruisce un router prima di sapere se le query si raggruppano in regioni dove modalità diverse dominano. Se queste regioni non esistono, nessun router (euristico o neurale) può funzionare. Va misurato indipendentemente dalla performance del router.

**Aggiungere un'analisi di clustering delle performance per query** nel report finale.

Procedura:

1. **Costruire la matrice di performance:** per ogni esempio dei benchmark (su tutti e 5 — MMLU, GSM8K, HumanEval, custom IT, multi_turn_it), calcolare il vettore quadruplo:

   ```
   v_q = [DIRECT_score(q), RAG_score(q), PLANNER_SOLVE_score(q), PLANNER_SOLVE_CRITIC_score(q)]
   ```

   Dimensione della matrice: `n_esempi × 4`.

2. **Calcolare la modalità dominante per query** come `argmax(v_q)`. Se più modalità sono pareggio, marcare come "tie".

3. **Clustering non supervisionato sulle query**, usando come rappresentazione gli embedding delle query stesse (riutilizzando il modello embedding già necessario per RAG, vedi Addendum I §5). K-means con K = 4 (numero modalità), oppure clustering gerarchico con cutoff a 4-6 cluster.

4. **Per ogni cluster, calcolare la distribuzione delle modalità dominanti** (la `argmax(v_q)` di tutte le query nel cluster). Visualizzazione attesa: matrice cluster × modalità con frazione di query del cluster per cui ciascuna modalità è dominante.

5. **Interpretazione strutturale:**
   - Se in almeno un cluster una modalità è dominante per > 60% delle query, **la struttura del problema è catturabile**: esiste segnale per un selettore. Il Selettore neurale di Fase 1 può sperare.
   - Se in tutti i cluster la modalità dominante è omogenea (es. tutti i cluster hanno DIRECT dominante), **non c'è segnale per nessun selettore**: la Fase 1 non deve investire sul selettore ma sulle modalità.
   - Se la distribuzione delle modalità dominanti è uniforme in tutti i cluster, **lo spazio delle query non si struttura rispetto alle modalità**: caso peggiore, la decomposizione in modalità potrebbe essere categorialmente sbagliata per questo trunk.

6. **Output:** sezione dedicata del report "Struttura dello spazio delle modalità", con:
   - Matrice cluster × modalità
   - Visualizzazione 2D delle query con UMAP/t-SNE, colorata per modalità dominante
   - Interpretazione esplicita di uno dei tre casi sopra

**Costo implementativo:** scikit-learn per clustering, UMAP per visualizzazione. ≈1 giorno. I dati per l'analisi sono già prodotti dall'esecuzione dei benchmark.

**Valore epistemico:** questa analisi produce informazione azionabile per la Fase 1 **indipendentemente dall'esito del router**. Anche se il router fallisce e l'esito è `router_blind`, sapere se le query si strutturano permette di decidere se vale la pena costruire un Selettore neurale o se si sta inseguendo un problema senza soluzione.

---

## 4. VISIBILITÀ DI `capability_threshold` NEL REPORT

Integra Addendum III §3.

L'esito `capability_threshold` (modalità funzionano sul trunk di controllo, non sul trunk locale) è trattato dall'Addendum III come scenario speciale incrociato con gli esiti principali. **Modificare la prima riga del report finale** per dichiararlo come dimensione di pari visibilità:

```
Esito Fase 0:
- Esito principale (router): {success | router_partial | router_blind | modalities_insufficient}
- Capability threshold: {below | above | inconclusive}
- gain_available: {valore} pp, gain_ratio: {valore}
```

`below` significa: il sottoinsieme di controllo con trunk esterno mostra gain positivo dove il trunk locale mostra gain neutro o negativo. Il trunk locale è sotto soglia di capacità.

`above` significa: il trunk locale e il trunk di controllo mostrano pattern coerenti. La capacità del trunk non è il fattore limitante.

`inconclusive` significa: dati insufficienti per discriminare (es. trunk di controllo non disponibile o subset troppo piccolo).

Questa modifica non cambia la struttura degli esiti, ma garantisce che la dimensione `capability_threshold` sia visibile quanto l'esito principale del router — non un asterisco di lettura.

---

## 5. CHIARIMENTO SUL PRINCIPIO DI TRASPARENZA

Integra `docs/phase0-design.md`.

Il brief originale (sezione 9, principio 1) dichiara: "niente magia, ogni decisione automatica deve essere ispezionabile". Questo principio confligge con lo scopo dichiarato della Fase 0 di produrre evidenza per un Selettore neurale di Fase 1 che sarà, per natura, non ispezionabile direttamente.

**Aggiungere a `docs/phase0-design.md` una nota di chiarimento:**

> Il principio di trasparenza del brief si applica al **router della Fase 0** in quanto strumento diagnostico: le sue regole devono essere ispezionabili perché lo scopo della Fase 0 è capire cosa funziona e cosa no, e solo regole ispezionabili permettono questa analisi.
>
> Il principio non si applica nello stesso modo al **Selettore neurale della Fase 1**, che sarà un componente di produzione validato esternamente sulle metriche prodotte dalla Fase 0. La sua opacità è accettabile a condizione che la sua performance sia certificata su dati di test indipendenti.
>
> Riformulazione operativa del principio: "trasparenza degli strumenti di analisi, validazione esterna dei componenti di produzione". Le due cose non sono in conflitto: sono ruoli epistemici diversi.

Aggiunge una sezione al design doc, non modifica il brief. Risolve la tensione concettuale senza richiedere riprogettazione.

---

## 6. PRIORITÀ DI ESECUZIONE — aggiornate

In aggiunta alle priorità precedenti:

1. **Conferma delle soglie per il test del critic** (sezione 1): precision ≥ 0.7, recall ≥ 0.6, oppure valori alternativi.
2. **Conferma delle soglie per le modalità individuali** (sezione 2): `retrieval_precision`, `improvement_rate`, `critic_corrections_helpful`, con i valori suggeriti o modificati.
3. **Disponibilità di Antonio per etichettare 30-50 esempi del set di validazione critic** (sezione 1, punto 1). Va programmato come task esplicito, non assunto.

Aggiungere all'issue cumulativa pre-implementazione `clarification-needed: pre-implementation decisions`.

---

## 7. CRITERI DI ACCETTAZIONE AGGIUNTIVI

In aggiunta ai criteri degli addendum precedenti:

- [ ] Set di validazione del critic creato e etichettato manualmente prima del run finale.
- [ ] Metriche di accuratezza del critic (precision/recall/F1 per voce della rubrica) calcolate e riportate nel report.
- [ ] Validità di ciascuna modalità (`valid` / `failed` / `untested`) dichiarata nel report con soglie esplicite.
- [ ] Analisi di clustering delle performance per query eseguita e riportata come sezione dedicata.
- [ ] Visualizzazione 2D delle query (UMAP/t-SNE) inclusa nel report.
- [ ] Esito `capability_threshold` riportato come dimensione di pari visibilità nella prima riga del report.
- [ ] Nota di chiarimento sul principio di trasparenza presente in `docs/phase0-design.md`.

---

## 8. PRINCIPIO

Gli addendum precedenti hanno reso il progetto **misurabile**. Questo addendum lo rende **diagnostico**.

La differenza è: un progetto misurabile dice "il router ha funzionato o no". Un progetto diagnostico dice anche "**perché** ha funzionato o no", e "se non fosse il router, sarebbe potuto funzionare qualcos'altro". L'analisi di clustering risponde alla seconda domanda indipendentemente dall'esito del router. Il test del critic risponde alla prima per uno dei componenti critici. Le soglie sulle modalità individuali permettono di non confondere un fallimento dell'orchestrazione con un fallimento di una specifica modalità.

Senza queste tre cose, la Fase 0 può misurare onestamente senza saper interpretare. Con queste tre cose, il report finale produce decisioni difendibili per la Fase 1 anche nello scenario peggiore in cui tutto fallisce: si sa cosa è fallito, perché, e cosa resta possibile.

---

*Addendum IV versione 1.0 — Maggio 2026*
*Nessuna sostituzione di precedenti. Tre fix e due chiarimenti.*

---
