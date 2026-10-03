"""Extended TEP external benchmark: data access and Phase I (Gate 3).

A thin application layer over ``pipeline.py``, which remains the authoritative
implementation. It follows ``application/GATE2_PROTOCOL_FREEZE.md`` and
``application/tep_protocol.json``; roles come from the committed run registry.

Run Phase I with ``python application/tep_pipeline.py``. It reads D1, D2 and D3 only.
"""

import csv
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import h5py
import numpy as np
import scipy
import sklearn
import threadpoolctl
import torch

APP = Path(__file__).resolve().parent
ROOT = APP.parent
sys.path.insert(0, str(ROOT))
import pipeline as P  # noqa: E402

H5_PATH = APP / "data" / "raw" / "TEP_Mode1.h5"
REGISTRY_PATH = APP / "tep_run_registry.csv"
PROTOCOL_PATH = APP / "tep_protocol.json"
MODELS_DIR = APP / "results" / "models"
PHASE1_DIR = APP / "results" / "phase1"
MANIFEST_PATH = APP / "results" / "phase1_manifest.json"

REGISTRY_SHA256 = "0c03350d207f0127c179b87670a09e5b538fc4450def2ce4fe52547fb6f4e97c"
PROTOCOL_SHA256 = "558ffcb6eeb7d0c99047f06032390a6ab6b706ee81254366f50630182586490f"

PREFIX_ROWS = 599          # t = 0.05 ... 29.95 h
J0 = PREFIX_ROWS - (P.WINDOW_LENGTH - 1)   # 568 pre-onset decisions
ALPHA_DENOMINATOR = 20     # alpha = 1/20
N3 = 2000
LAMBDA = 0.05
M_FIRST_UPDATE_INDEX = P.WINDOW_LENGTH     # 32: c_32 at M's first reported decision

# Phase I may read these roles only. D4 and D5 are refused until their stage.
PHASE1_ROLES = ("D1_train", "D1_val", "D2", "D3")


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_protocol():
    assert sha256_file(PROTOCOL_PATH) == PROTOCOL_SHA256, "protocol changed after freeze"
    return json.loads(PROTOCOL_PATH.read_text())


def load_registry():
    assert sha256_file(REGISTRY_PATH) == REGISTRY_SHA256, "registry changed after freeze"
    with REGISTRY_PATH.open(newline="") as fh:
        return list(csv.DictReader(fh))


def role_runs(registry, role):
    """Return the registry rows of one role, in registry (IDV, magnitude, run) order."""
    return [r for r in registry if r["role"] == role]


def selected_columns(protocol):
    columns = protocol["variables"]["selected_processdata_col0"]
    assert len(columns) == protocol["variables"]["final_p"] == 31
    assert columns == sorted(columns)
    return columns


def reference_grid(handle, protocol):
    """The common stored time grid, verified against its frozen hash."""
    ref = protocol["grid_and_onset"]["reference_grid"]
    grid = handle[ref["path"]]["processdata"][:, 0]
    grid = grid[1:] if grid[0] == 0.0 else grid
    digest = hashlib.sha256(np.ascontiguousarray(grid, dtype="<f8").tobytes()).hexdigest()
    assert digest == ref["sha256_float64le_2000"]
    return grid


def load_nominal_prefixes(runs, columns, protocol, allowed_roles=PHASE1_ROLES):
    """Load aligned rows 1..599 (t < 30 h) of the selected columns as ``(runs, 599, p)``."""
    assert all(r["role"] in allowed_roles for r in runs), "role not permitted in this stage"
    bank = np.empty((len(runs), PREFIX_ROWS, len(columns)), dtype=np.float64)
    with h5py.File(H5_PATH, "r") as handle:
        grid = reference_grid(handle, protocol)[:PREFIX_ROWS]
        assert np.array_equal(np.rint(grid * 20.0), np.arange(1, PREFIX_ROWS + 1))
        assert grid[-1] < 30.0
        for index, run in enumerate(runs):
            dataset = handle[run["path"]]["processdata"]
            offset = 1 if run["dropped_t0"] == "true" else 0
            assert dataset[0, 0] == (0.0 if offset else grid[0])
            assert np.array_equal(dataset[offset:offset + PREFIX_ROWS, 0], grid), run["path"]
            bank[index] = dataset[offset:offset + PREFIX_ROWS, columns]
    assert np.all(np.isfinite(bank))
    return bank


