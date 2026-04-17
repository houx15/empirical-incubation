"""Synthetic trajectory generators used as TDD fixtures for detection & plotting."""

import numpy as np


def sleeping_beauty(n_steps: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.arange(n_steps)
    early = 1.0 * np.exp(-0.5 * ((t - 0.1 * n_steps) / (0.02 * n_steps)) ** 2)
    main = 5.0 * np.exp(-0.5 * ((t - 0.8 * n_steps) / (0.04 * n_steps)) ** 2)
    noise = 0.05 * rng.standard_normal(n_steps)
    return np.clip(early + main + noise, 0.0, None)


def steady_trender(n_steps: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.arange(n_steps) / n_steps
    ramp = 0.2 + 4.0 * t
    noise = 0.1 * rng.standard_normal(n_steps)
    return np.clip(ramp + noise, 0.0, None)


def one_shot_burst(n_steps: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.arange(n_steps)
    burst = 5.0 * np.exp(-0.5 * ((t - 0.7 * n_steps) / (0.04 * n_steps)) ** 2)
    noise = 0.05 * rng.standard_normal(n_steps)
    return np.clip(burst + noise, 0.0, None)


def pure_noise(n_steps: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    baseline = 0.3
    noise = 0.15 * rng.standard_normal(n_steps)
    return np.clip(baseline + noise, 0.0, None)
