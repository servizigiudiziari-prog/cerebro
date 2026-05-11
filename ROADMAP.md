# CEREBRO — Roadmap

> Da prototipo Phase 0 a sistema usato nel mondo. Documento strategico
> vivo; ogni modifica passa da un commit con motivazione esplicita.
> Le **date sono indicative** e si aggiornano dopo ogni release. La
> roadmap è **anti-iperbole**: niente promesse non difendibili, niente
> "rivoluzione", niente date che assumono zero attriti.

**Ultima revisione**: 2026-05-11
**Stato attuale**: bootstrap repo (commit `284866a`); 9 issue Phase 0
aperte; Fase 0 governata da `docs/_brief/` (brief base + 4 addenda).

---

## 0. Tesi strategica (sopra cui sta tutto il resto)

CEREBRO scommette su tre cose, in quest'ordine:

1. **Hardware locale Apple Silicon è abbastanza per orchestrazione utile**
   a livello di assistente personale e di assistente da sviluppatore, se
   il software è progettato attorno ai limiti di quel hardware invece di
   trattarlo come una versione lenta del cloud.
2. **L'orchestrazione modulare di un trunk piccolo batte un trunk grosso
   denso usato come oracolo monolitico**, su sotto-task ben caratterizzati,
   a parità di latenza/energia. Questa è l'ipotesi che la Phase 0 sta
   testando in modo falsificabile (vedi `docs/_brief/03-addendum-III.md`
   §1).
3. **Esiste uno spazio di prodotto open-source** fra Ollama/LM Studio (run
   un modello locale) e GPT-4-via-Cursor (assistente sviluppatore frontier
   chiuso). Lo spazio è: "agente personale locale che decide come pensare,
   non solo cosa generare". Nessun progetto open al 2026-05-11 lo occupa
   in modo serio.

Se una di queste tre cade, la roadmap si riscrive. Le tre ipotesi sono
falsificabili e ognuna ha milestone di verifica.

---

## 1. Asse tecnico — da prototipo a sistema

### Phase 0 — Validazione (2-3 settimane, **in corso**)

**Governata da** `docs/_brief/` (brief base + Addenda I–IV). **Letti
PRIMA di scrivere codice.**

Esce con un **report onesto** (`results/phase0_report.md`) che dichiara
come prima riga l'esito qualificato (`success` / `router_partial` /
`router_blind` / `modalities_insufficient`) + il `capability_threshold`
e i numeri `gain_available` / `gain_ratio`. Tag `v0.1.0-phase0`.

**Decisione di soglia**: se l'esito è `modalities_insufficient` *o*
`router_blind` su tutti i benchmark, la **Phase 1 si ridisegna**, non
si esegue come pianificato qui. La roadmap onora il risultato negativo.

#### Strategia di implementazione: slice testabile prima del setup modelli

Il brief §7.2 elenca l'ordine foundational delle issue partendo da
Trunk MLX (#1). L'ordine **di consegna del valore** è quello. L'ordine
**di implementazione testabile** è diverso e migliore (review esterna
Codex 2026-05-11, registrata in `docs/reviews/`):

1. **Issue #2 (router + features) prima**: implementabile senza modelli,
   senza retrieval, senza GPU. Coverage > 70% con test puri.
2. **Issue #4 (4 modes) contro un `FakeTrunk`**: `FakeTrunk` implementa
   l'interfaccia `MlxTrunk.generate()` ritornando stringhe canned dal
   test. Permette di testare orchestratore, fallback, critic loop in
   modo deterministico senza dipendenze pesanti.
3. **Issue #1 (trunk MLX reale)**: integrato dietro la stessa
   interfaccia. A questo punto il sistema è osservabile end-to-end.
4. **Issue #3 (LanceDB RAG)**: in parallelo a #1, ma il router gira già
   senza retrieval.
5. Il resto (#5 telemetria, #6 benchmark, #7 custom IT, #8 CLI, #9
   docs) segue.

Razionale: il rischio principale del bootstrap è "affogare nel setup
modelli" (download Qwen, conversione MLX, ingestion Wikipedia 100k →
ore di lavoro prima del primo segnale di vita). Iniziando da router +
modes con `FakeTrunk`, c'è un sistema in moto già al giorno 2-3 e il
debug iniziale si fa senza GPU. Il brief §7.3 esclude esplicitamente
da `clarification-needed` le scelte di ordine di operazioni, quindi
questa è una scelta del maintainer.

