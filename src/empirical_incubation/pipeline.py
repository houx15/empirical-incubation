"""End-to-end pipeline: raw SNAP MemeTracker quote files -> detection report.

Finds every `*.txt.gz` under `raw_dir`, builds per-phrase trajectories over the
requested time window, runs the three-phase detector, and writes a report
(plus per-meme PDFs and histograms) to `out_dir`.
"""

import hashlib
from datetime import datetime
from itertools import chain
from pathlib import Path

from .detect import extract_features, is_sleeping_beauty
from .parse import build_trajectories, parse_quotes_file
from .report import Record, generate_report


def run_analysis(
    raw_dir: Path,
    out_dir: Path,
    *,
    start: datetime,
    end: datetime,
    bin_width_days: int = 1,
    min_total_mentions: int = 5,
) -> Path:
    raw_dir = Path(raw_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    quote_files = sorted(raw_dir.glob("*.txt.gz"))
    record_iter = chain.from_iterable(parse_quotes_file(p) for p in quote_files)

    trajectories = build_trajectories(
        record_iter,
        bin_width_days=bin_width_days,
        start=start,
        end=end,
    )

    records: list[Record] = []
    for phrase, traj in trajectories.items():
        if int(traj.sum()) < min_total_mentions:
            continue
        features = extract_features(traj.astype(float))
        records.append(
            Record(
                id=_safe_id(phrase),
                trajectory=traj.astype(float),
                features=features,
                qualified=is_sleeping_beauty(traj.astype(float)),
            )
        )

    return generate_report(records, out_dir)


def _safe_id(phrase: str) -> str:
    # Phrases can contain chars that break filenames; hash-prefix for uniqueness.
    digest = hashlib.sha1(phrase.encode("utf-8")).hexdigest()[:8]
    slug = "".join(c if c.isalnum() else "_" for c in phrase)[:40].strip("_") or "meme"
    return f"{slug}-{digest}"
