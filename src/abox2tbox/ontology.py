"""Joint ontology repair, OWL graph construction, and validated export."""

from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import hashlib
import json
import tempfile
import networkx as nx
import rdflib
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS
from .induction_evidence import term_key
from .pipeline_support import class_closure, repair_roles, validate_export
from .utils import local_name, inferred_namespace
from .state import PipelineState


def repair_taxonomy(state: PipelineState) -> None:
    "Remove taxonomy cycles greedily and reduce redundant edges."
    state.G_sub = nx.DiGraph()
    state.G_sub.add_nodes_from(state.all_universe_classes)
    for edge in state.adjudicated_subsumptions:
        weight = edge["conf"] * edge.get("prob", edge.get("support_fraction", 0))
        state.G_sub.add_edge(edge["sub"], edge["super"], weight=weight, **edge)
    state.final_equivalences = list(state.adjudicated_equivalences)
    state.cec_count = 0
    while True:
        try:
            cycle = nx.find_cycle(state.G_sub)
        except nx.NetworkXNoCycle:
            break
        weakest = min(cycle, key=lambda e: (state.G_sub[e[0]][e[1]]["weight"], e))
        state.G_sub.remove_edge(*weakest)
        state.cec_count += 1
    state.G_reduced = nx.transitive_reduction(state.G_sub)
    for u, v in state.G_reduced.edges():
        state.G_reduced[u][v].update(state.G_sub[u][v])
    state.log(
        f"Greedy repair removed {state.cec_count} edges; reduced taxonomy has {state.G_reduced.number_of_edges()} edges"
    )


def repair_consistency(state: PipelineState) -> None:
    "Repair disjointness and conservative OWL role constraints."
    state.class_ancestors = class_closure(
        state.all_universe_classes, state.G_reduced.edges(), state.final_equivalences
    )
    state.get_ancestors_set = lambda c: state.class_ancestors.get(c, {c})
    state.inst_inferred_types = {
        entity: set().union(*(state.get_ancestors_set(c) for c in classes))
        for entity, classes in state.entity_direct_types.items()
    }

    def disjoint_conflict(c1, c2):
        return any(
            (
                c1 in ancestors and c2 in ancestors
                for ancestors in state.class_ancestors.values()
            )
        ) or any(
            (
                c1 in classes and c2 in classes
                for classes in state.inst_inferred_types.values()
            )
        )

    state.clean_disjoint_pairs = [
        pair
        for pair in state.adjudicated_disjoint_pairs
        if not disjoint_conflict(pair[0], pair[1])
    ]
    state.dvc_pre = len(state.adjudicated_disjoint_pairs) - len(
        state.clean_disjoint_pairs
    )
    state.DVC_POST = sum(
        (disjoint_conflict(c1, c2) for c1, c2, *_ in state.clean_disjoint_pairs)
    )
    assert state.DVC_POST == 0
    (
        state.adjudicated_property_characteristics,
        state.adjudicated_chains,
        state.rejected_chains,
    ) = repair_roles(
        state.adjudicated_property_characteristics,
        state.adjudicated_subproperties,
        state.adjudicated_inverses,
        state.adjudicated_chains,
    )
    for prop, chars in state.adjudicated_property_characteristics.items():
        for left, right in [("Symmetric", "Asymmetric"), ("Reflexive", "Irreflexive")]:
            if left in chars and right in chars:
                chars.remove(left)
                chars.remove(right)
    state.log(
        f"Disjoint conflicts removed={state.dvc_pre}, remaining={state.DVC_POST}; irregular chains rejected={len(state.rejected_chains)}"
    )


