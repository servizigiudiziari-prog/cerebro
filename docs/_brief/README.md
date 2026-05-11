# Brief autorevole — leggere PRIMA del codice

Questa cartella contiene il materiale autorevole consegnato dal committente
(Antonio) per la Fase 0 di CEREBRO. Sono i documenti normativi del
progetto: in caso di conflitto fra codice/PR e questi documenti, vincono
questi documenti.

## File

| Ordine | File                  | Origine in `~/Downloads/`                    | Dimensione |
|--------|-----------------------|----------------------------------------------|------------|
| 0      | `00-brief.md`         | `CEREBRO-Brief-Claude-Code.md`               | 16.9 KB    |
| 1      | `01-addendum-I.md`    | `CEREBRO-Brief-Addendum.md`                  | 12.0 KB    |
| 2      | `02-addendum-II.md`   | `CEREBRO-Brief-Addendum-II.md`               | 14.6 KB    |
| 3      | `03-addendum-III.md`  | `CEREBRO-Brief-Addendum-III.md`              | 15.0 KB    |
| 4      | `04-addendum-IV.md`   | `CEREBRO-Brief-Addendum-IV.md`               | 14.5 KB    |

I file mantengono il contenuto originale dei documenti consegnati. I nomi
sono rinumerati per imporre l'ordine di lettura corretto (un `ls` li mostra
in ordine cronologico di consegna).

## Regole di precedenza (autodichiarate negli addendum)

1. **Tutti gli Addendum prevalgono sul brief base** (`00-brief.md`) in caso
   di conflitto. Lo dichiarano esplicitamente le loro intestazioni.
2. **Addendum III §1 sostituisce integralmente Addendum II §1**. Il
   criterio di falsificazione iniziale (router vs `DIRECT`) è ritirato; il
   criterio rivisto è router vs `best_fixed` con quattro esiti qualificati
   (`modalities_insufficient` / `router_blind` / `router_partial` /
   `success`).
3. **Resto dell'Addendum II resta in vigore** (router-confidence config,
   benchmark multi-turn IT, anomalies log, nota cecità sintattica router).
4. **Addendum IV non sostituisce nulla**: aggiunge 3 fix (validation
   critic con gold standard, criteri fallimento per modalità individuali,
   analisi clustering performance) e 2 chiarimenti (visibilità
   `capability_threshold`, principio di trasparenza Fase 0 vs Fase 1).

## Cosa fare se trovi un conflitto

1. Verifica la data di ciascun documento e applica la regola di precedenza
   sopra.
2. Se il conflitto persiste, NON decidere unilateralmente: apri un'issue
   `clarification-needed` su GitHub con il riferimento esatto ai paragrafi
   in disaccordo e attendi risposta di Antonio.

## File concatenato per upload a un LLM esterno

`ALL_CONCATENATED.md` (~73 KB, 1.328 righe) contiene tutti e 5 i file in
sequenza, con header di separazione e regole di precedenza in apertura. È
generato da uno script `cat`-style: se modifichi un singolo file, va
rigenerato (vedi commit di bootstrap). Utile per upload manuale a Claude
web, ChatGPT, Gemini, ecc. quando vuoi un secondo parere sull'intero
materiale autorevole.

Comando di rigenerazione (da repo root):
```bash
{
  echo "# CEREBRO Phase 0 — Authoritative Material (concatenated)"
  echo ""
  echo "Generated from \`docs/_brief/\`. Read order: brief base → I → II → III → IV."
  echo ""
  for f in docs/_brief/0[01234]-*.md; do
    echo ""
    echo "# === $(basename "$f" .md) ==="
    echo ""
    cat "$f"
    echo ""
    echo "---"
  done
} > docs/_brief/ALL_CONCATENATED.md
```

## Specifica tecnica completa (assente)

Il brief base §0 cita `CEREBRO-v2-Specifica-Tecnica.md` come materiale
companion. Quel documento **non è stato consegnato** al 2026-05-11. Per la
Fase 0 si lavora esclusivamente con i 5 file sopra; se una decisione tocca
forward-compat con fasi 1+ ed è bloccante senza la specifica, apri un
`clarification-needed`.