#### Issue Phase 0 (totale 17 + 1 chiarimento, 2026-05-11)

Brief base: #1-9 (foundational). Addenda I-IV: #11-#18 (extension).
Tensioni: #10 (`torch` via `sentence-transformers`,
`clarification-needed`). Lista completa con `gh issue list --label
phase-0` sul repo.

### Phase 1 — Adapter e fine-tuning leggero (4-6 settimane)

**Pre-requisito**: Phase 0 chiusa con esito ≠ `modalities_insufficient`,
e analisi clustering performance (Addendum IV §3) mostra struttura
catturabile.

- **LoRA-tuning di Qwen2.5-1.5B su pattern emersi**: una LoRA per
  modalità (DIRECT/RAG/PLANNER_SOLVE/PLANNER_SOLVE_CRITIC) addestrata sui
  cluster di query dove quella modalità domina ex-post.
- **Fusion**: il trunk base resta uno. Le LoRA si attivano per
  modalità senza moltiplicare il footprint memoria.
- **Validazione**: ri-eseguire l'intero benchmark Phase 0 (5
  configurazioni) con le LoRA attive. Confronto `gain_ratio` pre/post.
  Successo se almeno una modalità migliora ≥10 pp su uno dei benchmark
  senza degradare le altre.
- **Rischio principale**: i dataset di training per le LoRA sono piccoli
  (~500-2000 esempi per modalità). Probabile overfitting. Mitigation:
  augmentation tramite il trunk di controllo (Sonnet 4.6 via API,
  Addendum I §3).

Tag esteso `v0.2.0-phase1-adapters`.

### Phase 2 — Selettore neurale (4-6 settimane)

**Pre-requisito**: Phase 1 chiusa, o esito Phase 0 = `router_blind` (dove
priorità Selettore è diretta, Addendum III §3).

- **Modello selettore**: classifier piccolo (~20-50M parametri o
  embedding+MLP) addestrato sui `(query, executed_mode_with_best_score)`
  raccolti in Phase 0+1. Input: embedding della query (e opzionalmente
  segnale di confidence del trunk, vedi Addendum II §2). Output:
  distribuzione su 4 modalità.
- **Confronto rigoroso vs router euristico**: stessi benchmark, stesso
  protocollo di significatività (Wilson 95%). Il delta selettore vs
  oracle è la metrica chiave.
- **Eval bias-aware**: held-out **20%** dei dati di training MAI visti
  durante validation. Il rischio data-leakage qui è alto.

Tag `v0.3.0-phase2-selector`.

### Phase 3 — Memoria episodica + procedurale (4 settimane)

Phase 0/1/2 lavorano in modalità "single-shot per query". Una memoria
seria cambia il prodotto.

- **Memoria episodica**: per ogni esecuzione, salvataggio (query, mode,
  output, telemetry, user_feedback se presente). Recupero per similarità
  semantica con tag temporale.
- **Memoria procedurale**: pattern ricorrenti dell'utente (es. "ogni
  lunedì chiede status di X") che diventano shortcut o pre-fetch.
- **Privacy by default**: tutto locale, niente sync cloud non
  esplicitamente abilitata.

Tag `v0.4.0-phase3-memory`.

### Phase 4 — Tool use + function calling (4 settimane)

A questo punto CEREBRO smette di essere "un LLM con quattro modalità" e
diventa un agente.

- **Tool primitive**: shell (read-only), filesystem (whitelist), HTTP
  GET, calculator. Estensibile.
- **Tool calling protocol**: schema compatibile con OpenAI function
  calling per facilitare migration in entrambi i sensi.
- **Sandbox**: ogni tool call con preview + diff prima dell'esecuzione
  destruttiva. Pattern già conosciuto da antonio-agent.

Tag `v0.5.0-phase4-tools`.

### Phase 5 — Hardening, multi-trunk, cross-platform (3 settimane)

- **Multi-trunk swap**: il trunk MLX (Qwen 1.5B) deve essere
  sostituibile a runtime (Qwen 3B, Llama 3.2 3B, Mistral piccoli) senza
  ri-addestrare LoRA — perché le LoRA sono per-modello.
- **Cross-platform tentativo**: backend llama.cpp per Linux/Windows
  GPU. Apple Silicon resta first-class.
