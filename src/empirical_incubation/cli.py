"""Command-line entry point — `empirical-incubation <subcommand> ...`.

Subcommands:
  download   Fetch SNAP MemeTracker `quotes_*.txt.gz` files listed in a manifest.
  clean      Stage 1: raw gz -> clean (phrase, iso_ts) tsvs.
  aggregate  Stage 2: clean tsvs -> phrases.txt + timelines.npy (dense int32).
  score      Stage 3: timelines.npy -> features.csv (one row per phrase).
  report     Stage 4: features.csv -> report.md + histograms + top-N plots.
  analyze    Run stages 1-4 end to end (convenience wrapper).
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from . import download as download_mod
from . import pipeline
from .stages import aggregate, clean, report, score


def _parse_manifest(path: Path) -> list[str]:
    urls: list[str] = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def _iso_date(s: str) -> datetime:
    return datetime.fromisoformat(s)


def _cmd_download(args: argparse.Namespace) -> int:
    urls = _parse_manifest(args.manifest)
    download_mod.download_all(urls, args.dest_dir)
    return 0


def _cmd_clean(args: argparse.Namespace) -> int:
    clean.run_clean(
        raw_dir=args.raw_dir,
        out_dir=args.out_dir,
        start=args.start,
        end=args.end,
    )
    return 0


def _cmd_aggregate(args: argparse.Namespace) -> int:
    aggregate.run_aggregate(
        clean_dir=args.clean_dir,
        out_dir=args.out_dir,
        start=args.start,
        end=args.end,
        bin_width_days=args.bin_width_days,
        min_total_mentions=args.min_total_mentions,
    )
    return 0


def _cmd_score(args: argparse.Namespace) -> int:
    score.run_score(aggregate_dir=args.aggregate_dir, out_dir=args.out_dir)
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    report.run_report(
        aggregate_dir=args.aggregate_dir,
        score_dir=args.score_dir,
        out_dir=args.out_dir,
        top_n=args.top_n,
    )
    return 0


def _cmd_analyze(args: argparse.Namespace) -> int:
    pipeline.run_analysis(
        raw_dir=args.raw_dir,
        out_dir=args.out_dir,
        start=args.start,
        end=args.end,
        bin_width_days=args.bin_width_days,
        min_total_mentions=args.min_total_mentions,
        top_n=args.top_n,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="empirical-incubation")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_dl = sub.add_parser("download", help="Download files listed in a manifest.")
    p_dl.add_argument("--manifest", type=Path, required=True)
    p_dl.add_argument("--dest-dir", type=Path, required=True)
    p_dl.set_defaults(func=_cmd_download)

    p_cl = sub.add_parser("clean", help="Stage 1: raw gz -> clean tsvs.")
    p_cl.add_argument("--raw-dir", type=Path, required=True)
    p_cl.add_argument("--out-dir", type=Path, required=True)
    p_cl.add_argument("--start", type=_iso_date, required=True)
    p_cl.add_argument("--end", type=_iso_date, required=True)
    p_cl.set_defaults(func=_cmd_clean)

    p_ag = sub.add_parser("aggregate", help="Stage 2: clean tsvs -> timelines.npy.")
    p_ag.add_argument("--clean-dir", type=Path, required=True)
    p_ag.add_argument("--out-dir", type=Path, required=True)
    p_ag.add_argument("--start", type=_iso_date, required=True)
    p_ag.add_argument("--end", type=_iso_date, required=True)
    p_ag.add_argument("--bin-width-days", type=int, default=1)
    p_ag.add_argument("--min-total-mentions", type=int, default=5)
    p_ag.set_defaults(func=_cmd_aggregate)

    p_sc = sub.add_parser("score", help="Stage 3: timelines.npy -> features.csv.")
    p_sc.add_argument("--aggregate-dir", type=Path, required=True)
    p_sc.add_argument("--out-dir", type=Path, required=True)
    p_sc.set_defaults(func=_cmd_score)

    p_rp = sub.add_parser("report", help="Stage 4: features.csv -> report.md + plots.")
    p_rp.add_argument("--aggregate-dir", type=Path, required=True)
    p_rp.add_argument("--score-dir", type=Path, required=True)
    p_rp.add_argument("--out-dir", type=Path, required=True)
    p_rp.add_argument("--top-n", type=int, default=100)
    p_rp.set_defaults(func=_cmd_report)

    p_an = sub.add_parser("analyze", help="Run stages 1-4 end to end.")
    p_an.add_argument("--raw-dir", type=Path, required=True)
    p_an.add_argument("--out-dir", type=Path, required=True)
    p_an.add_argument("--start", type=_iso_date, required=True)
    p_an.add_argument("--end", type=_iso_date, required=True)
    p_an.add_argument("--bin-width-days", type=int, default=1)
    p_an.add_argument("--min-total-mentions", type=int, default=5)
    p_an.add_argument("--top-n", type=int, default=100)
    p_an.set_defaults(func=_cmd_analyze)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
