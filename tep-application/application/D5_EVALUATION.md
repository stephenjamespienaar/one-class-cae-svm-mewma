# Extended TEP Application — D5 Final Evaluation (IDV(2))

**Status: COMPLETE (2026-09-30). Pending human review and commit.**

All 500 frozen IDV(2) runs were evaluated once with the frozen Phase-I artifacts:
- 25 %: 100 runs; 50 %: 100; 75 %: 100; 100 %: 200.
- Each run has 2000 aligned rows and 1969 decisions: pre-onset j = 1…568, post-onset
  j = 569…1969.
- Before any D5 read, the Gate 2, Phase-I and D4 hashes were verified.

Nothing was refitted, recalibrated or excluded, and there was no restart after a
pre-onset alarm.

**Charts:**
- **H(0.05):** D1 preprocessing, then the CAE and OC-SVM, then [score, log SPE], with
  μ_y and Σ_y. **h_H = 325.46159653296104.**
- **M(0.05):** the D1-standardised representation (the Phase-I fallback), applied to the
  31 run-in rows and to the monitored rows, with μ_x and Σ_x. **h_M = 423.59388643957266.**

**Estimand: the onset-referenced conditional detection delay D.** It is not ARL1.
- D is computed over runs with no pre-onset alarm in that chart.
- **D = 1 means a signal at t = 30.00 h**, and Δ = 0.05·(D − 1) h.
- A run with no signal by j = 1969 would be censored at D = 1401. **No run was censored.**

## Primary table

| Severity | n | Pre-FAP H | Pre-FAP M | Eligible H | Eligible M | Median D H (h) | Median D M (h) | Restr. mean D H | Restr. mean D M | Paired n | Mean paired H − M (SE) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 25 % | 100 | 0.040 | 0.020 | 96 | 98 | 39 (1.90) | 29 (1.40) | 39.1 | 28.9 | 96 | 10.1 (0.4) |
| 50 % | 100 | 0.060 | 0.040 | 94 | 96 | 25 (1.20) | 18 (0.85) | 25.3 | 18.4 | 91 | 6.9 (0.2) |
| 75 % | 100 | 0.040 | 0.030 | 96 | 97 | 20 (0.95) | 14 (0.65) | 19.8 | 14.3 | 96 | 5.5 (0.2) |
| 100 % | 200 | 0.020 | 0.050 | 196 | 190 | 17 (0.80) | 12 (0.55) | 17.0 | 12.2 | 188 | 4.8 (0.1) |

- Delays are in monitoring decisions (3 min each).
- Positive H − M means H signals later.
- There is no censoring, so no cell is truncation-limited, and every restricted mean is an
  ordinary mean.
- The source table is `results/d5/d5_primary_table.csv`, and the full statistics are in
  `results/d5/d5_summary.json`.
- The figure is `results/figures/tep_d5_median_delay.{pdf,png}`: median D against severity
  for H and M.

## Pre-onset false alarms (external in-control check, j = 1…568)

| Chart | 25 % | 50 % | 75 % | 100 % | Pooled (500) |
|---|---|---|---|---|---|
| H | 4/100 [0.011, 0.099] | 6/100 [0.022, 0.126] | 4/100 [0.011, 0.099] | 4/200 [0.005, 0.050] | **18/500 = 0.036** [0.022, 0.056] |
| M | 2/100 [0.002, 0.070] | 4/100 [0.011, 0.099] | 3/100 [0.006, 0.085] | 10/200 [0.024, 0.090] | **19/500 = 0.038** [0.023, 0.059] |

Intervals are exact Clopper–Pearson 95 %.

## Delay variability and paired eligibility

| Severity | SD of D, H | SD of D, M | n_E_H | n_E_M | n_E_HM | Censored pairs |
|---|---|---|---|---|---|---|
| 25 % | 4.4 | 3.8 | 96 | 98 | 96 | 0 |
| 50 % | 2.2 | 2.1 | 94 | 96 | 91 | 0 |
| 75 % | 1.7 | 1.5 | 96 | 97 | 96 | 0 |
| 100 % | 1.7 | 1.4 | 196 | 190 | 188 | 0 |

