"""Stage 3 tests: aggregate dir -> features.csv."""

import csv
from pathlib import Path

import numpy as np

from empirical_incubation.stages import score
from empirical_incubation.synth import one_shot_burst, pure_noise, sleeping_beauty


def _write_aggregate(out_dir: Path, phrases: list[str], timelines: np.ndarray) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "phrases.txt").write_text("\n".join(phrases) + "\n")
    np.save(out_dir / "timelines.npy", timelines.astype(np.int32))


def test_score_writes_features_per_phrase(tmp_path: Path):
    agg_dir = tmp_path / "agg"
    beauty = (sleeping_beauty(60, seed=1) * 10).astype(np.int32)
    burst = (one_shot_burst(60, seed=2) * 10).astype(np.int32)
    noise = (pure_noise(60, seed=3) * 10).astype(np.int32)
    _write_aggregate(agg_dir, ["beauty", "burst", "noise"], np.stack([beauty, burst, noise]))

    out_dir = tmp_path / "score"
    score.run_score(aggregate_dir=agg_dir, out_dir=out_dir)

    rows = list(csv.DictReader((out_dir / "features.csv").open()))
    assert [r["phrase"] for r in rows] == ["beauty", "burst", "noise"]
    expected = {"phrase", "amplitude_ratio", "gap_ratio", "main_peak_amplitude",
                "early_peak_amplitude", "middle_peak_amplitude", "main_peak_time",
                "early_peak_time", "qualified"}
    assert expected.issubset(rows[0].keys())


def test_score_flags_beauty_qualified(tmp_path: Path):
    agg_dir = tmp_path / "agg"
    beauty = (sleeping_beauty(60, seed=1) * 10).astype(np.int32)
    noise = (pure_noise(60, seed=3) * 10).astype(np.int32)
    _write_aggregate(agg_dir, ["beauty", "noise"], np.stack([beauty, noise]))

    out_dir = tmp_path / "score"
    score.run_score(aggregate_dir=agg_dir, out_dir=out_dir)

    rows = {r["phrase"]: r for r in csv.DictReader((out_dir / "features.csv").open())}
    assert rows["beauty"]["qualified"] == "True"
    assert rows["noise"]["qualified"] == "False"
