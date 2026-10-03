# Extended TEP Application — Gate 2 Protocol Freeze

Status: **FROZEN (Gate 2B, 2026-09-29), pending human review and commit.**

This document, together with its machine-readable twin `application/tep_protocol.json`
and the run registry `application/tep_run_registry.csv`, is the authoritative protocol
for the TEP external benchmark. Where they differ, the JSON and the registry win for exact
values, and this document wins for interpretation. `pipeline.py` remains the authoritative
implementation of every frozen method primitive.

| Artifact | SHA-256 |
|---|---|
| `application/tep_run_registry.csv` (14,000 rows) | `0c03350d207f0127c179b87670a09e5b538fc4450def2ce4fe52547fb6f4e97c` |
| `application/tep_protocol.json` | `558ffcb6eeb7d0c99047f06032390a6ab6b706ee81254366f50630182586490f` |
| `TEP_Mode1.h5`: MD5 (official = local) | `c79ecc6d12a5ccb49caffcd8f531feae` |
| `TEP_Mode1.h5`: SHA-256 (local) | `d6b0ed0ef3974ff571afd6717ba0418a5b8eb58a7822c84a05735572d52b3294` |

The HDF5 checksums were verified in Gate 1. Gate 2B re-verified the file size
(23,924,710,848 bytes). The explicit committed registry is authoritative; rerunning the
RNG does not override it.

---

## 1. Provenance chain

```
DESIGN_FREEZE.md            original TEP design (ARL0 = 370, D3/D4 on long healthy runs)
   -> TEP_AUDIT.md          pre-implementation audit (Path A preferred, Path B = STOP)
   -> GATE1_METADATA_REPORT.md
                            only 5 independent full-length nominal runs exist
                            -> GATE 1 FAILS FOR PATH A
   -> Gate 2A design review (O1-O6) plus manual amendments 1-20 (approved 2026-09-29)
   -> this protocol freeze (Gate 2B)
```

`DESIGN_FREEZE.md` is **not edited** and stays as the historical record. This freeze
amends or supersedes only the TEP-specific clauses that Gate 1 made infeasible:

1. **"Target in-control ARL = 370"** is replaced, for the TEP application only, by a 5 %
   finite-horizon false-alarm probability (§3).
2. **D3/D4 "healthy TEP runs"** are realised as the pre-fault nominal segments of non-IDV(2)
   SingleFault runs (S1).

**The architecture is not redesigned.** L = 32, q = 8, ν = 0.03, the median-γ rule,
λ = 0.05, the monitoring vector `[OC-SVM score, log SPE]`, pooled moments with the 1e8
guard, exact c_j, strict `>` signalling and M's 31-row silent run-in are all unchanged.
The empirical control-limit calibration is kept; only its in-control target changes.

### Why the in-control estimand changes

- **The synthetic study keeps ARL0 = 370.**
- **The TEP data cannot support it.** Estimating a long-run ARL0 = 370 on TEP would need
  independent long nominal trajectories, and the file contains only **5** (the 60
  `SpMagnitude100` runs are 12 bit-identical copies of each). Every other healthy source is
  a 30 h pre-fault segment of 568 monitoring opportunities.
- **So TEP uses a different estimand:** the probability of at least one false alarm over the
  568 observed nominal monitoring opportunities, α = 0.05.
- **No ARL-equivalent is claimed.**

### Design-review provenance (O1–O6, concise)

| Option | Idea | Outcome |
|---|---|---|
| O1 | Frozen estimator on S1 | Rejected: it becomes a mislabelled restricted mean, with about 39 % censoring. |
| O2 | Frozen estimator on the 5 S2 runs | Rejected: n ≈ 3/2. |
| **O3** | Empirical finite-horizon FAP on S1 | **Adopted.** |
| O4 | Censored-geometric ARL0 = 370 | Not adopted: it rests on a constant-hazard extrapolation that TEP cannot check, and about 78 % of D5 runs would false-alarm before onset. |
| O5 | Concatenated segments | Rejected: they are pseudo-trajectories. |
| O6 | New simulations | Out of scope. |

The full record is in `.claude/skills/tep-external-benchmark/design-review-2026-09-29.md`.