## Interpretation (factual)

1. **In-control behaviour.** Pre-onset false alarms stay compatible with the frozen 5 %
   finite-horizon design:
   - pooled FAP is 0.036 for H and 0.038 for M;
   - both 95 % CIs contain 0.05;
   - D4 gave 0.0435 and 0.0425.
   Per-severity counts are small, and their wide CIs all overlap 0.05.
2. **Severity.** Detection delay decreases monotonically with severity for both charts:
   - H, median D from 39 down to 17 (1.9 h → 0.8 h);
   - M, median D from 29 down to 12 (1.4 h → 0.55 h).
   Run-to-run spread is small (SD 1.4–4.4 decisions).
3. **H versus M.** **The raw-data MEWMA M detects IDV(2) sooner than the hybrid H at every
   severity.**
   - The mean paired H − M delay is +10.1, +6.9, +5.5 and +4.8 decisions (about 0.5, 0.35,
     0.28 and 0.24 h). Each is many paired SEs from zero.
   - H was slower in every jointly eligible pair at 25–75 %, and in 185 of 188 pairs at
     100 %.
   - This agrees in direction with the synthetic study, where M was faster than H beyond the
     smallest shift. IDV(2) is a step disturbance in feed composition, which reaches the raw
     process variables as persistent shifts: the setting a raw-data MEWMA is designed for.
   - No ranking or tuning follows from this; the result is reported as it stands.
4. **Censoring.** No cell has any censored run, so the medians and restricted means are
   fully identified. The post-horizon false-alarm caveat (point 7) therefore bears only on
   delays of 7–49 decisions, well inside the 1401-decision window.
5. **Window ramp-in (L = 32).** The H window at delay D contains only D post-change rows
   when D < 32; D = 32 is the first fully post-change window. M sees post-change input
   from D = 1.
   - At 50 %, 75 % and 100 %, every eligible H detection occurred with D < 32, while the
     window still contained nominal rows. At 25 % the H median (39) comes after the first
     fully post-change window.
   - This structural lag of the frozen hybrid design contributes to the H − M gap and was
     not corrected. The synthetic study had no such ramp-in, because τ = 1.
6. **Seed batch.** The 100 % severity comes entirely from the separate 100 %
   seed-generation batch (stratum B), so severity and batch are confounded in that cell.
   Its pre-onset FAP (H 0.020, M 0.050) and the D4 stratum-B values (H 0.0525, M 0.0400)
   show no consistent batch-related in-control shift.
7. **Horizon limitation.** The 5 % FAP is calibrated only over the 568-decision nominal
   prefix. It says nothing about the false-alarm probability beyond that exposure. Here all
   detections occur within 49 decisions of onset, so the limitation has little practical
   effect, but it bounds the in-control claim.
8. **Scope.** The Extended TEP is an industrial-process **simulation** benchmark, not
   measured plant data. The delays are onset-referenced conditional delays after 568
   in-control decisions. They are not the synthetic zero-state ARL1, and severity % is not
   δ; the two studies are compared only qualitatively.

## Provenance

- Gate 2 protocol `558ffcb6…490f`; registry `0c03350d…e97c`.
- Phase-I manifest `26a8f929…34bc`; D4 manifest `2c2e6377…7316`.
- Code at commit `40d737e`, plus `application/tep_d5.py`.
- `results/d5/d5_manifest.json` records the `tep_d5.py` hash at evaluation time.
  - After the evaluation, only the figure's y-axis was changed, from log to linear scale.
  - The summary, table and figure are regenerated from `d5_run_results.csv` alone and are
    hash-stable on regeneration.
- `results/final_manifest.json` holds the hashes of every final output and the final code.