- **Production-grade**: structured config, telemetry export
  (Prometheus/OpenTelemetry), error handling robusto.

Tag `v1.0.0-stable`.

---

## 2. Asse prodotto — da codice di ricerca a software usabile

Procede **in parallelo** all'asse tecnico, non in sequenza.

### Product-A — Developer experience (parallelo a Phase 1)

- **One-liner install**: `curl ... | sh` che fa setup + download modello
  + ingestion Wikipedia in <10 minuti.
- **CLI ergonomica**: `cerebro ask`, `cerebro chat`, `cerebro bench`,
  `cerebro doctor` (verifica setup), `cerebro why` (spiega routing
  scelto su una query — diagnostic).
- **Logging human-friendly**: la default deve essere leggibile, non
  JSON; `--json` esplicito per pipe.

### Product-B — Modalità interattive (parallelo a Phase 2)

- **REPL multi-turn** con memoria di sessione.
- **Streaming output al terminale** (lo streaming era escluso da Phase 0
  per misurazione TTFT pulita, Addendum III §2.3; da Phase 2 in poi si
  espone come API utente).
- **`cerebro chat --persona <name>`**: profili (programmatore, scrittore,
  legale) che caricano prompt template + memoria dedicata.

### Product-C — Integrazione IDE (parallelo a Phase 3-4)

- **Plugin VS Code**: usa CEREBRO come backend per code completion +
  spiegazioni. Differenziatore vs Copilot/Cursor: tutto locale, zero
  costo API, lavora offline.
- **Plugin Raycast** (macOS): comando rapido `cerebro` da spotlight.
- **Plugin Neovim / JetBrains**: target Phase 4.

### Product-D — Edge platforms (parallelo a Phase 5)

- **iPad/iPhone via MLX-Swift**: target ambizioso, non bloccante. Vale la
  pena solo se la fama del progetto giustifica lo sforzo.
- **Linux GPU** via llama.cpp backend.

---

## 3. Asse visibilità — da progetto a sistema noto

Onestà: "famoso in tutto il mondo" è un obiettivo **non interamente
controllabile**. Si controlla la **qualità del lavoro** e la **qualità
della comunicazione**. Il resto è amplificazione che si compra (PR pagato,
sconsigliato) o si guadagna (referer da grandi nomi, fortuna).

### Stage-I — Open source release (alla v0.2.0-phase1)

- **Repo pubblico** su GitHub. Oggi `servizigiudiziari-prog/cerebro` è
  privato; transizione a pubblico solo quando il README quickstart
  funziona davvero in <10 minuti su una macchina pulita (testato da una
  terza persona).
- **README in inglese** (mantenere copia IT). Quickstart, demo GIF/video
  di 30 secondi, link al report Phase 0.
- **Apache 2.0** in alternativa a MIT (più chiara su brevetti, pattern
  che progetti AI seri usano).
- **CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md**: dovere
  professionale, non opzionale.

### Stage-II — Comunicazione tecnica (continuativo, dal release)

Frequenza target: un articolo ogni 4-6 settimane per i primi 6 mesi
post-release.

- **Blog post di lancio** sul sito personale di Antonio (label tecnica
  separata da AntPitLab): "Why CEREBRO: orchestrating a small local LLM".
  Cross-post su dev.to e Hacker News (Show HN: ...).
- **Reddit r/LocalLLaMA**: post tecnico con numeri (non hype). Quella
  community premia onestà sui benchmark e punisce overclaim.
- **Twitter/X + Mastodon + Bluesky**: thread di lancio con grafici dei
  benchmark. Triplicare il post, non bruciarsi solo su una piattaforma.
- **YouTube/video tecnico**: walkthrough di 10-15 minuti del progetto +
  report Phase 0. Audience: developer curiosi di local LLM.

### Stage-III — Paper scientifico (target Phase 2 chiusa, ~mese 12)

- **Workshop NeurIPS / ICLR / ICML** prima di una conference principale.
  Workshop accetta paper più piccoli e in-progress.
- **Tema**: "Heuristic vs neural routing for local LLM orchestration:
  honest empirical study". Il valore del paper è il metodo, non il
  risultato — anche un risultato negativo (Phase 0 = `router_blind`) ha
  un paper interessante (cecità sintattica, Addendum II §5).
