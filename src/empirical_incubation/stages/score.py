"""Stage 3 — Compute per-phrase features and qualification flags.

Mmap-loads ``timelines.npy`` from the aggregate stage, runs the three-phase
detector row by row, and writes a flat ``features.csv`` with one row per
phrase. The CSV is small (one float row per meme); plotting happens in a
later stage that re-reads only the top-N rows from the timelines matrix.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from ..detect import extract_features, is_sleeping_beauty

_COLUMNS = [
    "phrase_idx",
    "phrase",
    "total_mentions",
    "early_peak_amplitude",
    "middle_peak_amplitude",
    "main_peak_amplitude",
    "early_peak_time",
    "main_peak_time",
    "amplitude_ratio",
    "gap_ratio",
    "qualified",
]


def run_score(
    *,
    aggregate_dir: Path,
    out_dir: Path,
) -> Path:
    aggregate_dir = Path(aggregate_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    phrases = (aggregate_dir / "phrases.txt").read_text().splitlines()
    timelines = np.load(aggregate_dir / "timelines.npy", mmap_mode="r")
    assert timelines.shape[0] == len(phrases), "phrases.txt and timelines.npy disagree"

    out_path = out_dir / "features.csv"
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_COLUMNS)
        writer.writeheader()
        for i, phrase in enumerate(phrases):
            row = timelines[i]
            features = extract_features(row)
            qualified = is_sleeping_beauty(row)
            writer.writerow(
                {
                    "phrase_idx": i,
                    "phrase": phrase,
                    "total_mentions": int(row.sum()),
                    "early_peak_amplitude": features.early_peak_amplitude,
                    "middle_peak_amplitude": features.middle_peak_amplitude,
                    "main_peak_amplitude": features.main_peak_amplitude,
                    "early_peak_time": features.early_peak_time,
                    "main_peak_time": features.main_peak_time,
                    "amplitude_ratio": features.amplitude_ratio,
                    "gap_ratio": features.gap_ratio,
                    "qualified": qualified,
                }
            )
    print(f"[score] wrote {len(phrases):,} rows to {out_path}", flush=True)
    return out_path
