"""Dataset-level sleeping-beauty report.

Produces `report.md` under a target directory, along with:
  - plots/<id>.pdf for each qualifying record
  - hist_amplitude_ratio.pdf, hist_gap_ratio.pdf — feature distributions
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from .detect import Features
from .plot import plot_trajectory


@dataclass
class Record:
    id: str
    trajectory: np.ndarray
    features: Features
    qualified: bool


def generate_report(
    records: list[Record],
    out_dir: Path,
    *,
    title: str = "Sleeping-Beauty Detection Report",
    top_n: int = 20,
    sanity_n: int = 3,
) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(exist_ok=True)

    qualified = [r for r in records if r.qualified]
    rejected = [r for r in records if not r.qualified]

    for r in qualified:
        plot_trajectory(
            r.trajectory,
            plots_dir / f"{r.id}.pdf",
            features=r.features,
            title=r.id,
        )

    _render_histogram(
        [r.features.amplitude_ratio for r in records],
        out_dir / "hist_amplitude_ratio.pdf",
        xlabel="amplitude_ratio (main / early)",
    )
    _render_histogram(
        [r.features.gap_ratio for r in records],
        out_dir / "hist_gap_ratio.pdf",
        xlabel="gap_ratio (dormancy / total)",
    )

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total records: {len(records)}")
    lines.append(f"- Qualified (sleeping beauty): {len(qualified)}")
    rate = (len(qualified) / len(records) * 100.0) if records else 0.0
    lines.append(f"- Qualification rate: {rate:.2f}%")
    lines.append("")
    lines.append("### Distributions")
    lines.append("")
    lines.append("- [amplitude_ratio histogram](hist_amplitude_ratio.pdf)")
    lines.append("- [gap_ratio histogram](hist_gap_ratio.pdf)")
    lines.append("")

    lines.append("## Top sleeping beauties")
    lines.append("")
    top = sorted(qualified, key=lambda r: r.features.amplitude_ratio, reverse=True)[:top_n]
    if top:
        lines.append("| id | main_peak | early_peak | amplitude_ratio | awakening_time | plot |")
        lines.append("| --- | ---: | ---: | ---: | ---: | --- |")
        for r in top:
            lines.append(
                f"| {r.id} "
                f"| {r.features.main_peak_amplitude:.3f} "
                f"| {r.features.early_peak_amplitude:.3f} "
                f"| {r.features.amplitude_ratio:.2f} "
                f"| {r.features.main_peak_time} "
                f"| [pdf](plots/{r.id}.pdf) |"
            )
    else:
        lines.append("_No records qualified._")
    lines.append("")

    lines.append("## Sanity check")
    lines.append("")
    lines.append("A sample of rejected records (to eyeball false negatives):")
    lines.append("")
    if rejected:
        for r in rejected[:sanity_n]:
            lines.append(
                f"- **{r.id}** — amplitude_ratio={r.features.amplitude_ratio:.2f}, "
                f"early_peak={r.features.early_peak_amplitude:.3f}, "
                f"main_peak={r.features.main_peak_amplitude:.3f}"
            )
    else:
        lines.append("_(none)_")
    lines.append("")

    report_path = out_dir / "report.md"
    report_path.write_text("\n".join(lines))
    return report_path


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
