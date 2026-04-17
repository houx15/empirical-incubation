"""Tests for the three-phase sleeping-beauty detector."""

from empirical_incubation import detect, synth


def test_detector_flags_sleeping_beauty_fixture():
    x = synth.sleeping_beauty(n_steps=500, seed=0)
    assert detect.is_sleeping_beauty(x) is True


def test_detector_rejects_steady_trender():
    x = synth.steady_trender(n_steps=500, seed=0)
    assert detect.is_sleeping_beauty(x) is False


def test_detector_rejects_one_shot_burst():
    x = synth.one_shot_burst(n_steps=500, seed=0)
    assert detect.is_sleeping_beauty(x) is False


def test_detector_rejects_pure_noise():
    x = synth.pure_noise(n_steps=500, seed=0)
    assert detect.is_sleeping_beauty(x) is False


def test_extract_features_on_sleeping_beauty():
    n = 500
    x = synth.sleeping_beauty(n_steps=n, seed=0)
    f = detect.extract_features(x)

    assert 0 <= f.early_peak_time < n // 3
    assert 2 * n // 3 <= f.main_peak_time < n
    assert f.main_peak_time > f.early_peak_time
    assert f.main_peak_amplitude > f.early_peak_amplitude > 0
    assert f.amplitude_ratio == f.main_peak_amplitude / f.early_peak_amplitude
    assert 0.0 < f.gap_ratio <= 1.0
    assert f.dormancy_duration > 0
