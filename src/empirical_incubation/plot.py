"""Per-trajectory plotting — renders a single time-series as a vector PDF.

x-axis: time (step index)
y-axis: frequency / mention count

Optional `Features` overlay shades the early / dormancy / late phase regions
and marks the early bump and main peak.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from .detect import Features


def plot_trajectory(
    x: np.ndarray,
    path: Path,
    *,
    features: Features | None = None,
    title: str | None = None,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 3.2))
    t = np.arange(len(x))
    ax.plot(t, x, color="#1a1a1a", linewidth=1.0)

    if features is not None:
        ax.axvspan(*features.early_window, color="#4caf50", alpha=0.12, label="early")
        ax.axvspan(*features.middle_window, color="#9e9e9e", alpha=0.12, label="dormancy")
        ax.axvspan(*features.late_window, color="#e53935", alpha=0.12, label="late")
        ax.scatter(
            [features.early_peak_time, features.main_peak_time],
            [features.early_peak_amplitude, features.main_peak_amplitude],
            color=["#2e7d32", "#c62828"],
            zorder=3,
            s=25,
        )
        ax.legend(loc="upper left", fontsize=8, frameon=False)

    ax.set_xlabel("time")
    ax.set_ylabel("frequency")
    if title:
        ax.set_title(title)
    ax.set_xlim(0, len(x))
    ax.set_ylim(bottom=0)

    fig.tight_layout()
    fig.savefig(path, format="pdf")
    plt.close(fig)
