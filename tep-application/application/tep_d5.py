"""Extended TEP external benchmark: final D5 evaluation (IDV(2), 25/50/75/100 %).

``evaluate()`` is the only function that reads D5 process values. It applies the frozen
Phase-I artifacts unchanged and writes compact per-run results. ``summarise()`` rebuilds
every summary, the primary table and the primary figure from that CSV alone.

Run: ``python application/tep_d5.py`` (both), or ``python application/tep_d5.py summarise``.
"""

import csv
import json
import sys
import time

import h5py
import numpy as np

import tep_d4
import tep_pipeline as T

P = T.P
D5_ROLES = ("D5",)
D4_MANIFEST_SHA256 = "2c2e6377c1a79b028a4e00ff9c0ae7c1a01a5a9e3d7563aaeebcaa6a29b07316"
D5_DIR = T.APP / "results" / "d5"
FIGURES_DIR = T.APP / "results" / "figures"
RUN_RESULTS = D5_DIR / "d5_run_results.csv"
D5_ROWS, D5_DECISIONS, J_TAU, J1 = 2000, 1969, 569, 1401
SEVERITIES = {25: 100, 50: 100, 75: 100, 100: 200}
CHARTS = ("H", "M")


def verify_frozen():
    """Gate 2, Phase-I and D4 provenance must be intact before D5 access."""
    manifest = tep_d4.verify_phase1()
    assert T.sha256_file(tep_d4.D4_DIR / "d4_manifest.json") == D4_MANIFEST_SHA256, "D4 manifest changed"
    d4 = json.loads((tep_d4.D4_DIR / "d4_manifest.json").read_text())
    for name, digest in d4["artifacts_sha256"].items():
        assert T.sha256_file(T.APP / "results" / name) == digest, name
    return manifest


def load_full_runs(runs, columns, protocol, allowed_roles=D5_ROLES):
    """Aligned rows 1..2000 (t = 0.05 ... 100.00 h) of the selected columns."""
    assert all(r["role"] in allowed_roles for r in runs), "role not permitted in this stage"
    bank = np.empty((len(runs), D5_ROWS, len(columns)), dtype=np.float64)
    with h5py.File(T.H5_PATH, "r") as handle:
        grid = T.reference_grid(handle, protocol)
        assert grid.size == D5_ROWS and grid[T.PREFIX_ROWS] == 30.0   # row 600 <-> t = 30.00
        for index, run in enumerate(runs):
            assert run["status"] == "completed" and run["n_rows_aligned"] == str(D5_ROWS)
            dataset = handle[run["path"]]["processdata"]
            offset = 1 if run["dropped_t0"] == "true" else 0
            assert dataset.shape[0] == D5_ROWS + offset
            assert np.array_equal(dataset[offset:, 0], grid), run["path"]
            bank[index] = dataset[offset:, columns]
    assert np.all(np.isfinite(bank))
    return bank


def onset_quantities(t2, h):
    """Pre-onset alarm, first pre-onset j, and conditional delay D (strict T2 > h)."""
    assert t2.shape[1] == D5_DECISIONS
    pre = t2[:, : T.J0] > h
    post = t2[:, T.J0:] > h
    assert post.shape[1] == J1
    pre_alarm = pre.any(axis=1)
    first_pre_j = np.where(pre_alarm, pre.argmax(axis=1) + 1, 0)
    detected = post.any(axis=1)
    delay = np.where(detected, post.argmax(axis=1) + 1, J1)
    return pre_alarm, first_pre_j, delay, ~detected


