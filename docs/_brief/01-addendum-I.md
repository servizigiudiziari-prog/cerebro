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
