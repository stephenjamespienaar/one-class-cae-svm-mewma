# Extended TEP Application — Pre-Implementation Audit

Status: **audit only**. Nothing here amends `DESIGN_FREEZE.md` or authorises
implementation.

Markers:

- **[verified]**: confirmed directly from repository code, official dataset metadata or
  the dataset paper text.
- **[verify]**: inferred (from the Readme example path, the paper, or an expected HDF5
  layout) and not yet confirmed from `TEP_Mode1.h5` itself.
- **[decision]**: an unresolved scientific or engineering choice that needs approval.

Nothing marked [verify] may be used to make an allocation or protocol decision.

Sources consulted:

- Repository: `application/DESIGN_FREEZE.md`, `pipeline.py`, `tests/test_pipeline.py`,
  `methodology.md`, `README.md`, `application/README.md`, `01_pipeline.ipynb`,
  `02_results.ipynb`, `requirements.txt`, `.gitignore`, `models/*`, `results/*.json`.
- Figshare/DTU Data metadata API for article 13385936 (DOI
  10.11583/DTU.13385936.v1, CC0).
- The official dataset `Readme.html` (8.5 KB).
- Reinartz, Kulahci & Ravn (2021), *Comput. Chem. Eng.* 149:107281. The full text was read
  as Appendix A of C. Reinartz's DTU PhD thesis (2021): §A.3.1–A.3.4, Tables A.2–A.4,
  §A.4.2–A.4.4.
- Montesuma et al., arXiv:2308.11247 (an independent user of the same data).
- The AIRI `fddbenchmark` README.
- One 16-byte HTTP range request to `TEP_Mode1.h5`. It returned the HDF5 signature and
  confirms partial reads are possible. No data was downloaded.

---

## 1. Repository architecture

`pipeline.py` contains every scientific function but **no Phase-I orchestrator**
[verified]. Nothing chains D1→D3 or writes `models/preprocessing.npz`, `autoencoder.pt`,
`ocsvm.npz`, `mewma.npz` or `control_limits.json`. There is no `torch.save` and no writer
for those files. The staged code that produced them was removed in `5109707`/`eab9958`.
The only orchestrated path is Phase II (`evaluate_phase2`), which loads the frozen
synthetic artifacts.

| Role | Synthetic data | Code path |
|---|---|---|
| D1 | one 2000×4 series | `generate_d1` → `split_d1` (chronological 1600/400 rows, before windowing) → `fit_preprocessing` (train rows) → `apply_preprocessing` + `window_series` → `train_autoencoder` (early stopping on validation windows) |
| D2 | one 2000×4 series | `generate_d2` → `infer_series` (frozen CAE) → `to_ocsvm_input` → `fit_ocsvm` (median-distance γ via `exact_gamma`) |
| D3 | 300×3000×4 | `monitoring_bank` → `pooled_moments(y)`; `benchmark_bank(raw)` → `pooled_moments(x)`; `calibrate_charts` → `mewma_t2` + `calibrate_limit` (6 charts) |
| D4 | 500×3000×4 | `evaluate_phase2` → `evaluate_bank` → zero-state `run_lengths` → `d4_entry` |
| D5 | 15×500×3000×4 | as D4 per δ → `d5_entry`, `paired_contrast` |