---

## 2. Data, grid and onset

**Grid alignment.** If a run's pd(1)[0] = 0.00, drop that row. This applies to every 100 %
magnitude run, completed or stopped.
- After alignment, every run satisfies `rint(20·t) == 1..n`.
- Every run is also bitwise identical to the common stored reference grid (reference run
  IDV1 25 % Run1; grid SHA-256 `1278b25f5c905eb43dcba811517cfd4486fee41e564fb6166fb3ab6cfd7b1443`).
- The stored grid differs from a freshly computed `0.05*k` by at most 1.4e-14, which is
  float rounding. The index check plus the common grid is the frozen assertion.

**Onset convention (P3′).**
- **In-control iff t < 30.00 h; post-change iff t ≥ 30.00 h.** The fault activates at
  exactly 30.0 h in every run.
- Aligned row 599 is t = 29.95, and row 600 is exactly 30.00.

**Indices.** Raw rows r are 1-based (r = 1 ↔ t = 0.05). Decisions j are 1-based
(j = 1 ↔ the window ending at row 32).

| Quantity | Value |
|---|---|
| Nominal prefix | 599 rows (t = 0.05 … 29.95) |
| Pre-onset decisions J₀ | 568 |
| τ (first post-change raw row) | 600 |
| j_τ | 569 |
| Post-onset decisions J₁ | 1401 (j = 569 … 1969) |
| D5 aligned rows / decisions | 2000 / 1969 |

**Start-up.** The full trajectory from t = 0.05 is retained, with no transient trimming.
D1–D4 and the D5 pre-onset segments all share the simulator start condition, and the FAP
calibration includes that start-up.

---

## 3. In-control calibration (O3) and validation

For each chart C ∈ {H(0.05), M(0.05)}, calibrated **independently** on the **same** 2000
D3 runs:

1. **Maximum per run:** R_i = max_{j=1..568} T²_ij. T² comes from the unchanged
   `mewma_t2`: Z₀ = μ̂, exact c_j; H starts at first_update_index = 1; M uses a silent
   run-in over rows 1–31 and starts at first_update_index = 32.
2. **Signal rule:** strict T² > h, with FAP̂(h) = #{R_i > h} / n₃.
3. **Order-statistic index:** k = n₃ − n₃ // 20 = **1900**. This is 1-based: R_(1) ≤ … ≤ R_(n).
4. **Limit:** **h\* = R_(1900) = `np.sort(R)[1899]`.** No interpolation.
   - It is the smallest attained value with FAP̂ ≤ 0.05, and it leaves exactly 100
     exceedances.
   - When n·α is not an integer, the rule stays conservative.
5. **Assertions:**
   - `sum(R > h*) <= 100`;
   - `sum(R > sort(R)[1898]) > 100`;
   - `sum(R == h*) == 1`, otherwise **STOP**.
6. **No run-length assumption.** There is no geometric, constant-hazard or run-length
   extrapolation. The only assumption is that D3, D4 and D5 pre-onset segments are
   exchangeable i.i.d. in-control trajectories. Gate 1 supports this: same-seed runs from
   different fault families are bit-identical before onset.
7. **Finite-sample behaviour:** for continuous i.i.d. R, the true FAP of h* is distributed
   Beta(101, 1900), with mean 0.0505 and SD 0.0049. The D3 in-sample FAP is reported
   separately and never as validation.

**D4 validation** (2000 runs, run once, no recalibration afterwards):
- X = #{R^D4 > h*}, with p̂ = X/2000 and SE = √(p̂(1−p̂)/2000).
- A Clopper–Pearson exact 95 % CI.
- Reported overall, and **descriptively** for stratum A (1200) and stratum B (800).
- The stratum values never trigger recalibration, a limit change, a variable or
  architecture change, batch exclusion, or any other tuning. Their only purpose is to
  expose a possible in-control batch difference, because D5's 100 % cell is stratum B.

---

## 4. Run allocation (registry-authoritative)

**Eligibility (P6).** A non-IDV(2) SingleFault run is eligible iff its seed occurs exactly
once among all 14,000 SingleFault runs. The rule removes:
- **IDV21 50 % Run68**, whose seed is shared with IDV2 75 % Run99;
- **both members of each of the 27 duplicate pairs** (54 runs).

