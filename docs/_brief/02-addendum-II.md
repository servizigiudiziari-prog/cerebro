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
