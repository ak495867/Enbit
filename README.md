# Enbit

Enbit is a Python research environment for comparing quantum amplitude estimation with classical Monte Carlo alternatives for derivative pricing and risk estimation. It is designed around transparent assumptions, reproducible random seeds, analytical baselines, confidence intervals, and explicit resource accounting.

The project follows the scenario described in the reference brief: a quantum finance scenario engine that evaluates quantum amplitude-estimation workflows alongside Monte Carlo methods on derivative pricing and risk problems.

## Research scope

Enbit currently supports European call and put options under the Black–Scholes model. It provides the following layers:

| Layer | Purpose | Primary output |
|---|---|---|
| Analytical baseline | Compute a closed-form reference value | Black–Scholes price |
| Classical baseline | Estimate discounted payoff expectations with reproducible Monte Carlo paths | Price, standard error, confidence interval |
| Risk engine | Convert scenario payoffs into losses | Expected loss, VaR, CVaR, distribution summaries |
| Amplitude-estimation simulator | Map a bounded expectation into an idealized amplitude-estimation workflow | Estimate, target error, logical qubits, oracle calls, depth proxy |
| Benchmark report | Put the approaches into one comparable result | Structured rows suitable for JSON or notebooks |

Quantum amplitude estimation is modeled as an algorithmic research abstraction rather than a hardware execution layer. The implementation makes the payoff normalization, target error, confidence, oracle-call count, logical-qubit count, and circuit-depth proxy visible. It does not claim that the idealized resource counts include state-preparation synthesis, fault-tolerant overhead, noise, error correction, or hardware calibration.

The research framing follows the derivative-pricing construction in Rebentrost, Gupt, and Bromley, which describes preparing probability distributions in superposition, implementing payoff functions, and extracting prices through amplitude estimation [1]. The Qiskit Finance tutorial provides the amplitude-estimation notation and discusses canonical and iterative variants [2].

## Installation

Enbit requires Python 3.10 or newer.

```bash
git clone https://github.com/ak495867/Enbit.git
cd Enbit
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Command-line usage

Analytical and Monte Carlo pricing:

```bash
enbit price --spot 100 --strike 100 --rate 0.05 --volatility 0.2 --maturity 1 --option call --paths 100000 --seed 7
```

Risk estimation:

```bash
enbit risk --spot 100 --strike 100 --rate 0.05 --volatility 0.2 --maturity 1 --option call --scenarios 100000 --confidence 0.95 --seed 7
```

Quantum-versus-classical benchmark report:

```bash
enbit benchmark --spot 100 --strike 100 --rate 0.05 --volatility 0.2 --maturity 1 --option call --paths 100000 --target-error 0.02 --quantum-method iterative --seed 7
```

Every command emits JSON so that results can be saved, compared, or consumed by a notebook or pipeline.

## Python usage

```python
from enbit import MarketParams, OptionType, benchmark_option, estimate_risk, price_monte_carlo

params = MarketParams(spot=100.0, strike=100.0, rate=0.05, volatility=0.2, maturity=1.0)
price = price_monte_carlo(params, OptionType.CALL, paths=100_000, seed=7)
risk = estimate_risk(params, OptionType.CALL, scenarios=100_000, confidence=0.95, seed=7)
report = benchmark_option(params, OptionType.CALL, target_error=0.02, monte_carlo_paths=100_000)
```

## Design principles

The codebase uses a small dependency surface centered on NumPy. Public functions validate their numerical inputs and return typed dataclasses. Random experiments accept explicit seeds. Classical results retain the analytical Black–Scholes reference and sample variance. Quantum results separate an amplitude estimate from its resource estimate so that algorithmic claims are not confused with hardware performance.

The risk engine defines loss as initial option value minus discounted scenario payoff. VaR is the selected loss quantile and CVaR is the mean of losses at or beyond that quantile. This is a research convention for the included one-period scenario engine, not a production risk policy.

## Testing

```bash
pytest
ruff check .
```

## Repository layout

```text
Enbit/
├── enbit/
│   ├── benchmark.py
│   ├── cli.py
│   ├── monte_carlo.py
│   ├── pricing.py
│   ├── quantum.py
│   └── risk.py
├── examples/
├── tests/
├── docs/
├── pyproject.toml
├── LICENSE
└── README.md
```

## Limitations and next steps

Enbit is intentionally a transparent research baseline. It does not include a quantum SDK, a noisy backend, amplitude-loading circuit synthesis, exotic derivatives, stochastic volatility, calibration to market data, portfolio aggregation, or production model governance. A natural next step is to add optional Qiskit circuit adapters while retaining the current SDK-independent reference implementation and its explicit resource assumptions.

## References

[1]: https://journals.aps.org/pra/abstract/10.1103/PhysRevA.98.022321 "Quantum computational finance: Monte Carlo pricing of financial derivatives"

[2]: https://qiskit-community.github.io/qiskit-finance/tutorials/00_amplitude_estimation.html "Quantum Amplitude Estimation - Qiskit Finance"
