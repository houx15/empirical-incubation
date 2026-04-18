"""Stage 2 tests: clean tsv.gz files -> phrases.txt + timelines.npy."""

import gzip
import json
from datetime import datetime
from pathlib import Path

import numpy as np

from empirical_incubation.stages import aggregate


def _write_clean(path: Path, lines: list[str]) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def test_aggregate_writes_phrases_and_timelines(tmp_path: Path):
    clean_dir = tmp_path / "clean"
    clean_dir.mkdir()
    _write_clean(
        clean_dir / "2008-09.tsv.gz",
        [
            "hot meme\t2008-09-01T12:00:00",
            "hot meme\t2008-09-01T13:00:00",
            "hot meme\t2008-09-03T08:00:00",
            "other\t2008-09-02T08:00:00",
            "other\t2008-09-03T09:00:00",
        ],
    )

    out_dir = tmp_path / "agg"
    aggregate.run_aggregate(
        clean_dir=clean_dir,
        out_dir=out_dir,
        start=datetime(2008, 9, 1),
        end=datetime(2008, 9, 4),
        bin_width_days=1,
        min_total_mentions=2,
    )

    phrases = (out_dir / "phrases.txt").read_text().splitlines()
    timelines = np.load(out_dir / "timelines.npy")
    config = json.loads((out_dir / "config.json").read_text())

    assert set(phrases) == {"hot meme", "other"}
    assert timelines.dtype == np.int32
    assert timelines.shape == (2, 3)
    hot_row = timelines[phrases.index("hot meme")]
    other_row = timelines[phrases.index("other")]
    assert hot_row.tolist() == [2, 0, 1]
    assert other_row.tolist() == [0, 1, 1]
    assert config["start"] == "2008-09-01T00:00:00"
    assert config["end"] == "2008-09-04T00:00:00"
    assert config["bin_width_days"] == 1


def test_aggregate_drops_phrases_below_threshold(tmp_path: Path):
    clean_dir = tmp_path / "clean"
    clean_dir.mkdir()
    _write_clean(
        clean_dir / "2008-09.tsv.gz",
        [
            "kept\t2008-09-01T00:00:00",
            "kept\t2008-09-02T00:00:00",
            "dropped\t2008-09-01T00:00:00",  # only 1 mention
        ],
    )

    out_dir = tmp_path / "agg"
    aggregate.run_aggregate(
        clean_dir=clean_dir,
        out_dir=out_dir,
        start=datetime(2008, 9, 1),
        end=datetime(2008, 9, 3),
        bin_width_days=1,
        min_total_mentions=2,
    )

    phrases = (out_dir / "phrases.txt").read_text().splitlines()
    assert phrases == ["kept"]
