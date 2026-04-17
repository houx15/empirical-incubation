"""Command-line entry point — `empirical-incubation <subcommand> ...`.

Subcommands:
  download  Fetch SNAP MemeTracker `quotes_*.txt.gz` files listed in a manifest.
  analyze   Parse raw quote files, detect sleeping beauties, render a report.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from . import download as download_mod
from . import pipeline


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


def _cmd_analyze(args: argparse.Namespace) -> int:
    pipeline.run_analysis(
        raw_dir=args.raw_dir,
        out_dir=args.out_dir,
        start=args.start,
        end=args.end,
        bin_width_days=args.bin_width_days,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="empirical-incubation")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_dl = sub.add_parser("download", help="Download files listed in a manifest.")
    p_dl.add_argument("--manifest", type=Path, required=True)
    p_dl.add_argument("--dest-dir", type=Path, required=True)
    p_dl.set_defaults(func=_cmd_download)

    p_an = sub.add_parser("analyze", help="Run sleeping-beauty detection over raw quote files.")
    p_an.add_argument("--raw-dir", type=Path, required=True)
    p_an.add_argument("--out-dir", type=Path, required=True)
    p_an.add_argument("--start", type=_iso_date, required=True, help="YYYY-MM-DD")
    p_an.add_argument("--end", type=_iso_date, required=True, help="YYYY-MM-DD (exclusive)")
    p_an.add_argument("--bin-width-days", type=int, default=1)
    p_an.set_defaults(func=_cmd_analyze)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