**Strata.** Stratum A is source magnitudes 25/50/75 %. Stratum B is 100 %, a separate
seed-generation batch, and includes the stopped IDV6 100 % runs. Stopping happens only
after the fault, so it does not matter here.

**Algorithm.**
1. Sort each stratum by (IDV, magnitude, run) ascending.
2. Create one generator: `np.random.Generator(np.random.PCG64DXSM(np.random.SeedSequence([795, 6])))`.
3. Draw `permA = rng.permutation(8045)` **first**, then `permB = rng.permutation(5400)`.
4. Slice with the half-open ranges in the JSON.

| Role | A | B | Total |
|---|---|---|---|
| D1 train | 24 | 16 | 40 |
| D1 validation | 6 | 4 | 10 |
| D2 | 12 | 8 | 20 |
| D3 | 1200 | 800 | 2000 |
| D4 | 1200 | 800 | 2000 |
| unused (never read) | 5603 | 3772 | 9375 |
| **Eligible pool** | **8045** | **5400** | **13445** |
| D5 (IDV(2)) | 300 | 200 | 500 |

**Verified assertions:**
- Counts are exact.
- Runs and seeds are disjoint across D1_train, D1_val, D2, D3, D4 and D5.
- No D1–D4 seed is an IDV(2) seed.
- No role seed is among the 5 SpVariation or 20 ModeTransition seeds.
- Every D1–D4 run contains the complete aligned 599-row nominal prefix. 63 stopped IDV6
  100 % runs are allocated, and all have it.

**S2** (`SpMagnitude100`, 5 independent trajectories) **is not used**: no D3/D4 role and no
diagnostic. Only five independent full-length nominal trajectories exist, so they support
no inference.

---

## 5. Variables and Phase-I rules

**Candidates.** pd(2–23) and pd(43–54), i.e. `processdata` columns 1–22 and 42–53 (0-based),
**selected by index**.

**Constancy rule.** Drop a column iff its range is exactly zero on the pooled D1-train rows
(40 runs × 599 rows = 23,960). This check read only D1-train rows 1–599 of the 34 candidate
columns. No D1-val, D2, D3, D4 or D5 value was read.

| Dropped (ptp = 0) | |
|---|---|
| pd(47) | Recycle (XMV 5) |
| pd(51) | Steam (XMV 9) |
| pd(54) | Agitator (XMV 12) |

**Final p = 31.** Columns are in ascending index order, which fixes the CAE channel order
and M's coordinate order:
- **XMEAS 1–22:** pd 2–23.
- **XMV:** pd 43–46 and 48–50, 52–53.

All 31 pass the existing scale > 1e-12 guard on D1-train. `tep_protocol.json` lists each
candidate with its 0-based index, label, ptp and decision.

**Never used:**
- pd(1), the time column;
- the pd(24–42) analysers;
- `additional_meas`, including "B in stream 4";
- `economic_data` and `idv_monitoring`;
- the `mean*` run attributes;
- any metadata as a model input.

**Phase-I rules.**
- **D1:** 40/10 runs, split by run. Standardisation (ddof = 0) is fitted on pooled D1-train
  rows only. Windows are built within each run. Early stopping uses the D1-val windows.
- **D2:** 20 runs, giving 11,360 windows. The OC-SVM and γ are fitted on D2 features only.
- **D3 moments:** H on 2000 × 568 monitoring rows; M on the aligned raw rows 32–599.
- **CAE:** the same architecture and training procedure, with only the input/output channel
  count set to p = 31 (q = 8).
  - The mechanism is deferred to Gate 3, where tests must verify that the only structural
    change is the channel count.
  - The synthetic 4-channel behaviour stays unchanged, and `pipeline.py` is not rewritten.
- **M input:** raw selected variables, following the original methodology.
  - **Fallback trigger:** `pooled_moments` raises on the raw D3 rows (Cholesky failure or
    κ > 1e8).
  - **Fallback:** apply the frozen D1 standardisation and re-run the unchanged
    `pooled_moments`. This is a numerical representation: T² is invariant to it.
  - If that also fails: **STOP**.
  - Never choose raw versus standardised from detection results.