- **Reproducibility**: paper companion = repo. Tutti i risultati
  riproducibili in <24h su un M-series 16GB.
- **Pre-print su arXiv** prima della submission.

### Stage-IV — Conferenze / talk (target dal mese 12)

- **PyData / PyCon**: talk applicativo, audience developer.
- **Apple WWDC**: se il progetto cattura attenzione interna ad Apple per
  la qualità su MLX, richiesta per sessione community è possibile (poco
  controllabile).
- **AI conferences regionali**: BAAI, AI for Good, eventi locali italiani
  (PyCon Italia, Codemotion). Più realistici a breve.

### Stage-V — Community (target dal mese 12)

- **Discord o Zulip pubblico**: solo se c'è momentum reale (>500 stars
  GitHub). Una community vuota è peggio di nessuna community.
- **Contributor program**: issue etichettate `good-first-issue`,
  documentazione di onboarding, code review responsiva (<48h).
- **Showcase progetti utenti**: pagina con applicazioni di terzi che
  usano CEREBRO come backend.

---

## 4. Asse affidabilità — onestà operativa continua

Vincoli che valgono **in ogni fase**, non solo nelle release.

- **Eval honesty (Addendum I §2, III §1)**: ogni release dichiara
  `gain_available`, `gain_ratio`, esito qualificato. Niente cherry-picking
  di benchmark.
- **Reproducibility (brief §6.5)**: setup → bench → report in <1 ora
  uomo su una macchina pulita. Verificato a ogni release da una persona
  che non ha visto il codice.
- **Determinismo**: temperature 0, seed fissato, hash dei modelli
  registrato in ogni run.
- **Hardware honesty**: README dichiara esattamente su quale M-series è
  stato misurato. Niente "M-series" generico.
- **Cost honesty**: latenza in p50/p90/p99, energia se misurata. Niente
  medie da sole.
- **Vendor lock-in zero**: nessuna dipendenza obbligatoria a servizi
  cloud o API a pagamento. Il trunk di controllo via API è solo per
  validazione, mai per uso di produzione.

---

## 5. Milestone temporali (scenari, non promesse)

| Mese | Stato auspicato                                              | Verifica |
|------|--------------------------------------------------------------|----------|
| 1    | Phase 0 chiusa, `v0.1.0-phase0`, report onesto.              | Tag git + CI verde + report committato in `results/`. |
| 3    | Phase 1 chiusa, `v0.2.0`, repo pubblico, primo blog post.    | Repo public, blog post live, ≥1 PR esterna anche se piccola. |
| 6    | Phase 2 chiusa, `v0.3.0`, post HN/Reddit.                    | ≥500 GitHub stars, ≥3 issue da utenti reali. |
| 9    | Phase 3 chiusa, `v0.4.0`, primo plugin IDE (VS Code).         | Plugin installabile, ≥50 install. |
| 12   | Phase 4 chiusa, `v0.5.0`, pre-print arXiv, paper sottoposto. | arXiv link pubblico, paper su workshop. |
| 18   | `v1.0.0-stable`, talk a PyCon Italia o equivalente.          | Tag stabile, slide pubbliche, video registrazione. |
| 24   | ≥2.000 GitHub stars, ≥10 contributor attivi.                 | Numeri verificabili su GitHub. |
| 36   | Paper su conference principale (NeurIPS/ICLR/ICML).          | Accettato. Se rifiutato, riproporre. |
| 48   | Integrazione con almeno un tool noto (Cursor, Raycast, ...). | Riferimento ufficiale del tool a CEREBRO. |

**Numeri ≠ obiettivi rigidi.** Se al mese 6 ci sono 200 stars ma 20
contributor attivi, è meglio di 5.000 stars senza nessuno che contribuisce.
La metrica vera è "il progetto si sostiene da solo senza che Antonio sia
l'unico a spingerlo".

---

## 6. Rischi e mitigation

### Rischio R-001 — La tesi Phase 0 fallisce (esito `modalities_insufficient`)

**Probabilità**: 25-35%. Le 4 modalità sintetizzate da letteratura
potrebbero non differenziare su Qwen 1.5B.

**Mitigation**: Phase 0 prevede già il `capability_threshold` (Addendum
III §3, IV §4) che riapre il problema con un trunk più grande (3B/7B). La
roadmap diventa: replicare Phase 0 su trunk diverso prima di Phase 1.

