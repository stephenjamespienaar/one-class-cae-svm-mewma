# Extended TEP Application — Gate 1 Metadata Verification Report

Status: **Gate 1 only (metadata verification).** Nothing here allocates runs, amends
`DESIGN_FREEZE.md`, or authorises implementation. No model was trained, fitted, calibrated
or evaluated. No figure was produced.

Evidence markers:

- **[FILE]** — VERIFIED FROM FILE (`TEP_Mode1.h5`, read locally with h5py).
- **[DOC]** — VERIFIED FROM OFFICIAL DOCUMENTATION (Figshare/DTU article metadata, official
  `Readme.html`, or Reinartz, Kulahci & Ravn (2021) as cited in `TEP_AUDIT.md`).
- **[INFERENCE]** — reasoned from verified facts, not directly stated.
- **[UNRESOLVED]** — cannot be settled from metadata/documentation under the Gate 1
  data-access rule.

Date of inspection: 2026-09-29.

---

## 0. Data-access compliance

What was read from `TEP_Mode1.h5`:

- The full object tree: names, shapes, dtypes, chunking and attribute names.
- `Processdata_Labels` and `Additional_Meas_Labels`.
- For every one of the 14,440 run groups:
  - the attributes `seed`, `modeAtInit`, `simTerminatedSuccessfully` and `tRampSetpoint`;
  - the datasets `idv_init`, `setpoint_init` and `time_info`;
  - dataset shapes;
  - `processdata[:, 0]`, the pd(1) time column only.
- Conditional duplicate detection (§7), triggered by seed reuse. This took SHA-256 hashes of
  the raw bytes of `processdata` rows with 0 < t < 30 h, for 116 runs:
  - the 60 S2 runs;
  - the 56 SingleFault runs that share a seed. One of these is IDV(2) 75 % Run99, whose
    pre-fault rows only were hashed.

  Only hashes and duplicate-group membership were retained. No value was printed,
  summarised, plotted, or used for any other purpose.

What was **not** read:

- Any post-onset IDV(2) process value.
- `additional_meas`, `economic_data` and `idv_monitoring`.
- Any `processdata` column other than pd(1), outside the hashing above.
- The run-group attributes `meanOpCost`, `meanProduction` and `meanQuality`. These are
  run-level summaries that include the post-onset period, so for IDV(2) runs they are
  post-onset summaries. The structure pass captured them into a local, git-ignored scratch
  file outside the repository. They were deleted from that file without being viewed, and
  excluded from every later read.

Inspection scripts live outside the repository (`~/.cache/tep_gate1/`), as the Gate 1 rule
requires. They ran in an ephemeral environment: `uv run --no-project --with h5py --with
numpy`, with h5py 3.16.0, HDF5 2.0.0 and numpy 2.5.3. `requirements.txt` is unchanged.

---

## 1. Acquisition provenance and integrity

| Item | Value | Marker |
|---|---|---|
| Dataset | Reinartz, Kulahci & Ravn, *Tennessee Eastman Reference Data for Fault-Detection and Decision Support Systems*, DTU Data, DOI 10.11583/DTU.13385936.v1, CC0, published 2021-03-12 | [DOC] |
| File | `TEP_Mode1.h5`, Figshare/DTU file ID **26003087** | [DOC] |
| Source URL | `https://ndownloader.figshare.com/files/26003087` (302 redirect to the DTU S3 store `s3q.ait.dtu.dk`) | [DOC] |
| Expected size | 23,924,710,848 bytes (article API) | [DOC] |
| Local size | **23,924,710,848 bytes** | [FILE] |
| Official MD5 (Figshare `supplied_md5` = `computed_md5`) | `c79ecc6d12a5ccb49caffcd8f531feae` | [DOC] |
| Local MD5 | **`c79ecc6d12a5ccb49caffcd8f531feae`** — matches | [FILE] |
| Local SHA-256 | **`d6b0ed0ef3974ff571afd6717ba0418a5b8eb58a7822c84a05735572d52b3294`** | [FILE] |
| Acquisition date | 2026-09-29 (download started 00:30:32Z; file finalised 04:13Z; independent re-hash completed 04:56:40Z) | — |
| Local path | `application/data/raw/TEP_Mode1.h5` (git-ignored by `.gitignore:40`) | [FILE] |

Acquisition method:

- **Download.** The server throttles each connection to about 0.3 MB/s, so the file was
  fetched as 12 parallel byte-range segments. Each fetch used `curl -L --fail`, only HTTP 206
  responses were accepted, and every segment was checked for its exact expected size.
- **Crash during assembly.** WSL stopped unexpectedly while the parts were being joined. All
  12 parts had already completed at their exact sizes.
- **Spot check after restart.** 48 samples of 1 MiB each (4 per part: start, ⅓, ⅔, end) were
  byte-compared with the server. All matched.
- **Final file.** It was then assembled from the parts. Its MD5 matches the official value,
  and the MD5/SHA-256 were recomputed independently afterwards (the table above).
- **Leftovers.** The segment directory `application/data/raw/parts/` (~23.9 GB, git-ignored)
  still exists. It can be removed after review.

**Correction to `TEP_AUDIT.md` §4.** The audit stated that no published checksum had been
identified. **That statement is superseded.** The Figshare article API
(`api.figshare.com/v2/articles/13385936`) publishes the MD5 above for file 26003087, and the
local file matches it.

