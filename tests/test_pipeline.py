"""End-to-end pipeline test: raw quote files -> detection report."""

import gzip
from datetime import datetime
from pathlib import Path

from empirical_incubation import pipeline


def _write_quotes(path: Path, lines: list[str]) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write("\n".join(lines))


def test_run_analysis_produces_report(tmp_path: Path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    lines: list[str] = []
    # phrase1: early bump (days 1-2) -> dormancy -> late burst (days 28-29)
    for ts in ["2008-09-01 10:00:00", "2008-09-01 11:00:00", "2008-09-02 12:00:00"]:
        lines += [f"P\thttp://a.com", f"T\t{ts}", "Q\tphrase one", ""]
    for day in (28, 29):
        for hr in range(6):
            lines += [
                f"P\thttp://a.com",
                f"T\t2008-09-{day:02d} {hr:02d}:00:00",
                "Q\tphrase one",
                "",
            ]
    # phrase2: flat background — not a sleeping beauty
    for day in range(1, 30):
        lines += [
            "P\thttp://b.com",
            f"T\t2008-09-{day:02d} 12:00:00",
            "Q\tphrase two",
            "",
        ]

    _write_quotes(raw_dir / "quotes_2008-09.txt.gz", lines)

    out_dir = tmp_path / "out"
    report_path = pipeline.run_analysis(
        raw_dir=raw_dir,
        out_dir=out_dir,
        start=datetime(2008, 9, 1),
        end=datetime(2008, 9, 30),
        bin_width_days=1,
    )

    assert report_path == out_dir / "report.md"
    content = report_path.read_text()
    assert "# Sleeping-Beauty Detection Report" in content
    assert "## Summary" in content
    assert "Total phrases scored:" in content