| Responsibility | Function(s) |
|---|---|
| preprocessing / standardisation | `split_d1` pipeline.py:361, `fit_preprocessing` :367, `apply_preprocessing` :377, `load_preprocessing` :559 |
| windowing | `window_series` :381, `window_bank` :387 (right-aligned, stride 1, never across replications) |
| CAE | `configure_determinism` :398, `ConvAutoencoder1d` :416, `_epoch_loss` :468, `train_autoencoder` :485, `load_autoencoder` :457, `infer_windows` :564, `infer_series` :586, `infer_bank` :594, `spe` :576, `log_spe` :582 |
| OC-SVM | `to_ocsvm_input` :620, `exact_gamma` :625, `fit_ocsvm` :641, `load_ocsvm` :674, `ocsvm_score` :691 |
| hybrid monitoring vector | `Frozen`/`load_frozen` :706/:714, `monitoring_series` :719, `monitoring_bank` :728 |
| MEWMA moments | `condition_number` :744, `pooled_moments` :750, `load_moments` :941 |
| MEWMA statistic | `finite_start_factors` :819, `mewma_states` :835, `mewma_t2` :851 |
| empirical limit calibration | `calibrate_limit` :885, `calibrate_charts` :908, `chart_plan` :800, `limit_key` :810 |
| run lengths | `run_lengths` :876 (strict `>`, explicit censor flag) |
| raw MEWMA benchmark | `CHARTS["M"]` :199, `benchmark_bank` :780, `benchmark_run_in` :814, the `else` branches in `calibrate_charts`/`evaluate_bank` |
| summaries | `cell_summary` :1063, `d4_entry` :1084, `d5_entry` :1101, `paired_contrast` :1111 |
| persistence | `cached_bank_cells` :1038, `write_json` :1123, `evaluate_phase2` :1129 |
| plotting | none in `pipeline.py`; figures live in `02_results.ipynb` |

**Reusable unchanged:** `fit_preprocessing`, `apply_preprocessing`, `window_series`,
`window_bank`, `configure_determinism`, `ConvAutoencoder1d` (once the channel count is
handled; see §7), `train_autoencoder`, `infer_*`, `spe`, `log_spe`, `single_threaded`,
`OCSVM`, `to_ocsvm_input`, `exact_gamma`, `fit_ocsvm`, `ocsvm_score`, `Frozen`,
`monitoring_series`, `monitoring_bank`, `pooled_moments`, `benchmark_bank`,
`benchmark_run_in`, `finite_start_factors`, `mewma_states`, `mewma_t2`, `run_lengths`
(for zero-state D3/D4 run lengths), `calibrate_limit`, `paired_contrast`, `write_json`.
The `load_*` functions take a `path` argument and can read TEP artifacts written in the
same key formats.

**Not reusable as-is:** the synthetic generators; `split_d1` (single series);
`evaluate_bank` (asserts shape `(3000, 4)` and runs six charts); `evaluate_phase2` and
`cached_bank_cells` (paths, `SHIFT_GRID` and cache token are tied to `models/` and
`results/`); `calibrate_charts` (the six-chart plan). `cell_summary` hard-codes
`n_windows = 2969`.

---

## 2. Hard-coded assumptions

**A. Must change for TEP**

| Assumption | Where | TEP counterpart |
|---|---|---|
| p = 4 (`OBS_DIM`, `INPUT_CHANNELS`) | :43, :108; CAE first/last layer | p = number of selected variables [verify: expected 31] |
| synthetic generator (`PHI, Q, W1, W2, B1, B2, R, BURN_IN, INITIAL_STATE, LATENT_DIM`, `generator_for`, `simulate*`, `generate_*`) | :23–356 | HDF5 loader; not called |
| τ = 1 (`CHANGE_POINT`), `D5_INTERPRETATION` text | :82, :970 | onset from metadata [verify: row 601, j_τ = 570] |
| trajectory length 3000 (`D3/D4/D5_HORIZON`) | :71–75 | 2000 rows per full run [verified from paper; verify in file] |
| reportable horizon 2969 (`CALIBRATION_HORIZON`) | :173, `evaluate_bank` asserts, `cell_summary` | 1969 for 2000-row runs |
| D1/D2 = one 2000-row series each; 80/20 chronological split | :68–69, `split_d1` | several independent runs; split by run |
| D3 = 300, D4 = 500 replications | :70, :72 | set by the verified count of independent healthy runs (§5) |
| δ grid (`SHIFT_GRID`, `delta_code`, `scenario_name`) | :84–337 | magnitudes {25, 50, 75, 100}% |
| raw-MEWMA dimension 4 (`CHARTS["M"]`) | :199–205 | p (metadata only; the code path takes the dimension from the data) |
| artifact/result paths (`models/*`, `results/*`, `results/cache`, `CACHE_INPUTS`) | :395–968 | must not be written; TEP uses `application/results/…` |
| six-chart plan | `chart_plan` :800 | H(0.05) and M(0.05) only (the freeze prohibits ablation/sensitivity) |

