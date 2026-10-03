#!/usr/bin/env python3
"""Front end to the repository's validated reproduction routes.

Orchestration only: every scientific step runs in the existing study code
(simulation/reproduce_all.py and pipeline.py, tep-application/application/tep_d5.py,
thesis/scripts/*.py and latexmk). Nothing here fits, calibrates or evaluates a model.

commands:
  verify      fast integrity and reproducibility checks
  simulation  rerun the simulation study from scratch and compare with the published artifacts
  tep         rebuild the published TEP outputs from the committed per-run results
  thesis      compile the thesis PDF
  all         everything reproducible without the external 24 GB TEP dataset

A raw-data rerun of the TEP application is not wrapped: see tep-application/README.md.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SIM = ROOT / "simulation"
TEP = ROOT / "tep-application"
THESIS = ROOT / "thesis"
LATEX = THESIS / "final_report"
PY = sys.executable
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
PASS, FAIL, SKIP = "PASS", "FAIL", "SKIPPED"

# SHA-256 of the published simulation files (validated 2026-10-03), relative to simulation/.
SIM_PUBLISHED = {
    "pipeline.py": "56f28a01e3410ccea7827a6d0ed33b6166b459362bee61d5e7fe9fdd4426a875",
    "models/autoencoder.pt": "53e42cf50bff4f2d021f692a031662dc6e3105f4be7d6a3114c2570a7e1b808d",
    "models/control_limits.json": "a6b259a102be0ae1c08970387cf30a144a61555df82ae05fe3006b605f58e11e",
    "models/mewma.npz": "4edfce9bcd10f1b50f061c1dbd2a480ca0d45b971c49ff5d7cb1fb0121ace3a0",
    "models/ocsvm.npz": "045822682c164aff21df5de04cafafcbe78b2cb3cba7728d9a215a85ecbb6704",
    "models/preprocessing.npz": "ae48e1556504cb5ecbce2e64218c6bf96d7bb53855865c973a5832c81d7c8f43",
    "results/d4_validation_summary.json": "ee1f2195a4bedcec994f9e3da46d4292ebfe5ee4ff8fa1765aeab518ea15c813",
    "results/d5_performance_summary.json": "bad47a939d44ca5f467145e78e7aebbc3beff594ea90b49b977f2b1949eef345",
    "results/run_lengths.npz": "d8f94d77343a6e0638ed8224d56c9d25f661558c41655dd08b61007340bcde22",
}
SIM_OUTPUTS = [p for p in SIM_PUBLISHED if p != "pipeline.py"]

# Section 4.5 evidence (relative to simulation/diagnostics/) and the ranges it records.
DIAG_PUBLISHED = {
    "s01_verification.json": "cce59f5e96abfd10de7d9fc3312e4b000bdc6a286f8e0d2ab147913d97fe1354",
    "s03_geometry.json": "39cf6dd6264436026687b2cb8c9b52f27be4f6008d66fb85ad9a78113a47f80a",
    "s05_counterfactuals.json": "ecca005d158fee10746cfe12114fab13fb1ffc90b3a4fef138ccc77b571700af",
    "s06_late_change.json": "1d96825e205a3161213284801988f9b822f9581a0abc9ee33e0dc9a90a1e6a72",
    "s10_budget.json": "8ba1bc6678dcbf0de7d04f43c739a48647882ddf33e4583e16796b1fae57c433",
}
DIAG_RANGES = {"retained %": (1.65, 36.35), "late-change ratio": (1.996, 2.535), "startup share": (0.52, 0.79)}

TEP_D5 = ["application/results/d5/d5_summary.json", "application/results/d5/d5_primary_table.csv",
          "application/results/figures/tep_d5_median_delay.pdf",
          "application/results/figures/tep_d5_median_delay.png"]
TEP_IMPORT = "import sys; sys.path.insert(0, 'application'); import tep_d5; tep_d5.verify_frozen()"
NO_RAW_TEP = ("Full raw-data TEP experiment not run: external dataset not included.\n"
              "See tep-application/README.md for full application reproduction.")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(cmd, cwd, quiet=False):
    """Run one existing command in its own directory; True on success."""
    where = cwd.relative_to(ROOT) if cwd.is_relative_to(ROOT) else cwd
    print(f"\n$ {' '.join(cmd)}    [in {where}]", flush=True)
    result = subprocess.run(cmd, cwd=cwd, env=ENV, capture_output=quiet, text=True)
    if quiet and result.returncode:
        print((result.stdout + result.stderr)[-3000:])
    return result.returncode == 0


def mismatches(published, base):
    return [p for p, digest in published.items() if not (base / p).is_file() or sha256(base / p) != digest]


# ---------------------------------------------------------------- simulation

def simulation_tests():
    ok = run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"], SIM)
    return (PASS, "simulation/tests/test_pipeline.py") if ok else (FAIL, "pytest failed")


def simulation_artifacts():
    bad = mismatches(SIM_PUBLISHED, SIM)
    return (FAIL, "changed or missing: " + ", ".join(bad)) if bad else \
        (PASS, "pipeline.py, 5 models and 3 results match the published SHA-256")


def simulation_rerun():
    """reproduce_all.py refuses to overwrite data/models/results, so it runs in an empty copy."""
    with tempfile.TemporaryDirectory(prefix="simulation-rerun-") as tmp:
        tmp = Path(tmp)
        for name in ("pipeline.py", "reproduce_all.py"):
            shutil.copy2(SIM / name, tmp / name)
        print(f"\nRerunning the simulation study from scratch in {tmp} (about 3.5 min, ~0.8 GB temporary data).")
        if not run([PY, "reproduce_all.py"], tmp):
            return FAIL, "reproduce_all.py failed"
        bad = mismatches({p: SIM_PUBLISHED[p] for p in SIM_OUTPUTS}, tmp)
    return (FAIL, "differs from published: " + ", ".join(bad)) if bad else \
        (PASS, "from scratch: 5 models and 3 results byte-identical to the published files")


def diagnostics():
    base = SIM / "diagnostics"
    bad = mismatches(DIAG_PUBLISHED, base)
    if bad:
        return FAIL, "changed or missing: " + ", ".join(bad)
    load = lambda name: json.loads((base / name).read_text())
    retained = [100 * r["y"]["I"] / r["x"]["I"] for r in load("s03_geometry.json")["geometry"]]
    late = load("s06_late_change.json")["results"]
    ratio = [h["ced"] / m["ced"] for h, m in zip(late["H(.05)"], late["M(.05)"]) if h["delta"] >= 0.6]
    share = [r["A"] / r["G"] for r in load("s10_budget.json")["budget"] if r["delta"] >= 1.8]
    got = {"retained %": (round(min(retained), 2), round(max(retained), 2)),
           "late-change ratio": (round(min(ratio), 3), round(max(ratio), 3)),
           "startup share": (round(min(share), 2), round(max(share), 2))}
    detail = "; ".join(f"{k} {lo}-{hi}" for k, (lo, hi) in got.items())
    return (PASS, detail) if got == DIAG_RANGES else (FAIL, "recorded ranges differ: " + detail)


# ---------------------------------------------------------------- TEP

def tep_tests():
    ok = run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "application/tests"], TEP)
    return (PASS, "application/tests (the HDF5 test skips without the dataset)") if ok else (FAIL, "pytest failed")


def tep_manifest_mismatches(paths=None):
    published = json.loads((TEP / "application/results/final_manifest.json").read_text())["sha256"]
    return mismatches({p: published[p] for p in (paths or published)}, TEP)


def tep_provenance():
    if not run([PY, "-c", TEP_IMPORT], TEP):
        return FAIL, "tep_d5.verify_frozen() failed"
    bad = tep_manifest_mismatches()
    return (FAIL, "final_manifest.json mismatch: " + ", ".join(bad)) if bad else \
        (PASS, "verify_frozen() and every final_manifest.json hash")


def tep_reconstruct():
    print("\nReconstructing the PUBLISHED TEP outputs (D5 summary, table and figure) from the committed\n"
          "per-run experiment results (application/results/d5/d5_run_results.csv).\n"
          "This is NOT a raw-data rerun: the external 24 GB Extended TEP dataset is not used.")
    if not run([PY, "-c", TEP_IMPORT + "; tep_d5.summarise()"], TEP):
        return FAIL, "tep_d5.summarise() failed"
    bad = tep_manifest_mismatches(TEP_D5)
    return (FAIL, "differs from final_manifest.json (restore with git checkout): " + ", ".join(bad)) if bad else \
        (PASS, "D5 summary, table and figure byte-identical to final_manifest.json")


# ---------------------------------------------------------------- thesis

def thesis_outputs():
    return sorted([*(LATEX / "figures").iterdir(), *(LATEX / "tables").glob("*.tex"),
                   *(THESIS / "planning").glob("derived_*.json")])


def thesis_figures():
    before = {p: sha256(p) for p in thesis_outputs()}
    steps = [([PY, "-c", "import pipeline; pipeline.generate_datasets('data/generated')"], SIM),
             ([PY, "make_all_figures.py"], THESIS / "scripts"),
             ([PY, "make_tep_figure4.py"], THESIS / "scripts")]
    if not all(run(cmd, cwd) for cmd, cwd in steps):
        return FAIL, "a figure script failed"
    changed = [p.name for p in thesis_outputs() if before.get(p) != sha256(p)]
    return (FAIL, "changed (restore with git checkout): " + ", ".join(changed)) if changed else \
        (PASS, f"{len(before)} figure, table and derived-number files byte-identical")


def thesis_build():
    missing = [t for t in ("latexmk", "pdflatex", "bibtex") if shutil.which(t) is None]
    if missing:
        return SKIP, "optional LaTeX toolchain not found: " + ", ".join(missing)
    if not run(["latexmk", "-g"], LATEX, quiet=True):
        return FAIL, "latexmk failed (see thesis/final_report/build/main.log)"
    log = (LATEX / "build" / "main.log").read_text(errors="replace")
    match = re.search(r"Output written on \S+ \((\d+) pages", log)
    pages = int(match.group(1)) if match else 0
    built, public = LATEX / "main.pdf", THESIS / "main.pdf"
    if pages != 28:
        return FAIL, f"{pages} pages, expected 28"
    if sha256(built) == sha256(public):
        return PASS, "28 pages, byte-identical to thesis/main.pdf (dated 2 October 2026)"
    if shutil.which("pdftotext") is None:
        return SKIP, "built 28 pages; not byte-identical and pdftotext is unavailable to compare content"
    text = lambda pdf: subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True).stdout
    if text(built) == text(public) and b"2 October 2026" in text(built):
        return PASS, "28 pages, same text as thesis/main.pdf (bytes differ: different TeX toolchain)"
    return FAIL, "content differs from thesis/main.pdf"


# ---------------------------------------------------------------- commands

def checked(name, step):
    try:
        return (name, *step())
    except Exception as error:  # report, do not hide, unexpected failures
        return name, FAIL, f"{type(error).__name__}: {error}"


VERIFY_STEPS = [("Simulation tests", simulation_tests),
                ("Simulation artifacts", simulation_artifacts),
                ("Section 4.5 diagnostics", diagnostics),
                ("TEP tests", tep_tests),
                ("TEP provenance", tep_provenance),
                ("Thesis", thesis_build)]


def verify():
    return [checked(name, step) for name, step in VERIFY_STEPS]


def reproduce_all():
    results = [checked("Simulation (from scratch)", simulation_rerun),
               checked("Section 4.5 diagnostics", diagnostics),
               checked("TEP published outputs", tep_reconstruct),
               checked("Thesis figures and tables", thesis_figures),
               checked("Thesis", thesis_build)]
    done = {name for name, _, _ in results}
    results += [checked(name, step) for name, step in VERIFY_STEPS if name not in done]
    print("\n" + NO_RAW_TEP)
    print("Generated simulation banks are kept in simulation/data/ (git-ignored, ~0.8 GB); delete them when done.")
    return results


COMMANDS = {
    "verify": verify,
    "simulation": lambda: [checked("Simulation (from scratch)", simulation_rerun)],
    "tep": lambda: [checked("TEP published outputs", tep_reconstruct)],
    "thesis": lambda: [checked("Thesis", thesis_build)],
    "all": reproduce_all,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=COMMANDS)
    results = COMMANDS[parser.parse_args().command]()
    print("\n" + "-" * 78)
    for name, status, detail in results:
        print(f"{name:28s} {status:8s} {detail}")
    sys.exit(1 if any(status == FAIL for _, status, _ in results) else 0)


if __name__ == "__main__":
    main()
