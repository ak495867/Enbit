from __future__ import annotations

from dataclasses import dataclass
from math import exp

import numpy as np

from .pricing import (
    MarketParams,
    OptionType,
    black_scholes_price,
    simulate_terminal_spots,
    terminal_payoffs,
)


@dataclass(frozen=True)
class RiskResult:
    option_type: str
    scenarios: int
    horizon: float
    confidence: float
    initial_value: float
    expected_loss: float
    value_at_risk: float
    conditional_value_at_risk: float
    loss_quantile: float
    loss_mean: float
    loss_standard_deviation: float
    worst_loss: float
    best_loss: float


def _validate_confidence(confidence: float) -> None:
    if not 0.5 < confidence < 1.0:
        raise ValueError("confidence must be strictly between 0.5 and 1.0")


def option_loss_scenarios(
    params: MarketParams,
    option_type: OptionType,
    scenarios: int = 100_000,
    seed: int | None = 7,
    horizon: float | None = None,
    antithetic: bool = True,
):
    if scenarios < 2:
        raise ValueError("scenarios must be at least 2")
    horizon_value = params.maturity if horizon is None else horizon
    if horizon_value <= 0.0 or horizon_value > params.maturity:
        raise ValueError("horizon must be positive and no greater than maturity")
    if horizon_value == params.maturity:
        horizon_params = params
    else:
        horizon_params = MarketParams(
            spot=params.spot,
            strike=params.strike,
            rate=params.rate,
            volatility=params.volatility,
            maturity=horizon_value,
            notional=params.notional,
        )
    initial_value = black_scholes_price(params, option_type)
    terminal_spots = simulate_terminal_spots(horizon_params, scenarios, seed, antithetic)
    discounted_payoff = (
        exp(-params.rate * horizon_value)
        * params.notional
        * terminal_payoffs(terminal_spots, params.strike, option_type)
    )
    return initial_value - discounted_payoff


def estimate_risk(
    params: MarketParams,
    option_type: OptionType,
    scenarios: int = 100_000,
    seed: int | None = 7,
    confidence: float = 0.95,
    horizon: float | None = None,
    antithetic: bool = True,
) -> RiskResult:
    _validate_confidence(confidence)
    losses = option_loss_scenarios(params, option_type, scenarios, seed, horizon, antithetic)
    quantile = float(np.quantile(losses, confidence))
    tail = losses[losses >= quantile]
    cvar = float(np.mean(tail)) if len(tail) else quantile
    return RiskResult(
        option_type=option_type.value,
        scenarios=scenarios,
        horizon=params.maturity if horizon is None else horizon,
        confidence=confidence,
        initial_value=black_scholes_price(params, option_type),
        expected_loss=float(np.mean(losses)),
        value_at_risk=quantile,
        conditional_value_at_risk=cvar,
        loss_quantile=quantile,
        loss_mean=float(np.mean(losses)),
        loss_standard_deviation=float(np.std(losses, ddof=1)),
        worst_loss=float(np.max(losses)),
        best_loss=float(np.min(losses)),
    )
