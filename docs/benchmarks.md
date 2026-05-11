# Benchmarks — how to reproduce

This document is a placeholder filled out by the
`[Phase 0] Benchmark suite` and `[Phase 0] Documentation and reproducibility`
issues. Once those land, this page covers:

- Data sources (MMLU, GSM8K, HumanEval, custom IT) and how to fetch them
- Exact configurations: which CEREBRO mode runs on which benchmark
- How to compute and report scores (per benchmark)
- How to compute and report latency (TTFT, tok/s, total, p50/p90/p99)
- How to compute and report energy (`powermetrics` setup + sudo notes)
- How to regenerate `results/phase0_report.md`

Minimal command (once implemented):

```bash
uv run python benchmarks/run_all.py
uv run python scripts/run_phase0_report.py --out results/phase0_report.md
```

Until then, see `cerebro/cli.py` and `cerebro/execution/orchestrator.py`
stubs and the corresponding issues for status.
