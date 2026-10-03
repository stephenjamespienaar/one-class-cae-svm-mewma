"""Focused correctness tests for the TEP Phase-I application layer."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tep_pipeline as T  # noqa: E402

P = T.P
needs_h5 = pytest.mark.skipif(not T.H5_PATH.exists(), reason="TEP_Mode1.h5 not present")
needs_artifacts = pytest.mark.skipif(not T.MANIFEST_PATH.exists(), reason="Phase I not run")


@pytest.fixture(scope="module")
def protocol():
    return T.load_protocol()


@pytest.fixture(scope="module")
def registry():
    return T.load_registry()


def test_registry_roles(registry):
    counts = {role: len(T.role_runs(registry, role))
              for role in ("D1_train", "D1_val", "D2", "D3", "D4", "D5", "unused", "excluded")}
    assert counts == {"D1_train": 40, "D1_val": 10, "D2": 20, "D3": 2000, "D4": 2000,
                      "D5": 500, "unused": 9375, "excluded": 55}


def test_selected_columns_frozen_order(protocol):
    columns = T.selected_columns(protocol)
    assert columns == list(range(1, 23)) + [42, 43, 44, 45, 47, 48, 49, 51, 52]
    assert not set(columns) & ({0} | set(range(23, 42)) | {46, 50, 53})


def test_loader_refuses_phase2_roles(protocol, registry):
    for role in ("D4", "D5", "unused", "excluded"):
        with pytest.raises(AssertionError, match="not permitted"):
            T.load_nominal_prefixes(T.role_runs(registry, role)[:1], [1], protocol)


@needs_h5
def test_nominal_prefix_extraction(protocol, registry):
    runs = T.role_runs(registry, "D1_train")
    run_a = next(r for r in runs if r["stratum"] == "A")
    run_b = next(r for r in runs if r["stratum"] == "B")    # has a t = 0 row to drop
    assert run_b["dropped_t0"] == "true"
    bank = T.load_nominal_prefixes([run_a, run_b], T.selected_columns(protocol), protocol)
    assert bank.shape == (2, 599, 31) and bank.dtype == np.float64


def test_windows_never_cross_runs():
    runs, rows, p = 3, 599, 31
    bank = np.repeat(np.arange(runs, dtype=np.float64)[:, None, None], rows, axis=1)
    bank = np.repeat(bank, p, axis=2)
    windows = T.run_windows(bank)
    assert windows.shape == (runs * 568, p, 32)
    per_window = windows.reshape(windows.shape[0], -1)
    assert np.all(per_window.min(axis=1) == per_window.max(axis=1))
    assert np.array_equal(per_window[:, 0], np.repeat(np.arange(runs), 568))


def test_cae_channel_parameterisation():
    torch.manual_seed(0)
    default = P.ConvAutoencoder1d()
    torch.manual_seed(0)
    explicit = P.ConvAutoencoder1d(4)
    assert all(torch.equal(default.state_dict()[k], v) for k, v in explicit.state_dict().items())
    assert sum(x.numel() for x in default.parameters()) == 3180

    tep = P.ConvAutoencoder1d(31)
    assert sum(x.numel() for x in tep.parameters()) == 2984 + 49 * 31
    names = lambda m: [(n, tuple(v.shape)) for n, v in m.state_dict().items()]
    differing = [a[0] for a, b in zip(names(default), names(tep)) if a != b]
    assert differing == ["encoder_conv.0.weight", "decoder_conv.3.weight", "decoder_conv.3.bias"]
    x = torch.zeros(5, 31, 32)
    assert tep.encode(x).shape == (5, 8) and tep(x).shape == (5, 31, 32)


def test_h_and_m_align_on_568_decisions():
    bank = np.zeros((2, 599, 31))
    assert P.window_bank(bank).shape[1] == 568
    assert P.benchmark_bank(bank).shape == (2, 568, 31)
    assert P.benchmark_run_in(bank).shape == (2, 31, 31)
    c_h = P.finite_start_factors(568, 0.05, 1)
    c_m = P.finite_start_factors(568, 0.05, 32)
    assert c_h[0] == 0.05 ** 2 and c_m[0] == P.finite_start_factors(32, 0.05)[-1]


def test_fap_order_statistic_rule():
    rng = np.random.default_rng(1)
    t2 = rng.random((2000, 568))
    h, maxima, k, exceed = T.calibrate_fap(t2)
    assert k == 1900 and h == np.sort(maxima)[1899] and exceed == 100
    assert np.sum(t2.max(axis=1) > h) == 100           # strict: R == h is not an alarm
    _, _, k_odd, exceed_odd = T.calibrate_fap(rng.random((1999, 568)))
    assert k_odd == 1900 and exceed_odd == 99           # conservative when n * alpha is fractional
    tied = np.sort(rng.random(2000))
    tied[1899] = tied[1900]
    with pytest.raises(AssertionError, match="tie"):
        T.calibrate_fap(tied[:, None])


def test_content_digest_is_deterministic():
    arrays = {"b": np.arange(3.0), "a": np.eye(2)}
    assert T.content_digest(arrays) == T.content_digest(dict(reversed(arrays.items())))
    assert T.content_digest(arrays) != T.content_digest({"b": np.arange(3.0), "a": np.eye(2) * 2})


@needs_artifacts
def test_phase1_artifacts_load_and_match_manifest(protocol):
    manifest = json.loads(T.MANIFEST_PATH.read_text())
    assert manifest["protocol_sha256"] == T.PROTOCOL_SHA256
    assert manifest["registry_sha256"] == T.REGISTRY_SHA256
    assert manifest["roles_read"]["D4"] == manifest["roles_read"]["D5"] == 0
    base = T.APP / "results"
    for name, digest in manifest["artifacts_sha256"].items():
        assert T.sha256_file(base / name) == digest, name

    mean, scale = P.load_preprocessing(T.MODELS_DIR / "preprocessing.npz")
    model = P.load_autoencoder(T.MODELS_DIR / "autoencoder.pt", input_channels=31)
    ocsvm = P.load_ocsvm(T.MODELS_DIR / "ocsvm.npz")
    hybrid, benchmark = P.load_moments(T.MODELS_DIR / "mewma.npz")
    assert mean.shape == scale.shape == (31,) and benchmark.covariance.shape == (31, 31)
    assert P.condition_number(hybrid.covariance) <= P.CONDITION_NUMBER_GUARD

    # Monitoring vector order: column 0 is the OC-SVM score, column 1 is log SPE.
    frozen = P.Frozen(mean, scale, model, ocsvm)
    rng = np.random.default_rng(0)
    series = mean + scale * rng.standard_normal((40, 31))
    y = P.monitoring_series(frozen, series)
    features, spe_values = P.infer_series(model, series, mean, scale)
    assert y.shape == (9, 2)
    assert np.array_equal(y[:, 0], P.ocsvm_score(ocsvm, P.to_ocsvm_input(features)))
    assert np.array_equal(y[:, 1], P.log_spe(spe_values))

    limits = {e["chart_id"]: e for e in json.loads((T.MODELS_DIR / "control_limits.json").read_text())}
    maxima = np.load(T.PHASE1_DIR / "d3_maxima.npz")
    for chart, key in (("H", "R_H"), ("M", "R_M")):
        R = maxima[key]
        assert R.shape == (2000,)
        assert limits[chart]["h_star"] == np.sort(R)[1899]
        assert int(np.sum(R > limits[chart]["h_star"])) == limits[chart]["exceedances"] == 100


def test_d4_stage_still_refuses_d5(protocol, registry):
    import tep_d4
    assert tep_d4.D4_ROLES == ("D4",)
    for role in ("D5", "D3", "unused"):
        with pytest.raises(AssertionError, match="not permitted"):
            T.load_nominal_prefixes(T.role_runs(registry, role)[:1], [1], protocol,
                                    allowed_roles=tep_d4.D4_ROLES)


def test_d5_onset_quantities_and_censoring():
    import tep_d5
    assert tep_d5.D5_ROLES == ("D5",)
    t2 = np.zeros((4, 1969))
    t2[0, 567] = 2.0          # pre-onset alarm at j = 568
    t2[1, 568] = 2.0          # signal at j = 569 (t = 30.00 h) -> D = 1
    t2[2, 1968] = 2.0         # signal at the last decision -> D = 1401, not censored
    t2[3, 600] = 1.0          # equal to h: not a signal (strict) -> censored
    pre, first_j, delay, censored = tep_d5.onset_quantities(t2, 1.0)
    assert pre.tolist() == [True, False, False, False] and first_j[0] == 568
    assert delay[1:].tolist() == [1, 1401, 1401] and censored[1:].tolist() == [False, False, True]
    cell = tep_d5.delay_cell(np.array([1, 1401, 1401]), np.array([False, True, True]))
    assert cell["median_D"] is None and cell["truncation_limited"]
    cell = tep_d5.delay_cell(np.array([3, 5, 1401]), np.array([False, False, True]))
    assert cell["median_D"] == 5 and cell["median_hours"] == 0.2
