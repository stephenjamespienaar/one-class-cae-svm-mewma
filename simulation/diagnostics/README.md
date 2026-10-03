# Section 4.5 diagnostic evidence

These files support three numbers in thesis **Section 4.5 (Interpretation)**. That sentence
attributes them to "a separate diagnostic audit":

> … a separate diagnostic audit estimated that **y_t retains 2–36 % of the raw data's mean-shift
> information per update**, that **startup mechanics account for most of the gap in monitoring
> opportunities at δ ≥ 1.8**, and that **with the change after 100 IC reports H(0.05) still needed
> 2.0–2.5 times as many post-change observations as M(0.05) for δ ≥ 0.6**.

The audit was a post-hoc analysis of the frozen experiment. It is **not part of the production
pipeline** and does not change any canonical result. The files are kept here only so the
published numbers can be traced. (The "0.10–0.21 IC standard deviations" in the same sentence
comes from the thesis scripts instead: `thesis/planning/derived_diagnostics.json`.)

## Files

The JSON files are unchanged copies of the audit's outputs. `MANIFEST.md` is unchanged except
that its two machine-specific paths now read `<original-workspace>/…`. The audit workspace was
not under Git.

| File | Role |
|---|---|
| `MANIFEST.md` | The audit's own record: source commit, environment, seeds, script order |
| `s01_verification.json` | Shows the audit's inputs were bitwise canonical: regenerated D1–D5 banks, moments, all six limits, and 96/96 run-length cells matched |
| `s03_geometry.json` | Information rates (claim 1) |
| `s05_counterfactuals.json` | Calibration of the dependence-corrected counterfactual chart H-V used in claim 2 |
| `s10_budget.json` | Paired delay budget (claim 2) |
| `s06_late_change.json` | Change-during-monitoring counterfactual (claim 3) |

The audit ran against simulation commit `1993315`. Its source-tree hashes for `pipeline.py`,
`models/`, `results/` and the regenerated data banks equal the files in this repository (commit
`e62bdee`).

## How the reported ranges were obtained

1. **Information retained, 1.65–36.35 % (thesis: 2–36 %).** `s03_geometry.json` → `geometry[i]`,
   one entry per δ. For each representation u:
   - Δ_u is the D5 mean shift of u;
   - Ω_u is its long-run covariance, from batch means over the 800 D3+D4 replications;
   - I_u = Δ_uᵀ Ω_u⁻¹ Δ_u.

   Retained = 100 · `y.I` / `x.I`. It rises from 1.65 % (δ = 0.2) to 36.35 % (δ = 3.0).
2. **Startup share of the gap, 52–79 % for δ ≥ 1.8.** `s10_budget.json` → `budget[i]`.
   - G = ARL_H − ARL_M is the canonical paired gap. It equals the paired mean of
     `../results/run_lengths.npz`.
   - A = ARL_H − ARL_H-V is the part removed by dependence-corrected startup scaling.
   - A / G is 0.52–0.79 for δ ≥ 1.8, i.e. more than half. At δ = 1.6 it is 0.42.
3. **Late-change ratio, 1.996–2.535 for δ ≥ 0.6 (thesis: 2.0–2.5×).** `s06_late_change.json`.
   - The change starts at τ = 132, after 100 in-control reports, with 500 new replications per δ.
   - `results["H(.05)"][i].ced / results["M(.05)"][i].ced` is the ratio of conditional expected
     delays in post-change observations.
   - Each delay is conditional on that chart having no alarm before the change.

Recompute all three from these files:

```python
import json
g = json.load(open("s03_geometry.json"))["geometry"]
print([round(100 * r["y"]["I"] / r["x"]["I"], 2) for r in g])                          # 1.65 … 36.35
b = json.load(open("s10_budget.json"))["budget"]
print([round(r["A"] / r["G"], 2) for r in b if r["delta"] >= 1.8])                       # 0.52 … 0.79
L = json.load(open("s06_late_change.json"))["results"]
print([round(h["ced"] / m["ced"], 3) for h, m in zip(L["H(.05)"], L["M(.05)"]) if h["delta"] >= 0.6])  # 1.996 … 2.535
```

The audit's scripts and its ~2.8 GB feature cache were not migrated. The cache is regenerable,
and the scripts depend on absolute paths of the original workspace.
