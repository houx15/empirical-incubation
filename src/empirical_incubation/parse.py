"""SNAP MemeTracker parser.

Streams records from gzipped `quotes_YYYY-MM.txt.gz` files. Each record is a
group of lines separated by a blank line, with line-type tags:
  P<tab><post url>
  T<tab><timestamp YYYY-MM-DD HH:MM:SS>
  Q<tab><phrase>   (0+ per record)
  L<tab><link>     (0+ per record — ignored here)

Records with no timestamp or no phrase are skipped.
"""

import gzip
from collections import defaultdict
from collections.abc import Iterable, Iterator
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def parse_quotes_file(path: Path) -> Iterator[tuple[str, datetime]]:
    timestamp: datetime | None = None
    phrases: list[str] = []

    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line:
                yield from _flush(timestamp, phrases)
                timestamp, phrases = None, []
                continue
            tag, _, value = line.partition("\t")
            if tag == "T":
                try:
                    timestamp = datetime.strptime(value, _TIMESTAMP_FORMAT)
                except ValueError:
                    timestamp = None
            elif tag == "Q" and value:
                phrases.append(value)
    yield from _flush(timestamp, phrases)


def _flush(
    timestamp: datetime | None, phrases: list[str]
) -> Iterator[tuple[str, datetime]]:
    if timestamp is None:
        return
    for phrase in phrases:
        yield phrase, timestamp


def build_trajectories(
    records: Iterable[tuple[str, datetime]],
    *,
    bin_width_days: int,
    start: datetime,
    end: datetime,
) -> dict[str, np.ndarray]:
    if end <= start:
        raise ValueError("end must be strictly after start")
    bin_width = timedelta(days=bin_width_days)
    n_bins = (end - start) // bin_width

    counts: dict[str, np.ndarray] = defaultdict(lambda: np.zeros(n_bins, dtype=np.int64))
    for phrase, ts in records:
        if ts < start or ts >= end:
            continue
        idx = (ts - start) // bin_width
        counts[phrase][idx] += 1
    return dict(counts)