**B. Parameterise in the application layer, not `pipeline.py`:** the variable list and p;
the onset index; run IDs/seeds per role; the horizon (from array shape); the magnitude
list; output paths.

**C. Unchanged:** `STAGE3_SEED`; L = 32, stride 1; standardisation (`ddof=0`, float64,
`SCALE_THRESHOLD`); CAE architecture and training hyperparameters; q = 8, `FEATURE_DIM` = 8;
SPE sum and log floor; OC-SVM (RBF, ν = 0.03, median-γ rule, tolerances); monitoring
vector `[s, log SPE]`; moments `ddof=1` and the 1e8 guard; λ = 0.05; target ARL0 = 370;
strict `>` rule; exact finite-start factors; M's 31-row silent run-in (c₃₂ at the first
report); `calibrate_limit`; the 5 % truncation flag; single-thread/precision policy;
paired contrast.

"First monitorable time = 32" follows from L. The computation does not assume exactly 500
OOC runs: `cell_summary` and `paired_contrast` use `size`, and only `D5_REPLICATIONS`
(used in tests and docs) encodes 500.

---

## 3. Minimal TEP adaptation (proposed; not implemented)

The adaptation is an application layer that imports `pipeline.py` and never edits it
(subject to the §7 [decision]).

- `application/tep_data.py`: read `TEP_Mode1.h5` with **h5py** (a new dependency; the data
  is HDF5). Select the pre-registered runs and columns and write one compressed subset
  `.npz` in pipeline shapes, `(runs, rows, p)` per role, with run IDs and seeds.
- `application/run_tep_application.py`:
  - Phase I: standardise on the D1 train rows, `window_bank`, `train_autoencoder`,
    `fit_ocsvm` on the D2 features, D3 moments, `mewma_t2` + `calibrate_limit` for H(0.05)
    and M(0.05). Artifacts go under `application/results/models/` in the existing key
    formats.
  - Phase II: D4 zero-state run lengths; D5 onset-referenced analysis (§6);
    `paired_contrast`; JSON/npz; one table; one figure.
- A small `application/test_tep_application.py`.

`tests/test_pipeline.py` must keep passing unchanged. These files are written only at
Gate 3 (§10).

---

## 4. Extended TEP data requirements

**Source [verified].** Reinartz, Kulahci & Ravn (2021), "Tennessee Eastman Reference Data
for Fault-Detection and Decision Support Systems", DTU Data, DOI
10.11583/DTU.13385936.v1, CC0.

**Files [verified].** There is one HDF5 file per operating mode and no per-fault files.
Mode 1 is `TEP_Mode1.h5`, 23,924,710,848 bytes (23.9 GB), at
`https://ndownloader.figshare.com/files/26003087`. Modes 2–6 are not needed. There is no
published checksum in the metadata, so compute the SHA-256 locally.

**Structure.**

- [verified, Readme] Root datasets are `Processdata_Labels` and `Additional_Meas_Labels`.
  Mode 1 has the groups `SingleFault/{SimulationCompleted, SimulationStopped}/IDV{1–28}`,
  `SpVariation`, and `ModeTransition`. The Readme's example is
  `Mode1_IDVInfo_1_{100,75,50,25}/Run{k}`. Each run holds `processdata`,
  `additional_meas`, `economic_data`, `setpoint_init`, `idv_init` and `time_info`.
- [verified, paper] Run metadata includes the RNG seed and the initial mode. `idv_init` is
  3×28 (magnitude before, magnitude after, activation time in hours).
