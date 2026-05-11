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
