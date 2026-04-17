"""Tests for synthetic trajectory generators in empirical_incubation.synth."""

import numpy as np

from empirical_incubation import synth


def test_sleeping_beauty_main_peak_dominates_early_bump():
    n = 500
    x = synth.sleeping_beauty(n_steps=n, seed=0)

    assert x.shape == (n,)
    early = x[: n // 3]
    late = x[2 * n // 3 :]
    assert early.max() > 0, "sleeping beauty must have a visible early bump"
    assert late.max() > 3 * early.max(), "main peak must dominate the early bump"


def test_steady_trender_rises_without_dormancy():
    n = 500
    x = synth.steady_trender(n_steps=n, seed=0)

    assert x.shape == (n,)
    first_half_mean = x[: n // 2].mean()
    second_half_mean = x[n // 2 :].mean()
    middle_third_mean = x[n // 3 : 2 * n // 3].mean()
    assert second_half_mean > first_half_mean, "trender must rise overall"
    # No dormancy: the middle of the trajectory must not drop well below the early signal.
    assert middle_third_mean > 0.5 * first_half_mean


def test_one_shot_burst_has_late_peak_but_no_early_bump():
    n = 500
    x = synth.one_shot_burst(n_steps=n, seed=0)

    assert x.shape == (n,)
    early = x[: n // 3]
    late = x[2 * n // 3 :]
    # A single late burst: late must dominate the global maximum.
    assert late.max() > 5 * (early.max() + 1e-6), "late burst must dominate"
    # Early region should be near the noise floor — no meaningful early bump.
    assert early.max() < 0.5, "one-shot burst must NOT have a visible early bump"


def test_pure_noise_has_no_dominant_peak():
    n = 500
    x = synth.pure_noise(n_steps=n, seed=0)

    assert x.shape == (n,)
    # No section should dominate another by more than ~3x — it's noise, not structure.
    thirds = [x[: n // 3], x[n // 3 : 2 * n // 3], x[2 * n // 3 :]]
    maxes = [t.max() for t in thirds]
    assert max(maxes) < 3 * min(maxes) + 1.0, "noise must not have a dominant peak"