def build_ontology(state: PipelineState) -> None:
    "Build OWL declarations, admitted hypotheses, and evidence annotations."
    state.g_tbox: rdflib.Graph = rdflib.Graph()
    state.pipeline_agent = URIRef("urn:abox2tbox:pipeline:v4.0")
    state.prov_attributed = URIRef("http://www.w3.org/ns/prov#wasAttributedTo")
    state.g_tbox.add((state.prov_attributed, RDF.type, OWL.AnnotationProperty))
    state.g_tbox.add((state.pipeline_agent, RDF.type, OWL.NamedIndividual))
    state.g_tbox.add(
        (state.pipeline_agent, RDFS.label, Literal("ABox-to-TBox pipeline v4.0"))
    )
    state.ontology_uri = URIRef(inferred_namespace + "Ontology")
    state.g_tbox.add((state.ontology_uri, RDF.type, OWL.Ontology))
    state.g_tbox.add(
        (state.ontology_uri, RDFS.label, Literal("Induced ontology hypotheses (v4.0)"))
    )
    state.g_tbox.add(
        (
            state.ontology_uri,
            URIRef("http://www.w3.org/ns/prov#wasAttributedTo"),
            state.pipeline_agent,
        )
    )
    for c in state.all_universe_classes:
        c_ref = URIRef(c)
        state.g_tbox.add((c_ref, RDF.type, OWL.Class))
        state.g_tbox.add((c_ref, RDFS.label, Literal(local_name(c))))
        if c in state.induced_classes:
            state.g_tbox.add(
                (c_ref, RDFS.comment, Literal(state.induced_classes[c]["gloss"]))
            )
            state.g_tbox.add(
                (
                    c_ref,
                    URIRef(inferred_namespace + "competencyQuestion"),
                    Literal(state.induced_classes[c]["cq"]),
                )
            )
    for u, v in state.G_reduced.edges():
        u_ref, v_ref = (URIRef(u), URIRef(v))
        state.g_tbox.add((u_ref, RDFS.subClassOf, v_ref))
        edata = state.G_reduced[u][v]
        stmt = BNode()
        state.g_tbox.add((stmt, RDF.type, OWL.Axiom))
        state.g_tbox.add((stmt, OWL.annotatedSource, u_ref))
        state.g_tbox.add((stmt, OWL.annotatedProperty, RDFS.subClassOf))
        state.g_tbox.add((stmt, OWL.annotatedTarget, v_ref))
        if "prob" in edata:
            state.g_tbox.add(
                (
                    stmt,
                    URIRef(inferred_namespace + "modelDecisionProbability"),
                    Literal(edata["prob"]),
                )
            )
        if "support_fraction" in edata:
            state.g_tbox.add(
                (
                    stmt,
                    URIRef(inferred_namespace + "empiricalSupportFraction"),
                    Literal(edata["support_fraction"]),
                )
            )
        state.g_tbox.add(
            (
                stmt,
                URIRef(inferred_namespace + "decisionSource"),
                Literal(edata["source"]),
            )
        )
        state.g_tbox.add(
            (
                stmt,
                URIRef(inferred_namespace + "confidenceScore"),
                Literal(round(edata["conf"], 3)),
            )
        )
        if "score" in edata:
            state.g_tbox.add(
                (
                    stmt,
                    URIRef(inferred_namespace + "ontologicalNecessityScore"),
                    Literal(edata["score"]),
                )
            )
        state.g_tbox.add(
            (
                stmt,
                URIRef(inferred_namespace + "aboxSupportCount"),
                Literal(int(edata["supp"])),
            )
        )
        state.g_tbox.add(
            (
                stmt,
                URIRef(inferred_namespace + "miningMode"),
                Literal(str(edata["mode"])),
            )
        )
        state.g_tbox.add(
            (
                stmt,
                URIRef("http://www.w3.org/ns/prov#wasAttributedTo"),
                state.pipeline_agent,
            )
        )
    for u, v, _ in state.final_equivalences:
        state.g_tbox.add((URIRef(u), OWL.equivalentClass, URIRef(v)))
    for c1, c2, _, _ in state.clean_disjoint_pairs:
        state.g_tbox.add((URIRef(c1), OWL.disjointWith, URIRef(c2)))
    for p in state.all_domain_properties:
        p_ref = URIRef(p)
        is_obj = p in state.object_props
        state.g_tbox.add(
            (p_ref, RDF.type, OWL.ObjectProperty if is_obj else OWL.DatatypeProperty)
        )
        state.g_tbox.add((p_ref, RDFS.label, Literal(local_name(p))))
        if p in state.property_domains:
            state.g_tbox.add((p_ref, RDFS.domain, URIRef(state.property_domains[p])))
        if p in state.property_ranges:
            state.g_tbox.add((p_ref, RDFS.range, URIRef(state.property_ranges[p])))
        for ch in state.adjudicated_property_characteristics.get(p, []):
            ch_map = {
                "Functional": OWL.FunctionalProperty,
                "InverseFunctional": OWL.InverseFunctionalProperty,
                "Transitive": OWL.TransitiveProperty,
                "Symmetric": OWL.SymmetricProperty,
                "Asymmetric": OWL.AsymmetricProperty,
                "Reflexive": OWL.ReflexiveProperty,
                "Irreflexive": OWL.IrreflexiveProperty,
            }
            if ch in ch_map:
                state.g_tbox.add((p_ref, RDF.type, ch_map[ch]))
    for res in state.adjudicated_local_restrictions:
        rb = BNode()
        state.g_tbox.add((rb, RDF.type, OWL.Restriction))
        state.g_tbox.add((rb, OWL.onProperty, URIRef(res["property"])))
        if res["type"] == "someValuesFrom":
            state.g_tbox.add((rb, OWL.someValuesFrom, URIRef(res["filler"])))
        else:
            state.g_tbox.add((rb, OWL.allValuesFrom, URIRef(res["filler"])))
        state.g_tbox.add((rb, RDFS.comment, Literal(res["verbalization"])))
        state.g_tbox.add(
            (
                rb,
                URIRef(inferred_namespace + "celoeScore"),
                Literal(round(float(res["phi_celoe"]), 3)),
            )
        )
        state.g_tbox.add((URIRef(res["class"]), RDFS.subClassOf, rb))
    for sp in state.adjudicated_subproperties:
        sp_sub = URIRef(sp["sub"])
        sp_super = URIRef(sp["super"])
        state.g_tbox.add((sp_sub, RDFS.subPropertyOf, sp_super))
        stmt_sp = BNode()
        state.g_tbox.add((stmt_sp, RDF.type, OWL.Axiom))
        state.g_tbox.add((stmt_sp, OWL.annotatedSource, sp_sub))
        state.g_tbox.add((stmt_sp, OWL.annotatedProperty, RDFS.subPropertyOf))
        state.g_tbox.add((stmt_sp, OWL.annotatedTarget, sp_super))
        state.g_tbox.add(
            (
                stmt_sp,
                URIRef(inferred_namespace + "amiePcaConfidence"),
                Literal(round(float(sp["conf_pca"]), 3)),
            )
        )
        state.g_tbox.add(
            (
                stmt_sp,
                URIRef(inferred_namespace + "amieHeadCoverage"),
                Literal(round(float(sp["hc"]), 3)),
            )
        )
    for inv in state.adjudicated_inverses:
        inv_p = URIRef(inv["p"])
        inv_q = URIRef(inv["q"])
        state.g_tbox.add((inv_p, OWL.inverseOf, inv_q))
        stmt_inv = BNode()
        state.g_tbox.add((stmt_inv, RDF.type, OWL.Axiom))
        state.g_tbox.add((stmt_inv, OWL.annotatedSource, inv_p))
        state.g_tbox.add((stmt_inv, OWL.annotatedProperty, OWL.inverseOf))
        state.g_tbox.add((stmt_inv, OWL.annotatedTarget, inv_q))
        state.g_tbox.add(
            (
                stmt_inv,
                URIRef(inferred_namespace + "amiePcaConfidence"),
                Literal(round(float(inv["conf_pca"]), 3)),
            )
        )
        state.g_tbox.add(
            (
                stmt_inv,
                URIRef(inferred_namespace + "amieHeadCoverage"),
                Literal(round(float(inv["hc"]), 3)),
            )
        )
    for ch in state.adjudicated_chains:
        ch_props = ch.get("chain", [ch.get("p1"), ch.get("p2")])
        super_p = ch.get("super", ch.get("p3"))
        if len(ch_props) >= 2 and super_p:
            list_nodes = [BNode() for _ in ch_props]
            for idx_c, p_c in enumerate(ch_props):
                state.g_tbox.add((list_nodes[idx_c], RDF.first, URIRef(p_c)))
                if idx_c + 1 < len(ch_props):
                    state.g_tbox.add(
                        (list_nodes[idx_c], RDF.rest, list_nodes[idx_c + 1])
                    )
                else:
                    state.g_tbox.add((list_nodes[idx_c], RDF.rest, RDF.nil))
            state.g_tbox.add((URIRef(super_p), OWL.propertyChainAxiom, list_nodes[0]))
    annotation_names = [
        "competencyQuestion",
        "modelDecisionProbability",
        "confidenceScore",
        "empiricalSupportFraction",
        "decisionSource",
        "ontologicalNecessityScore",
        "aboxSupportCount",
        "miningMode",
        "celoeScore",
        "amiePcaConfidence",
        "amieHeadCoverage",
    ]
    for name in annotation_names:
        state.g_tbox.add(
            (URIRef(inferred_namespace + name), RDF.type, OWL.AnnotationProperty)
        )
    state.evidence_annotation = URIRef("urn:abox2tbox:evidenceRecord")
    state.g_tbox.add((state.evidence_annotation, RDF.type, OWL.AnnotationProperty))
    for record in state.evidence_gate.records:
        if record["status"] == "accepted":
            family, spec = (record["family"], record["candidate"])
            retained = True
            if family == "subclass":
                retained = nx.has_path(state.G_reduced, spec["sub"], spec["super"])
            elif family == "chain":
                retained = spec in state.adjudicated_chains
            elif family in state.characteristic_metrics:
                retained = family in state.adjudicated_property_characteristics.get(
                    spec["property"], []
                )
            if not retained:
                record["status"] = "withheld"
                record["reasons"].append("withdrawn_by_joint_graph_repair")
        if record["status"] != "accepted":
            continue
        state.g_tbox.add(
            (
                state.ontology_uri,
                state.evidence_annotation,
                Literal(
                    json.dumps(
                        {k: v for k, v in record.items() if k != "model_critique"},
                        sort_keys=True,
                    )
                ),
            )
        )
    state.normalization_annotation = URIRef("urn:abox2tbox:normalization")
    state.g_tbox.add((state.normalization_annotation, RDF.type, OWL.AnnotationProperty))
    for mapping in state.INPUT_REPORT["mixed_properties"]:
        state.g_tbox.add(
            (
                state.ontology_uri,
                state.normalization_annotation,
                Literal(json.dumps(mapping, sort_keys=True)),
            )
        )
    for s, prop, o in state.training_graph:
        if prop == RDF.type or str(prop) in state.all_domain_properties:
            continue
        state.g_tbox.add(
            (
                prop,
                RDF.type,
                OWL.DatatypeProperty if isinstance(o, Literal) else OWL.ObjectProperty,
            )
        )
    for prop, datatype in state.property_datatype_ranges.items():
        state.g_tbox.add((URIRef(prop), RDFS.range, URIRef(datatype)))


