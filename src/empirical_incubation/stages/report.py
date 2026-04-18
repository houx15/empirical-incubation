"""Stage 4 — Render the final report.

Reads features.csv + timelines.npy, keeps only qualified rows sorted by
amplitude_ratio, caps to ``top_n``, and renders PDFs for that small set only
(the whole point of staging: cheap plotting even on large corpora). Also
writes feature histograms computed over every scored row.
"""

from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from ..detect import extract_features
from ..plot import plot_trajectory


def run_report(
    *,
    aggregate_dir: Path,
    score_dir: Path,
    out_dir: Path,
    top_n: int = 100,
    sanity_n: int = 3,
    title: str = "Sleeping-Beauty Detection Report",
) -> Path:
    aggregate_dir = Path(aggregate_dir)
    score_dir = Path(score_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(exist_ok=True)

    with (score_dir / "features.csv").open() as f:
        rows = list(csv.DictReader(f))

    timelines = np.load(aggregate_dir / "timelines.npy", mmap_mode="r")

    qualified = [r for r in rows if r["qualified"] == "True"]
    qualified.sort(key=lambda r: float(r["amplitude_ratio"]), reverse=True)
    top = qualified[:top_n]

    for r in top:
        idx = int(r["phrase_idx"])
        row = timelines[idx]
        features = extract_features(row)
        plot_trajectory(
            row,
            plots_dir / f"{_safe_id(r['phrase'])}.pdf",
            features=features,
            title=r["phrase"],
        )

    _render_histogram(
        [float(r["amplitude_ratio"]) for r in rows],
        out_dir / "hist_amplitude_ratio.pdf",
        xlabel="amplitude_ratio (main / early)",
    )
    _render_histogram(
        [float(r["gap_ratio"]) for r in rows],
        out_dir / "hist_gap_ratio.pdf",
        xlabel="gap_ratio (dormancy / total)",
    )

    rejected = [r for r in rows if r["qualified"] != "True"]
    report_path = out_dir / "report.md"
    report_path.write_text(
        _render_markdown(
            rows=rows,
            qualified=qualified,
            top=top,
            rejected=rejected,
            title=title,
            sanity_n=sanity_n,
        )
    )
    print(
        f"[report] {len(qualified):,} qualified, rendered {len(top):,} plots -> {out_dir}",
        flush=True,
    )
    return report_path


def _render_markdown(
    *,
    rows: list[dict],
    qualified: list[dict],
    top: list[dict],
    rejected: list[dict],
    title: str,
    sanity_n: int,
) -> str:
    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total phrases scored: {len(rows)}")
    lines.append(f"- Qualified (sleeping beauty): {len(qualified)}")
    rate = (len(qualified) / len(rows) * 100.0) if rows else 0.0
    lines.append(f"- Qualification rate: {rate:.2f}%")
    lines.append(f"- Plots rendered (top by amplitude_ratio): {len(top)}")
    lines.append("")
    lines.append("### Distributions")
    lines.append("")
    lines.append("- [amplitude_ratio histogram](hist_amplitude_ratio.pdf)")
    lines.append("- [gap_ratio histogram](hist_gap_ratio.pdf)")
    lines.append("")

    lines.append("## Top sleeping beauties")
    lines.append("")
    if top:
        lines.append("| phrase | main_peak | early_peak | amplitude_ratio | awakening_time | plot |")
        lines.append("| --- | ---: | ---: | ---: | ---: | --- |")
        for r in top:
            safe = _safe_id(r["phrase"])
            lines.append(
                f"| {r['phrase']} "
                f"| {float(r['main_peak_amplitude']):.3f} "
                f"| {float(r['early_peak_amplitude']):.3f} "
                f"| {float(r['amplitude_ratio']):.2f} "
                f"| {r['main_peak_time']} "
                f"| [pdf](plots/{safe}.pdf) |"
            )
    else:
        lines.append("_No phrases qualified._")
    lines.append("")

    lines.append("## Sanity check")
    lines.append("")
    lines.append("A sample of rejected phrases (to eyeball false negatives):")
    lines.append("")
    if rejected:
        for r in rejected[:sanity_n]:
            lines.append(
                f"- **{r['phrase']}** — amplitude_ratio={float(r['amplitude_ratio']):.2f}, "
                f"early_peak={float(r['early_peak_amplitude']):.3f}, "
                f"main_peak={float(r['main_peak_amplitude']):.3f}"
            )
    else:
        lines.append("_(none)_")
    lines.append("")
    return "\n".join(lines)


def _render_histogram(values: list[float], path: Path, *, xlabel: str) -> None:
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    finite = [v for v in values if np.isfinite(v)]
    if finite:
        ax.hist(finite, bins=20, color="#1f77b4", edgecolor="white")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("count")
    fig.tight_layout()
    fig.savefig(path, format="pdf")
    plt.close(fig)


def _safe_id(phrase: str) -> str:
    digest = hashlib.sha1(phrase.encode("utf-8")).hexdigest()[:8]
    slug = "".join(c if c.isalnum() else "_" for c in phrase)[:40].strip("_") or "meme"
    return f"{slug}-{digest}"