### Rischio R-002 — Apple deprecate MLX o cambia strategia

**Probabilità**: 10-15% sui 4 anni.

**Mitigation**: backend swappable previsto in Phase 5. Il codice non è
mai stato accoppiato direttamente a `mlx_lm` (il wrapper trunk astrae).

### Rischio R-003 — Competitor open-source superano CEREBRO prima del
release

**Probabilità**: 40-50%. È un campo affollato (Ollama, LM Studio, Open
Interpreter, dspy, langchain locale, ecc.).

**Mitigation**: differenziatore = **router/selettore che pensa prima di
generare**, niente di analogo open al 2026-05-11. Se qualcuno arriva
prima con la stessa idea, CEREBRO si reposiziona come "implementazione
più rigorosa empiricamente" (paper + benchmark riproducibili) invece di
"primo a farlo".

### Rischio R-004 — Burnout di Antonio (singolo maintainer)

**Probabilità**: 30-40% senza mitigation, alta sulla finestra 24 mesi.

**Mitigation**: roadmap pubblica per attirare contributor genuini.
Funding via GitHub Sponsors / Open Collective dopo Stage I-II se la
community esiste. Anti-mitigation: NON cercare investimenti VC. La forma
"side-project ben fatto" è sostenibile, "startup con cap table" non lo è
con questo scope.

### Rischio R-005 — Drift di scope ("aggiungiamo questa feature simpatica")

**Probabilità**: 50%+. Endemica di tutti i side-project.

**Mitigation**: questa roadmap è il documento di anti-drift. Ogni issue
non in roadmap richiede un commento del tipo "perché ora, perché qui".
Issue rifiutate vanno in `docs/_brief/parking-lot.md`.

---

## 7. Anti-roadmap — cosa NON facciamo, per chiarezza

- **No SaaS hosting commerciale.** CEREBRO è local-first. Niente
  `cerebro.cloud`, niente cap table, niente revenue dipendente da uptime.
- **No competizione con frontier model providers** (OpenAI, Anthropic,
  Google). CEREBRO usa modelli piccoli locali; il caso d'uso è
  complementare, non concorrenziale.
- **No GUI grafica monolitica.** Plugin per editor/IDE sì, applicazione
  Electron standalone no. Sarebbe un secondo prodotto.
- **No fork di llama.cpp / Ollama.** CEREBRO orchestra, non
  re-implementa il runtime. Backend swappabili, sì.
- **No "agentic AGI" claim.** CEREBRO è un orchestratore di modalità
  esplicite con regole esplicite (Phase 0) o un selettore neurale
  validato empiricamente (Phase 2+). Niente narrativa di
  "ragionamento emergente".
- **No closed-source layer.** Tutto il codice di produzione è open
  source. Eventuali utility interne private (es. credenziali API per
  benchmark) vivono fuori repo.
- **No premature optimization per modelli che ancora non esistono.** La
  roadmap si aggiorna quando esce un trunk MLX 7B competitivo, non
  prima.

---

## 8. Come si aggiorna questo documento

- **Editor primario**: il maintainer (Antonio o agente delegato Opus 4.7
  + ultrathink — vedi `memory/preferences.md` § "Modello e ragionamento"
  in `antonio-agent`).
- **Cadenza**: revisione obbligatoria a ogni tag (`v0.X.0`). Revisione
  spot-check ogni 4 settimane.
- **Modifiche sostanziali** (cambio di tesi, eliminazione di una phase,
  spostamento >2 mesi di una milestone) → commit dedicato con messaggio
  che spiega cosa è cambiato e perché.
- **Modifiche cosmetiche** → squash in commit di manutenzione.

---

## 9. Definition of done della roadmap stessa

La roadmap è "fatta bene" quando:

1. Un contributor nuovo che legge solo `ROADMAP.md` + `docs/_brief/`
   sa cosa sta succedendo e dove può aiutare.
2. Un osservatore esterno (giornalista tech, reviewer accademico) può
   verificare claim e milestone leggendo solo questo documento + il repo.
3. Quando una milestone manca, si capisce dal commit history **perché**
   è mancata e cosa si è imparato.
4. Nessuna sezione contiene aggettivi superlativi senza un numero
   verificabile vicino.

Se uno di questi quattro punti cede, la roadmap va riscritta, non
toppata.