- [verify] The exact IDV(2) paths are expected to be
  `Mode1/SingleFault/SimulationCompleted/IDV2/Mode1_IDVInfo_2_{25,50,75,100}/Run{k}/processdata`,
  extrapolated from the IDV1 example. Also verify the `Stopped` counterpart and where the
  seed is stored.

**Healthy/reference data.** [verified, paper] **No dedicated normal-operation group
exists.** Candidate healthy sources:

- **S1, pre-fault segments.** [verified, paper] Every fault run is nominal for the first
  30 h, and the authors' Phase I used the first 500 observations of all faults at 100 %
  magnitude as in-control data. [verify] Segment length (600 rows), independence of seeds
  across faults.
- **S2, `SpVariation/…/SpMagnitude100`.** [verify, all of it] Set-point variations span
  85–115 % in 5 % steps (paper), so a "100 %" level would be a no-change run. That suggests
  up to 12 set-points × 5 ramp profiles = 60 full-length nominal Mode 1 runs. Whether
  these runs exist, are genuinely nominal and stationary, have distinct seeds, and share
  no seed with fault runs is **unconfirmed**. The paper does not describe `SpMagnitude100`
  explicitly.

**IDV(2).** [verified, paper] B composition in stream 4 (A/C ratio constant), a step
fault. Documented simulations per magnitude: **25 %: 100, 50 %: 100, 75 %: 100,
100 %: 200**. [verify] Completed vs stopped counts per magnitude, the lengths of stopped
runs and their shutdown times.

**Timing.** [verified, paper] 100 h per run, 3-min sampling, 2000 observations; nominal
for 30 h, then a fault or set-point event at 30 h. [verify] That the file holds exactly
2000 rows, the `pd(1)` time grid, the `idv_init` activation time, and therefore that the
**first faulty row is 601**.

**Schema.** [verified, paper Table A.4; verify against `Processdata_Labels`]
`processdata` has 54 columns:

| Columns | Content | Use |
|---|---|---|
| pd(1) | time (h) | identifier, excluded |
| pd(2–23) | XMEAS(1–22), continuous measurements (measurement noise added) | candidate |
| pd(24–42) | XMEAS(23–41), sampled composition analysers | excluded |
| pd(43–54) | XMV(1–12), manipulated variables | candidate |
| other datasets | extra measurements / labels / metadata | excluded |

**Variable rule (provisionally acceptable; frozen before any fault value is read).**

1. Take pd(2–23) and pd(43–54): 34 candidates, matching the authors' own Phase I.
2. Remove structurally constant columns using **D1 training rows only**.
3. Confirm the official labels and meanings from `Processdata_Labels`.
4. Record the resulting list in the protocol.

IDV(2) fault responses are never inspected for this choice. The Mode 1 Ricker set-points
(Table A.2) fix XMV(5) at 1 %, XMV(9) at 1 % and XMV(12) at 100 %, so **p = 31 is
expected [verify]**. The excluded composition analysers, for example B in purge, may carry
the most direct information about IDV(2). They must **not** be reintroduced post hoc.

---

## 5. D1–D5 allocation (all counts provisional)

Principles:

- Runs are the unit of allocation.
- Each run is used in at most one role.
- Seeds are unique across all roles and different from every IDV(2) seed [verify]. Seed
  metadata is checked first. Only if the metadata alone cannot establish independence may
  pre-fault nominal rows (IDV(2) runs included) be read, mechanically, for hashing or
  bitwise duplicate detection (see the data-access rule below).
- No fault-period observation enters D1–D4.
- Independence is never traded for reproducing the synthetic sample sizes.

**Data-access rule before the protocol freeze (Gate 2).**

- **No post-onset IDV(2) fault-response values may be inspected.**
- Pre-fault nominal rows may be read only mechanically, for hashing or bitwise duplicate
  detection, and only if seed metadata cannot establish independence.
- Those pre-fault values must not be plotted, summarised, used for variable selection or
  model fitting, or used for any scientific decision other than duplicate detection.

**Path A — preferred if metadata verification confirms that the SpMagnitude100 runs are
genuinely nominal, stationary Mode-1 runs with sufficient independent seeds.**

