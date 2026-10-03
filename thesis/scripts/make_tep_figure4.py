"""Body Figure 4 (Extended TEP, IDV(2) median delay) without its in-plot title.

Presentation-only redraw requested by the supervisor. The plotting code is write_figure() of the
frozen TEP repository (pipeline-thesis-tep, commit 0a121fa, application/tep_d5.py), copied
verbatim; it reads the frozen application/results/d5/d5_summary.json read-only, and the only
change is that ax.set_title(...) is skipped. Before writing anything, the copy is run with the
title and checked byte-for-byte against the frozen PDF, so the untitled figure differs from the
frozen one only by the title. Run from thesis/scripts/ in the repository's pinned environment
(requirements.txt), without writing bytecode:

  PYTHONDONTWRITEBYTECODE=1 python make_tep_figure4.py
"""

import csv
import hashlib
import json
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
TEP = (ROOT.parent / "tep-application" / "application" / "results").resolve()
FROZEN_PDF = TEP / "figures" / "tep_d5_median_delay.pdf"
OUT = ROOT / "final_report" / "figures" / "tep_d5_median_delay.pdf"
SEVERITIES = ("25", "50", "75", "100")  # order of SEVERITIES in tep_d5.py, as in the frozen run
J1 = 1401  # tep_d5.J1; only used if a median were unidentified (none is)


def draw(summary, path, title):
    """tep_d5.write_figure() verbatim, writing the PDF only; title=False skips ax.set_title."""
    severities = list(SEVERITIES)
    x = np.arange(len(severities))
    fig, ax = plt.subplots(figsize=(8, 5))
    plotted = {}
    for chart, label, marker in (("H", "H(0.05) hybrid", "o"), ("M", "M(0.05) raw-data MEWMA", "s")):
        cells = [summary["severities"][s][chart] for s in severities]
        med = np.array([np.nan if c["median_D"] is None else c["median_D"] for c in cells])
        line, = ax.plot(x, med, marker=marker, label=label)
        plotted[chart] = line.get_ydata().tolist()
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
    if title:
        ax.set_title("Extended TEP, IDV(2): onset-referenced conditional detection delay")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, metadata={"CreationDate": None})
    plt.close(fig)
    return plotted


def main():
    summary = json.loads((TEP / "d5" / "d5_summary.json").read_text())
    with open(TEP / "d5" / "d5_primary_table.csv", newline="") as f:
        table = {r["Severity"]: r for r in csv.DictReader(f)}
    expected = {c: [float(table[f"{s}%"][f"Median D {c}"]) for s in SEVERITIES] for c in ("H", "M")}

    with tempfile.TemporaryDirectory() as tmp:
        check = Path(tmp) / "with_title.pdf"
        assert draw(summary, check, title=True) == expected
        sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        assert sha(check) == sha(FROZEN_PDF), "copied write_figure() no longer reproduces the frozen figure"
    assert draw(summary, OUT, title=False) == expected
    print(f"frozen figure reproduced byte-for-byte; wrote {OUT.relative_to(ROOT)} without the title")
    print(f"plotted medians H={expected['H']} M={expected['M']} (severities {', '.join(SEVERITIES)}%)")


if __name__ == "__main__":
    main()
