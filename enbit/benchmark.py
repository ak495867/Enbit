from __future__ import annotations

from dataclasses import asdict, dataclass
from math import ceil

import numpy as np

from .monte_carlo import price_monte_carlo
from .pricing import MarketParams, OptionType, discounted_payoffs
from .quantum import estimate_bounded_expectation


@dataclass(frozen=True)
class BenchmarkRow:
    method: str
    estimate: float
    absolute_error_to_black_scholes: float
    target_error: float
    confidence: float
    oracle_calls_or_samples: int
    logical_qubits: int
    circuit_depth_proxy: int


@dataclass(frozen=True)
class BenchmarkReport:
    option_type: str
    analytical_price: float
    rows: tuple[BenchmarkRow, ...]

    def as_dict(self) -> dict:
        return {
            "option_type": self.option_type,
            "analytical_price": self.analytical_price,
            "rows": [asdict(row) for row in self.rows],
        }


def _required_mc_paths(target_error: float, confidence: float, payoff_variance: float) -> int:
    z_values = {0.90: 1.6448536269514722, 0.95: 1.959963984540054, 0.99: 2.5758293035489004}
    z_value = z_values[round(confidence, 2)]
    return max(2, ceil((z_value * np.sqrt(payoff_variance) / target_error) ** 2))


def benchmark_option(
    params: MarketParams,
    option_type: OptionType,
    target_error: float = 0.02,
    confidence: float = 0.95,
    monte_carlo_paths: int = 100_000,
    seed: int | None = 7,
    antithetic: bool = True,
    quantum_method: str = "iterative",
) -> BenchmarkReport:
    classical = price_monte_carlo(
        params, option_type, monte_carlo_paths, seed, antithetic, confidence
    )
    payoff_samples = discounted_payoffs(params, option_type, monte_carlo_paths, seed, antithetic)
    quantum = estimate_bounded_expectation(
        payoff_samples,
        target_error=target_error,
        confidence=confidence,
        payoff_scale=max(float(np.max(payoff_samples)), 1e-12),
        method=quantum_method,
    )
    required_paths = _required_mc_paths(target_error, confidence, classical.payoff_variance)
    rows = (
        BenchmarkRow(
            method="black_scholes",
            estimate=classical.analytical_baseline,
            absolute_error_to_black_scholes=0.0,
            target_error=0.0,
            confidence=1.0,
            oracle_calls_or_samples=0,
            logical_qubits=0,
            circuit_depth_proxy=0,
        ),
        BenchmarkRow(
            method="monte_carlo",
            estimate=classical.estimate,
            absolute_error_to_black_scholes=classical.absolute_error,
            target_error=target_error,
            confidence=confidence,
            oracle_calls_or_samples=monte_carlo_paths,
            logical_qubits=0,
            circuit_depth_proxy=0,
        ),
        BenchmarkRow(
            method="monte_carlo_required_sample_estimate",
            estimate=classical.analytical_baseline,
            absolute_error_to_black_scholes=0.0,
            target_error=target_error,
            confidence=confidence,
            oracle_calls_or_samples=required_paths,
            logical_qubits=0,
            circuit_depth_proxy=0,
        ),
        BenchmarkRow(
            method=f"amplitude_estimation_{quantum_method}",
            estimate=quantum.estimate,
            absolute_error_to_black_scholes=abs(quantum.estimate - classical.analytical_baseline),
            target_error=quantum.target_error,
            confidence=confidence,
            oracle_calls_or_samples=quantum.resource_estimate.oracle_calls,
            logical_qubits=quantum.resource_estimate.logical_qubits,
            circuit_depth_proxy=quantum.resource_estimate.circuit_depth_proxy,
        ),
    )
    return BenchmarkReport(option_type.value, classical.analytical_baseline, rows)