def evaluate():
    started = time.perf_counter()
    manifest = verify_frozen()
    protocol, registry = T.load_protocol(), T.load_registry()
    columns = T.selected_columns(protocol)
    p = len(columns)
    assert columns == manifest["selected_processdata_col0"]
    g = protocol["grid_and_onset"]
    assert (g["j_tau"], g["J0_pre_onset_decisions"], g["J1_post_onset_decisions"]) == (J_TAU, T.J0, J1)

    mean, scale = P.load_preprocessing(T.MODELS_DIR / "preprocessing.npz")
    frozen = P.Frozen(mean, scale, P.load_autoencoder(T.MODELS_DIR / "autoencoder.pt", input_channels=p),
                      P.load_ocsvm(T.MODELS_DIR / "ocsvm.npz"))
    hybrid, benchmark = P.load_moments(T.MODELS_DIR / "mewma.npz")
    with np.load(T.MODELS_DIR / "mewma.npz") as archive:
        assert str(archive["m_representation"]) == "d1_standardised_fallback"
    limits = {e["chart_id"]: e["h_star"] for e in json.loads((T.MODELS_DIR / "control_limits.json").read_text())}
    assert limits["H"] == manifest["results"]["d3"]["h_H"] and limits["M"] == manifest["results"]["d3"]["h_M"]

    runs = T.role_runs(registry, "D5")
    assert len(runs) == 500 and all(r["idv"] == "2" for r in runs)
    assert {m: sum(r["magnitude"] == str(m) for r in runs) for m in SEVERITIES} == SEVERITIES
    bank = load_full_runs(runs, columns, protocol)

    y = np.ascontiguousarray(P.monitoring_bank(frozen, bank))
    assert y.shape == (500, D5_DECISIONS, 2)
    t2 = {"H": P.mewma_t2(y, hybrid.mean, hybrid.covariance, T.LAMBDA)}
    x_m = np.ascontiguousarray(P.apply_preprocessing(P.benchmark_bank(bank), mean, scale))
    run_in = np.ascontiguousarray(P.apply_preprocessing(P.benchmark_run_in(bank), mean, scale))
    del bank, y
    assert x_m.shape == (500, D5_DECISIONS, p) and run_in.shape == (500, P.WINDOW_LENGTH - 1, p)
    t2["M"] = P.mewma_t2(x_m, benchmark.mean, benchmark.covariance, T.LAMBDA, run_in, T.M_FIRST_UPDATE_INDEX)
    per_chart = {c: onset_quantities(t2[c], limits[c]) for c in CHARTS}

    D5_DIR.mkdir(parents=True, exist_ok=True)
    fields = ["path", "severity", "run", "seed", "stratum"]
    for c in CHARTS:
        fields += [f"{c}_pre_alarm", f"{c}_first_pre_j", f"{c}_eligible", f"{c}_D", f"{c}_censored"]
    fields.append("paired_eligible")
    with RUN_RESULTS.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(fields)
        for i, r in enumerate(runs):
            row = [r["path"], r["magnitude"], r["run"], r["seed"], r["stratum"]]
            for c in CHARTS:
                pre_alarm, first_j, delay, censored = (a[i] for a in per_chart[c])
                eligible = not pre_alarm
                row += [int(pre_alarm), int(first_j) if pre_alarm else "", int(eligible),
                        int(delay) if eligible else "", int(censored) if eligible else ""]
            row.append(int(not per_chart["H"][0][i] and not per_chart["M"][0][i]))
            writer.writerow(row)

    P.write_json(D5_DIR / "d5_manifest.json", {
        "stage": "D5 final evaluation (frozen artifacts; no fitting, no calibration)",
        "protocol_sha256": T.PROTOCOL_SHA256, "registry_sha256": T.REGISTRY_SHA256,
        "phase1_manifest_sha256": tep_d4.PHASE1_MANIFEST_SHA256, "d4_manifest_sha256": D4_MANIFEST_SHA256,
        "code": {"git": T.git_state(), "tep_d5.py_sha256": T.sha256_file(__file__)},
        "frozen_limits": limits, "m_representation": "d1_standardised_fallback",
        "runs_evaluated": {str(m): n for m, n in SEVERITIES.items()},
        "rows_per_run": D5_ROWS, "decisions_per_run": D5_DECISIONS, "J0": T.J0, "j_tau": J_TAU, "J1": J1,
        "run_results_sha256": T.sha256_file(RUN_RESULTS),
        "versions": T.versions(),
    })
    return round(time.perf_counter() - started, 1)


