# Enbit Research Notes

The reference image describes a Quantum Finance Scenario Engine: a research environment for quantum amplitude estimation and Monte Carlo alternatives on derivative pricing and risk estimation, with transparent resource estimates and classical baselines.

## Verified sources

1. The APS abstract for Rebentrost, Gupt, and Bromley, published in Physical Review A in 2018, states that quantum algorithms can prepare relevant probability distributions in superposition, implement payoff functions as quantum circuits, extract derivative prices through measurements, and apply amplitude estimation for a quadratic speedup in the number of steps needed for a high-confidence estimate. Source: https://journals.aps.org/pra/abstract/10.1103/PhysRevA.98.022321

2. The Qiskit Finance amplitude-estimation tutorial defines an operator A that prepares a state with a target amplitude, describes amplitude estimation as estimating that amplitude, and presents the Grover operator plus canonical, iterative, maximum-likelihood, and faster amplitude-estimation variants. It also notes that canonical phase-estimation-based amplitude estimation uses larger and more expensive circuits than alternatives. Source: https://qiskit-community.github.io/qiskit-finance/tutorials/00_amplitude_estimation.html

## Architecture implications

Enbit will be a dependency-light Python research package with deterministic classical baselines, a simulator-backed amplitude-estimation abstraction, explicit payoff normalization, confidence intervals, and resource estimates. The quantum layer will expose an idealized amplitude-estimation estimator that can be used without a quantum SDK, while optional integrations can be added later. Results will distinguish theoretical query complexity from actual classical simulation work and circuit-level estimates.
