"""Stage 1 — Clean raw SNAP MemeTracker gz files into compact (phrase, iso_ts) tsvs.

Streams one input file at a time, drops P/L tags and records outside the
analysis window, and writes `<basename>.tsv.gz` to the output directory.
Constant memory per file.
"""

from __future__ import annotations

import gzip
from datetime import datetime
from pathlib import Path

from ..parse import parse_quotes_file

_ISO = "%Y-%m-%dT%H:%M:%S"


def run_clean(
    *,
    raw_dir: Path,
    out_dir: Path,
    start: datetime,
    end: datetime,
) -> list[Path]:
    raw_dir = Path(raw_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if end <= start:
        raise ValueError("end must be strictly after start")

    written: list[Path] = []
    for src in sorted(raw_dir.glob("*.txt.gz")):
        dst = out_dir / (src.name.replace(".txt.gz", ".tsv.gz"))
        print(f"[clean] {src.name} -> {dst.name}", flush=True)
        n_in = n_out = 0
        with gzip.open(dst, "wt", encoding="utf-8") as out:
            for phrase, ts in parse_quotes_file(src):
                n_in += 1
                if ts < start or ts >= end:
                    continue
                out.write(f"{phrase}\t{ts.strftime(_ISO)}\n")
                n_out += 1
        print(f"[clean]   {n_in:,} records in, {n_out:,} kept", flush=True)
        written.append(dst)
    return written


def parse_clean_file(path: Path):
    """Yield (phrase, datetime) from a cleaned tsv.gz produced by run_clean."""
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line:
                continue
            phrase, _, iso = line.partition("\t")
            yield phrase, datetime.strptime(iso, _ISO)
