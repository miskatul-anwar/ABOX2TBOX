"""Public Python API and explicit pipeline orchestration.

Every stage is an ordinary Python function. Running this module neither reads
nor executes a notebook, and importing it performs no induction or network IO.
"""

from __future__ import annotations
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rdflib import Graph

from .config import load_config
from .state import PipelineState
from .transport import initialize_transport
from .data import parse_input, cluster_signatures, detect_namespace, name_concepts
from .mining import mine_taxonomy, mine_roles_and_restrictions
from .adjudication import (
    adjudicate_taxonomy,
    assess_disjointness,
    adjudicate_roles,
    infer_domains_ranges,
)
from .ontology import (
    repair_taxonomy,
    repair_consistency,
    build_ontology,
    validate_and_export,
)
from .evaluation import evaluate_recovery, evaluate_calibration, plot_telemetry

STAGES: tuple[Callable[[PipelineState], None], ...] = (
    initialize_transport,
    parse_input,
    cluster_signatures,
    detect_namespace,
    name_concepts,
    mine_taxonomy,
    mine_roles_and_restrictions,
    adjudicate_taxonomy,
    assess_disjointness,
    adjudicate_roles,
    repair_taxonomy,
    repair_consistency,
    infer_domains_ranges,
    build_ontology,
    validate_and_export,
    evaluate_recovery,
    evaluate_calibration,
    plot_telemetry,
)


@dataclass(frozen=True)
class PipelineResult:
    """Validated ontology, evidence, metrics, and locations written by a run."""

    tbox: Graph
    output_path: Path
    evidence_path: Path
    plot_path: Path | None
    validation: dict[str, Any]
    evidence: dict[str, Any]
    metrics: dict[str, Any]
    state: PipelineState

    def summary(self) -> dict[str, Any]:
        return {
            "output_path": str(self.output_path),
            "evidence_path": str(self.evidence_path),
            "plot_path": str(self.plot_path) if self.plot_path is not None else None,
            "tbox_triples": len(self.tbox),
            "validation": self.validation,
            "decisions": self.evidence["status_counts"],
            "metrics": self.metrics,
            "stages_completed": self.state.completed_stages,
        }


def create_state(
    config: Mapping[str, Any] | None = None, *, seed: int = 42, verbose: bool = False
) -> PipelineState:
    """Create independent stage state; configuration uses env plus API overrides."""
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    return PipelineState(config=load_config(config), seed_value=seed, verbose=verbose)


def run_pipeline(
    input_path: str | Path | None = None,
    output_path: str | Path | None = None,
    *,
    plot_path: str | Path | None = None,
    rdf_format: str | None = None,
    config: Mapping[str, Any] | None = None,
    seed: int = 42,
    verbose: bool = False,
    plot: bool = True,
) -> PipelineResult:
    """Induce and validate a TBox; source files and process environment are preserved.

    Explicit arguments override config, which overrides environment defaults.
    Validation failures propagate and preserve the prior ontology export. SQLite
    is closed even when parsing, inference, export, or plotting raises an error.
    The returned state is diagnostic; its SQLite connection has been closed.
    """
    overrides = dict(config or {})
    for key, value in (
        ("ABOX_PATH", input_path),
        ("TBOX_PATH", output_path),
        ("PLOT_PATH", plot_path),
        ("ABOX_FORMAT", rdf_format),
    ):
        if value is not None:
            overrides[key] = str(value)
    state = create_state(overrides, seed=seed, verbose=verbose)
    source = Path(state.config["ABOX_PATH"]).resolve()
    target = Path(state.config["TBOX_PATH"])
    # Derive the actual sidecar name before resolving a possible output symlink.
    destinations = [target.resolve(), target.with_suffix(".evidence.json").resolve()]
    if plot:
        destinations.append(Path(state.config["PLOT_PATH"]).resolve())
    if source in destinations or len(set(destinations)) != len(destinations):
        raise ValueError(
            "Input, TBox, evidence ledger, and plot must have distinct paths"
        )
    try:
        for stage in STAGES:
            if stage is plot_telemetry and not plot:
                continue
            state.log(f"Running {stage.__name__}")
            stage(state)
            state.completed_stages.append(stage.__name__)
        target = Path(state.config["TBOX_PATH"]).resolve()
        return PipelineResult(
            tbox=state.g_tbox,
            output_path=target,
            evidence_path=target.with_suffix(".evidence.json"),
            plot_path=Path(state.config["PLOT_PATH"]).resolve() if plot else None,
            validation=state.VALIDATION_REPORT,
            evidence=state.EVIDENCE_REPORT,
            metrics=state.ONTOQA_METRICS,
            state=state,
        )
    finally:
        state.close()