---

## 6. D5 estimands

**Runs.** All 100/100/100/200 runs, with no subsampling and reporting within each severity.
Severity and seed batch are confounded in the 100 % cell.

**Chart operation.** Each chart starts at raw row 1 with the frozen artifacts (Z₀ = μ̂, M's
silent run-in over rows 1–31) and never restarts.

**Pre-onset, j = 1…568.** Stored per run and chart:
- `pre_alarm`, whether T² exceeded h at any pre-onset decision;
- `first_pre_j`;
- `eligible = not pre_alarm`.

The pre-onset FAP (X, n, p̂, CP 95 %) is reported by severity and pooled over all 500 runs.
Alarm counts are not an estimand.

**Onset-referenced conditional detection delay** (not ARL1). For eligible runs only:
- `post = t2[i, 568:] > h`;
- D = `argmax + 1` if any exceedance, else 1401 with the run censored;
- D = j_signal − 569 + 1;
- Δ = 0.05·(D − 1) h = t_signal − 30.00 h.

**Window ramp-in.** The H window at D ≤ 32 contains D post-change rows, and D = 32 is the
first fully post-change H window. M sees a post-change row from D = 1. This asymmetry is a
property of the frozen architecture and is not corrected.

**Reporting emphasis:**
- the pre-onset FAP;
- the **median** D and Δ, reported as "> 1401, not identified" when ≥ 50 % of runs are
  censored;
- the restricted mean of min(D, 1401);
- the censor count and fraction (a truncation flag if above 0.05);
- SD and SE.

**Paired H − M contrast.**
- Computed on E_HM, the runs with no pre-onset alarm in **either** chart, using restricted D
  and the unchanged `paired_contrast`.
- Report n_E^H, n_E^M, n_E^HM and the number of censored pairs.
- The estimand is conditional on both charts staying alarm-free through the nominal prefix.
  That condition uses only in-control data, so it is not selection on the fault response,
  but it is still a conditional estimand.

---

## 7. Limitations (preserve in the thesis)

- **The 5 % FAP covers only the 568-decision nominal horizon.** It does not establish a
  long-run false-alarm probability beyond that exposure. Very late signals for weak faults
  therefore need cautious interpretation, because they cannot be cleanly separated from
  background chart signalling.
- The TEP delay is not the synthetic zero-state ARL1. Magnitude % is not δ, and the two are
  never compared numerically.
- TEP is simulated, not plant data.

---

## 8. Freeze sequence and stop conditions

| Stage | What is frozen or done |
|---|---|
| **A. Gate 2 (this document)** | Protocol, registry, variables, analysis definitions. |
| **B. Gate 3 / Phase I** | Frozen **before D4**: preprocessing, CAE weights and history, OC-SVM state, γ and median distance, moments, H/M limits, D3 R_i arrays, software versions, artifact hashes. |
| **C. D4** | Run once; results frozen and committed; no recalibration. |
| **D. D5** | Only after explicit approval. D5 arrays are not extracted before then. |

**Artifact tracking.** `application/results/models/autoencoder.pt` is currently excluded by
the global `*.pt` rule. Gate 3 must choose a deliberate mechanism, such as
`!application/results/models/autoencoder.pt`, so the CAE artifact is not silently left out
of the reproducibility record.

**Stop conditions:**
- a failed count, allocation, prefix or guard assertion;
- the M fallback failing;
- a tie at h*;
- CAE non-convergence;
- any exposure to post-onset IDV(2) values;
- `tests/test_pipeline.py` failing;
- any discrepancy with `pipeline.py`;
- any need to change a frozen parameter, estimator, chart or variable;
- completion of each stage (Phase I, D4, D5), which then waits for approval.

**Access record for Gate 2B:**
- Gate 2B read only HDF5 metadata: seed attributes, `idv_init`, and the pd(1) time column.
- The only process values read were the 34 candidate columns of the 40 D1-train runs, rows
  1–599.
- **No post-onset IDV(2) response value has been read.**
- Nothing was trained, fitted, calibrated or evaluated.
- The scripts are kept outside the repository in `~/.cache/tep_gate2/`.
