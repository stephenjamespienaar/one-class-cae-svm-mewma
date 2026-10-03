# Extended TEP Application — Phase I Freeze (Gate 3)

**Status: FROZEN (2026-09-29), before any D4 or D5 access. Pending human review and commit.**

Phase I follows `application/GATE2_PROTOCOL_FREEZE.md` and `application/tep_protocol.json`.
The inputs were D1-train (40 runs), D1-val (10), D2 (20) and D3 (2000), taken from the
committed registry, using aligned nominal rows 1–599 (t = 0.05…29.95 h) of the 31 frozen
columns.

**No D4 or D5 process value was read.** The loader refuses every role outside D1-train,
D1-val, D2 and D3. Nothing was tuned, and every frozen constant comes from `pipeline.py`.

- Code: `application/tep_pipeline.py`.
- Run: `.venv/bin/python application/tep_pipeline.py`. It takes about 80 s wall-clock,
  single-threaded, with a peak RSS of 2.4 GB.
- Two complete runs produced **byte-identical** Phase-I artifacts.

## Outcomes

| Stage | Result |
|---|---|
| D1 standardisation | ddof = 0, fitted on 23,960 pooled D1-train rows |
| D1 CAE (p = 31, q = 8, frozen training settings, seed 3795) | 22,720 train windows and 5,680 validation windows, all formed within runs. Early stopping at epoch 62. **Best epoch 52; best validation MSE 0.6774** (standardised units). |
| D2 OC-SVM (RBF, ν = 0.03, inverse-median γ) | 11,360 windows; median squared distance 47.99005644145471; **γ = 0.020837650008183387**; **361 support vectors**; ρ = 43.47717355518905 |
| D3 hybrid moments (2000 × 568 rows) | κ(Σ_y) = 1.985e4, which is below 1e8 ✓ |
| D3 M moments | **Pre-registered fallback ACTIVATED.** On the raw selected variables, κ(Σ_x) = 4.053e8 > 1e8. With the frozen D1 standardisation, κ(Σ_x) = 280.4 ✓. |
| **h_H**, H(0.05), first_update_index 1 | **325.46159653296104**; D3 in-sample FAP 100/2000 = 0.0500 |
| **h_M**, M(0.05), 31-row run-in, first_update_index 32 | **423.59388643957266**; D3 in-sample FAP 100/2000 = 0.0500 |

**Calibration rule.** For each chart, h* = `np.sort(R)[1899]`, the 1-based order statistic
R_(1900), where R_i = max_{j = 1…568} T²_ij. This is the frozen O3 rule; there is no
interpolation and signalling is strict T² > h. All three assertions passed:
- `sum(R > h*) = 100`;
- `sum(R > R_(1899)) > 100`;
- no tie at h*.

The D3 FAP is an in-sample value by construction. It is **not validation**; D4 provides that.

**The M fallback** is a numerical representation, not a design change. Raw and standardised
coordinates give the same MEWMA T² in exact arithmetic. The fallback was triggered only by
the frozen condition-number guard on D3 in-control moments, and before any calibration
output existed.

For D4 and D5, M must use the same representation: standardise both the run-in rows and the
monitored rows with the frozen D1 (mean, scale) from `preprocessing.npz`. This is recorded
in `mewma.npz` as `m_representation`.

**Reconstruction loss.** The high loss (about 0.68 of unit variance) reflects the frozen
992 → 8 compression applied to noise-dominated TEP measurements. It is reported as it is
and was not tuned.

## Code changes

- **`pipeline.py`:** a backward-compatible `input_channels=INPUT_CHANNELS` parameter on
  `ConvAutoencoder1d`, `train_autoencoder` and `load_autoencoder` (7 lines).
  - The default of 4 is unchanged. Tests show that `ConvAutoencoder1d()` and
    `ConvAutoencoder1d(4)` initialise identically, and that for p = 31 only the first
    `Conv1d` and the last `ConvTranspose1d` change.
  - `tests/test_pipeline.py` passes unchanged (21/21).
  - Because `pipeline.py` is part of the synthetic Phase-II `cache_token`, a future
    synthetic re-run would recompute its git-ignored cache. The committed synthetic results
    are unaffected.
- **`.gitignore`:** the exception `!application/results/models/autoencoder.pt`. Verified with
  `git check-ignore`: this file is tracked, and other `.pt` files stay ignored.
- **`requirements.txt`:** adds `h5py==3.16.0`.

## Artifacts (SHA-256)

| Artifact | SHA-256 |
|---|---|
| `results/models/preprocessing.npz` (mean, scale, selected columns) | `e11634ca78bf1ac2ebf1b64541e6cb444680c851269d6d145b7cb4438bd0ac33` |
| `results/models/autoencoder.pt` (state_dict) | `dceb5500fdbfb82a72af10d8a69863b5f1d762efbde55bd54122697e7b7a1242` |
| `results/models/ocsvm.npz` (incl. gamma, median squared distance) | `53350e59263406cbaabe08e5102f9a859ab83671cbd47091b3eaf761e1d44277` |
| `results/models/mewma.npz` (mu_y, sigma_y, mu_x, sigma_x, m_representation) | `cedacfef2461c239fd28f21ad3107097ae691d60ef1318f90e931171a669a759` |
| `results/models/control_limits.json` | `fb2c08425c59215d644a0f684e25c4d9dcf087169e9e6c3803320178613d4615` |
| `results/phase1/d3_maxima.npz` (R_H, R_M, D3 paths) | `3714f8d91b60deb3ff92cc1b1471e4cd8f685438847259c6144ca67938ffe7ee` |
| `results/phase1/cae_training_history.json` | `89aad62fa6149d21f4c711d4f514c767bf4604c8fa98213fd62e1f8d0198be91` |
| `results/phase1_manifest.json` | `26a8f929c86d68032240471f48e2924d5762b04206a54eef0410b562d2dd34bc` |

**Frozen inputs:**
- Protocol `558ffcb6…490f`; registry `0c03350d…e97c`.
- HDF5 SHA-256 `d6b0ed0e…3294`.
- Base commit `7082c51`. The manifest also records the hashes of `pipeline.py` and
  `tep_pipeline.py` from the working tree.

**Versions:** Python 3.14.4, numpy 2.4.6, torch 2.13.0+cpu, scikit-learn 1.9.0,
scipy 1.18.1, h5py 3.16.0, threadpoolctl 3.6.0.

## Next stage (requires explicit approval)

The next stage is D4: independent in-control validation, run **once** with the artifacts
above. It reports:
- the realised FAP overall, with SE and a Clopper–Pearson 95 % CI;
- the realised FAP for stratum A and stratum B, descriptively only.

There is no recalibration after D4. D5 stays untouched until D4 is frozen and approved.
