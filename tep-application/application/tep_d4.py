"""Extended TEP external benchmark: D4 one-shot in-control validation.

Applies the frozen Phase-I artifacts, unchanged, to the 2000 D4 nominal prefixes. It fits
nothing and calibrates nothing. D5 stays refused: the loader is opened for role "D4" only.

Run: ``python application/tep_d4.py``.
"""

import json
import time

import numpy as np
import torch
from scipy.stats import binomtest

import tep_pipeline as T

P = T.P
D4_ROLES = ("D4",)
PHASE1_MANIFEST_SHA256 = "26a8f929c86d68032240471f48e2924d5762b04206a54eef0410b562d2dd34bc"
D4_DIR = T.APP / "results" / "d4"
N4 = 2000
STRATA = {"A": 1200, "B": 800}


def verify_phase1():
    """Check the frozen Phase-I manifest and every artifact hash before any D4 access."""
    assert T.sha256_file(T.MANIFEST_PATH) == PHASE1_MANIFEST_SHA256, "Phase-I manifest changed"
    manifest = json.loads(T.MANIFEST_PATH.read_text())
    assert manifest["protocol_sha256"] == T.PROTOCOL_SHA256
    assert manifest["registry_sha256"] == T.REGISTRY_SHA256
    for name, digest in manifest["artifacts_sha256"].items():
        assert T.sha256_file(T.APP / "results" / name) == digest, name
    assert T.sha256_file(T.ROOT / "pipeline.py") == manifest["code"]["pipeline.py_sha256"]
    assert T.sha256_file(T.APP / "tep_pipeline.py") == manifest["code"]["tep_pipeline.py_sha256"]
    state = torch.load(T.MODELS_DIR / "autoencoder.pt", map_location="cpu", weights_only=True)
    assert T.content_digest({k: v.numpy() for k, v in state.items()}) == \
        manifest["autoencoder_state_content_sha256"]
    return manifest


def proportion(x, n):
    ci = binomtest(x, n).proportion_ci(confidence_level=0.95, method="exact")
    p_hat = x / n
    return {"false_alarm_runs": x, "n": n, "fap": p_hat,
            "se": float(np.sqrt(p_hat * (1.0 - p_hat) / n)),
            "clopper_pearson_95": [float(ci.low), float(ci.high)]}


def run_d4():
    started = time.perf_counter()
    manifest = verify_phase1()
    protocol, registry = T.load_protocol(), T.load_registry()
    columns = T.selected_columns(protocol)
    p = len(columns)
    assert columns == manifest["selected_processdata_col0"]

    mean, scale = P.load_preprocessing(T.MODELS_DIR / "preprocessing.npz")
    frozen = P.Frozen(mean, scale, P.load_autoencoder(T.MODELS_DIR / "autoencoder.pt", input_channels=p),
                      P.load_ocsvm(T.MODELS_DIR / "ocsvm.npz"))
    hybrid, benchmark = P.load_moments(T.MODELS_DIR / "mewma.npz")
    with np.load(T.MODELS_DIR / "mewma.npz") as archive:
        m_representation = str(archive["m_representation"])
    assert m_representation == manifest["results"]["d3"]["m_representation"] == "d1_standardised_fallback"
    limits = {e["chart_id"]: e["h_star"]
              for e in json.loads((T.MODELS_DIR / "control_limits.json").read_text())}
    assert limits["H"] == manifest["results"]["d3"]["h_H"] and limits["M"] == manifest["results"]["d3"]["h_M"]

    runs = T.role_runs(registry, "D4")
    strata = np.array([r["stratum"] for r in runs])
    assert len(runs) == N4 and {s: int(np.sum(strata == s)) for s in STRATA} == STRATA
    bank = T.load_nominal_prefixes(runs, columns, protocol, allowed_roles=D4_ROLES)
    assert bank.shape == (N4, T.PREFIX_ROWS, p)

    # H: frozen preprocessing -> CAE -> OC-SVM -> [score, log SPE] -> MEWMA.
    y = np.ascontiguousarray(P.monitoring_bank(frozen, bank))
    assert y.shape == (N4, T.J0, 2)
    t2_h = P.mewma_t2(y, hybrid.mean, hybrid.covariance, T.LAMBDA)

    # M: D1-standardised representation (Phase-I fallback), run-in rows 1-31 silent.
    x_m = np.ascontiguousarray(P.apply_preprocessing(P.benchmark_bank(bank), mean, scale))
    run_in = np.ascontiguousarray(P.apply_preprocessing(P.benchmark_run_in(bank), mean, scale))
    del bank
    assert x_m.shape == (N4, T.J0, p) and run_in.shape == (N4, P.WINDOW_LENGTH - 1, p)
    t2_m = P.mewma_t2(x_m, benchmark.mean, benchmark.covariance, T.LAMBDA, run_in,
                      T.M_FIRST_UPDATE_INDEX)
    assert t2_h.shape == t2_m.shape == (N4, T.J0)

    maxima = {"H": t2_h.max(axis=1), "M": t2_m.max(axis=1)}
    results = {}
    for chart, r in maxima.items():
        alarm = r > limits[chart]                              # strict T2 > h
        results[chart] = {
            "h_star": limits[chart],
            "overall": proportion(int(alarm.sum()), N4),
            **{f"stratum_{s}_descriptive": proportion(int(alarm[strata == s].sum()), n)
               for s, n in STRATA.items()},
        }

    D4_DIR.mkdir(parents=True, exist_ok=True)
    np.savez(D4_DIR / "d4_maxima.npz", R_H=maxima["H"], R_M=maxima["M"],
             d4_paths=np.array([r["path"] for r in runs]), strata=strata)
    validation = {
        "stage": "D4 one-shot in-control validation (no fitting, no calibration)",
        "alpha_target": 1 / T.ALPHA_DENOMINATOR, "J0": T.J0, "n4": N4, "strata_n": STRATA,
        "signal_rule": "false alarm iff max_j T2_ij > h_star (strict)",
        "m_representation": m_representation,
        "d3_in_sample_fap": {"H": manifest["results"]["d3"]["fap_H"], "M": manifest["results"]["d3"]["fap_M"]},
        "results": results,
        "stratum_note": "stratum A/B values are descriptive only and trigger no action",
    }
    P.write_json(D4_DIR / "d4_validation.json", validation)
    d4_manifest = {
        "phase1_manifest_sha256": PHASE1_MANIFEST_SHA256,
        "protocol_sha256": T.PROTOCOL_SHA256,
        "registry_sha256": T.REGISTRY_SHA256,
        "code": {"git": T.git_state(), "tep_d4.py_sha256": T.sha256_file(__file__)},
        "frozen_limits": limits,
        "m_representation": m_representation,
        "roles_read": {"D4": N4, "D5": 0},
        "d4_counts": {"total": N4, **STRATA, "rows_per_run": T.PREFIX_ROWS, "decisions_per_run": T.J0},
        "results": results,
        "artifacts_sha256": {"d4/d4_maxima.npz": T.sha256_file(D4_DIR / "d4_maxima.npz"),
                             "d4/d4_validation.json": T.sha256_file(D4_DIR / "d4_validation.json")},
        "versions": T.versions(),
    }
    P.write_json(D4_DIR / "d4_manifest.json", d4_manifest)
    return results, round(time.perf_counter() - started, 1)


if __name__ == "__main__":
    results, seconds = run_d4()
    print(json.dumps(results, indent=2))
    print("RUNTIME_S", seconds, "| D4_MANIFEST_SHA256", T.sha256_file(D4_DIR / "d4_manifest.json"))