def validate_and_export(state: PipelineState) -> None:
    "Validate joint semantics, retract invalid hypotheses, and replace outputs atomically."
    serialized = state.g_tbox.serialize(format="turtle")
    g_verification = Graph().parse(data=serialized, format="turtle")
    validation_abox = Graph()
    validation_abox += state.training_graph
    validation_abox += state.semantic_context
    training_subjects = {
        term_key(term): term
        for triple in state.training_graph
        for term in (triple[0], triple[2])
        if not isinstance(term, Literal)
    }
    for uri, cluster in state.induced_classes.items():
        for entity in cluster["entities"]:
            validation_abox.add((training_subjects[entity], RDF.type, URIRef(uri)))
    try:
        state.VALIDATION_REPORT = validate_export(g_verification, validation_abox)
    except (RuntimeError, ValueError) as validation_error:
        if not any((r["status"] == "accepted" for r in state.evidence_gate.records)):
            raise
        baseline = Graph()
        declaration_types = {
            OWL.Class,
            OWL.ObjectProperty,
            OWL.DatatypeProperty,
            OWL.AnnotationProperty,
            OWL.Ontology,
            OWL.NamedIndividual,
        }
        for s, p, o in g_verification:
            if isinstance(s, URIRef) and (
                p == RDF.type
                and o in declaration_types
                or p
                in {
                    RDFS.label,
                    RDFS.comment,
                    state.prov_attributed,
                    state.normalization_annotation,
                }
            ):
                baseline.add((s, p, o))
        state.VALIDATION_REPORT = validate_export(baseline, validation_abox)
        state.VALIDATION_REPORT.update(
            repaired=True,
            repair="retracted learned axioms after joint validation failure",
            original_error=str(validation_error),
        )
        for record in state.evidence_gate.records:
            if record["status"] == "accepted":
                record["status"] = "withheld"
                record["reasons"].append("withdrawn_after_joint_reasoner_failure")
        state.G_reduced = nx.DiGraph()
        state.G_reduced.add_nodes_from(state.all_universe_classes)
        state.final_equivalences, state.clean_disjoint_pairs = ([], [])
        (
            state.adjudicated_subproperties,
            state.adjudicated_inverses,
            state.adjudicated_chains,
        ) = ([], [], [])
        state.adjudicated_local_restrictions, state.adjudicated_subsumptions = ([], [])
        state.adjudicated_property_characteristics = defaultdict(list)
        (
            state.property_domains,
            state.property_ranges,
            state.property_datatype_ranges,
        ) = ({}, {}, {})
        state.class_ancestors = class_closure(state.all_universe_classes, [], [])
        state.g_tbox = baseline
        serialized = baseline.serialize(format="turtle")
        g_verification = Graph().parse(data=serialized, format="turtle")
    state.tbox_path = str(state.config["TBOX_PATH"])
    target = Path(state.tbox_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=target.parent, suffix=".ttl", delete=False
    ) as handle:
        pending_output = Path(handle.name)
        handle.write(serialized)
    try:
        pending_output.replace(target)
    finally:
        pending_output.unlink(missing_ok=True)
    state.log(
        f"Complete TBox and training ABox validated; serialized {len(g_verification)} triples to {target}"
    )
    state.EVIDENCE_REPORT = state.evidence_gate.report()
    state.EVIDENCE_REPORT.update(
        input=state.INPUT_REPORT,
        search=state.MINING_REPORT,
        validation=state.VALIDATION_REPORT,
        output_sha256=hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
    )
    report_path = target.with_suffix(".evidence.json")
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=target.parent, suffix=".json", delete=False
    ) as handle:
        pending_report = Path(handle.name)
        json.dump(state.EVIDENCE_REPORT, handle, indent=2, allow_nan=False)
    try:
        pending_report.replace(report_path)
    finally:
        pending_report.unlink(missing_ok=True)
    state.log(f"Evidence ledger: {report_path}")