Candidate counts, to be fixed only after the number of genuinely independent healthy runs
is reported:

| Role | Source | Candidate runs | Rows/run | Windows/decisions per run |
|---|---|---|---|---|
| D1 train / validation | S1 | 16 / 4 | 600 | 569 |
| D2 | S1 | 10 | 600 | 569 |
| D3 | S2 | ≈ half of the verified independent S2 runs | 2000 | 1969 |
| D4 | S2 | the remainder | 2000 | 1969 |
| D4b (diagnostic, optional) | S1 | e.g. 500 | 600 | 569 (horizon-matched false-alarm frequency, D4b vs D3) |
| D5 | IDV(2) | per the §5 inclusion [decision] | 2000 | 569 pre-onset + 1400 post-onset |

Why D3/D4 need full-length runs: the frozen `calibrate_limit` takes the mean of RL
censored at the horizon. With 600-row segments (H = 569) and a target of 370, censoring is
heavy. A rough geometric approximation suggests about 40 %, and a biased limit follows.
With 2000-row runs (H = 1969) censoring should be small; measure it empirically.

**Path B — if sufficient full-length independent healthy trajectories do not exist, STOP
and return for a design decision. Do not silently replace the calibration estimator.** No
alternative calibration estimator is authorised.

**D5 inclusion [decision].**

- Documented counts are 100/100/100/200, subject to verification. Whether production uses
  all valid runs, or an equal pre-specified number per magnitude, is undecided. Equal
  counts (e.g. 100 each) would bring the four severity comparisons closer to the synthetic
  study's equal-replication design.
- Stopped/shutdown runs are fully unresolved. The metadata audit must first report, per
  magnitude: total, completed and stopped runs, the lengths of stopped runs and the
  shutdown times. Excluding shutdown runs conditions on the fault outcome and could bias
  the application. After that report, choose one of: all runs usable with censoring,
  completed runs only, or another pre-specified rule.

---

## 6. Fault timing

**Fixed conventions (unchanged from the synthetic design):**

- Row t = 1…2000; decision index j = t − 31 (j = 1 ↔ t = 32).
- With the first faulty row τ = 601 [verify], the onset decision is **j_τ = 570**. The
  pre-onset decisions are j = 1…569 and the post-onset decisions are j = 570…1969 (1400).
- Each D5 run is charted end-to-end by the unchanged `mewma_t2`: Z₀ = μ at the start of
  the run, exact finite-start factors, and M's 31-row silent run-in (rows 1–31 are healthy
  here). By onset the chart has had 569 decisions, far more than 1/λ = 20.
- Windows are right-aligned and causal. Windows ending at t ≤ 600 contain no fault rows.
  Windows ending at t = 601…631 straddle the onset and are kept as post-onset decisions.
  t = 632 is the first fully faulty window. Nothing is discarded. M sees x₆₀₁ fully at
  t = 601, while H's window is then 1/32 faulty. This ramp-in is a property of the frozen
  method; it did not occur in the synthetic study, where every window was post-change.
  Report it, don't correct it.
- **Estimand difference.** The synthetic D5 metric was a *zero-state* ARL1: the shift was
  present from τ = 1 and the chart started with the change. TEP gives an
  *onset-referenced (steady-state) detection delay* after 569 in-control decisions. The
  two must not be called the same quantity or compared numerically.
- **Pre-fault alarms must be recorded explicitly** for every run and chart: whether one
  occurred, the first index, the count, and whether T² exceeds h at j = 569 (an alarm in
  progress at onset).
- **Pre-fault alarm frequency.** A substantial number of runs may alarm during the 569
  pre-onset opportunities. This must be measured empirically on D5's pre-onset segments
  (and D4b if used). *Rough geometric approximation only:* 1 − exp(−569/370) ≈ 0.78. The
  MEWMA statistic is strongly serially dependent and its RL distribution is not
  geometric, so this is not an expected probability.

**Treatment of runs with a pre-fault alarm [decision].** Candidate policies, compared
conceptually and not implemented:

