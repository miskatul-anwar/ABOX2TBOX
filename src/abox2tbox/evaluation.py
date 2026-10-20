"""Independent positive recovery and descriptive telemetry."""

from __future__ import annotations
from collections import defaultdict
from pathlib import Path
from typing import Any
import itertools
import json
import networkx as nx
from rdflib import Literal
from rdflib.namespace import RDF
from .induction_evidence import term_key
from .pipeline_support import recover_assertions, calibration_metrics
from .utils import local_name, lexical_similarity
from .state import PipelineState


def evaluate_recovery(state: PipelineState) -> None:
    "Evaluate held-out positives in the supported entailment fragment."
    state.num_classes = len(state.all_universe_classes)
    state.num_properties = len(state.all_domain_properties)
    state.num_subclasses = len(state.G_reduced.edges())
    state.rr_val = (
        state.num_properties / (state.num_properties + state.num_subclasses)
        if state.num_properties + state.num_subclasses > 0
        else 0.0
    )
    state.ir_val = (
        state.num_subclasses / state.num_classes if state.num_classes > 0 else 0.0
    )
    state.ccr_val = (
        sum((1 for c in state.all_universe_classes if state.class_instances[c]))
        / state.num_classes
        if state.num_classes > 0
        else 0.0
    )
    evaluation_types, evaluation_edges = (defaultdict(set), defaultdict(set))
    for s, p, o in state.training_graph:
        if p == RDF.type:
            evaluation_types[term_key(s)].add(str(o))
        elif not isinstance(o, Literal):
            evaluation_edges[str(p)].add((term_key(s), term_key(o)))
    state.inst_inferred_types, inferred_role_edges = recover_assertions(
        evaluation_types,
        evaluation_edges,
        state.class_ancestors,
        state.adjudicated_subproperties,
        state.adjudicated_inverses,
        state.adjudicated_chains,
        state.adjudicated_property_characteristics,
        state.property_domains,
        state.property_ranges,
    )
    for p in state.datatype_props:
        if p in state.property_domains:
            for entity, _ in state.edges_by_prop[p]:
                state.inst_inferred_types[entity].update(
                    state.get_ancestors_set(state.property_domains[p])
                )
    tp_hold = sum(
        (
            c in state.inst_inferred_types.get(e, set())
            for e, c in state.held_out_type_assertions
        )
    )
    fn_hold = len(state.held_out_type_assertions) - tp_hold
    state.prec_hold = None
    state.f1_hold = None
    state.rec_hold = (
        tp_hold / len(state.held_out_type_assertions)
        if state.held_out_type_assertions
        else None
    )
    role_hits = sum(
        ((s, o) in inferred_role_edges[p] for s, p, o in state.held_out_role_assertions)
    )
    state.role_recall = (
        role_hits / len(state.held_out_role_assertions)
        if state.held_out_role_assertions
        else None
    )
    jw_alignments = [
        lexical_similarity(local_name(c), local_name(c2))
        for c, c2 in itertools.islice(
            itertools.combinations(state.all_universe_classes, 2),
            state.config["MAX_DECISION_PAIRS"],
        )
    ]
    state.jw_rate = sum((1 for s in jw_alignments if s >= 0.8)) / max(
        1, len(jw_alignments)
    )
    expressive_axioms_count = (
        len(state.adjudicated_local_restrictions)
        + len(state.adjudicated_subproperties)
        + len(state.adjudicated_inverses)
        + len(state.adjudicated_chains)
        + sum((len(c) for c in state.adjudicated_property_characteristics.values()))
    )
    total_axioms_count = (
        state.num_subclasses
        + len(state.final_equivalences)
        + len(state.clean_disjoint_pairs)
        + expressive_axioms_count
    )
    state.aei_val = expressive_axioms_count / max(1, total_axioms_count)
    max_disj_pairs = (
        state.num_classes * (state.num_classes - 1) / 2
        if state.num_classes > 1
        else 0.0
    )
    state.ddr_val = (
        len(state.clean_disjoint_pairs) / max_disj_pairs if max_disj_pairs else 0.0
    )
    state.ONTOQA_METRICS: dict[str, Any] = {
        "relationship_richness": state.rr_val,
        "inheritance_richness": state.ir_val,
        "class_coverage_ratio": state.ccr_val,
        "hold_out_precision": state.prec_hold,
        "hold_out_recall": state.rec_hold,
        "hold_out_f1": state.f1_hold,
        "hold_out_type_count": len(state.held_out_type_assertions),
        "hold_out_role_count": len(state.held_out_role_assertions),
        "hold_out_role_recall": state.role_recall,
        "lexical_similarity_rate": state.jw_rate,
        "axiom_expressivity_index": state.aei_val,
        "disjointness_density_ratio": state.ddr_val,
    }
    state.log("ONTOQA METRICS:", state.ONTOQA_METRICS)


