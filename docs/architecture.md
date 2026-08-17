# Enbit Architecture

## Overview

Enbit separates the scenario engine into four computational layers. The pricing layer defines market inputs and payoff functions. The Monte Carlo layer simulates risk-neutral terminal prices and summarizes sampling uncertainty. The risk layer transforms discounted payoffs into losses and estimates VaR and CVaR. The quantum layer exposes a simulator-independent amplitude-estimation abstraction and tracks resource assumptions explicitly.

## Data flow

```text
MarketParams
    |
    +--> Black-Scholes analytical baseline
    |
    +--> Risk-neutral terminal spot simulation
              |
              +--> discounted payoff samples --> Monte Carlo estimate
              |                              |
              |                              +--> bounded normalization --> amplitude estimate
              |
              +--> initial value minus discounted payoff --> loss distribution --> VaR and CVaR
```

## Quantum abstraction

A payoff sample `X` is mapped to a bounded variable `Y = X / B` with `0 <= Y <= 1`, where `B` is the declared payoff scale. The expectation of `X` is then represented as `B E[Y]`. Enbit estimates `E[Y]` through an idealized amplitude grid and reports the scaled result.

The current implementation does not synthesize a state-preparation circuit or invoke a quantum backend. Its purpose is to make the numerical interface and resource accounting testable before an SDK-backed adapter is introduced.

## Resource accounting

| Quantity | Meaning |
|---|---|
| Logical qubits | State, payoff, and control registers under a compact abstract register model |
| Oracle calls | State-preparation and payoff-oracle query proxy |
| Grover iterations | Iteration-scale proxy derived from phase resolution |
| Circuit depth proxy | Oracle calls multiplied by register and reflection overhead |
| Classical samples | Number of payoff samples used to estimate the expectation before the quantum abstraction is applied |

The resource estimates are intentionally labeled as proxies. They exclude hardware-specific transpilation, synthesis, connectivity, noise, error correction, measurement mitigation, and data loading costs.

## Risk convention

For each scenario, Enbit defines the loss as

`loss = initial_option_value - discounted_scenario_payoff`.

VaR at confidence `c` is the `c` quantile of losses. CVaR is the arithmetic mean of the losses greater than or equal to that quantile. This convention is useful for a one-period research scenario and should be replaced or extended when modeling a production risk horizon, hedging, or a multi-instrument portfolio.
