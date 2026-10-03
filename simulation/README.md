# Simulation study

This is the pre-specified simulation experiment behind thesis Sections 3–4 and Appendices A–D.

A nonlinear four-variable process is driven by an eight-dimensional latent VAR(1). The fault is a
sustained latent mean shift of 15 sizes (δ = 0.2, 0.4, …, 3.0). Five independent datasets separate
the roles:

| Dataset | Role |
|---|---|
| D1 | train the CAE |
| D2 | fit the OC-SVM |
| D3 | estimate in-control moments and calibrate all six charts to ARL0 = 370 |
| D4 | independent in-control validation |
| D5 | out-of-control evaluation |

The study shows that the hybrid chart H(0.05) beats its single-component ablations S(0.05) and
R(0.05) at every shift. It does not beat the classical MEWMA M(0.05) on the raw variables.

## Contents

| Path | What it is |
|---|---|
| `pipeline.py` | The complete implementation: simulator, D1–D5 generation, windowing, CAE, OC-SVM, monitoring vector, MEWMA, calibration and Phase II evaluation. All design constants are at the top. |
| `methodology.md` | Detailed scientific specification |
| `models/` | Frozen Phase I artifacts: preprocessing, CAE weights, OC-SVM, D3 moments, control limits |
| `results/` | Published Phase II results: `d4_validation_summary.json`, `d5_performance_summary.json`, `run_lengths.npz` (every run length) |
| `tests/test_pipeline.py` | 21 regression tests covering the frozen constants, artifacts, MEWMA conventions and committed results |
| `reproduce_all.py` | From-scratch production run (generate → train → fit → calibrate → evaluate) |
| `01_pipeline.ipynb`, `02_results.ipynb`, `thesis_plots.py` | Methodology walkthrough and results analysis. They write `figures/`. |
| `figures/` | Notebook figures (PDF and PNG). Thesis Figures 7 and 8 are copies of two of them. |
| `reproduction-report-G8ud52MN/` | Log and timing of the original from-scratch run (206.58 s). `thesis/scripts` reads `production.log`. |
| `diagnostics/` | Evidence for three post-hoc numbers quoted in thesis Section 4.5. Not part of the production pipeline; see [`diagnostics/README.md`](diagnostics/README.md). |

## Run the tests

```bash
cd simulation
python -m pytest tests          # 21 passed
```

## Verify the published results

**Phase II from the committed models.** This takes about 3.5 minutes and writes 761 MB of
ignored data under `data/generated/`. It rewrites `results/` byte-for-byte unchanged.

```bash
cd simulation
python -c "import pipeline; pipeline.generate_datasets('data/generated')"
python -c "import pipeline; pipeline.evaluate_phase2('data/generated')"
git status --short results/     # no output: the results are reproduced exactly
```

**Full study from scratch** (about 3.5 minutes). `reproduce_all.py` refuses to overwrite existing
`data/`, `models/` or `results/`, so run it in an empty copy and compare:

```bash
REPO=$PWD                       # repository root
mkdir /tmp/simulation-rerun && cp simulation/pipeline.py simulation/reproduce_all.py /tmp/simulation-rerun/
cd /tmp/simulation-rerun && python reproduce_all.py
for f in models/* results/*.json results/*.npz; do cmp "$f" "$REPO/simulation/$f" && echo "identical: $f"; done
```

During consolidation (2026-10-03) both routes reproduced every committed model and result file
byte-for-byte.

## Notebooks

```bash
cd simulation
jupyter execute 01_pipeline.ipynb 02_results.ipynb
```

Both notebooks use the frozen models and committed results, so nothing is refitted. Rerunning
them rewrites `figures/`. The PNGs come out byte-identical, but the PDFs embed a new creation
date and therefore show as modified even though they render identically.

## Notes

- `pipeline.py` resolves `models/`, `results/` and `data/` relative to its own folder, so keep
  this folder's layout intact.
- This file is the validated simulation version (SHA-256 `56f28a01…`). The TEP application keeps
  its own hash-checked copy; see the root [`README.md`](../README.md).
