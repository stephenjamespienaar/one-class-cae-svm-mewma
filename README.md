# One-Class CAE–OC-SVM–MEWMA Monitoring Scheme

Research repository for the STK 795 BCom(Hons) Statistics and Data Science research report
**"One-class hybrid SVM-CAE based MEWMA monitoring scheme"** (Stephen Pienaar, Department of
Statistics, University of Pretoria, 2 October 2026).

The report develops and evaluates a hybrid monitoring scheme for nonlinear, serially dependent
multivariate processes. It combines a one-dimensional convolutional autoencoder (CAE), a one-class
support vector machine (OC-SVM) and a multivariate exponentially weighted moving average (MEWMA)
control chart. The scheme is studied on a simulated nonlinear process and then applied to
simulated Extended Tennessee Eastman Process (TEP) data.

## Repository contents

- [`thesis/`](thesis/) — final manuscript (`main.pdf`), its LaTeX source, and the scripts that
  regenerate its figures and tables
- [`simulation/`](simulation/) — the simulation study: implementation, frozen models, results,
  tests and the Section 4.5 diagnostic evidence
- [`tep-application/`](tep-application/) — the Extended TEP application
- [`reproduce.py`](reproduce.py) — thin front end to the validated reproduction routes

## Reproducing the results

Install the pinned environment. Python 3.14.4 was used for all results, and everything runs on CPU.

```bash
python3.14 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

| Command | What it does | Time |
|---|---|---|
| `python reproduce.py verify` | Quick verification: both test suites, published-artifact hashes, the TEP frozen hash chain, the Section 4.5 evidence, and a thesis rebuild | ~10 s |
| `python reproduce.py simulation` | Reproduces the simulation study from scratch and checks that all models and results are byte-identical | ~4 min |
| `python reproduce.py tep` | Rebuilds the published TEP outputs (D5 summary, table, figure) from the committed per-run results | seconds |
| `python reproduce.py thesis` | Compiles the thesis (28 pages, dated 2 October 2026), byte-identical to `thesis/main.pdf` | ~10 s |
| `python reproduce.py all` | Reproduces all outputs available from the public repository, without the external TEP dataset | ~5 min |

Each command prints a PASS/FAIL summary and exits non-zero on a genuine failure. The thesis steps
need pdfLaTeX, BibTeX and latexmk. Without them, those steps report SKIPPED instead of failing.

A **raw-data rerun of the TEP application is deliberately not wrapped**. It needs the external
24 GB dataset. The frozen protocol was run once, and its Phase I manifest records the Git state,
so a rerun cannot pass the published hash chain. See
[`tep-application/README.md`](tep-application/README.md).

The CPU-only PyTorch build (`torch 2.13.0+cpu`, used for the TEP results) can be installed from
`https://download.pytorch.org/whl/cpu` before the other requirements. The standard
`torch==2.13.0` wheel also reproduces the simulation bit-for-bit.

## Method overview

For every window of 32 observations:

```text
window of x_t ─► CAE ─► latent code h_t ─► OC-SVM ─► anomaly score s_t ───────┐
                  └───► reconstruction error SPE_t ─► ℓ_t = log SPE_t ─────────┴► y_t = [s_t, ℓ_t] ─► MEWMA T² ─► signal when T² > h
```

The CAE supplies reconstruction information and the OC-SVM supplies one-class anomaly
information. The MEWMA accumulates the two-dimensional monitoring vector over time. The
primary hybrid chart is H(0.05). It is compared with H(0.10) and H(0.20) (smoothing
sensitivity), with S(0.05) and R(0.05) (ablations using only s_t or only ℓ_t), and with the
classical MEWMA M(0.05) on the raw variables.

**Main findings.** In the simulation, H(0.05) has a shorter out-of-control ARL than both of its
single-component ablations at every shift. It does not outperform the classical MEWMA: the two
are indistinguishable at the smallest shift, and M(0.05) detects faster at every shift of 0.4 or
more. On the Extended TEP data (fault IDV(2)), the classical MEWMA again detected sooner at every
severity, by 4.8 to 10.1 monitoring decisions on average.

## Simulation study