A successful download is not taken as evidence of the internal structure. The structure is
verified separately in §2.

---

## 2. Verified HDF5 structure

**Root [FILE]:** `Additional_Meas_Labels` (32,) object, `Processdata_Labels` (54,) object,
and the group `Mode1`. The root has no attributes. The whole file holds 110,321 objects and
**14,440 run groups**; a run group is any group containing `processdata`.

**Hierarchy under `Mode1` [FILE]:**

```
Mode1/
├── SingleFault/
│   ├── SimulationCompleted/IDV{1..28}/Mode1_IDVInfo_{i}_{25,50,75,100}/Run{k}
│   │      111 magnitude groups, 13,800 runs
│   │      (IDV6 has 25/50/75 only; its 100 % group is under SimulationStopped)
│   └── SimulationStopped/IDV6/Mode1_IDVInfo_6_100/Run{1..200}
│          the ONLY stopped SingleFault group; 200 runs
├── SpVariation/
│   ├── SimulationCompleted/SP{1..12}/tRamp_{0,10,20,30,40}/SpMagnitude{85..115}
│   │      405 runs; the SpMagnitude group IS the run (no Run{k} level)
│   └── SimulationStopped/SP{5,9}/tRamp_*/SpMagnitude*
│          15 runs
└── ModeTransition/
    ├── SimulationCompleted/Mode1ToMode{2..6}/TransitionTime{10,20,30,40}
    │      18 runs
    └── SimulationStopped/Mode1ToMode{3,6}/TransitionTime10
           2 runs
```

- **The Readme differs from the file.** It lists `SimulationStopped/IDV (1-28)` [DOC], but
  the file contains **only IDV6 (100 %)** under `SingleFault/SimulationStopped` [FILE].
- **The paths in `TEP_AUDIT.md` were right.** Its extrapolated path pattern for IDV(2) is
  confirmed, for example
  `Mode1/SingleFault/SimulationCompleted/IDV2/Mode1_IDVInfo_2_25/Run1` [FILE].

**Contents of a run group [FILE]:**

| Object | Shape / type | Content |
|---|---|---|
| attr `seed` | float, e.g. `[21812.0]` | RNG seed |
| attr `modeAtInit` | `[1.0]` in all 14,440 runs | initial operating mode |
| attr `simTerminatedSuccessfully` | 1 in all 14,223 completed runs; 0 in all 217 stopped runs | completion flag |
| attr `tRampSetpoint` | SpVariation/ModeTransition: equals the ramp duration. SingleFault: 1.0 at 100 %, 0.0 at 25–75 % (no set-point change in either case) | ramp duration (h) |
| attrs `meanOpCost`, `meanProduction`, `meanQuality` | not read | run-level economic summaries (§0) |
| `processdata` | (2000, 54) or (2001, 54) float64; shorter if stopped | pd(1) = time; 53 process variables |
| `additional_meas` | (n, 32) float64 | Bathelt additional measurements (not read) |
| `economic_data` | (2001, 5) float64 (shorter if stopped) | not read |
| `idv_init` | (3, 28) float64 | row 1 = magnitude before, row 2 = magnitude after, row 3 = activation time (h), per IDV. Layout [DOC paper] matches the values [FILE]. |
| `setpoint_init` | (3, 12) float64 | row 1 = initial set point, row 2 = target set point, row 3 = change time (h), per set point [INFERENCE from values; consistent with Readme "setpoint profiles"] |
| `time_info` | (1, 5) float64 = `[0, 100, 0.05, 0.0005, 70]` in **all** runs | Readme: "internal simulation parameters … can be ignored" [DOC]. The first three match start/end/sampling interval (h) [INFERENCE]; the last two are [UNRESOLVED], not needed. |
| `idv_monitoring` | (2000, 21) or (2001, 21) float64 | present only in completed runs of IDV 8–13, 16–18, 20–28 (9,000 datasets). **Not present in IDV(2).** Not read; undocumented in the Readme. |

**There is no per-row label or fault-indicator dataset [FILE].** The fault state of a row must
be derived from `idv_init` together with pd(1).

---

## 3. Process-variable schema

`Processdata_Labels` (54 entries) [FILE]. The XMEAS/XMV numbering comes from the paper's
Table A.4 [DOC]. The file labels carry names only, so the numbering below is by position.

