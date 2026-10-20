"""Command-line entry point for the same API used by Python callers and tests."""

from __future__ import annotations
import argparse
from contextlib import redirect_stdout
import json
import sys

from . import __version__
from .pipeline import run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="abox2tbox",
        description="Induce a validated, defeasible TBox and an evidence ledger from local RDF.",
    )
    parser.add_argument("input", nargs="?", help="Input RDF file (or ABOX_INPUT_PATH)")
    parser.add_argument("-i", "--input", dest="input_path", help="Input RDF file")
    parser.add_argument(
        "-o", "--output", help="Turtle output path (or TBOX_OUTPUT_PATH)"
    )
    parser.add_argument(
        "--format",
        dest="rdf_format",
        help="RDF syntax override, e.g. turtle or json-ld",
    )
    parser.add_argument("--plot", dest="plot_path", help="Telemetry PNG path")
    parser.add_argument(
        "--no-plot", action="store_true", help="Skip telemetry plotting"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--llm",
        dest="use_llm",
        action="store_true",
        help="Enable optional model naming/critique",
    )
    mode.add_argument(
        "--offline",
        dest="use_llm",
        action="store_false",
        help="Disable all model requests",
    )
    parser.set_defaults(use_llm=None)
    parser.add_argument(
        "--max-input-triples", type=int, help="Input size guard after parsing"
    )
    parser.add_argument(
        "--max-join-edges", type=int, help="Materialized chain-join limit"
    )
    parser.add_argument(
        "--max-candidates", type=int, help="Full evidence-assessment budget"
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--verbose", action="store_true", help="Write stage diagnostics to stderr"
    )
    parser.add_argument(
        "--json", action="store_true", help="Write a machine-readable result summary"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Show a traceback on failure"
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    args = parser.parse_args(argv)
    if args.input and args.input_path:
        parser.error("Specify input either positionally or with --input")
    overrides = {
        key: value
        for key, value in (
            ("USE_LLM", args.use_llm),
            ("MAX_INPUT_TRIPLES", args.max_input_triples),
            ("MAX_JOIN_EDGES", args.max_join_edges),
            ("MAX_EVIDENCE_CANDIDATES", args.max_candidates),
        )
        if value is not None
    }
    try:
        # Third-party reasoners/transports can print; preserve stdout for JSON.
        with redirect_stdout(sys.stderr):
            result = run_pipeline(
                args.input_path or args.input,
                args.output,
                plot_path=args.plot_path,
                rdf_format=args.rdf_format,
                config=overrides,
                seed=args.seed,
                verbose=args.verbose,
                plot=not args.no_plot,
            )
    except Exception as exc:
        if args.debug:
            raise
        print(f"abox2tbox: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result.summary(), indent=2, allow_nan=False))
    else:
        print(f"Validated TBox: {result.output_path}")
        print(f"Evidence ledger: {result.evidence_path}")
        print(
            f"Decisions: {json.dumps(result.evidence['status_counts'], sort_keys=True)}"
        )
    return 0