def run_windows(standardized_bank):
    """Windows formed within each run, flattened to ``(runs * 568, p, L)``."""
    windows = P.window_bank(standardized_bank)
    runs, per_run, channels, length = windows.shape
    assert per_run == standardized_bank.shape[1] - (P.WINDOW_LENGTH - 1)
    return windows.reshape(runs * per_run, channels, length)


def calibrate_fap(t2, alpha_denominator=ALPHA_DENOMINATOR):
    """Frozen O3 rule: h* = R_(k), k = n - n // 20 (1-based), strict T2 > h."""
    maxima = t2.max(axis=1)
    n = maxima.size
    allowed = n // alpha_denominator
    k = n - allowed
    ordered = np.sort(maxima)
    h_star = float(ordered[k - 1])
    exceedances = int(np.sum(maxima > h_star))
    assert exceedances <= allowed
    assert k == 1 or int(np.sum(maxima > ordered[k - 2])) > allowed
    assert int(np.sum(maxima == h_star)) == 1, "STOP: tie at h* (degenerate statistic)"
    return h_star, maxima, k, exceedances


def content_digest(arrays):
    """SHA-256 over names, dtypes, shapes and bytes of a dict of arrays."""
    digest = hashlib.sha256()
    for name in sorted(arrays):
        value = np.ascontiguousarray(arrays[name])
        digest.update(f"{name}|{value.dtype.str}|{value.shape}|".encode())
        digest.update(value.tobytes())
    return digest.hexdigest()


def m_moments(x_rows, run_in, mean, scale):
    """Raw M moments, or the pre-registered D1-standardised fallback."""
    assert x_rows.dtype == np.float64 and x_rows.flags["C_CONTIGUOUS"]
    assert np.all(np.isfinite(x_rows))
    try:
        return P.pooled_moments(x_rows), x_rows, run_in, "raw", None
    except np.linalg.LinAlgError as error:
        reason = f"raw Cholesky failure: {error!r}"
    except AssertionError:
        # Identify which guard fired; only the 1e8 condition guard is a valid trigger.
        flat = x_rows.reshape(-1, x_rows.shape[-1])
        kappa = P.condition_number(np.cov(flat, rowvar=False, ddof=P.MOMENTS_DDOF))
        assert kappa > P.CONDITION_NUMBER_GUARD, f"STOP: unexpected raw-moment assertion (kappa={kappa})"
        reason = f"raw condition number {kappa:.6e} > {P.CONDITION_NUMBER_GUARD:.0e}"
    x_std = np.ascontiguousarray(P.apply_preprocessing(x_rows, mean, scale))
    run_in_std = np.ascontiguousarray(P.apply_preprocessing(run_in, mean, scale))
    try:
        return P.pooled_moments(x_std), x_std, run_in_std, "d1_standardised_fallback", reason
    except (np.linalg.LinAlgError, AssertionError) as error:
        raise SystemExit(f"STOP: standardised M moments also fail the guard ({error!r})")


def versions():
    return {
        "python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__,
        "scikit-learn": sklearn.__version__, "scipy": scipy.__version__, "h5py": h5py.__version__,
        "threadpoolctl": threadpoolctl.__version__, "platform": platform.platform(),
    }


def git_state():
    def run(*args):
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return {"head": run("rev-parse", "HEAD"), "status_short": run("status", "--short").splitlines()}


