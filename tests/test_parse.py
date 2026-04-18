"""Tests for the SNAP MemeTracker parser.

The MemeTracker9 dataset uses gzipped text files where each record describes
one post with one timestamp and one or more quoted phrases. Format:

    P<tab><post url>
    T<tab><timestamp YYYY-MM-DD HH:MM:SS>
    Q<tab><phrase>
    Q<tab><phrase>
    L<tab><outgoing link>
    <blank line separates records>
"""

import gzip
from datetime import datetime
from pathlib import Path

from empirical_incubation import parse


def _write_fixture(path: Path, content: str) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write(content)


def test_parse_quotes_file_yields_phrase_timestamp_pairs(tmp_path: Path):
    content = (
        "P\thttp://a.example/1\n"
        "T\t2008-09-01 12:00:00\n"
        "Q\tyes we can\n"
        "L\thttp://link.example/a\n"
        "\n"
        "P\thttp://b.example/2\n"
        "T\t2008-09-02 08:30:00\n"
        "Q\tyes we can\n"
        "Q\tchange we believe in\n"
    )
    path = tmp_path / "quotes.txt.gz"
    _write_fixture(path, content)

    records = list(parse.parse_quotes_file(path))

    assert records == [
        ("yes we can", datetime(2008, 9, 1, 12, 0, 0)),
        ("yes we can", datetime(2008, 9, 2, 8, 30, 0)),
        ("change we believe in", datetime(2008, 9, 2, 8, 30, 0)),
    ]


def test_build_trajectories_bins_counts_per_phrase():
    records = [
        ("yes we can", datetime(2008, 9, 1, 12, 0)),
        ("yes we can", datetime(2008, 9, 1, 20, 0)),  # same day
        ("yes we can", datetime(2008, 9, 3, 8, 0)),
        ("other meme", datetime(2008, 9, 2, 8, 0)),
        ("other meme", datetime(2008, 9, 10, 0, 0)),  # outside window — dropped
    ]

    trajectories = parse.build_trajectories(
        records,
        bin_width_days=1,
        start=datetime(2008, 9, 1),
        end=datetime(2008, 9, 4),  # exclusive — 3 full-day bins
    )

    assert set(trajectories.keys()) == {"yes we can", "other meme"}
    assert trajectories["yes we can"].tolist() == [2, 0, 1]
    assert trajectories["other meme"].tolist() == [0, 1, 0]


def test_count_total_mentions_respects_window():
    records = [
        ("yes we can", datetime(2008, 9, 1, 12, 0)),
        ("yes we can", datetime(2008, 9, 2, 8, 0)),
        ("yes we can", datetime(2008, 9, 10, 0, 0)),  # outside window — dropped
        ("rare phrase", datetime(2008, 9, 1, 1, 0)),
        ("other meme", datetime(2008, 9, 3, 8, 0)),
        ("other meme", datetime(2008, 9, 3, 9, 0)),
    ]

    counts = parse.count_total_mentions(
        records,
        start=datetime(2008, 9, 1),
        end=datetime(2008, 9, 4),
    )

    assert counts == {"yes we can": 2, "rare phrase": 1, "other meme": 2}


def test_build_trajectories_respects_allowed_phrases():
    records = [
        ("yes we can", datetime(2008, 9, 1, 12, 0)),
        ("rare phrase", datetime(2008, 9, 2, 12, 0)),
        ("other meme", datetime(2008, 9, 3, 8, 0)),
    ]

    trajectories = parse.build_trajectories(
        records,
        bin_width_days=1,
        start=datetime(2008, 9, 1),
        end=datetime(2008, 9, 4),
        allowed_phrases={"yes we can", "other meme"},
    )

    assert set(trajectories.keys()) == {"yes we can", "other meme"}
    assert trajectories["yes we can"].tolist() == [1, 0, 0]
    assert trajectories["other meme"].tolist() == [0, 0, 1]


def test_parse_quotes_file_skips_record_with_no_timestamp(tmp_path: Path):
    content = (
        "P\thttp://a.example/1\n"
        "Q\tphrase without timestamp\n"
        "\n"
        "P\thttp://b.example/2\n"
        "T\t2008-09-02 08:30:00\n"
        "Q\tvalid phrase\n"
    )
    path = tmp_path / "quotes.txt.gz"
    _write_fixture(path, content)

    records = list(parse.parse_quotes_file(path))

    assert records == [("valid phrase", datetime(2008, 9, 2, 8, 30, 0))]