| pd | Label (file) | Standard ID [DOC] | Candidate? |
|---|---|---|---|
| 1 | Time | time (h) | excluded (identifier) |
| 2 | A Feed | XMEAS(1) | **yes** |
| 3 | D Feed | XMEAS(2) | **yes** |
| 4 | E Feed | XMEAS(3) | **yes** |
| 5 | A and C Feed | XMEAS(4) | **yes** |
| 6 | Recycle Flow | XMEAS(5) | **yes** |
| 7 | Reactor Feed Rate | XMEAS(6) | **yes** |
| 8 | Reactor Pressure | XMEAS(7) | **yes** |
| 9 | Reactor Level | XMEAS(8) | **yes** |
| 10 | Reactor Temperature | XMEAS(9) | **yes** |
| 11 | Purge Rate | XMEAS(10) | **yes** |
| 12 | Product Sep Temp | XMEAS(11) | **yes** |
| 13 | Product Sep Level | XMEAS(12) | **yes** |
| 14 | Product Sep Pressure | XMEAS(13) | **yes** |
| 15 | Product Sep Underflow | XMEAS(14) | **yes** |
| 16 | Stripper Level | XMEAS(15) | **yes** |
| 17 | Stripper Pressure | XMEAS(16) | **yes** |
| 18 | Stripper Underflow | XMEAS(17) | **yes** |
| 19 | Stripper Temp | XMEAS(18) | **yes** |
| 20 | Stripper Steam Flow | XMEAS(19) | **yes** |
| 21 | Compressor Work | XMEAS(20) | **yes** |
| 22 | Reactor Coolant Temp | XMEAS(21) | **yes** |
| 23 | Separator Coolant Temp | XMEAS(22) | **yes** |
| 24–29 | Component A–F to Reactor | XMEAS(23–28) | excluded (analyser) |
| 30–37 | Component A–H in Purge | XMEAS(29–36) | excluded (analyser) |
| 38–42 | Component D–H in Product | XMEAS(37–41) | excluded (analyser) |
| 43 | D feed | XMV(1) | **yes** |
| 44 | E Feed | XMV(2) | **yes** |
| 45 | A Feed | XMV(3) | **yes** |
| 46 | A and C Feed | XMV(4) | **yes** |
| 47 | Recycle | XMV(5) | **yes** |
| 48 | Purge | XMV(6) | **yes** |
| 49 | Separator | XMV(7) | **yes** |
| 50 | Stripper | XMV(8) | **yes** |
| 51 | Steam | XMV(9) | **yes** |
| 52 | Reactor Coolant | XMV(10) | **yes** |
| 53 | Condenser Coolant | XMV(11) | **yes** |
| 54 | Agitator | XMV(12) | **yes** |

**Schema facts:**

- The file has 54 columns [FILE]. pd(1) is the time in hours [FILE: label "Time"; the values
  form the 0.05 h grid].
- **The 34 pre-registered candidates are pd(2–23) and pd(43–54)**, as the table shows.
- **Label names are not unique** [FILE]. "A Feed", "E Feed" and "A and C Feed" each appear
  twice, once as an XMEAS and once as an XMV. Any loader must therefore select columns **by
  index, never by name**.
- **No constant-column check was run.** Per protocol it belongs to Gate 2, on D1 training
  rows only. The audit's expectation of p = 31 (XMV 5, 9 and 12 fixed in Mode 1) remains
  [UNRESOLVED].
- **`additional_meas` contains "B in stream 4"** [FILE, label only]. That is the directly
  disturbed quantity of IDV(2). It sits outside `processdata` and outside the pre-registered
  rule, and it must never be introduced.

---

## 4. IDV(2) — counts and timing

**Paths and counts [FILE].** Paths have the form
`Mode1/SingleFault/SimulationCompleted/IDV2/Mode1_IDVInfo_2_{M}/Run{k}`.

| Magnitude M | Total runs | Completed | Stopped | Run IDs | Rows per run | Unique seeds | Seed range |
|---|---|---|---|---|---|---|---|
| 25 % | 100 | 100 | **0** | Run1–Run100 | 2000 (all) | 100 | 135,854 – 1,303,132 |
| 50 % | 100 | 100 | **0** | Run1–Run100 | 2000 (all) | 100 | 145,716 – 1,300,043 |
| 75 % | 100 | 100 | **0** | Run1–Run100 | 2000 (all) | 100 | 163,843 – 1,308,423 |
| 100 % | 200 | 200 | **0** | Run1–Run200 | **2001** (all) | 200 | 350 – 60,183 |

**Structure facts:**

- **There are no stopped IDV(2) runs** [FILE]. So there are no stopped-run lengths or
  shutdown times to report for IDV(2), and the audit's shutdown-inclusion decision is moot
  for IDV(2).
- **The counts match the paper's 100/100/100/200** [DOC].
- **Seeds:** all 500 IDV(2) seeds are distinct. No IDV(2) seed is shared with S2, the
  ModeTransition runs, or any other magnitude. Exactly **one** IDV(2) seed is shared with a
  non-IDV(2) run (§7).
- **Fault magnitude and timing:** `idv_init` for IDV(2) is `[0, M/100, 30.0]` in every run
  (for example `[0, 0.25, 30]` at 25 %). No other IDV column is active in any SingleFault
  run [FILE].
- **`time_info`** is `[0, 100, 0.05, 0.0005, 70]` for every run [FILE].
- **The 100 % seeds are a separate batch.** Their range (350–60,183) is disjoint from the
  25–75 % range [FILE]. The 100 % runs were evidently generated separately [INFERENCE].

Every seed, by run, is listed in Appendix A.

**Time grid [FILE]:**

- The sampling interval is **0.05 h (3 min)** in every one of the 14,440 runs, and it is
  uniform.
- **The grid differs by magnitude.** This holds for every fault family, not just IDV(2):

| Group | Rows | pd(1) first → last | Row stamped t = 30.00 h | First row with t > 30 h |
|---|---|---|---|---|
| 25 %, 50 %, 75 % (and all S2) | 2000 | 0.05 → 100.00 | row **600** | row **601** (t = 30.05) |
| 100 % | 2001 | **0.00** → 100.00 | row **601** | row **602** (t = 30.05) |

