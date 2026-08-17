from __future__ import annotations

import json
from dataclasses import asdict

from enbit import MarketParams, OptionType, benchmark_option, estimate_risk, price_monte_carlo

params = MarketParams(
    spot=100.0,
    strike=100.0,
    rate=0.05,
    volatility=0.2,
    maturity=1.0,
)

pricing = price_monte_carlo(params, OptionType.CALL, paths=50_000, seed=7)
risk = estimate_risk(params, OptionType.CALL, scenarios=50_000, confidence=0.95, seed=7)
benchmark = benchmark_option(params, OptionType.CALL, target_error=0.02, monte_carlo_paths=50_000)

payload = {
    "pricing": asdict(pricing),
    "risk": asdict(risk),
    "benchmark": benchmark.as_dict(),
}

print(json.dumps(payload, indent=2, sort_keys=True))
