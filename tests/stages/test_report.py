"""Stage 4 tests: aggregate + features.csv -> report.md + plots."""

import csv
from pathlib import Path

import numpy as np

from empirical_incubation.stages import report
from empirical_incubation.synth import one_shot_burst, pure_noise, sleeping_beauty


def _build_inputs(tmp_path: Path) -> tuple[Path, Path]:
    agg_dir = tmp_path / "agg"
    agg_dir.mkdir()
    phrases = ["beauty_a", "beauty_b", "beauty_c", "burst", "noise"]
    rows = [
        (sleeping_beauty(60, seed=i) * 10).astype(np.int32)
        for i in range(3)
    ] + [
        (one_shot_burst(60, seed=99) * 10).astype(np.int32),
        (pure_noise(60, seed=77) * 10).astype(np.int32),
    ]
    np.save(agg_dir / "timelines.npy", np.stack(rows))
    (agg_dir / "phrases.txt").write_text("\n".join(phrases) + "\n")

    # Reuse the score stage to produce features.csv so the test exercises the
    # same inputs report expects.
    from empirical_incubation.stages import score

    score_dir = tmp_path / "score"
    score.run_score(aggregate_dir=agg_dir, out_dir=score_dir)
    return agg_dir, score_dir


def test_report_renders_only_top_n_qualified_plots(tmp_path: Path):
    agg_dir, score_dir = _build_inputs(tmp_path)
    out_dir = tmp_path / "report"

    report.run_report(
        aggregate_dir=agg_dir,
        score_dir=score_dir,
        out_dir=out_dir,
        top_n=2,
    )

    report_md = (out_dir / "report.md").read_text()
    assert "# Sleeping-Beauty Detection Report" in report_md
    assert "## Summary" in report_md

    plots = list((out_dir / "plots").glob("*.pdf"))
    # Cap at 2 even though 3 qualified.
    assert len(plots) <= 2
    for p in plots:
        assert p.stat().st_size > 0


def test_report_writes_histograms(tmp_path: Path):
    agg_dir, score_dir = _build_inputs(tmp_path)
    out_dir = tmp_path / "report"

    report.run_report(
        aggregate_dir=agg_dir,
        score_dir=score_dir,
        out_dir=out_dir,
        top_n=100,
    )

    assert (out_dir / "hist_amplitude_ratio.pdf").exists()
    assert (out_dir / "hist_gap_ratio.pdf").exists()