The time grid is bitwise identical across all runs within each group [FILE].

**Onset.** The fault activation time is **exactly 30.0 h** for all 500 IDV(2) runs
(`idv_init` row 3) [FILE], which matches the paper's 30 h [DOC]. Converting that to a row
index for L = 32 (decision j = t_row − 31):

| Grid | If the t = 30.00 sample is pre-fault (first faulty row = first t > 30) | If the t = 30.00 sample is faulty | Decisions per run |
|---|---|---|---|
| 2000-row (25/50/75 %) | τ = 601, **j_τ = 570** (pre-onset j = 1…569; post-onset 1400) | τ = 600, j_τ = 569 | 1969 |
| 2001-row (100 %) | τ = 602, **j_τ = 571** (pre-onset j = 1…570; post-onset 1400) | τ = 601, j_τ = 570 | 1970 |

- **Verified:** the activation instant is 30.0 h; the sampling grid is as above. "Row 601 /
  j = 570" is correct **only** for the 2000-row grid, under the "first sample strictly after
  activation" convention. It is **not** correct for the 100 % runs as stored.
- **[UNRESOLVED]** Whether the sample stamped exactly t = 30.00 h reflects the post-switch
  process. Metadata cannot settle this. Under continuous-state dynamics, a step disturbance
  entering through the state derivatives cannot have changed the state at the instant of
  activation, which favours "pre-fault" [INFERENCE]. This is not verified.
- **[UNRESOLVED / decision]** How to align the two grids. One option is to drop the t = 0
  row of the 2001-row runs, which makes every run 2000 rows with an identical grid [FILE:
  the grids are otherwise identical from t = 0.05]. This must be pre-registered at Gate 2.

---

## 5. S1 — pre-fault nominal segments

**A. S1-all census** (every SingleFault run, including IDV(2)) [FILE]:

- **Totals.** 14,000 runs = 13,800 completed + 200 stopped (IDV6 100 %).
- **Every run has a complete 30 h nominal segment.** The activation time is 30.0 h in all
  14,000 runs, with no other fault active.
- **The stopped IDV6 runs are no exception.** They shut down at t = 37.00–37.15 h (741–744
  rows, starting at t = 0), so all 30 pre-fault hours are present.
- **Segment length** in rows:

| Grid | Rows with 0 < t < 30 | Rows with t < 30 | Rows with t ≤ 30 |
|---|---|---|---|
| 2000-row (25/50/75 %) — 8,400 runs | 599 | 599 | 600 |
| 2001-row (100 %) — 5,400 runs | 599 | 600 (includes t = 0) | 601 |
| Stopped IDV6 100 % — 200 runs | 599 | 600 (includes t = 0) | 601 |

- **Seeds.** There are 13,972 unique seeds across the 14,000 runs.
- **Repeated seeds.** 28 seeds are used by exactly two runs each, always in different fault
  families or magnitudes. Hashing shows that **all 28 pairs have bitwise-identical pre-fault
  blocks** (§7).
- **Seeds do not follow a (magnitude, run) pattern.** Each (magnitude, run index) position
  has 28 distinct seeds across the 28 families.

**B. S1-eligible pool for future D1/D2** (IDV(2) excluded entirely) [FILE]:

| Step | Runs |
|---|---|
| S1-all | 14,000 |
| minus every IDV(2) run | 13,500 |
| minus non-IDV(2) runs whose seed equals any IDV(2) seed: **IDV21 50 % Run68** (seed 1,213,745 = IDV2 75 % Run99; identical pre-fault block) | 13,499 |
| of which: runs with a seed unique within the pool | **13,445** |
| of which: runs in 27 within-pool duplicate pairs (identical pre-fault blocks) | 54 |
| maximum number of distinct, independent pre-fault trajectories (one per duplicate pair) | 13,472 |

Per family (non-IDV(2)):

- Every family has 500 runs (100/100/100/200).
- Runs lost to within-pool duplicate pairs, per family:

  | Loss | Families |
  |---|---|
  | 0 | IDV1, IDV6, IDV13, IDV27 |
  | 1 | IDV5, IDV12, IDV15, IDV18, IDV20, IDV26 |
  | 2 | IDV3, IDV9, IDV10, IDV17, IDV23, IDV25 |
  | 3 | IDV4, IDV8, IDV11, IDV14, IDV16 |
  | 4 | IDV7, IDV19, IDV22, IDV24, IDV28 |

- Separately from those, IDV21 loses one run (50 % Run68) to the IDV(2)-seed exclusion.
- IDV6's 100 % runs are the stopped ones; their pre-fault segments are complete.

**Independence [INFERENCE].** Runs with a shared seed have identical pre-fault blocks, and
runs with distinct seeds were never found to coincide. So the seed is the effective key of
the pre-fault stochastic trajectory. Distinct seeds are taken to mean independent
realisations; this is standard for a seeded simulator but is not proven from the file. No
D1/D2 allocation is made here.

---

## 6. S2 — `SpVariation/…/SpMagnitude100`

**Existence and structure [FILE]:**

