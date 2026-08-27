from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import numpy as np

from .pricing import MarketParams, OptionType, black_scholes_price, discounted_payoffs


@dataclass(frozen=True)
class ConfidenceInterval:
    estimate: float
    lower: float
    upper: float
    confidence: float
    standard_error: float


@dataclass(frozen=True)
class MonteCarloResult:
    method: str
    option_type: str
    paths: int
    seed: int | None
    estimate: float
    standard_error: float
    confidence_interval: ConfidenceInterval
    analytical_baseline: float
    absolute_error: float
    relative_error: float
    payoff_mean: float
    payoff_variance: float


def _normal_quantile(confidence: float) -> float:
    table = {
        0.90: 1.6448536269514722,
        0.95: 1.959963984540054,
        0.99: 2.5758293035489004,
    }
    rounded = round(confidence, 2)
    if rounded not in table:
        raise ValueError("confidence must be one of 0.90, 0.95, or 0.99")
    return table[rounded]


def confidence_interval(
    estimate: float, standard_error: float, confidence: float
) -> ConfidenceInterval:
    if standard_error < 0.0:
        raise ValueError("standard_error must be non-negative")
    z_value = _normal_quantile(confidence)
    margin = z_value * standard_error
    return ConfidenceInterval(
        estimate, estimate - margin, estimate + margin, confidence, standard_error
    )


def price_monte_carlo(
    params: MarketParams,
    option_type: OptionType,
    paths: int = 100_000,
    seed: int | None = 7,
    antithetic: bool = True,
    confidence: float = 0.95,
) -> MonteCarloResult:
    if paths < 2:
        raise ValueError("paths must be at least 2")
    payoffs = discounted_payoffs(params, option_type, paths, seed, antithetic)
    estimate = float(np.mean(payoffs))
    variance = float(np.var(payoffs, ddof=1))
    standard_error = sqrt(variance / paths)
    interval = confidence_interval(estimate, standard_error, confidence)
    analytical = black_scholes_price(params, option_type)
    absolute_error = abs(estimate - analytical)
    relative_error = absolute_error / abs(analytical) if analytical else absolute_error
    return MonteCarloResult(
        method="monte_carlo",
        option_type=option_type.value,
        paths=paths,
        seed=seed,
        estimate=estimate,
        standard_error=standard_error,
        confidence_interval=interval,
        analytical_baseline=analytical,
        absolute_error=absolute_error,
        relative_error=relative_error,
        payoff_mean=estimate,
        payoff_variance=variance,
    )


def convergence_curve(
    params: MarketParams,
    option_type: OptionType,
    path_counts: list[int],
    seed: int | None = 7,
    antithetic: bool = True,
):
    if not path_counts or any(paths < 2 for paths in path_counts):
        raise ValueError("path_counts must contain values of at least 2")
    return [
        price_monte_carlo(params, option_type, paths, seed, antithetic)
        for paths in path_counts
    ]