# ---------------------------------------------------------------- summaries (CSV only)

def delay_cell(delay, censored):
    n = delay.size
    values = delay.astype(np.float64)
    censor_count = int(censored.sum())
    sd = float(values.std(ddof=1)) if n > 1 else 0.0
    identified = censor_count < n / 2            # >= 50 % censored: median not identified
    median = float(np.median(values)) if identified else None
    return {
        "n_eligible": n,
        "median_D": median,
        "median_hours": None if median is None else 0.05 * (median - 1.0),
        "median_note": None if identified else f"> {J1} (not identified)",
        "restricted_mean_D": float(values.mean()),
        "sd_D": sd, "se_D": sd / np.sqrt(n),
        "censor_count": censor_count, "censor_fraction": censor_count / n,
        "truncation_limited": censor_count / n > P.TRUNCATION_FRACTION_THRESHOLD,
    }


def read_run_results():
    with RUN_RESULTS.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 500 and len({r["path"] for r in rows}) == 500
    return rows


def summarise():
    rows = read_run_results()
    col = lambda sel, key: np.array([int(r[key]) for r in sel])
    summary = {"definitions": {
        "delay": "onset-referenced conditional detection delay D (not ARL1); D = 1 <=> signal at t = 30.00 h",
        "hours": "Delta = 0.05 * (D - 1)", "censoring": f"no signal in j = 569..1969 -> D = {J1}, censored",
        "restricted_mean": f"mean of min(D, {J1}) over chart-specific eligible runs",
        "paired": "d = D_H - D_M on runs with no pre-onset alarm in H or M; positive = H slower",
    }, "severities": {}, "pooled_pre_onset": {}}
    for chart in CHARTS:
        summary["pooled_pre_onset"][chart] = tep_d4.proportion(int(col(rows, f"{chart}_pre_alarm").sum()), 500)
    for severity, n in SEVERITIES.items():
        sel = [r for r in rows if r["severity"] == str(severity)]
        assert len(sel) == n
        cell = {"n": n}
        for chart in CHARTS:
            eligible = [r for r in sel if r[f"{chart}_eligible"] == "1"]
            cell[chart] = {
                "pre_onset": tep_d4.proportion(int(col(sel, f"{chart}_pre_alarm").sum()), n),
                **delay_cell(col(eligible, f"{chart}_D"), col(eligible, f"{chart}_censored").astype(bool)),
            }
        paired = [r for r in sel if r["paired_eligible"] == "1"]
        contrast = P.paired_contrast(col(paired, "H_D"), col(paired, "M_D"))
        cell["paired"] = {
            "n_E_H": cell["H"]["n_eligible"], "n_E_M": cell["M"]["n_eligible"], "n_E_HM": len(paired),
            "mean_difference_H_minus_M": contrast["mean_difference"], "se_paired": contrast["se_paired"],
            "pairs_with_censoring": int(sum(r["H_censored"] == "1" or r["M_censored"] == "1" for r in paired)),
        }
        summary["severities"][str(severity)] = cell
    P.write_json(D5_DIR / "d5_summary.json", summary)
    write_table(summary)
    write_figure(summary)
    return summary


def fmt_median(cell):
    text = cell["median_note"] or f"{cell['median_D']:g}"
    return text + ("†" if cell["truncation_limited"] else "")