def run_phase1():
    started = time.perf_counter()
    timings = {}
    protocol, registry = load_protocol(), load_registry()
    columns = selected_columns(protocol)
    p = len(columns)
    runs = {role: role_runs(registry, role) for role in PHASE1_ROLES}
    assert {k: len(v) for k, v in runs.items()} == {"D1_train": 40, "D1_val": 10, "D2": 20, "D3": N3}
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    PHASE1_DIR.mkdir(parents=True, exist_ok=True)

    # D1: standardisation on pooled D1-train rows; CAE with early stopping on D1-val.
    d1_train = load_nominal_prefixes(runs["D1_train"], columns, protocol)
    d1_val = load_nominal_prefixes(runs["D1_val"], columns, protocol)
    mean, scale = P.fit_preprocessing(d1_train.reshape(-1, p))
    train_windows = run_windows(P.apply_preprocessing(d1_train, mean, scale))
    validation_windows = run_windows(P.apply_preprocessing(d1_val, mean, scale))
    assert train_windows.shape == (40 * J0, p, P.WINDOW_LENGTH)
    assert validation_windows.shape == (10 * J0, p, P.WINDOW_LENGTH)
    t0 = time.perf_counter()
    model, history = P.train_autoencoder(train_windows, validation_windows, input_channels=p)
    timings["cae_training_s"] = round(time.perf_counter() - t0, 1)
    np.savez(MODELS_DIR / "preprocessing.npz", mean=mean, scale=scale,
             selected_processdata_col0=np.asarray(columns, dtype=np.int64))
    torch.save(model.state_dict(), MODELS_DIR / "autoencoder.pt")
    history_payload = {
        "epochs": [{"epoch": e, "train_loss": tr, "validation_loss": va} for e, tr, va in history["epochs"]],
        "best_epoch": history["best_epoch"],
        "best_validation_loss": history["best_validation_loss"],
        "n_train_windows": int(train_windows.shape[0]),
        "n_validation_windows": int(validation_windows.shape[0]),
        "input_channels": p,
        "stage3_seed": P.STAGE3_SEED,
    }
    P.write_json(PHASE1_DIR / "cae_training_history.json", history_payload)
    del train_windows, validation_windows, d1_train, d1_val

    # Reload the persisted CAE so every later stage uses exactly the frozen state.
    autoencoder = P.load_autoencoder(MODELS_DIR / "autoencoder.pt", input_channels=p)

    # D2: OC-SVM on CAE features of D2 windows.
    d2 = load_nominal_prefixes(runs["D2"], columns, protocol)
    t0 = time.perf_counter()
    features, _ = P.infer_bank(autoencoder, d2, mean, scale)
    assert features.shape == (20, J0, P.FEATURE_DIM)
    features = P.to_ocsvm_input(features.reshape(-1, P.FEATURE_DIM))
    ocsvm = P.fit_ocsvm(features)
    with P.single_threaded():
        gamma_check, median_sq = P.exact_gamma(features)
    assert gamma_check == ocsvm.gamma
    timings["ocsvm_fit_s"] = round(time.perf_counter() - t0, 1)
    np.savez(MODELS_DIR / "ocsvm.npz",
             support_vectors_=ocsvm.support_vectors,
             dual_coef_=ocsvm.dual_coefficients[np.newaxis, :],
             intercept_=np.array([-ocsvm.rho]),
             gamma=np.array(ocsvm.gamma),
             median_squared_distance=np.array(median_sq),
             n_fit_windows=np.array(features.shape[0]))
    del d2, features

    frozen = P.Frozen(*P.load_preprocessing(MODELS_DIR / "preprocessing.npz"), autoencoder,
                      P.load_ocsvm(MODELS_DIR / "ocsvm.npz"))
    assert np.array_equal(frozen.mean, mean) and np.array_equal(frozen.scale, scale)
    assert frozen.ocsvm.gamma == ocsvm.gamma and frozen.ocsvm.rho == ocsvm.rho

    # D3: moments and independent FAP calibration of H(0.05) and M(0.05).
    d3 = load_nominal_prefixes(runs["D3"], columns, protocol)
    t0 = time.perf_counter()
    y = np.ascontiguousarray(P.monitoring_bank(frozen, d3))
    assert y.shape == (N3, J0, 2) and y.dtype == np.float64
    timings["d3_monitoring_s"] = round(time.perf_counter() - t0, 1)
    hybrid = P.pooled_moments(y)
    x_raw = P.benchmark_bank(d3)
    run_in_raw = P.benchmark_run_in(d3)
    assert x_raw.shape == (N3, J0, p) and run_in_raw.shape == (N3, P.WINDOW_LENGTH - 1, p)
    del d3
    benchmark, x_m, run_in, m_representation, fallback_reason = m_moments(x_raw, run_in_raw, mean, scale)

    t0 = time.perf_counter()
    t2_h = P.mewma_t2(y, hybrid.mean, hybrid.covariance, LAMBDA)
    t2_m = P.mewma_t2(x_m, benchmark.mean, benchmark.covariance, LAMBDA, run_in, M_FIRST_UPDATE_INDEX)
    assert t2_h.shape == t2_m.shape == (N3, J0)
    h_h, r_h, k, exceed_h = calibrate_fap(t2_h)
    h_m, r_m, k_m, exceed_m = calibrate_fap(t2_m)
    assert k == k_m == 1900
    timings["d3_calibration_s"] = round(time.perf_counter() - t0, 1)

    np.savez(MODELS_DIR / "mewma.npz", mu_y=hybrid.mean, sigma_y=hybrid.covariance,
             mu_x=benchmark.mean, sigma_x=benchmark.covariance,
             m_representation=np.array(m_representation))
    np.savez(PHASE1_DIR / "d3_maxima.npz", R_H=r_h, R_M=r_m,
             d3_paths=np.array([r["path"] for r in runs["D3"]]))
    limits = [
        {"chart_id": chart, "lambda": LAMBDA, "h_star": h, "alpha": 1 / ALPHA_DENOMINATOR,
         "n3": N3, "k_one_based": k, "numpy_index": k - 1, "exceedances": exc,
         "d3_in_sample_fap": exc / N3, "J0": J0, "signal_rule": "T2 > h",
         "first_update_index": first, "dimension": dim, "source": source}
        for chart, h, exc, first, dim, source in (
            ("H", h_h, exceed_h, 1, 2, "hybrid_monitoring_vector"),
            ("M", h_m, exceed_m, M_FIRST_UPDATE_INDEX, p, f"selected_variables_{m_representation}"),
        )
    ]
    P.write_json(MODELS_DIR / "control_limits.json", limits)

    summary = {
        "d1": {k2: history_payload[k2] for k2 in ("best_epoch", "best_validation_loss",
                                                    "n_train_windows", "n_validation_windows")},
        "d1_epochs_run": len(history_payload["epochs"]),
        "d2": {"n_windows": 20 * J0, "median_squared_distance": median_sq, "gamma": ocsvm.gamma,
               "n_support_vectors": int(ocsvm.support_vectors.shape[0]), "rho": ocsvm.rho},
        "d3": {"condition_number_sigma_y": P.condition_number(hybrid.covariance),
               "condition_number_sigma_x": P.condition_number(benchmark.covariance),
               "m_representation": m_representation, "m_fallback_reason": fallback_reason,
               "h_H": h_h, "h_M": h_m, "fap_H": exceed_h / N3, "fap_M": exceed_m / N3},
        "timings_s": {**timings, "total": round(time.perf_counter() - started, 1)},
    }
    write_manifest(protocol, columns, summary)
    return summary