- **A. Signal-and-continue.** The delay is the first post-onset exceedance, and pre-fault
  alarms neither stop nor reset the chart. Uses every run. It measures the delay of a
  chart operated continuously, which is closest to "the chart operates during the nominal
  portion". Consequence: the state at onset depends on pre-fault history. A run whose
  statistic is already above h at onset records D = 1, crediting a false-alarm excursion
  as detection. With λ = 0.05 excursions persist, so this can shorten delays, possibly
  unequally between H and M. The alarm-at-onset count must accompany it. The estimand is
  unconditional on the pre-fault history.
- **B. Conditional detection delay (CED).** The delay is computed only among runs with no
  alarm before onset. This is the classical conditional-expected-delay idea: the chart is
  in control and has not signalled at τ. Consequence: a clean estimand free of carry-over
  from false alarms. But it conditions on a chart-specific event, so H and M are evaluated
  on different run subsets and the paired contrast is only possible on the intersection.
  The usable subset may be small if pre-fault alarms are frequent, which widens the SEs.
  It also selects runs whose pre-fault noise happened to be quiet, which may bias the
  steady-state state distribution at onset.
- **C. Established conventions in the consulted sources.**
  - Reinartz et al. (A.4.2–A.4.4) define ARL as observations until a signal and report
    ARL1 per fault. Their PCA T²/Q charts are memoryless (Shewhart-type), so a pre-fault
    alarm does not carry into the post-onset statistic. The paper does not state an
    explicit rule for pre-fault alarms, and its convention does **not** settle the
    question for a chart with memory such as the MEWMA.
  - `fddbenchmark` defines ADD as samples between the first faulty sample and the first
    detected faulty sample, averaged over faulty runs **excluding undetected runs**, with
    false alarms reported separately (FPR). That is an A-type rule. Excluding undetected
    runs instead of censoring them is itself a choice with a downward bias on delay.
  - A third SPC variant, not verified against a cited source in this audit, restarts the
    chart at Z = μ after each false alarm (cyclical steady state). It removes carry-over
    but introduces a restart rule absent from the frozen design.

No policy is chosen here. Selection must rest on the estimand, not on convenience, and
must be frozen in the protocol before D5 values are read.

**Computing the first post-onset crossing.** Compute it directly from the post-onset
T² sequence:

    post = t2[:, 569:] > h            # strict rule, decisions j = 570…1969
    signalled = post.any(axis=1)
    delay = np.where(signalled, post.argmax(axis=1) + 1, post.shape[1])
    censored = ~signalled

`run_lengths` reads its censor flag from the last column (`~exceeded[:, -1]`), so it is
only correct on a running maximum. Passing raw T² would mis-flag runs that crossed and
then fell back. The direct form above avoids that. Under the CED policy the same
computation applies to the retained subset.

---

## 7. CAE dimensionality

- Only the first `Conv1d` (`in_channels`) and the last `ConvTranspose1d` (`out_channels`)
  depend on p; both read the module global `INPUT_CHANNELS` [verified].
- The flattened dimension is `ENCODER_CHANNELS[1] × ENCODED_LENGTH` = 16 × 8 = 128. It
  depends on L only, not on p [verified]. q = 8 and `FEATURE_DIM` = 8 are unchanged, and
  `load_ocsvm`'s assert still holds.
- The parameter count is 2984 + 49p: 3180 at p = 4, and 4503 at p = 31, which was verified
  by instantiating the class with 31 channels.
- SPE sums over p × 32 elements (992 at p = 31, against 128). The log-SPE level shifts, and
  the D3 moments absorb it.
- The synthetic weights cannot be reused. Layer shapes differ, and the weights encode a
  different process. The same holds for the standardisation, the OC-SVM, the moments and
  the limits.
- Retraining counts as applying the frozen method. The method is the procedure
  (architecture, hyperparameters, seed, early stopping, ν, median-γ rule, empirical
  calibration), re-run as specified on healthy data only. The freeze explicitly permits the
  channel change.
