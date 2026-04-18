"""End-to-end pipeline: raw SNAP MemeTracker gz files -> detection report.

Runs the four stages (clean, aggregate, score, report) in order, placing the
intermediate artifacts under ``out_dir/stages/`` and the final report at
``out_dir/report.md``. Each stage can also be invoked individually via the
corresponding CLI subcommand; this wrapper exists for one-shot runs.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .stages import aggregate, clean, report, score


def run_analysis(
    raw_dir: Path,
    out_dir: Path,
    *,
    start: datetime,
    end: datetime,
    bin_width_days: int = 1,
    min_total_mentions: int = 5,
    top_n: int = 100,
) -> Path:
    out_dir = Path(out_dir)
    stages = out_dir / "stages"
    clean_dir = stages / "clean"
    aggregate_dir = stages / "aggregate"
    score_dir = stages / "score"

    clean.run_clean(raw_dir=raw_dir, out_dir=clean_dir, start=start, end=end)
    aggregate.run_aggregate(
        clean_dir=clean_dir,
        out_dir=aggregate_dir,
        start=start,
        end=end,
        bin_width_days=bin_width_days,
        min_total_mentions=min_total_mentions,
    )
    score.run_score(aggregate_dir=aggregate_dir, out_dir=score_dir)
    return report.run_report(
        aggregate_dir=aggregate_dir,
        score_dir=score_dir,
        out_dir=out_dir,
        top_n=top_n,
    )
