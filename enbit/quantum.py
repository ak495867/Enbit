from __future__ import annotations

from dataclasses import dataclass
from math import asin, ceil, log2, pi, sin, sqrt

import numpy as np


@dataclass(frozen=True)
class ResourceEstimate:
    algorithm: str
    target_error: float
    confidence: float
    logical_qubits: int
    oracle_calls: int
    grover_iterations: int
    circuit_depth_proxy: int
    classical_samples: int
    assumptions: tuple[str, ...]


@dataclass(frozen=True)
class AmplitudeEstimationResult:
    method: str
    probability: float
    estimate: float
    absolute_error: float
    target_error: float
    confidence: float
    phase_bits: int
    resource_estimate: ResourceEstimate


def _validate_probability(probability: float) -> None:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be between 0 and 1")


def _validate_target_error(target_error: float) -> None:
    if not 0.0 < target_error < 1.0:
        raise ValueError("target_error must be between 0 and 1")


def _phase_grid_estimate(probability: float, phase_bits: int) -> float:
    grid_size = 2**phase_bits
    phase = asin(sqrt(probability)) / pi
    phase_index = int(round(phase * grid_size))
    phase_index = min(max(phase_index, 0), grid_size)
    return sin(pi * phase_index / grid_size) ** 2


def estimate_resources(
    target_error: float,
    confidence: float = 0.95,
    payoff_qubits: int = 8,
    state_qubits: int = 10,
    method: str = "iterative",
) -> ResourceEstimate:
    _validate_target_error(target_error)
    if not 0.5 < confidence < 1.0:
        raise ValueError("confidence must be strictly between 0.5 and 1.0")
    if payoff_qubits < 1 or state_qubits < 1:
        raise ValueError("qubit counts must be positive")
    phase_bits = max(1, ceil(log2(pi / (2.0 * target_error))))
    grover_iterations = 2 ** (phase_bits - 1)
    if method == "canonical":
        oracle_calls = 2 * (2**phase_bits - 1) + 1
        depth_proxy = oracle_calls * (state_qubits + payoff_qubits + 4)
        assumptions = (
            "ideal phase-estimation-style amplitude estimation",
            "one state-preparation and payoff oracle per Grover application",
            "logical gates are represented by a depth proxy",
        )
    elif method == "iterative":
        oracle_calls = max(1, ceil(pi / (2.0 * target_error)))
        depth_proxy = oracle_calls * (state_qubits + payoff_qubits + 4)
        assumptions = (
            "ideal iterative amplitude estimation query scaling",
            "one state-preparation and payoff oracle per Grover application",
            "logical gates are represented by a depth proxy",
        )
    elif method == "maximum_likelihood":
        oracle_calls = max(1, ceil(pi / (2.0 * target_error)))
        depth_proxy = oracle_calls * (state_qubits + payoff_qubits + 4)
        assumptions = (
            "ideal maximum-likelihood amplitude estimation query scaling",
            "measurement schedule is abstracted into an oracle-call count",
            "logical gates are represented by a depth proxy",
        )
    else:
        raise ValueError("method must be canonical, iterative, or maximum_likelihood")
    return ResourceEstimate(
        algorithm=method,
        target_error=target_error,
        confidence=confidence,
        logical_qubits=state_qubits + payoff_qubits + 2,
        oracle_calls=oracle_calls,
        grover_iterations=grover_iterations,
        circuit_depth_proxy=depth_proxy,
        classical_samples=0,
        assumptions=assumptions,
    )


def estimate_amplitude(
    probability: float,
    target_error: float = 0.02,
    confidence: float = 0.95,
    phase_bits: int | None = None,
    method: str = "iterative",
    payoff_qubits: int = 8,
    state_qubits: int = 10,
) -> AmplitudeEstimationResult:
    _validate_probability(probability)
    _validate_target_error(target_error)
    if phase_bits is None:
        phase_bits = max(1, ceil(log2(pi / (2.0 * target_error))))
    if phase_bits < 1:
        raise ValueError("phase_bits must be positive")
    estimate = _phase_grid_estimate(probability, phase_bits)
    resources = estimate_resources(target_error, confidence, payoff_qubits, state_qubits, method)
    return AmplitudeEstimationResult(
        method=method,
        probability=probability,
        estimate=estimate,
        absolute_error=abs(estimate - probability),
        target_error=target_error,
        confidence=confidence,
        phase_bits=phase_bits,
        resource_estimate=resources,
    )


def estimate_bounded_expectation(
    samples,
    target_error: float = 0.02,
    confidence: float = 0.95,
    payoff_scale: float | None = None,
    method: str = "iterative",
    payoff_qubits: int = 8,
    state_qubits: int = 10,
) -> AmplitudeEstimationResult:
    values = np.asarray(samples, dtype=float)
    if values.ndim != 1 or len(values) == 0:
        raise ValueError("samples must be a non-empty one-dimensional sequence")
    if not np.all(np.isfinite(values)):
        raise ValueError("samples must contain only finite values")
    scale = float(np.max(values) if payoff_scale is None else payoff_scale)
    if scale <= 0.0:
        raise ValueError("payoff_scale must be positive")
    if np.min(values) < 0.0 or np.max(values) > scale:
        raise ValueError("samples must lie in the interval [0, payoff_scale]")
    probability = float(np.mean(values / scale))
    result = estimate_amplitude(
        probability, target_error, confidence, None, method, payoff_qubits, state_qubits
    )
    estimate = result.estimate * scale
    resources = ResourceEstimate(
        algorithm=result.resource_estimate.algorithm,
        target_error=target_error * scale,
        confidence=confidence,
        logical_qubits=result.resource_estimate.logical_qubits,
        oracle_calls=result.resource_estimate.oracle_calls,
        grover_iterations=result.resource_estimate.grover_iterations,
        circuit_depth_proxy=result.resource_estimate.circuit_depth_proxy,
        classical_samples=len(values),
        assumptions=result.resource_estimate.assumptions
        + ("payoff values are linearly normalized into [0, 1]",),
    )
    return AmplitudeEstimationResult(
        method=method,
        probability=probability,
        estimate=estimate,
        absolute_error=abs(estimate - float(np.mean(values))),
        target_error=target_error * scale,
        confidence=confidence,
        phase_bits=result.phase_bits,
        resource_estimate=resources,
    )
