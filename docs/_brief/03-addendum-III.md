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