- **SpMagnitude100 exists** for all 12 set points (SP1–SP12) × 5 ramp profiles (`tRamp_0`,
  `10`, `20`, `30`, `40`): **60 runs, all under `SimulationCompleted`**. The Readme lists
  `SpMagnitude (85, 90, 95, 100, 105, 110)` plus 115 [DOC].
- **Every one is full-length:** 2000 rows, pd(1) from 0.05 to 100.00 h, on the same grid as
  the 2000-row fault runs.
- **None of the 15 stopped SpVariation runs is at magnitude 100.** They are SP5 at 110/115 %
  and SP9 at 85/90/115 %, shutting down between 30.1 and 58.55 h.

**Metadata for the 60 SpMagnitude100 runs [FILE]:**

- `idv_init` is all zero: no fault is scheduled.
- `setpoint_init` row 1 = row 2 in **all 12 columns** for all 60 runs, and row 3 = 30.0 in
  every column. So a set-point event is scheduled at 30 h, but **its target equals the
  initial value**: no scheduled change.
- The initial set points are identical across all 60 runs, and identical to those of every
  SingleFault run.
- `tRampSetpoint` equals the directory ramp value.
- For comparison, every non-100 SpVariation run changes exactly one set-point column (SPk
  changes column k).

**Seeds [FILE]:**

- **Only 5 unique seeds exist across all 60 SpMagnitude100 runs**, and across all 420
  SpVariation runs. The seed is `3010000 + ramp index`: `tRamp_0` → 3,010,000,
  `tRamp_10` → 3,010,001, `tRamp_20` → 3,010,002, `tRamp_30` → 3,010,003,
  `tRamp_40` → 3,010,004. The same seed is used for all 12 set points and all 7 magnitudes.
- **Seed overlap:** none with S1 or with IDV(2), and none with ModeTransition (whose 20
  seeds, 90,000–91,064, are all unique).

**Duplicate detection (triggered by seed reuse) [FILE]:**

- The 0 < t < 30 h blocks of the 60 runs hash to **exactly 5 distinct values**.
- Each hash is shared by the 12 SP runs with the same ramp/seed, so those 12 runs are
  bitwise identical over the first 30 h.

**Terminology:**

- Metadata establishes that these runs have **no scheduled set-point change and no fault**.
  They are candidate nominal runs.
- Whether the post-30 h portions of same-seed runs are also bitwise identical was not
  checked; only pre-event rows were hashed. With the same seed and no effective set-point
  change they are expected to be identical [INFERENCE]. Either way, they are not independent
  realisations.
- **Statistical stationarity is not established.** It would need a pre-registered
  healthy-data diagnostic [UNRESOLVED].

**Other full-length, no-event Mode 1 runs [FILE]:**

- All other SpVariation runs change a set point at 30 h.
- All ModeTransition runs start a mode transition at 30 h.
- All SingleFault runs activate a fault at 30 h.

**The file therefore contains no other full-length (100 h) nominal run.**

**Independent full-length no-change runs available: 5** (one per seed/ramp profile). The
ramp duration of a zero-magnitude change has no effect on the target [INFERENCE].

---

## 7. Seed-overlap and independence audit

Seed counts per source [FILE]:

| Source | Runs | Unique seeds | Seeds repeated within source | Runs involved in repeats |
|---|---|---|---|---|
| IDV(2) 25 % | 100 | 100 | 0 | 0 |
| IDV(2) 50 % | 100 | 100 | 0 | 0 |
| IDV(2) 75 % | 100 | 100 | 0 | 0 |
| IDV(2) 100 % | 200 | 200 | 0 | 0 |
| IDV(2) all | 500 | 500 | 0 | 0 |
| S1-all (all SingleFault) | 14,000 | 13,972 | 28 | 56 |
| S1-eligible (non-IDV(2), IDV(2)-seed overlap removed) | 13,499 | 13,472 | 27 | 54 |
| S2 SpMagnitude100 | 60 | **5** | 5 | **60** |
| SpVariation (all magnitudes) | 420 | 5 | 5 | 420 |
| ModeTransition | 20 | 20 | 0 | 0 |

Shared seed values between sources [FILE]:

| | IDV2 25 | IDV2 50 | IDV2 75 | IDV2 100 | SF non-IDV2 | S2 | MT |
|---|---|---|---|---|---|---|---|
| IDV2 25 | — | 0 | 0 | 0 | 0 | 0 | 0 |
| IDV2 50 | 0 | — | 0 | 0 | 0 | 0 | 0 |
| IDV2 75 | 0 | 0 | — | 0 | **1** | 0 | 0 |
| IDV2 100 | 0 | 0 | 0 | — | 0 | 0 | 0 |
| SF non-IDV2 | 0 | 0 | **1** | 0 | (27 internal pairs) | 0 | 0 |
| S2 | 0 | 0 | 0 | 0 | 0 | (5 seeds × 12) | 0 |

Duplicate groups from hashing [FILE]. The hashed rows are 0 < t < 30 h, 599 rows × 54
columns, aligned in time across the 2000/2001-row grids.

- **S2:** 5 groups of 12 identical runs (one per ramp profile, all 12 SPs each).
- **SingleFault:** all 28 repeated-seed pairs are identical. The pair involving IDV(2) is
  **IDV2 75 % Run99 ≡ IDV21 50 % Run68** (seed 1,213,745). The other 27 pairs, all
  non-IDV(2):