- Interpretive note: 992 → 8 is much stronger compression than 128 → 8. This follows from
  the fixed q and is not tuned.
- **Channel-count mechanism [decision]:**
  - A runtime override (`pipeline.INPUT_CHANNELS = p`) needs zero edits. But it mutates
    module state: it would break `tests/test_pipeline.py`'s parameter-count test if both
    ran in one pytest session without `monkeypatch`, and it is easy to leave set.
  - A backward-compatible constructor parameter (`ConvAutoencoder1d(input_channels=
    INPUT_CHANNELS)`, threaded through `train_autoencoder`/`load_autoencoder`) is explicit
    and has no hidden state. The synthetic default is unchanged, so the existing tests
    still pass. It is the cleaner and safer option, but it edits `pipeline.py`.
  - Either needs approval.

---

## 8. Computational scope

These figures come from micro-benchmarks of the existing functions at p = 31 on this
machine (20 cores, 7.6 GB RAM, ~4 GB free, 864 GB free disk), single-threaded:

| Item | Estimate |
|---|---|
| Acquisition | The whole 23.9 GB Mode 1 file (it cannot be split by fault): about 8 min at 50 MB/s, 40 min at 10 MB/s. Remote HTTP range reads are possible but slower and add dependencies (fsspec). |
| Extracted subset (float64, p = 31) | about 250 MB for D5 (500 runs), 30 MB for 60 S2 runs, ~80 MB for ~530 S1 segments: **≈ 360 MB**, git-ignored |
| Peak memory | < 1.5 GB (M chart on 200×1969×31; `exact_gamma` for about 5.7k D2 windows ≈ 130 MB of pairs). Keep D2 ≲ 15k windows. |
| CAE training | 0.38 s per epoch on 9,104 windows → ≤ 100 epochs ≈ 40 s |
| Inference | 0.07 s per 2000-row run → about 1 min in total |
| OC-SVM | fit 0.7 s (n = 5,690); scoring 6 ms per run |
| MEWMA + calibration | ~1 s |
| Total compute | **under 5 min**, dominated by HDF5 extraction I/O |

The single-thread deterministic setup is retained unchanged.

---

## 9. Risks and scientific issues

1. **No dedicated healthy runs.** Long healthy trajectories may not exist. This is the
   binding constraint (§5, Path B → STOP).
2. **Seed reuse across faults or groups** would make pre-fault segments identical copies:
   fake independence, and possible leakage into D5's pre-onset period. Verify via seed
   metadata first. Use hashing or bitwise duplicate detection of pre-fault rows only if the
   metadata is insufficient, under the §5 data-access rule.
3. **`SpMagnitude100` semantics** are unconfirmed (a nominal "no-change" run is an
   inference, not documentation).
4. **Truncated calibration** on 569-decision segments would bias the limit under the
   frozen estimator.
5. **Pre-fault alarms** may be frequent. Their treatment determines what the D5 delay
   means (§6 [decision]). Alarm-in-progress at onset can masquerade as detection.
6. **Estimand mismatch.** Onset-referenced delay ≠ synthetic zero-state ARL1. Magnitude %
   ≠ δ. Compare only qualitatively (ordering of H vs M).
7. **Variable selection.** Excluded analysers may carry IDV(2)'s direct signature. The
   rule is fixed from documentation and D1 only and is never revisited post hoc.
8. **Shutdown runs.** Excluding them conditions on the fault outcome (§5 [decision]).
9. **Unequal replication** (100 vs 200) unless an equal-count rule is chosen [decision].
10. **Start-up transient.** Check stationarity of early rows on D1 only. Any trimming rule
    must be pre-registered [decision].
