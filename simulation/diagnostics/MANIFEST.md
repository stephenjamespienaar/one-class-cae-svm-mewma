# Diagnostic audit manifest

- **Date of analysis:** 2026-09-24
- **Source repository (read-only):** `<original-workspace>/pipeline-thesis-independent`
- **Source commit:** `1993315d28a7f6a3fb3980c4ea33a95459d29810` (branch `simplify-pipeline-code`)
- **Initial working tree:** `M 01_pipeline.ipynb`, `M 02_results.ipynb`, `M README.md`, `?? .serena/`, `?? figures/`, `?? thesis_plots.py`
  (snapshot: `git_status_initial.txt`; SHA-256 of every file outside `.git/` and `.venv/`: `source_tree_sha256_initial.txt`)
- **Final verification:** `git_status_final.txt`, `source_tree_sha256_final.txt` (identical to the initial snapshots)
- **Audit workspace:** `<original-workspace>/pipeline-thesis-diagnostic`

## Environment

Python 3.14.4 (the source repository's own `.venv`, run with `python -B` and
`PYTHONDONTWRITEBYTECODE=1`; nothing installed or modified in it).
numpy 2.4.6, torch 2.13.0, scikit-learn 1.9.0, scipy 1.18.1, matplotlib 3.11.1,
pandas 3.0.5, threadpoolctl 3.6.0. LaTeX: MiKTeX-pdfTeX 4.26 (MiKTeX 26.2) and
latexmk 4.88 on the Windows host, called through WSL interop; no shell escape.

## Scripts (run in this order from `scripts/`)

| Script | Purpose | Randomness |
|---|---|---|
| `dump_notebooks.py` | notebook code + text outputs to `diagnostics/*.txt` | none |
| `common.py`, `plotstyle.py`, `charts.py` | shared helpers (read-only import of `pipeline.py`) | none |
| `s01_cache_and_verify.py` | frozen-model features for D3, D4, D5 (cached in `diagnostics/cache/`); bitwise checks of data regeneration, moments, limits, all 96 D4/D5 run-length cells | none |
| `s02_committed_results.py` | canonical result tables and figures | paired bootstrap, seed 20260924, B = 4000 |
| `s03_geometry.py` | fault geometry, information rates, ACFs, OC-SVM audit, latent geometry | deterministic subsampling |
| `s04_mewma_startup.py` | IC T2 profiles, first-report analysis, i.i.d. limits, calibration bootstrap | i.i.d. limits seed 4242 (2000 reps); calibration bootstrap seed 5150 (B = 200) |
| `s05_counterfactuals.py` | diagnostic charts M0, W4, L8, Hspe and the dependence-corrected (V) family; pooled D3+D4 calibration | none (canonical banks) |
| `s06_late_change.py` | change during monitoring (tau = 132): 500 new replications per delta, 15 deltas | `SeedSequence([6, round(1000*delta), replication, 795])` |
| `s07_cae_audit.py` | in-process CAE retraining check, reconstruction diagnostics, linear probe | pipeline training seed 3795 (as documented) |
| `s08_trajectories.py` | representative replication trajectories | none |
| `s09_cf_figures.py` | counterfactual figures | none |
| `s10_assemble.py` | delay budget (paired SEs), SPE sum/mean check, LaTeX tables and macros | none |

Process-local monkey-patch (s06 only): `pipeline.CHANGE_POINT` set to 132 inside a
`try/finally` around one `simulate()` call and restored immediately (asserted).

## Sample sizes

Canonical banks as committed: D3 300 x 3000, D4 500 x 3000, D5 15 x 500 x 3000.
New simulation (s06 only): 15 x 500 x 3000 in-control-then-shifted trajectories.

## Cache

`diagnostics/cache/` (about 2.8 GB) holds frozen-model features for D3, D4 and the D5 banks and the
new late-change banks. It is a regenerable cache (deterministic; `s01` and `s06` rebuild it in a
few minutes) and can be deleted safely.

## Outputs

`hybrid_mewma_diagnostic_report.tex/.pdf`, `figures/` (PDF + PNG), `tables/` (LaTeX
fragments and `macros.tex` used by the report), `diagnostics/*.json` (all numbers).