```
184607 IDV23_50_R10|IDV7_25_R53    194810 IDV11_75_R68|IDV8_75_R48    212238 IDV17_25_R61|IDV17_75_R68
292410 IDV14_75_R71|IDV28_75_R58   345186 IDV16_25_R74|IDV21_25_R88   390614 IDV15_25_R60|IDV7_50_R88
556578 IDV19_75_R63|IDV4_25_R60    597939 IDV16_50_R27|IDV28_50_R11   604985 IDV25_25_R19|IDV3_25_R28
646442 IDV26_25_R45|IDV9_50_R15    668153 IDV10_75_R74|IDV5_50_R46    720677 IDV11_50_R93|IDV12_50_R1
721608 IDV22_75_R73|IDV8_75_R82    761324 IDV14_50_R77|IDV19_25_R56   775020 IDV23_75_R73|IDV9_25_R70
869131 IDV22_25_R41|IDV24_75_R72   991145 IDV24_50_R16|IDV25_50_R75   1034703 IDV10_25_R10|IDV8_75_R79
1059846 IDV20_50_R15|IDV4_50_R82   1074816 IDV24_50_R97|IDV28_75_R25  1078118 IDV3_75_R52|IDV7_50_R79
1079009 IDV11_75_R20|IDV19_50_R48  1101663 IDV14_50_R42|IDV16_25_R27  1152610 IDV19_25_R41|IDV28_50_R31
1161013 IDV22_75_R48|IDV7_75_R20   1188587 IDV22_50_R30|IDV24_50_R79  1245695 IDV18_25_R15|IDV4_75_R29
```

**What this implies:**

- The seed fully determines the pre-fault trajectory. Seed metadata is therefore a
  sufficient independence key for every run with a unique seed [INFERENCE, supported by 33
  of 33 same-seed groups being identical].
- **The 12-fold S2 duplication and the IDV2 75 % Run99 ≡ IDV21 50 % Run68 pair are real
  duplications, not metadata artefacts.**

---

## 8. Exact unresolved facts

1. Whether the sample stamped t = 30.00 h is pre- or post-activation. This decides
   τ = 600/601 on the 2000-row grid and τ = 601/602 on the 2001-row grid.
2. How the 2000-row (25–75 %) and 2001-row (100 %) grids will be aligned. What the extra
   t = 0 row of the 100 % runs represents is also undocumented.
3. Whether the post-30 h portions of same-seed S2 runs are bitwise identical. This was not
   checked and does not change the count of independent seeds (5).
4. Statistical stationarity of any healthy source. It is not assessable from metadata.
5. Which of the 34 candidates are structurally constant (Gate 2, D1 rows only; p = 31 is
   only an expectation).
6. The meaning of `time_info[3:5]` (0.0005, 70) and the content of `idv_monitoring`. Neither
   is needed.
7. Whether distinct seeds give statistically independent streams. This is standard for the
   simulator's RNG but not proven from the file.

---

## 9. Gate 1 feasibility answers

1. **Are the documented IDV(2) 25/50/75/100 % scenarios present?** Yes [FILE]. They are at
   `Mode1/SingleFault/SimulationCompleted/IDV2/Mode1_IDVInfo_2_{25,50,75,100}`.
2. **Completed/stopped counts?**

   | Magnitude | Completed | Stopped |
   |---|---|---|
   | 25 % | 100 | 0 |
   | 50 % | 100 | 0 |
   | 75 % | 100 | 0 |
   | 100 % | 200 | 0 |

   [FILE]
3. **Is the fault onset exactly identifiable?**
   - **In time: yes.** Activation is at exactly 30.0 h in every run [FILE].
   - **At row level: only up to one convention [UNRESOLVED].** It depends on whether the
     t = 30.00 h sample counts as faulty. Under the strict-after convention, τ = 601
     (j = 570) for 25–75 % and τ = 602 (j = 571) for 100 % as stored. The audit's
     "row 601 / j = 570" is not universal.
4. **Enough independent S1 segments for D1/D2?** **Yes.**
   - There are 13,445 non-IDV(2) runs with unique seeds, and 13,472 distinct trajectories at
     most. Each has 599–600 pre-fault rows.
   - The audit's candidate need was about 30 runs.
   - The pool excludes all IDV(2) runs and every run sharing an IDV(2) seed.
5. **Do full-length S2 SpMagnitude100 no-change runs genuinely exist?** **Yes, but only as 5
   distinct simulations.**
   - There are 60 full-length (2000-row, 100 h) completed runs with no fault and no effective
     set-point change [FILE].
   - They come from 5 seeds, and each seed's 12 runs are bitwise identical over the hashed
     pre-event period [FILE].
6. **Independent full-length S2 runs after seed reuse/overlap: 5.** No S2 seed overlaps with
   S1 or IDV(2). No other full-length nominal Mode 1 run exists in the file.