See [`simulation/README.md`](simulation/README.md). It covers the frozen pipeline, the
from-scratch rerun, verification against the committed results, and the diagnostic evidence for
Section 4.5.

## TEP application

See [`tep-application/README.md`](tep-application/README.md). It covers the dataset, the frozen
protocol, the hash-checked provenance chain, and how to verify the published TEP table and figure
without the 24 GB dataset.

## Thesis

[`thesis/main.pdf`](thesis/main.pdf) is the final report, dated 2 October 2026 (28 pages). The
public manuscript corresponds to the submitted thesis, with the handwritten signature/initials and
student number omitted from the public copy. See [`thesis/README.md`](thesis/README.md) to rebuild
the PDF or regenerate its figures and tables.

## Reproducibility

- **Deterministic CPU execution.** `pipeline.py` fixes all seeds: 795 for the data, with
  independent PCG64DXSM streams, and 3795 for CAE training. It runs PyTorch on one CPU thread
  with deterministic algorithms and limits native thread pools to one thread. Numerical work is
  in float64; only the network runs in float32.
- **Checked for this release (2026-10-03):**
  - the from-scratch simulation run reproduces every committed model and result file
    byte-for-byte;
  - the TEP frozen hash chain verifies, and the published TEP summary, table and figure rebuild
    byte-identically;
  - the thesis figure scripts reproduce every figure and table byte-for-byte;
  - the thesis PDF rebuilds byte-identically (`latexmkrc` fixes the build timestamp).
- Identity is claimed relative to the pinned environment (`requirements.txt`), not across every
  platform.
- **Two `pipeline.py` files, on purpose.** `simulation/pipeline.py` and
  `tep-application/pipeline.py` are kept as separately validated copies:
  - The TEP copy adds only an optional `input_channels` argument (default 4) so the CAE can take
    the 31 TEP variables.
  - Running the simulation with the TEP copy reproduces it bit-for-bit.
  - The simulation's provenance records hash the original simulation file (SHA-256
    `56f28a01…`).
  - The TEP D4/D5 scripts refuse to run unless `tep-application/pipeline.py` has its frozen hash
    (`abd1b36c…`).
  - Keeping both is deliberate provenance, not accidental duplication. Do not merge them.

## Provenance

This is a clean research release. The original repositories keep the full development history.

| Folder | Source repository | Branch | Commit |
|---|---|---|---|
| `thesis/` | `pipeline-thesis-write` | `main` | `0c988f986f3c1d9f5d60cf03c835deb49c21f05e` |
| `simulation/` | `pipeline-thesis-independent` | `simplify-pipeline-code` | `e62bdeed620fca38350fe8e0021ee70ea7a0fad9` |
| `simulation/diagnostics/` | `pipeline-thesis-diagnostic` (not under Git) | — | audit of simulation commit `1993315d…`, whose pipeline, models and results equal `e62bdee` |
| `tep-application/` | `pipeline-thesis-tep` | `tep-application` | `0a121fa4adb4ef770c1d5821455103e31149d70a` |

Appendices D and E of the thesis cite these repositories and commits. Where they mention the
original workspace paths, `pipeline-thesis-independent` corresponds to `simulation/`, and
`pipeline-thesis-tep` (read through `08_tep_application/source`) corresponds to
`tep-application/`. `scripts/` and `planning/` correspond to `thesis/scripts/` and
`thesis/planning/`.

## Data

- **Simulation data** is not stored. It is regenerated deterministically from the seed (761 MB;
  see `simulation/README.md`).
- **The Extended TEP dataset** (`TEP_Mode1.h5`, 23.9 GB) is not distributed by this repository
  and is excluded from Git because of its size.
  [`tep-application/README.md`](tep-application/README.md) gives its source and checksums and
  where to place it.

## Licence

- The project code is released under the [MIT License](LICENSE).
- The thesis manuscript (`thesis/`) is the author's academic work. The software licence does not
  automatically relicense it.
- Third-party datasets and material keep their own terms. The Extended TEP dataset is not
  distributed by this repository; its source and licence are listed in
  [`tep-application/README.md`](tep-application/README.md).
