from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import erf, exp, log, sqrt


class OptionType(str, Enum):
    CALL = "call"
    PUT = "put"


@dataclass(frozen=True)
class MarketParams:
    spot: float
    strike: float
    rate: float
    volatility: float
    maturity: float
    notional: float = 1.0

    def validate(self) -> None:
        values = (self.spot, self.strike, self.volatility, self.maturity, self.notional)
        if any(value <= 0.0 for value in values):
            raise ValueError("spot, strike, volatility, maturity, and notional must be positive")
        if not -1.0 < self.rate < 10.0:
            raise ValueError("rate must be between -1 and 10")


def _standard_normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + erf(value / sqrt(2.0)))


def terminal_payoff(terminal_spot: float, strike: float, option_type: OptionType) -> float:
    intrinsic = terminal_spot - strike if option_type is OptionType.CALL else strike - terminal_spot
    return max(intrinsic, 0.0)


def terminal_payoffs(terminal_spots, strike: float, option_type: OptionType):
    import numpy as np

    spots = np.asarray(terminal_spots, dtype=float)
    if option_type is OptionType.CALL:
        return np.maximum(spots - strike, 0.0)
    if option_type is OptionType.PUT:
        return np.maximum(strike - spots, 0.0)
    raise ValueError(f"unsupported option type: {option_type}")


def black_scholes_price(params: MarketParams, option_type: OptionType) -> float:
    params.validate()
    denominator = params.volatility * sqrt(params.maturity)
    d1 = (
        log(params.spot / params.strike)
        + (params.rate + 0.5 * params.volatility**2) * params.maturity
    ) / denominator
    d2 = d1 - denominator
    discount = exp(-params.rate * params.maturity)
    if option_type is OptionType.CALL:
        value = params.spot * _standard_normal_cdf(
            d1
        ) - params.strike * discount * _standard_normal_cdf(d2)
    elif option_type is OptionType.PUT:
        value = params.strike * discount * _standard_normal_cdf(
            -d2
        ) - params.spot * _standard_normal_cdf(-d1)
    else:
        raise ValueError(f"unsupported option type: {option_type}")
    return params.notional * value


def simulate_terminal_spots(
    params: MarketParams, paths: int, seed: int | None = 7, antithetic: bool = True
):
    import numpy as np

    params.validate()
    if paths < 2:
        raise ValueError("paths must be at least 2")
    rng = np.random.default_rng(seed)
    draws = rng.standard_normal(paths)
    if antithetic:
        half = (paths + 1) // 2
        base = rng.standard_normal(half)
        draws = np.concatenate((base, -base))[:paths]
    drift = (params.rate - 0.5 * params.volatility**2) * params.maturity
    diffusion = params.volatility * sqrt(params.maturity) * draws
    return params.spot * np.exp(drift + diffusion)


def discounted_payoffs(
    params: MarketParams,
    option_type: OptionType,
    paths: int,
    seed: int | None = 7,
    antithetic: bool = True,
):
    terminal_spots = simulate_terminal_spots(params, paths, seed, antithetic)
    return (
        exp(-params.rate * params.maturity)
        * params.notional
        * terminal_payoffs(terminal_spots, params.strike, option_type)
    )
