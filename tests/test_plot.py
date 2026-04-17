"""Tests for per-trajectory PDF plotting."""

from pathlib import Path

from empirical_incubation import detect, plot, synth


def test_plot_trajectory_writes_nonempty_pdf(tmp_path: Path):
    x = synth.sleeping_beauty(n_steps=500, seed=0)
    out = tmp_path / "beauty.pdf"

    plot.plot_trajectory(x, out)

    assert out.exists()
    assert out.stat().st_size > 0
    assert out.read_bytes().startswith(b"%PDF-"), "file must be a valid PDF"


def test_plot_trajectory_with_features_annotates_phases(tmp_path: Path):
    x = synth.sleeping_beauty(n_steps=500, seed=0)
    f = detect.extract_features(x)
    out = tmp_path / "beauty_annotated.pdf"

    plot.plot_trajectory(x, out, features=f, title="Test meme")

    assert out.exists()
    assert out.stat().st_size > 0
