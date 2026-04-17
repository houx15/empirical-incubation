"""Smoke tests for the CLI entry point."""

import gzip
from pathlib import Path

from empirical_incubation import cli


def test_cli_analyze_produces_report(tmp_path: Path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    out_dir = tmp_path / "out"

    lines: list[str] = []
    for day in range(1, 30):
        lines += [
            "P\thttp://example.com",
            f"T\t2008-09-{day:02d} 12:00:00",
            "Q\tphrase",
            "",
        ]
    with gzip.open(raw_dir / "quotes.txt.gz", "wt", encoding="utf-8") as f:
        f.write("\n".join(lines))

    rc = cli.main(
        [
            "analyze",
            "--raw-dir",
            str(raw_dir),
            "--out-dir",
            str(out_dir),
            "--start",
            "2008-09-01",
            "--end",
            "2008-09-30",
            "--bin-width-days",
            "1",
        ]
    )

    assert rc == 0
    assert (out_dir / "report.md").exists()


def test_cli_help_exits_cleanly(capsys):
    try:
        cli.main(["--help"])
    except SystemExit as e:
        assert e.code == 0
    captured = capsys.readouterr()
    assert "analyze" in captured.out
    assert "download" in captured.out
