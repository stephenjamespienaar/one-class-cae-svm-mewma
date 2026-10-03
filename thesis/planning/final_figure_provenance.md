# Final figure and table provenance

> **Consolidated-repository note.** This record was written in the original thesis workspace and
> is kept unchanged below, except that one machine-specific path is written as
> `<original-workspace>/…`. In this repository, `01_repository/pipeline-thesis-independent` is
> `simulation/` (the same files as commit `e62bdee`), `08_tep_application/source` is
> `tep-application/` (the same files as commit `0a121fa`), and `scripts/`, `planning/` and
> `final_report/` live under `thesis/`. Regenerate from `thesis/scripts/` with
> `PYTHONDONTWRITEBYTECODE=1 python make_all_figures.py` (see `thesis/README.md`).

Authoritative source: `01_repository/pipeline-thesis-independent` (branch `simplify-pipeline-code`,
commit `e62bdeed620fca38350fe8e0021ee70ea7a0fad9`, clean working tree), read-only.
Regenerate the synthetic figures and tables below from `scripts/` with

    PYTHONDONTWRITEBYTECODE=1 "$(readlink -f ../01_repository/pipeline-thesis-independent)/.venv/bin/python" make_all_figures.py

Nothing is refitted, retuned or recalibrated. "Frozen inference" means the repository's own
`monitoring_bank()` applied with the committed `models/` to a committed data bank; the D3 vectors are
asserted to reproduce `models/mewma.npz` (`mu_y`, `sigma_y`) bitwise before any figure is drawn.
Figure PDFs are byte-identical across reruns (no timestamps).

## Body

| Figure / table | Question answered | Source artifacts | Derived calculation | Script | Status |
|---|---|---|---|---|---|
| Fig. 1 `methodology_pipeline_diagram` | What is the pipeline and which dataset fits which stage? | `methodology.md` §§1–13, `pipeline.py` (verified facts) | none (schematic) | `make_diagnostic_figures.py` | explanatory |
| Fig. 2 `diagnostic_ic_monitoring_vector` | How do the learned components behave in control (Objective 3)? Why empirical calibration? | `data/generated/D3.npz`; `models/{preprocessing.npz,autoencoder.pt,ocsvm.npz,mewma.npz}` | frozen inference of y_t on all 300x2969 D3 windows; hexbin + marginals; pooled ACF about the frozen D3 mean (raw x_t: aligned rows t=32..3000) | `make_diagnostic_figures.py` | canonical-derived (descriptive) |
| Table 1 `tables/ic_validation.tex` | How well did each chart realise IC behaviour on D4 vs its D3 calibration? | `models/control_limits.json`, `results/d4_validation_summary.json` | rounding only | `make_results_figures.py` | canonical |
| Fig. 3 `results_ooc_arl_panels` | H vs M across the full grid; paired contrast; ablation; lambda sensitivity | `results/d5_performance_summary.json` (cells, primary_contrast); cross-checked against `results/run_lengths.npz` | (a),(c),(d) ARL1 with +/-2 SE in (a); (b) canonical paired mean difference +/-2 paired SE | `make_results_figures.py` | canonical (replotted; replaces the three linear-scale repository figures used in the first build) |

## Appendix

| Figure / table | Question answered | Source artifacts | Derived calculation | Script | Status |
|---|---|---|---|---|---|
| Table 3 (W2, typed in `appendix.tex`) | Fixed mixing matrix | `pipeline.py` `W2` | transpose; checked `== pipeline.W2.T` exactly | manual, verified | canonical |
| Table 4 (CAE layers, typed) | Architecture | `pipeline.py` `ConvAutoencoder1d` | per-layer parameter counts (sum 3180) checked by instantiating the class | manual, verified | canonical |
| Fig. 5 `diagnostic_reconstruction_example` | What does the CAE reconstruct? | `data/generated/D3.npz` (trajectory 1, window 1001); frozen models | one frozen forward pass; SPE = 96.65 | `make_diagnostic_figures.py` | canonical-derived (descriptive) |
| Fig. 6 `diagnostic_component_response` | How far do s_t and l_t move under a shift? | `data/generated/D5/delta_{0p4,1p0,3p0}.npz` (first 100 trajectories each), D3 | frozen inference; standardised by frozen D3 moments; histograms; mean shifts | `make_diagnostic_figures.py` | **post-hoc descriptive diagnostic** (labelled as such in caption and text) |
| Fig. 7 `results_d4_arl0_validation` | D4 IC ARL +/-1 SE vs target | repository figure (produced by `02_results.ipynb` from `results/`) | none (copied unchanged) | `make_results_figures.py` (copy) | canonical |
| Table 5 `tables/d5_arl1_full.tex` | Full ARL1 (SE) grid | `results/d5_performance_summary.json` | rounding | `make_results_figures.py` | canonical |
| Table 6 `tables/primary_contrast.tex` | Primary contrast in detail | `results/run_lengths.npz` | paired mean diff/SE (identical to canonical `primary_contrast`); medians; P(RL_M=1); delay in post-change observations = ARL1+31 (canonical `t_signal = RL + 31`); ratios | `make_results_figures.py` | canonical-derived |
| Table 7 `tables/ablation_contrast.tex` | Does H beat S and R pairwise? | `results/run_lengths.npz` | paired H-S, H-R mean and SE (same estimator as canonical H-M contrast) | `make_results_figures.py` | canonical-derived |
| Fig. 8 `results_primary_run_length_boxplots` | Run-length distribution shape, H vs M | repository figure (from `results/run_lengths.npz`) | none (copied unchanged) | `make_results_figures.py` (copy) | canonical |

