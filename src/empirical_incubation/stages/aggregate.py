"""Stage 2 — Aggregate cleaned records into a dense (n_phrases, n_bins) matrix.

Two-pass streaming over `clean_dir/*.tsv.gz`:

  Pass 1: count total mentions per phrase. Phrases below ``min_total_mentions``
          are dropped before any trajectory memory is allocated.
  Pass 2: allocate a single int32 matrix of shape (n_allowed, n_bins) and fill
          it in place. One dense array, no dict-of-arrays.

Outputs under ``out_dir``:
  - phrases.txt    one phrase per line, in row order
  - timelines.npy  int32 matrix, shape (n_allowed, n_bins)
  - config.json    {start, end, bin_width_days, min_total_mentions}
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from .clean import parse_clean_file


def run_aggregate(
    *,
    clean_dir: Path,
    out_dir: Path,
    start: datetime,
    end: datetime,
    bin_width_days: int,
    min_total_mentions: int = 5,
) -> Path:
    clean_dir = Path(clean_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if end <= start:
        raise ValueError("end must be strictly after start")

    bin_width = timedelta(days=bin_width_days)
    n_bins = (end - start) // bin_width

    clean_files = sorted(clean_dir.glob("*.tsv.gz"))

    # Pass 1: count.
    totals: dict[str, int] = defaultdict(int)
    for f in clean_files:
        print(f"[aggregate pass 1] counting {f.name}", flush=True)
        for phrase, _ in parse_clean_file(f):
            totals[sys.intern(phrase)] += 1
    print(f"[aggregate pass 1] {len(totals):,} unique phrases seen", flush=True)

    # Filter + assign row indices.
    allowed = sorted(p for p, c in totals.items() if c >= min_total_mentions)
    phrase_to_idx = {p: i for i, p in enumerate(allowed)}
    print(
        f"[aggregate] {len(allowed):,} phrases pass min_total_mentions={min_total_mentions}",
        flush=True,
    )
    del totals

    # Pass 2: fill dense matrix.
    timelines = np.zeros((len(allowed), n_bins), dtype=np.int32)
    for f in clean_files:
        print(f"[aggregate pass 2] filling {f.name}", flush=True)
        for phrase, ts in parse_clean_file(f):
            idx = phrase_to_idx.get(sys.intern(phrase))
            if idx is None:
                continue
            if ts < start or ts >= end:
                continue
            bin_idx = (ts - start) // bin_width
            timelines[idx, bin_idx] += 1

    np.save(out_dir / "timelines.npy", timelines)
    (out_dir / "phrases.txt").write_text("\n".join(allowed) + "\n")
    (out_dir / "config.json").write_text(
        json.dumps(
            {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "bin_width_days": bin_width_days,
                "min_total_mentions": min_total_mentions,
                "n_phrases": len(allowed),
                "n_bins": int(n_bins),
            },
            indent=2,
        )
    )
    print(
        f"[aggregate] wrote timelines.npy shape={timelines.shape} "
        f"dtype={timelines.dtype}",
        flush=True,
    )
    return out_dir