7. **Is that plausibly sufficient for disjoint D3/D4 at ARL0 = 370 with the existing
   estimator?** **No.**
   - **How the estimator works.** `calibrate_limit` (`pipeline.py:885`) sets h as the
     smallest attained value at which the **mean of one zero-state run length per D3
     trajectory** reaches 370 (censored at the horizon, H = 1969 here).
   - **What 5 trajectories allow.** Any disjoint split gives D3 + D4 ≤ 5 trajectories: for
     example 3 + 2, so 3 run lengths to calibrate and 2 to validate. The synthetic design
     used 300 and 500.
   - **Precision.** With RL standard deviation of roughly ARL0, the relative standard error
     of a 3-run mean is about 1/√3 ≈ 58 % [INFERENCE]. D4 could not estimate the in-control
     ARL meaningfully.
   - **Duplicates add nothing.** Using all 60 runs would add bit-identical duplicates, not
     information, and would violate "no run in more than one role" in spirit.
   - **Full-length healthy data is available nowhere else.** S1 segments have 599–600 rows
     (≈ 568–569 decisions), the heavily censored case that `TEP_AUDIT.md` §5 flagged as
     biased under the frozen estimator. No alternative estimator is proposed here.

---

## 10. Decisions required before any Gate 2 protocol

Path A is not supported, so the first item is a design-review decision. The others still
need resolution under whatever design is approved.

1. **Healthy data for D3/D4 (design review).** Only 5 independent full-length nominal runs
   exist. A decision is needed on how, or whether, the D3/D4 analogue can be built under the
   frozen calibration procedure. This report does not propose or choose an alternative.
2. **Onset convention.** Decide whether the t = 30.00 h sample is pre- or post-fault.
3. **Grid alignment.** Decide how to treat the extra t = 0 row of the 2001-row runs
   (100 % IDV(2), 100 % S1 sources, stopped IDV6), for example dropping it.
4. **S1 segment definition.** Rows 0 < t < 30 (599) or t < 30 (599/600), and the handling of
   the t = 0 row.
5. **Within-pool duplicate pairs.** Choose between excluding both members of each of the 27
   pairs (13,445 remaining) and keeping one member of each (13,472).
6. **D5 inclusion.** There are no stopped IDV(2) runs, so stopped-run handling is moot for
   D5. It remains open whether to use all runs (100/100/100/200) or equal counts per
   magnitude.
7. **Pre-fault-alarm policy and delay definition** (`TEP_AUDIT.md` §6). This is unchanged.
8. **Raw vs standardised M inputs, and the CAE channel-count mechanism**
   (`TEP_AUDIT.md` §7, §9). These are unchanged.
9. **Excluded variables.** Formally confirm that `additional_meas` (including
   "B in stream 4") and the run attributes `meanOpCost`, `meanProduction` and `meanQuality`
   are excluded from every role.
10. **Cleanup.** Delete `application/data/raw/parts/` (~23.9 GB, git-ignored) after review.

---

## Appendix A — IDV(2) run seeds (run index : seed) [FILE]

**25 %** — 1:353528, 2:643826, 3:1206642, 4:354343, 5:966642, 6:1031100, 7:451132, 8:478187, 9:1264241, 10:381808, 11:579094, 12:917923, 13:571507, 14:936095, 15:1280879, 16:919330, 17:952971, 18:422053, 19:1159581, 20:1046350, 21:295295, 22:428283, 23:787354, 24:731617, 25:1281696, 26:1050298, 27:416678, 28:234641, 29:1078067, 30:959770, 31:1222270, 32:604931, 33:431105, 34:1003117, 35:608623, 36:766288, 37:317330, 38:1274144, 39:797363, 40:283563, 41:756582, 42:410164, 43:1144827, 44:1215470, 45:820346, 46:532364, 47:1303132, 48:933718, 49:341052, 50:408296, 51:998948, 52:785438, 53:176759, 54:787443, 55:1280767, 56:966424, 57:1270359, 58:1191556, 59:814602, 60:971743, 61:1125551, 62:942179, 63:321714, 64:295669, 65:537779, 66:1089030, 67:135854, 68:410526, 69:167601, 70:928793, 71:1134902, 72:1037908, 73:810208, 74:447182, 75:1211021, 76:1117244, 77:1227783, 78:1175952, 79:1032177, 80:847327, 81:1012252, 82:481874, 83:981089, 84:1193723, 85:182001, 86:534136, 87:411313, 88:213417, 89:659144, 90:213352, 91:1196765, 92:662268, 93:752855, 94:1276245, 95:1072438, 96:748865, 97:507073, 98:1119080, 99:202049, 100:372215

**50 %** — 1:465346, 2:994940, 3:803035, 4:866232, 5:432928, 6:330092, 7:412429, 8:237421, 9:1138716, 10:1167763, 11:945826, 12:408941, 13:856625, 14:497413, 15:663237, 16:322854, 17:398081, 18:180829, 19:481872, 20:688614, 21:535574, 22:1107970, 23:298433, 24:233183, 25:1199537, 26:1196432, 27:406783, 28:729209, 29:779740, 30:883231, 31:805892, 32:757134, 33:1214542, 34:148810, 35:374653, 36:817653, 37:1004646, 38:751187, 39:1260166, 40:1293426, 41:1072124, 42:988158, 43:314536, 44:1131818, 45:190829, 46:890226, 47:651421, 48:145716, 49:304685, 50:859170, 51:1231705, 52:883538, 53:1215522, 54:1004131, 55:576811, 56:556470, 57:1223460, 58:611380, 59:148990, 60:233853, 61:962964, 62:1191306, 63:1109315, 64:702341, 65:454365, 66:678233, 67:959562, 68:1030353, 69:1300043, 70:979366, 71:669230, 72:736363, 73:549150, 74:701800, 75:969243, 76:1095420, 77:1000204, 78:1248709, 79:544243, 80:918093, 81:1178037, 82:943405, 83:1030073, 84:781738, 85:209664, 86:808426, 87:365281, 88:741469, 89:1252711, 90:269556, 91:1272960, 92:1145540, 93:196516, 94:1086010, 95:453663, 96:151456, 97:548233, 98:876426, 99:557104, 100:735648