## Candidates generated or inspected but not used

| Candidate | Decision |
|---|---|
| Repository `results_primary_hybrid_vs_classical_arl`, `results_hybrid_ablation_arl`, `results_lambda_sensitivity_arl` (first build) | superseded by Fig. 3: one float instead of three, log scale shows the large-shift gap (M ~ 1 vs H ~ 12.5) that the linear scale hid |
| Repository `results_arl_all_schemes`, `_sdrl_`, `_mrl_`, `_primary_run_length_metrics`, `_small_shift_zoom`, `_primary_paired_difference`, `_primary_run_length_ecdf` | redundant with Fig. 3, Tables 5-6 and Fig. 8 |
| Repository `methodology_d2_component_distributions`, `methodology_d2_monitoring_vector` | D2 is in-sample for the OC-SVM; replaced by the D3 (calibration-bank) view in Fig. 2 |
| Repository `methodology_d1_observed_channels` | decorative for the argument; raw dependence is shown by the ACF in Fig. 2(b) |
| Repository `methodology_finite_start_factor` | secondary; c_j is defined in Eq. (4) |
| Correlation / covariance heatmaps | not drawn: the hybrid correlation is a single number (r = -0.147 from the frozen D3 covariance), which the text reports; a 4x4 raw heatmap adds nothing to the argument |
| CAE training/validation loss curve | not available as a stored canonical artifact; only the production log's best epoch (33) and validation MSE (0.6622) exist, and retraining is not permitted |

## Derived numbers quoted in the text

`planning/derived_results.json` (from `make_results_figures.py`) and
`planning/derived_diagnostics.json` (from `make_diagnostic_figures.py`) hold every derived number
quoted in the report (D4 z-scores and paired D4 differences, P(RL=1), post-change-observation delays,
paired ablation and lambda contrasts, component correlation/skewness/ACF, OC-SVM outside-boundary
shares, CAE per-element reconstruction error, component mean shifts).

## Extended TEP application (included: Table 2 and Fig. 4, Section 5.2; details in Appendix E)

Separate authoritative source: `08_tep_application/source`, resolving to `<original-workspace>/pipeline-thesis-tep`
(branch `tep-application`, commit `0a121fa4adb4ef770c1d5821455103e31149d70a`). Read-only.
The TEP figure and table are not produced by `scripts/make_all_figures.py`; Fig. 4 is produced by
`scripts/make_tep_figure4.py` (see the note below the table).

| Presentation file | Source in the TEP repository | Derivation | Status |
|---|---|---|---|
| `final_report/figures/tep_d5_median_delay.pdf` | `application/results/d5/d5_summary.json` (plotted data); `application/results/figures/tep_d5_median_delay.pdf` (reference) | Redrawn without the in-plot title (supervisor request, 2026-10-02) by `scripts/make_tep_figure4.py`, a verbatim copy of the frozen `tep_d5.write_figure()` that skips only `ax.set_title`; output SHA-256 `dd600e891a73fd97f8c9e0226d76d0d13ea7bdda55d13a2ed01a27b88a71af8c` | Frozen TEP results, title-free presentation; body Fig. 4 (`fig:tep`) |
| `final_report/tables/tep_d5_primary.tex` | `application/results/d5/d5_primary_table.csv`; `application/results/d5/d5_summary.json` | Six-column table-row fragment; retained eligible H/M/paired denominators; added median hours from the summary; displayed paired H-M and SE to one decimal | Frozen final TEP results; body Table 2 (`tab:tep`) |

The table reports onset-referenced conditional detection delay (not ARL1).
Hours = 0.05*(D-1). Chart-specific medians condition on no pre-onset alarm in that chart;
paired contrasts condition on neither chart having a pre-onset alarm. No eligible delay
was censored, and positive H-M means H detected later. No model inference, fitting,
recalibration or simulation was performed to prepare these presentation files.

Fig. 4 redraw check: `make_tep_figure4.py` first runs the copied `write_figure()` with the title and
asserts that its PDF is byte-identical to the frozen figure (SHA-256 `3d3634ae…`), then writes the
untitled version. Both versions plot the frozen medians H = 39, 25, 20, 17 and M = 29, 18, 14, 12
(25, 50, 75, 100%); these values were also read back from both PDFs' vector paths, and agree.
The page size (8 × 5 in) is unchanged. The TEP repository was only read.

Source SHA-256 values, verified against `application/results/final_manifest.json`:

| Original source path | SHA-256 |
|---|---|
| `application/results/d5/d5_primary_table.csv` | `63086174c821e51cf24f8a1515d2e984010688b1266c51c35e32d3bed4161b92` |
| `application/results/d5/d5_summary.json` | `9a5bb340c7be77ce5cd0f8162964f0a4eb404749f8a1b301d6b391e40a903456` |
| `application/results/figures/tep_d5_median_delay.pdf` | `3d3634ae0fb8b401d01f89701c9628c1303def351fcce79ecce0e352c3209bb5` |
