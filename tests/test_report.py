"""Tests for the dataset-level markdown report."""

from pathlib import Path

from empirical_incubation import detect, report, synth


def _make_record(rec_id: str, traj, qualified: bool):
    return report.Record(
        id=rec_id,
        trajectory=traj,
        features=detect.extract_features(traj),
        qualified=qualified,
    )


def test_generate_report_writes_markdown_with_expected_sections(tmp_path: Path):
    records = [
        _make_record("sb1", synth.sleeping_beauty(500, seed=0), qualified=True),
        _make_record("sb2", synth.sleeping_beauty(500, seed=1), qualified=True),
        _make_record("trender", synth.steady_trender(500, seed=0), qualified=False),
        _make_record("burst", synth.one_shot_burst(500, seed=0), qualified=False),
        _make_record("noise", synth.pure_noise(500, seed=0), qualified=False),
    ]

    report_path = report.generate_report(records, tmp_path)

    assert report_path == tmp_path / "report.md"
    content = report_path.read_text()
    assert "# Sleeping-Beauty Detection Report" in content
    assert "## Summary" in content
    assert "## Top sleeping beauties" in content
    assert "## Sanity check" in content
    assert "sb1" in content and "sb2" in content
    # Summary counts
    assert "5" in content  # total
    assert "2" in content  # qualified

    # Qualified records get a per-meme PDF
    assert (tmp_path / "plots" / "sb1.pdf").exists()
    assert (tmp_path / "plots" / "sb2.pdf").exists()

    # Histograms (PDFs) for distributions
    assert (tmp_path / "hist_amplitude_ratio.pdf").exists()
