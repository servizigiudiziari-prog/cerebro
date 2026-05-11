# results/

Output of benchmark runs lives here. **Everything in this directory is
gitignored except this README and `.gitkeep`.**

Expected artefacts (after `[Phase 0] Benchmark suite` lands):

- `phase0_report.md` — final report (committed manually at release time)
- `runs.jsonl` — one JSON line per single query, with telemetry
- `bench/<benchmark>/<configuration>/scores.json` — per-cell scores
- `bench/<benchmark>/<configuration>/latencies.csv` — raw latencies

The report is regenerated with:

```bash
uv run python scripts/run_phase0_report.py --out results/phase0_report.md
```
