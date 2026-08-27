import numpy as np
import pytest

from enbit import (
    MarketParams,
    OptionType,
    benchmark_option,
    black_scholes_price,
    estimate_amplitude,
    estimate_bounded_expectation,
    estimate_risk,
    price_monte_carlo,
    terminal_payoff,
)


@pytest.fixture
def params():
    return MarketParams(100.0, 100.0, 0.05, 0.2, 1.0)


def test_call_and_put_payoffs():
    assert terminal_payoff(110.0, 100.0, OptionType.CALL) == 10.0
    assert terminal_payoff(90.0, 100.0, OptionType.PUT) == 10.0


def test_put_call_parity(params):
    call = black_scholes_price(params, OptionType.CALL)
    put = black_scholes_price(params, OptionType.PUT)
    expected = params.spot - params.strike * np.exp(-params.rate * params.maturity)
    assert call - put == pytest.approx(expected, rel=1e-12)


def test_monte_carlo_is_close_to_analytical_price(params):
    result = price_monte_carlo(params, OptionType.CALL, paths=50_000, seed=19)
    assert result.estimate == pytest.approx(result.analytical_baseline, abs=0.15)
    assert (
        result.confidence_interval.lower
        < result.estimate
        < result.confidence_interval.upper
    )


def test_amplitude_estimation_is_bounded():
    result = estimate_amplitude(0.2, target_error=0.05)
    assert 0.0 <= result.estimate <= 1.0
    assert result.resource_estimate.oracle_calls > 0


def test_bounded_expectation_preserves_scale():
    values = np.array([0.0, 2.0, 4.0, 6.0])
    result = estimate_bounded_expectation(values, target_error=0.05, payoff_scale=6.0)
    assert result.probability == pytest.approx(0.5)
    assert result.resource_estimate.classical_samples == 4
    assert 0.0 <= result.estimate <= 6.0


def test_risk_metrics_are_ordered(params):
    result = estimate_risk(params, OptionType.CALL, scenarios=20_000, seed=11)
    assert result.best_loss <= result.value_at_risk <= result.worst_loss
    assert result.value_at_risk <= result.conditional_value_at_risk


def test_benchmark_contains_all_baselines(params):
    report = benchmark_option(
        params, OptionType.CALL, target_error=0.05, monte_carlo_paths=10_000
    )
    methods = {row.method for row in report.rows}
    assert "black_scholes" in methods
    assert "monte_carlo" in methods
    assert "amplitude_estimation_iterative" in methods
