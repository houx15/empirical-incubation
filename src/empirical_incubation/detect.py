"""Three-phase sleeping-beauty detector.

A trajectory qualifies iff:
  1. The early window (first third) has a peak clearly above the noise floor
     (early bump exists).
  2. The late window (last third) has a peak that dominates the early peak by
     `min_amplitude_ratio` (main peak dominates).
  3. The middle window (dormancy) stays well below the main peak — the signal
     genuinely went quiet before exploding.
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Features:
    n_steps: int
    early_window: tuple[int, int]
    middle_window: tuple[int, int]
    late_window: tuple[int, int]
    early_peak_time: int
    early_peak_amplitude: float
    middle_peak_amplitude: float
    main_peak_time: int
    main_peak_amplitude: float
    amplitude_ratio: float
    dormancy_duration: int
    gap_ratio: float


def extract_features(x: np.ndarray) -> Features:
    n = len(x)
    third = n // 3
    early_window = (0, third)
    middle_window = (third, 2 * third)
    late_window = (2 * third, n)

    early = x[early_window[0] : early_window[1]]
    middle = x[middle_window[0] : middle_window[1]]
    late = x[late_window[0] : late_window[1]]

    early_peak_amp = float(early.max())
    main_peak_amp = float(late.max())

    ratio = main_peak_amp / early_peak_amp if early_peak_amp > 0 else float("inf")

    return Features(
        n_steps=n,
        early_window=early_window,
        middle_window=middle_window,
        late_window=late_window,
        early_peak_time=int(early_window[0] + early.argmax()),
        early_peak_amplitude=early_peak_amp,
        middle_peak_amplitude=float(middle.max()),
        main_peak_time=int(late_window[0] + late.argmax()),
        main_peak_amplitude=main_peak_amp,
        amplitude_ratio=ratio,
        dormancy_duration=middle_window[1] - middle_window[0],
        gap_ratio=(middle_window[1] - middle_window[0]) / n,
    )


def is_sleeping_beauty(
    x: np.ndarray,
    *,
    min_early_amplitude: float = 0.3,
    min_amplitude_ratio: float = 3.0,
    max_middle_fraction_of_main: float = 0.3,
) -> bool:
    f = extract_features(x)

    if f.early_peak_amplitude < min_early_amplitude:
        return False
    if f.main_peak_amplitude < min_amplitude_ratio * f.early_peak_amplitude:
        return False
    if f.middle_peak_amplitude >= max_middle_fraction_of_main * f.main_peak_amplitude:
        return False
    return True