**75 %** — 1:1308423, 2:977927, 3:1162375, 4:633302, 5:678217, 6:288264, 7:238262, 8:698469, 9:1227744, 10:657589, 11:496671, 12:418153, 13:1239503, 14:534382, 15:1155378, 16:1227637, 17:528194, 18:449977, 19:750824, 20:836523, 21:796261, 22:276491, 23:799077, 24:687941, 25:448254, 26:1291056, 27:381333, 28:424944, 29:1252328, 30:1006826, 31:733754, 32:667032, 33:494062, 34:971669, 35:1201582, 36:654643, 37:1043863, 38:800316, 39:254540, 40:608401, 41:526454, 42:435734, 43:679863, 44:809437, 45:1138154, 46:163843, 47:996266, 48:403091, 49:1051473, 50:930297, 51:321860, 52:425040, 53:1280945, 54:1040816, 55:1130484, 56:566184, 57:928583, 58:639376, 59:901654, 60:931352, 61:1248036, 62:727607, 63:653031, 64:243777, 65:658478, 66:1094083, 67:617253, 68:838011, 69:232280, 70:268434, 71:1299941, 72:901578, 73:880690, 74:1152652, 75:455884, 76:915858, 77:218123, 78:194744, 79:1153016, 80:1177922, 81:1288033, 82:1189881, 83:280809, 84:312975, 85:1089881, 86:743697, 87:1064809, 88:847908, 89:1035233, 90:1240707, 91:913549, 92:998767, 93:426390, 94:243881, 95:1044648, 96:964249, 97:958304, 98:398321, 99:1213745, 100:682184

**100 %** — 1:20819, 2:13434, 3:36537, 4:26706, 5:18756, 6:19121, 7:10858, 8:42258, 9:3587, 10:18126, 11:5480, 12:45680, 13:2026, 14:11397, 15:17562, 16:44550, 17:24199, 18:10471, 19:15908, 20:44965, 21:350, 22:60177, 23:38387, 24:8779, 25:25367, 26:14691, 27:43663, 28:41175, 29:49942, 30:18728, 31:25405, 32:60178, 33:19996, 34:46583, 35:21385, 36:2111, 37:7878, 38:18068, 39:2943, 40:42169, 41:44500, 42:2945, 43:10125, 44:4369, 45:28654, 46:21850, 47:4441, 48:38787, 49:36697, 50:7262, 51:30792, 52:39911, 53:41012, 54:18432, 55:40497, 56:3035, 57:4538, 58:40280, 59:27350, 60:44757, 61:9343, 62:41624, 63:3132, 64:30002, 65:3004, 66:11677, 67:10986, 68:12963, 69:29965, 70:34746, 71:46107, 72:32779, 73:31683, 74:60179, 75:17893, 76:22700, 77:41947, 78:60180, 79:44484, 80:40573, 81:41113, 82:43245, 83:16938, 84:3164, 85:13344, 86:4629, 87:33566, 88:60181, 89:32816, 90:60182, 91:12081, 92:17550, 93:34988, 94:24436, 95:41019, 96:60183, 97:4704, 98:41589, 99:21334, 100:12848, 101:30295, 102:28857, 103:48073, 104:3169, 105:60171, 106:45101, 107:9760, 108:44884, 109:41081, 110:33298, 111:32834, 112:26778, 113:7402, 114:30769, 115:18696, 116:21937, 117:29959, 118:43899, 119:5796, 120:49287, 121:42863, 122:22081, 123:41581, 124:14633, 125:25547, 126:60172, 127:19017, 128:13314, 129:13131, 130:29132, 131:22157, 132:22324, 133:48935, 134:39569, 135:10574, 136:47429, 137:2928, 138:1198, 139:10425, 140:14715, 141:18302, 142:42504, 143:47088, 144:3190, 145:20479, 146:47373, 147:11144, 148:2379, 149:362, 150:10999, 151:33673, 152:6593, 153:35218, 154:19245, 155:18109, 156:48130, 157:4379, 158:12784, 159:20631, 160:35197, 161:37399, 162:1872, 163:39068, 164:15849, 165:60173, 166:4396, 167:17469, 168:6472, 169:15217, 170:47311, 171:38507, 172:41066, 173:5740, 174:10166, 175:29630, 176:535, 177:13591, 178:33046, 179:10038, 180:34287, 181:5365, 182:22350, 183:60174, 184:25989, 185:12839, 186:7997, 187:21086, 188:27935, 189:15034, 190:36779, 191:17009, 192:2235, 193:20410, 194:16110, 195:60175, 196:2711, 197:60176, 198:3987, 199:14628, 200:20829

---

GATE 1 FAILS FOR PATH A — STOP FOR DESIGN REVIEW.
