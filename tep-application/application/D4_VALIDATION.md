# Extended TEP Application — D4 In-Control Validation (one-shot)

**Status: COMPLETE (2026-09-30). Run once with the frozen Phase-I artifacts. Pending human
review and commit.**

D4 consists of the 2000 registry D4 runs (stratum A 1200, stratum B 800). Each run uses the
aligned nominal prefix t = 0.05…29.95 h: 599 rows, giving 568 decisions per chart.
- **H(0.05):** frozen D1 preprocessing, then the CAE and OC-SVM, then [score, log SPE],
  with μ_y and Σ_y.
- **M(0.05):** the frozen D1-standardised representation (the Phase-I fallback), applied to
  the run-in rows 1–31 and to the monitored rows, with μ_x, Σ_x and first_update_index 32.
- **False alarm iff max_j T²_ij > h** (strict).

**Nothing was fitted, recalibrated or changed.** Before D4 was read, every Phase-I artifact
hash, the manifest hash, and the `pipeline.py` / `tep_pipeline.py` hashes were verified. The
loader was opened for role `D4` only.

## Frozen limits used, unchanged

| Chart | h* | D3 in-sample FAP |
|---|---|---|
| H(0.05) | 325.46159653296104 | 0.050 |
| M(0.05) | 423.59388643957266 | 0.050 |

## Results (target α = 0.05 over 568 decisions)

| Chart | X / n | Realised FAP | SE | Clopper–Pearson 95 % |
|---|---|---|---|---|
| **H(0.05) overall** | 87 / 2000 | **0.0435** | 0.0046 | [0.0350, 0.0534] |
| H stratum A (descriptive) | 45 / 1200 | 0.0375 | 0.0055 | [0.0275, 0.0499] |
| H stratum B (descriptive) | 42 / 800 | 0.0525 | 0.0079 | [0.0381, 0.0703] |
| **M(0.05) overall** | 85 / 2000 | **0.0425** | 0.0045 | [0.0341, 0.0523] |
| M stratum A (descriptive) | 53 / 1200 | 0.0442 | 0.0059 | [0.0333, 0.0574] |
| M stratum B (descriptive) | 32 / 800 | 0.0400 | 0.0069 | [0.0275, 0.0560] |

- Both overall CIs contain the 0.05 target.
- The overall values lie within about 1.1 D4 standard errors of 0.05. The combined
  calibration-plus-validation SD expected at the design stage was about 0.007.
- The stratum values are descriptive only. They trigger no recalibration, limit change,
  exclusion or D5 change.

## Artifacts (SHA-256)

| Artifact | SHA-256 |
|---|---|
| `results/d4/d4_maxima.npz` (R_H, R_M, D4 paths, strata) | `095af74f20d9d136e26f875c3b0bcc64c750fbe57c595e73883c5d3d0e9d19aa` |
| `results/d4/d4_validation.json` | `ff23b30e8127a11726228cfc9816aa07e39c53155044e70f01784574fb4ffe8d` |
| `results/d4/d4_manifest.json` | `2c2e6377c1a79b028a4e00ff9c0ae7c1a01a5a9e3d7563aaeebcaa6a29b07316` |

**Inputs:**
- Phase-I manifest `26a8f929…34bc`;
- protocol `558ffcb6…490f`;
- registry `0c03350d…e97c`;
- code commit `1cb82c4`, plus `application/tep_d4.py`, whose hash is in the manifest.

## Boundary

**D5 was not read.** The D5 loader guard is unchanged and tested. No IDV(2) post-onset
process value has been read. The next stage, D5, requires explicit approval.