def write_manifest(protocol, columns, summary):
    artifacts = {
        "models/preprocessing.npz": MODELS_DIR / "preprocessing.npz",
        "models/autoencoder.pt": MODELS_DIR / "autoencoder.pt",
        "models/ocsvm.npz": MODELS_DIR / "ocsvm.npz",
        "models/mewma.npz": MODELS_DIR / "mewma.npz",
        "models/control_limits.json": MODELS_DIR / "control_limits.json",
        "phase1/d3_maxima.npz": PHASE1_DIR / "d3_maxima.npz",
        "phase1/cae_training_history.json": PHASE1_DIR / "cae_training_history.json",
    }
    state = torch.load(MODELS_DIR / "autoencoder.pt", map_location="cpu", weights_only=True)
    manifest = {
        "stage": "Phase I (Gate 3) - frozen before any D4/D5 access",
        "protocol_sha256": PROTOCOL_SHA256,
        "registry_sha256": REGISTRY_SHA256,
        "hdf5_sha256": protocol["source_data"]["sha256_local"],
        "code": {"git": git_state(), "pipeline.py_sha256": sha256_file(ROOT / "pipeline.py"),
                 "tep_pipeline.py_sha256": sha256_file(Path(__file__))},
        "roles_read": {"D1_train": 40, "D1_val": 10, "D2": 20, "D3": N3, "D4": 0, "D5": 0},
        "selected_processdata_col0": columns,
        "selected_pd": [c + 1 for c in columns],
        "p": len(columns),
        "seeds": {"stage3_seed": P.STAGE3_SEED, "allocation_entropy": [795, 6]},
        "artifacts_sha256": {name: sha256_file(path) for name, path in artifacts.items()},
        "autoencoder_state_content_sha256": content_digest({k: v.numpy() for k, v in state.items()}),
        "results": {k: v for k, v in summary.items() if k != "timings_s"},
        "versions": versions(),
    }
    P.write_json(MANIFEST_PATH, manifest)


if __name__ == "__main__":
    print(json.dumps(run_phase1(), indent=2))
    print("MANIFEST_SHA256", sha256_file(MANIFEST_PATH))
