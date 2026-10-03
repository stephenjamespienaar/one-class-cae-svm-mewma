# Extended TEP application

The frozen CAE–OC-SVM–MEWMA design applied to the **Extended Tennessee Eastman Process** dataset
(operating mode 1, feed-composition fault IDV(2)). This is thesis **Section 5** and **Appendix E**.
The TEP data are simulated, not measured plant data.

## Layout

| Path | What it is |
|---|---|
| `pipeline.py` | The TEP copy of the method (SHA-256 `abd1b36c…`). It adds only an optional `input_channels` argument so the CAE takes the 31 monitored variables. **Do not edit or replace it:** the scripts check its hash. |
| `application/tep_pipeline.py` | Data access and Phase I: TEP-D1 CAE, TEP-D2 OC-SVM, TEP-D3 moments and false-alarm-probability limits |
| `application/tep_d4.py` | One-shot in-control validation on TEP-D4 |
| `application/tep_d5.py` | Final IDV(2) evaluation at 25/50/75/100 % severity, summaries, table, figure, final manifest |
| `application/tep_protocol.json`, `application/tep_run_registry.csv` | Frozen protocol and run-to-role allocation (hash-checked at load) |
| `application/results/` | Frozen TEP models, Phase I, D4 and D5 outputs, the figure, and hash-chained manifests |
| `application/tests/` | 12 tests |
| `application/*.md` | Gated-workflow records, in order: `DESIGN_FREEZE`, `TEP_AUDIT`, `GATE1_METADATA_REPORT`, `GATE2_PROTOCOL_FREEZE`, `PHASE1_FREEZE`, `D4_VALIDATION`, `D5_EVALUATION`. They are kept verbatim; their "pending review" status lines predate the final commit. |

`application/` imports `../pipeline.py` and checks its hash, so keep the two side by side.

## Dataset (not included)

The dataset is **deliberately excluded from Git** because of its size.

| Item | Value |
|---|---|
| Dataset | Reinartz, Kulahci & Ravn, *Tennessee Eastman Reference Data for Fault-Detection and Decision Support Systems*, DTU Data, DOI [10.11583/DTU.13385936.v1](https://doi.org/10.11583/DTU.13385936.v1), published 2021-03-12, licence **CC0** |
| File | `TEP_Mode1.h5` (Figshare/DTU file ID 26003087), source URL `https://ndownloader.figshare.com/files/26003087` |
| Size | 23,924,710,848 bytes |
| MD5 | `c79ecc6d12a5ccb49caffcd8f531feae` (matches the official Figshare value) |
| SHA-256 | `d6b0ed0ef3974ff571afd6717ba0418a5b8eb58a7822c84a05735572d52b3294` |
| Expected location | `tep-application/application/data/raw/TEP_Mode1.h5` (ignored by Git) |

The code opens the file read-only with `h5py` at that fixed path: `H5_PATH` in
`application/tep_pipeline.py`, also recorded as `source_data.file` in the protocol. Runs are read
from the run groups listed in the `path` column of `application/tep_run_registry.csv`, all under
`Mode1/SingleFault/SimulationCompleted/…` or `Mode1/SingleFault/SimulationStopped/…`. Each run
group holds a `processdata` table. `application/GATE1_METADATA_REPORT.md` documents the verified
file structure.

The download server throttled each connection to about 0.3 MB/s. The original copy was fetched as
12 parallel byte-range segments and then checked against the MD5 above (see `GATE1_METADATA_REPORT.md` §1).

## Verify without the dataset

From the repository root, `python reproduce.py tep` runs this reconstruction and checks the
results against `final_manifest.json`.

```bash
cd tep-application
python -m pytest application/tests     # 11 passed, 1 skipped (12 passed with the dataset in place)
python -c "import sys; sys.path.insert(0, 'application'); import tep_d5; tep_d5.verify_frozen(); tep_d5.summarise()"
git status --short .                   # no output
```

- `verify_frozen()` checks the hashes of `pipeline.py`, `tep_pipeline.py`, the protocol, the
  registry, and the Phase I and D4 manifests and artifacts.
- `summarise()` rebuilds `d5_summary.json`, `d5_primary_table.csv` and
  `tep_d5_median_delay.{pdf,png}` from the committed per-run results (`d5_run_results.csv`). The
  output is byte-identical to the frozen files.
- Do **not** use `python application/tep_d5.py summarise` for this. Its command-line entry point
  also rewrites `final_manifest.json` with the current Git state.

## Full rerun (requires the dataset)

The protocol was run once, in order:
1. `python application/tep_pipeline.py` (Phase I);
2. `python application/tep_d4.py`;
3. `python application/tep_d5.py`.

These commands overwrite the frozen outputs. Phase I also writes the Git state into
`phase1_manifest.json`, after which `tep_d4.py`'s frozen-manifest check deliberately fails. Rerun
in a scratch copy and compare with the committed results.

## How to read the results

- The simulation calibrates to ARL0 = 370. TEP instead calibrates both charts to a 5 % probability
  of at least one false alarm over the 568-decision nominal prefix.
- TEP reports the **onset-referenced conditional detection delay** D, not ARL1. One decision is
  3 minutes, and elapsed hours = 0.05·(D − 1).
- A run is eligible only if it has no pre-onset alarm. Paired comparisons need eligibility in
  both charts. A positive H − M means the hybrid detected later.
- No eligible D5 delay was censored. The delay denominators are the eligible runs, not all 500.
- Architecture and Phase I artifacts were frozen before D4/D5. There are no TEP ablations.
- The thesis's Table 2 comes from `results/d5/d5_primary_table.csv` and `d5_summary.json`.
  Figure 4 is redrawn without its title from `d5_summary.json` by
  `thesis/scripts/make_tep_figure4.py`.
