from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .benchmark import benchmark_option
from .monte_carlo import price_monte_carlo
from .pricing import MarketParams, OptionType, black_scholes_price
from .risk import estimate_risk


def _option_type(value: str) -> OptionType:
    try:
        return OptionType(value.lower())
    except ValueError as error:
        raise argparse.ArgumentTypeError("option must be call or put") from error


def _add_market_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--spot", type=float, default=100.0)
    parser.add_argument("--strike", type=float, default=100.0)
    parser.add_argument("--rate", type=float, default=0.05)
    parser.add_argument("--volatility", type=float, default=0.2)
    parser.add_argument("--maturity", type=float, default=1.0)
    parser.add_argument("--notional", type=float, default=1.0)
    parser.add_argument("--option", type=_option_type, default=OptionType.CALL)


def _params(args: argparse.Namespace) -> MarketParams:
    return MarketParams(
        args.spot, args.strike, args.rate, args.volatility, args.maturity, args.notional
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="enbit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    price_parser = subparsers.add_parser("price")
    _add_market_arguments(price_parser)
    price_parser.add_argument("--paths", type=int, default=100_000)
    price_parser.add_argument("--seed", type=int, default=7)
    price_parser.add_argument("--confidence", type=float, default=0.95)
    price_parser.add_argument("--no-antithetic", action="store_true")

    risk_parser = subparsers.add_parser("risk")
    _add_market_arguments(risk_parser)
    risk_parser.add_argument("--scenarios", type=int, default=100_000)
    risk_parser.add_argument("--seed", type=int, default=7)
    risk_parser.add_argument("--confidence", type=float, default=0.95)
    risk_parser.add_argument("--horizon", type=float, default=None)
    risk_parser.add_argument("--no-antithetic", action="store_true")

    benchmark_parser = subparsers.add_parser("benchmark")
    _add_market_arguments(benchmark_parser)
    benchmark_parser.add_argument("--paths", type=int, default=100_000)
    benchmark_parser.add_argument("--seed", type=int, default=7)
    benchmark_parser.add_argument("--confidence", type=float, default=0.95)
    benchmark_parser.add_argument("--target-error", type=float, default=0.02)
    benchmark_parser.add_argument(
        "--quantum-method",
        choices=["canonical", "iterative", "maximum_likelihood"],
        default="iterative",
    )
    benchmark_parser.add_argument("--no-antithetic", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    params = _params(args)
    if args.command == "price":
        result = {
            "analytical": black_scholes_price(params, args.option),
            "monte_carlo": asdict(
                price_monte_carlo(
                    params,
                    args.option,
                    args.paths,
                    args.seed,
                    not args.no_antithetic,
                    args.confidence,
                )
            ),
        }
    elif args.command == "risk":
        result = asdict(
            estimate_risk(
                params,
                args.option,
                args.scenarios,
                args.seed,
                args.confidence,
                args.horizon,
                not args.no_antithetic,
            )
        )
    else:
        result = benchmark_option(
            params,
            args.option,
            args.target_error,
            args.confidence,
            args.paths,
            args.seed,
            not args.no_antithetic,
            args.quantum_method,
        ).as_dict()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