11. **Raw-MEWMA conditioning [decision].**
    - TEP raw units span orders of magnitude, so the 1e8 guard in `pooled_moments`/
      `mewma_t2` might trip.
    - If standardisation is applied consistently (x̃ = (x − m)/s, with μ and Σ transformed
      correspondingly, or estimated on x̃), the Mahalanobis MEWMA T² is affine-invariant
      in exact arithmetic. Standardising would then be a numerical stabilisation, not a
      methodological advantage.
    - **Test the raw formulation first.** Standardise M only if the raw form demonstrably
      fails, and only with approval. If the standardised form also fails, that indicates
      genuine collinearity: report it, don't relax the guard.
12. **Calibration vs validation.** D3 and D4 are disjoint by run and seed. No
    recalibration after D4 or D5.
13. **Post-hoc tuning.** Everything in the protocol (Gate 2) is frozen before any
    post-onset IDV(2) value is inspected. Before that, only IDV(2) metadata may be read,
    plus pre-fault rows read mechanically for duplicate detection (§5 data-access rule).
14. **Small D3/D4** if few independent full-length runs exist. SEs will be wide; report
    them.
15. **Simulation, not plant data.** TEP is simulated (as the freeze notes).

---

## 10. Recommendation

**Feasibility.** Mode 1, IDV(2) and the four magnitudes are **documented** in the dataset
(100/100/100/200 simulations, 2000 observations, 30 h onset) [verified, paper; verify in
file]. So the fault side appears feasible. Overall feasibility depends on Gate 1 confirming
enough **independent, full-length, nominal** healthy runs for D3/D4. If that fails, stop
(§5 Path B).

Recommended sequence (nothing here is implemented by this audit):

**Gate 1 — metadata only.**

- Acquire Mode 1 data. The method is an open engineering choice, settled when Gate 1
  starts:
  - **Full download** is the preferred reproducible option if practical. The file is
    about 23.9 GB and local disk space is sufficient. If chosen, compute and record the
    SHA-256.
  - **Remote range access** is the alternative. If chosen, record the official file ID
    (26003087), the byte size (23,924,710,848) and the source metadata, and hash every
    extracted local subset.
  - The acquisition method must not affect any scientific allocation decision.
- Read `Processdata_Labels`.
- Enumerate the tree and report:
  - the exact IDV(2) paths;
  - per magnitude: total, completed and stopped runs, stopped-run lengths and shutdown
    times;
  - row counts, the `pd(1)` time grid and the `idv_init` activation time (hence the first
    faulty row);
  - seeds for every candidate run, and any seed reuse across faults and groups;
  - `SpMagnitude100` existence, metadata (`setpoint_init` unchanged?) and seed
    uniqueness;
  - the number of genuinely independent healthy runs from each source.
- No post-onset IDV(2) fault-response values are inspected. Pre-fault rows are read only
  mechanically for duplicate detection, and only if seed metadata is insufficient (§5
  data-access rule). **STOP.**

**Gate 2 — protocol freeze (after approval).** Write and commit a protocol with:

- the exact variable list (constant check on D1 training rows only);
- run IDs and seeds per role and the D1–D5 counts;
- the fault-onset rule;
- the D5 run-inclusion rule (shutdowns, equal vs all counts);
- the pre-fault-alarm policy and detection-delay definition;
- the M-input formulation;
- the channel-count mechanism.

**STOP.**

**Gate 3 — implementation (only after the protocol is frozen).** Implement
`application/tep_data.py`, `application/run_tep_application.py` and a small test file. Run
Phase I and Phase II. Produce one table and one figure. `tests/test_pipeline.py` passes
unchanged.

**Open decisions.**

1. Path A viability and the D3/D4 split, after the Gate 1 counts.
2. The pre-fault-alarm policy (A / B / other) and the primary delay metric.
3. D5 inclusion for stopped runs.
4. All runs vs equal counts per magnitude.
5. Raw vs standardised M inputs (raw is tested first).
6. The channel-count mechanism (runtime override vs constructor parameter).
7. The final D1/D2 counts.
8. Acquisition method: full download (preferred if practical) vs range reads. Settled
   when Gate 1 starts; no bearing on allocation.
9. Whether to include the D4b diagnostic.
10. A start-up-transient rule, if needed.
