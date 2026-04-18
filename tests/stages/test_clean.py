"""Stage 1 tests: raw SNAP gz -> clean (phrase, iso_ts) tsv.gz."""

import gzip
from datetime import datetime
from pathlib import Path

from empirical_incubation.stages import clean


def _write_raw(path: Path, content: str) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write(content)


def test_clean_writes_filtered_tsv(tmp_path: Path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    _write_raw(
        raw_dir / "quotes_2008-09.txt.gz",
        "P\thttp://a/1\nT\t2008-09-01 12:00:00\nQ\tin-window phrase\n\n"
        "P\thttp://a/2\nT\t2008-12-01 00:00:00\nQ\tout-of-window phrase\n",
    )

    out_dir = tmp_path / "clean"
    paths = clean.run_clean(
        raw_dir=raw_dir,
        out_dir=out_dir,
        start=datetime(2008, 9, 1),
        end=datetime(2008, 10, 1),
    )

    assert len(paths) == 1
    with gzip.open(paths[0], "rt", encoding="utf-8") as f:
        lines = f.read().splitlines()
    assert lines == ["in-window phrase\t2008-09-01T12:00:00"]


def test_clean_processes_all_input_files(tmp_path: Path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    _write_raw(
        raw_dir / "quotes_2008-09.txt.gz",
        "P\thttp://a/1\nT\t2008-09-15 00:00:00\nQ\talpha\n",
    )
    _write_raw(
        raw_dir / "quotes_2008-10.txt.gz",
        "P\thttp://a/2\nT\t2008-10-15 00:00:00\nQ\tbeta\n",
    )

    out_dir = tmp_path / "clean"
    paths = clean.run_clean(
        raw_dir=raw_dir,
        out_dir=out_dir,
        start=datetime(2008, 9, 1),
        end=datetime(2008, 11, 1),
    )

    assert {p.name for p in paths} == {"quotes_2008-09.tsv.gz", "quotes_2008-10.tsv.gz"}