def write_table(summary):
    header = ["Severity", "n", "Pre-FAP H", "Pre-FAP M", "Eligible H", "Eligible M",
              "Median D H", "Median D M", "Restricted mean D H", "Restricted mean D M",
              "Paired n", "Mean paired H-M (SE)"]
    with (D5_DIR / "d5_primary_table.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(header)
        for severity, cell in summary["severities"].items():
            h, m, pair = cell["H"], cell["M"], cell["paired"]
            writer.writerow([
                f"{severity}%", cell["n"], f"{h['pre_onset']['fap']:.3f}", f"{m['pre_onset']['fap']:.3f}",
                h["n_eligible"], m["n_eligible"], fmt_median(h), fmt_median(m),
                f"{h['restricted_mean_D']:.1f}", f"{m['restricted_mean_D']:.1f}", pair["n_E_HM"],
                f"{pair['mean_difference_H_minus_M']:.1f} ({pair['se_paired']:.1f})",
            ])


def write_figure(summary):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    severities = list(summary["severities"])
    x = np.arange(len(severities))
    fig, ax = plt.subplots(figsize=(8, 5))
    for chart, label, marker in (("H", "H(0.05) hybrid", "o"), ("M", "M(0.05) raw-data MEWMA", "s")):
        cells = [summary["severities"][s][chart] for s in severities]
        med = np.array([np.nan if c["median_D"] is None else c["median_D"] for c in cells])
        line, = ax.plot(x, med, marker=marker, label=label)
        missing = np.isnan(med)
        if missing.any():   # median not identified: plot at the horizon as an open marker
            ax.plot(x[missing], np.full(missing.sum(), J1), marker=marker, linestyle="none",
                    markerfacecolor="none", color=line.get_color())
    ax.axhline(32, linestyle=":", color="grey", linewidth=1)
    ax.annotate("D = 32: first fully post-change H window", (x[-1], 32), textcoords="offset points",
                xytext=(0, 4), ha="right", fontsize=8, color="grey")
    ax.set_ylim(bottom=0)
    ax.set_xticks(x, [f"{s}%" for s in severities])
    ax.set_xlabel("IDV(2) fault severity")
    ax.set_ylabel("Median conditional detection delay D\n(monitoring decisions, 3 min each)")
    ax.set_title("Extended TEP, IDV(2): onset-referenced conditional detection delay")
    ax.legend()
    fig.tight_layout()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_DIR / "tep_d5_median_delay.pdf", metadata={"CreationDate": None})
    fig.savefig(FIGURES_DIR / "tep_d5_median_delay.png", dpi=300)
    plt.close(fig)


def write_final_manifest():
    outputs = {
        "application/tep_protocol.json": T.PROTOCOL_PATH,
        "application/tep_run_registry.csv": T.REGISTRY_PATH,
        "application/results/phase1_manifest.json": T.MANIFEST_PATH,
        "application/results/d4/d4_manifest.json": tep_d4.D4_DIR / "d4_manifest.json",
        "application/results/d5/d5_manifest.json": D5_DIR / "d5_manifest.json",
        "application/results/d5/d5_run_results.csv": RUN_RESULTS,
        "application/results/d5/d5_summary.json": D5_DIR / "d5_summary.json",
        "application/results/d5/d5_primary_table.csv": D5_DIR / "d5_primary_table.csv",
        "application/results/figures/tep_d5_median_delay.pdf": FIGURES_DIR / "tep_d5_median_delay.pdf",
        "application/results/figures/tep_d5_median_delay.png": FIGURES_DIR / "tep_d5_median_delay.png",
    }
    P.write_json(T.APP / "results" / "final_manifest.json", {
        "stage": "Extended TEP external benchmark - final provenance",
        "hdf5_sha256": json.loads(T.PROTOCOL_PATH.read_text())["source_data"]["sha256_local"],
        "code": {"git": T.git_state(),
                 **{f"{name}_sha256": T.sha256_file(T.APP / name)
                    for name in ("tep_pipeline.py", "tep_d4.py", "tep_d5.py")},
                 "pipeline.py_sha256": T.sha256_file(T.ROOT / "pipeline.py")},
        "sha256": {name: T.sha256_file(path) for name, path in outputs.items()},
    })


if __name__ == "__main__":
    if sys.argv[1:] != ["summarise"]:
        print("D5_EVALUATION_S", evaluate())
    print(json.dumps(summarise(), indent=1))
    write_final_manifest()