def evaluate_calibration(state: PipelineState) -> None:
    "Report calibration only when the prediction target has independent labels."
    calibration_gold = {}
    labels_path = state.config["CALIBRATION_LABELS_PATH"]
    if labels_path:
        for row in json.loads(Path(labels_path).read_text()):
            key = (row["sub"], row["super"])
            if row["label"] not in (0, 1) or key in calibration_gold:
                raise ValueError(
                    "Calibration labels must be unique directed pairs with binary labels"
                )
            calibration_gold[key] = row["label"]
    state.CALIBRATION = calibration_metrics(
        state.taxonomic_predictions, calibration_gold
    )
    state.ECE, state.brier_score = (
        state.CALIBRATION["ece"],
        state.CALIBRATION["brier"],
    )
    state.bin_centers = [b["confidence"] for b in state.CALIBRATION["bins"]]
    state.bin_accuracies = [b["accuracy"] for b in state.CALIBRATION["bins"]]
    state.total_so_calls = sum(
        (
            e["endpoint"] == "/v1/systemone" and e["status"] in ("success", "error")
            for e in state.payload_token_audit_log
        )
    )
    state.total_tokens_measured = sum(
        (
            e["input_tokens"]
            for e in state.payload_token_audit_log
            if e.get("input_tokens") is not None
        )
    )
    state.unknown_token_calls = sum(
        (
            e["status"] in ("success", "error") and e.get("input_tokens") is None
            for e in state.payload_token_audit_log
        )
    )
    state.log(
        f"Calibration: {state.CALIBRATION}; measured input tokens={state.total_tokens_measured}, calls without usage={state.unknown_token_calls}"
    )


def plot_telemetry(state: PipelineState) -> None:
    "Save descriptive telemetry and the named-class taxonomy."
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plot_path: str = str(state.config["PLOT_PATH"])
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    axes[0].plot([0, 1], [0, 1], "k--", label="Ideal Calibration")
    if state.ECE is not None:
        axes[0].plot(
            state.bin_centers,
            state.bin_accuracies,
            "o-",
            label=f"ECE={state.ECE:.3f}, n={state.CALIBRATION['count']}",
        )
    else:
        axes[0].text(
            0.5,
            0.5,
            "Calibration unavailable\nRequires model probabilities and independent labels",
            ha="center",
            va="center",
            wrap=True,
        )
    axes[0].set_title("Reliability Calibration Curve (M=10)")
    axes[0].set_xlabel("Predicted Probability")
    axes[0].set_ylabel("Empirical Accuracy")
    axes[0].set_xlim([0, 1])
    axes[0].set_ylim([0, 1])
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    cats = [
        "SubClass",
        "Equivalent",
        "Disjoint",
        "Restrictions",
        "SubProperty",
        "InverseOf",
        "Chains",
        "Characteristics",
    ]
    counts = [
        state.num_subclasses,
        len(state.final_equivalences),
        len(state.clean_disjoint_pairs),
        len(state.adjudicated_local_restrictions),
        len(state.adjudicated_subproperties),
        len(state.adjudicated_inverses),
        len(state.adjudicated_chains),
        sum((len(c) for c in state.adjudicated_property_characteristics.values())),
    ]
    axes[1].barh(cats, counts, color="#2ca02c")
    axes[1].set_title("Axiom Expressivity Breakdown")
    axes[1].set_xlabel("Axiom Count")
    axes[1].grid(True, axis="x", alpha=0.3)
    subgraph_nodes = sorted(state.G_reduced.nodes())[:20]
    G_vis = state.G_reduced.subgraph(subgraph_nodes)
    node_colors = [
        "#ff7f0e" if n in state.induced_class_uris else "#1f77b4" for n in G_vis.nodes()
    ]
    pos = nx.spring_layout(G_vis, seed=42)
    nx.draw_networkx_nodes(
        G_vis, pos, ax=axes[2], node_color=node_colors, node_size=1000
    )
    nx.draw_networkx_edges(
        G_vis, pos, ax=axes[2], edge_color="#7f7f7f", arrows=True, arrowsize=12
    )
    nx.draw_networkx_labels(
        G_vis,
        pos,
        labels={n: local_name(n) for n in G_vis.nodes()},
        ax=axes[2],
        font_size=7,
        font_color="white",
    )
    axes[2].set_title("Top-20 Hasse Taxonomic DAG")
    axes[2].axis("off")
    plt.tight_layout()
    Path(plot_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_path, dpi=72)
    plt.close()
    state.log(f"Diagnostic plot saved to {plot_path}.")
    state.log("Pipeline completed; complete export validation passed.")
