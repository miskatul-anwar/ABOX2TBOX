"""Generate the optional notebook example; algorithms live in src/abox2tbox/."""

import argparse
import json
from pathlib import Path


def build_notebook():
    def cell(kind, source, cell_id):
        result = {
            "cell_type": kind,
            "metadata": {},
            "id": cell_id,
            "source": source.splitlines(keepends=True),
        }
        if kind == "code":
            result.update(execution_count=None, outputs=[])
        return result

    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python"},
        },
        "cells": [
            cell(
                "markdown",
                """# ABox-to-TBox Python API example

The maintained pipeline is the `abox2tbox` Python package in `src/abox2tbox/`.
Manage it with `uv sync --locked` and `uv run abox2tbox`, or use the runner
`scripts/run_pipeline.py`. This notebook is an optional API example and contains
no independent implementation. See `README.md` and `docs/falsification.md` for
the evidence model, input contract, and remaining limits.
""",
                "intro",
            ),
            cell(
                "code",
                """from pathlib import Path
from abox2tbox import run_pipeline

# Paths below are relative to the kernel's working directory.
input_path = Path("input/ABox.ttl")
output_path = Path("output/TBox.ttl")
""",
                "setup",
            ),
            cell(
                "code",
                """result = run_pipeline(
    input_path,
    output_path,
    plot_path=output_path.with_name("telemetry.png"),
    config={"USE_LLM": False},
)
result.summary()
""",
                "run",
            ),
            cell(
                "markdown",
                """The output contains defeasible schema hypotheses. Posterior probabilities
concern observable coverage, not guaranteed universal truth or human agreement.
The evidence ledger records accepted, rejected, and withheld candidates. Missing
facts are not logical negatives. Weak evidence can yield vocabulary-only output.
""",
                "interpretation",
            ),
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "ABOX2TBOX.ipynb",
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(build_notebook(), indent=1) + "\n", encoding="utf-8"
    )
    print(f"Generated API example: {args.output}")


if __name__ == "__main__":
    main()
