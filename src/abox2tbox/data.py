"""RDF ingestion, discovery partitioning, and provisional signature concepts."""

from __future__ import annotations
from collections import Counter, defaultdict
from typing import Any
import hashlib
import math
import os
import random
import re
import sqlite3
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, XSD
from .induction_evidence import (
    EvidenceGate,
    load_abox,
    split_assertions,
    term_key,
    bucket,
)
from .utils import (
    is_meta_uri,
    local_name,
    rdf_type_str,
    inferred_namespace,
    standard_vocabulary_prefixes,
)
from .state import PipelineState


def parse_input(state: PipelineState) -> None:
    "Parse and normalize RDF, isolate test subjects, and create the discovery store."
    abox_path = str(state.config["ABOX_PATH"])
    if not os.path.isfile(abox_path):
        raise FileNotFoundError(f"ABox file missing at {abox_path}")
    abox_graph, state.INPUT_REPORT = load_abox(
        abox_path, state.config["ABOX_FORMAT"], state.config["MAX_INPUT_TRIPLES"]
    )
    state.training_graph, state.semantic_context = split_assertions(abox_graph)
    state.entity_types_map = defaultdict(list)
    entity_terms = {}
    for s, o in state.training_graph.subject_objects(RDF.type):
        state.entity_types_map[term_key(s)].append(str(o))
        entity_terms[term_key(s)] = s
    for values in state.entity_types_map.values():
        values.sort()
    rng_holdout = random.Random(state.seed_value)
    multi_typed_entities = sorted(
        (e for e, values in state.entity_types_map.items() if len(values) >= 2)
    )
    fraction = float(state.config["HOLD_OUT_FRACTION"])
    role_fraction = float(state.config["ROLE_HOLD_OUT_FRACTION"])
    if not 0 <= fraction < 1 or not 0 <= role_fraction < 1:
        raise ValueError("Hold-out fractions must lie in [0, 1)")
    hold_out_type_count = round(fraction * len(multi_typed_entities))
    state.held_out_type_assertions = []
    for entity in rng_holdout.sample(multi_typed_entities, hold_out_type_count):
        masked_class = rng_holdout.choice(state.entity_types_map[entity])
        state.held_out_type_assertions.append((entity, masked_class))
        state.training_graph.remove(
            (entity_terms[entity], RDF.type, URIRef(masked_class))
        )
    role_triples = sorted(
        (
            (s, predicate, o)
            for s, predicate, o in state.training_graph
            if predicate != RDF.type and (not isinstance(o, Literal))
        ),
        key=lambda t: tuple((x.n3() for x in t)),
    )
    state.held_out_role_assertions = []
    role_by_subject = defaultdict(list)
    for triple in role_triples:
        role_by_subject[term_key(triple[0])].append(triple)
    role_test_subjects = rng_holdout.sample(
        sorted(role_by_subject), round(role_fraction * len(role_by_subject))
    )
    for subject in role_test_subjects:
        triple = rng_holdout.choice(role_by_subject[subject])
        state.held_out_role_assertions.append(tuple(map(term_key, triple)))
        state.training_graph.remove(triple)
    state.test_subjects = {
        entity for entity, _ in state.held_out_type_assertions
    } | set(role_test_subjects)
    state.input_triple_count = len(abox_graph)
    del abox_graph, role_triples
    state.confirmation_subjects = {
        term_key(s)
        for s in state.training_graph.subjects()
        if term_key(s) not in state.test_subjects
        and bucket(term_key(s)) < 10000 * state.config["CONFIRMATION_FRACTION"]
    }
    state.discovery_graph = Graph()
    for triple in state.training_graph:
        if term_key(triple[0]) not in state.confirmation_subjects | state.test_subjects:
            state.discovery_graph.add(triple)
    state.evidence_gate = EvidenceGate(
        state.training_graph,
        state.semantic_context,
        state.confirmation_subjects,
        state.config,
    )
    state.INPUT_REPORT.update(
        training_triples=len(state.training_graph),
        discovery_triples=len(state.discovery_graph),
        confirmation_subjects=len(state.confirmation_subjects),
        context_triples=len(state.semantic_context),
        final_test_subjects=len(state.test_subjects),
    )
    state.conn = sqlite3.connect(":memory:")
    state.cur = state.conn.cursor()
    state.cur.execute(
        "CREATE TABLE triples (subject TEXT, predicate TEXT, object TEXT, is_literal INTEGER, datatype TEXT)"
    )
    triple_rows = []
    for s, predicate, o in state.discovery_graph:
        datatype = (
            str(o.datatype or (RDF.langString if o.language else XSD.string))
            if isinstance(o, Literal)
            else None
        )
        value = o.n3() if isinstance(o, Literal) else term_key(o)
        triple_rows.append(
            (term_key(s), str(predicate), value, int(isinstance(o, Literal)), datatype)
        )
    state.cur.executemany(
        "INSERT INTO triples VALUES (?, ?, ?, ?, ?)", sorted(triple_rows)
    )
    state.cur.execute("CREATE INDEX idx_sub_pred ON triples(subject, predicate)")
    state.cur.execute("CREATE INDEX idx_pred_obj ON triples(predicate, object)")
    state.cur.execute("CREATE INDEX idx_obj ON triples(object)")
    state.conn.commit()
    state.active_type_rows = state.cur.execute(
        "SELECT subject, object FROM triples WHERE predicate = ?", (rdf_type_str,)
    ).fetchall()
    typed_subjects = {s for s, _ in state.active_type_rows}
    state.all_subjects = sorted(
        {r[0] for r in state.cur.execute("SELECT DISTINCT subject FROM triples")}
        | {
            r[0]
            for r in state.cur.execute(
                "SELECT DISTINCT object FROM triples WHERE is_literal=0 AND predicate != ?",
                (rdf_type_str,),
            )
        }
    )
    state.untyped_subjects = set(state.all_subjects) - typed_subjects
    state.log(
        f"Loaded {state.input_triple_count} triples; training={len(state.training_graph)}, subjects={len(state.all_subjects)}, untyped={len(state.untyped_subjects)}"
    )


def cluster_signatures(state: PipelineState) -> None:
    "Consolidate untyped signatures without inventing confirmation labels."
    df_map: dict[str, int] = defaultdict(int)
    for p_row in state.cur.execute("SELECT DISTINCT predicate FROM triples").fetchall():
        p_val: str = p_row[0]
        cnt: int = state.cur.execute(
            "SELECT COUNT(DISTINCT subject) FROM triples WHERE predicate = ?", (p_val,)
        ).fetchone()[0]
        df_map[p_val] = cnt
    total_subjects_count: int = max(1, len(state.all_subjects))
    idf_map: dict[str, float] = {
        p: math.log(1.0 + float(total_subjects_count) / float(df_map[p]))
        for p in df_map
    }
    out_preds_by_subject: dict[str, set[str]] = defaultdict(set)
    in_preds_by_subject: dict[str, set[str]] = defaultdict(set)
    for s, p, o, is_lit, _ in state.cur.execute(
        "SELECT subject, predicate, object, is_literal, datatype FROM triples"
    ):
        if s in state.untyped_subjects:
            out_preds_by_subject[s].add(p)
        if not is_lit and o in state.untyped_subjects:
            in_preds_by_subject[o].add(p)
    hash_to_entities: dict[str, list[str]] = defaultdict(list)
    for s in sorted(state.untyped_subjects):
        sig_str: str = (
            "OUT:"
            + ",".join(sorted(out_preds_by_subject[s]))
            + "|IN:"
            + ",".join(sorted(in_preds_by_subject[s]))
        )
        h_digest: str = hashlib.blake2b(
            sig_str.encode("utf-8"), digest_size=8
        ).hexdigest()
        hash_to_entities[h_digest].append(s)
    micro_clusters: list[dict[str, Any]] = []
    for h_code, ents in hash_to_entities.items():
        p_counts: dict[str, int] = defaultdict(int)
        for e in ents:
            for p in out_preds_by_subject[e]:
                p_counts[p] += 1
        core_preds: set[str] = {p for p, c in p_counts.items() if c >= 0.5 * len(ents)}
        in_preds_set: set[str] = (
            set.union(*[in_preds_by_subject[e] for e in ents]) if ents else set()
        )
        micro_clusters.append(
            {
                "hash": h_code,
                "entities": sorted(ents),
                "core_preds": core_preds,
                "in_preds": in_preds_set,
            }
        )
    tau_merge: float = float(state.config["TAU_MERGE_JACCARD"])
    state.consolidated_clusters: list[dict[str, Any]] = [
        dict(c) for c in micro_clusters
    ]
    merge_happened: bool = True
    while merge_happened:
        merge_happened = False
        for i in range(len(state.consolidated_clusters)):
            for j in range(i + 1, len(state.consolidated_clusters)):
                c_a = state.consolidated_clusters[i]
                c_b = state.consolidated_clusters[j]
                inter = c_a["core_preds"] & c_b["core_preds"]
                union = c_a["core_preds"] | c_b["core_preds"]
                w_inter = sum((idf_map.get(p, 1.0) for p in inter))
                w_union = sum((idf_map.get(p, 1.0) for p in union)) if union else 1.0
                j_w = w_inter / w_union if w_union > 0 else 0.0
                in_compatible = (
                    not c_a["in_preds"]
                    and (not c_b["in_preds"])
                    or bool(c_a["in_preds"] & c_b["in_preds"])
                )
                if j_w >= tau_merge and in_compatible:
                    c_a["entities"] = sorted(c_a["entities"] + c_b["entities"])
                    counts = Counter(
                        (
                            p
                            for entity in c_a["entities"]
                            for p in out_preds_by_subject[entity]
                        )
                    )
                    c_a["core_preds"] = {
                        p
                        for p, count in counts.items()
                        if count >= 0.5 * len(c_a["entities"])
                    }
                    c_a["in_preds"] = c_a["in_preds"] | c_b["in_preds"]
                    state.consolidated_clusters.pop(j)
                    merge_happened = True
                    break
            if merge_happened:
                break
    state.log(f"Consolidated clusters: {len(state.consolidated_clusters)}")


def detect_namespace(state: PipelineState) -> None:
    "Describe the observed vocabulary namespace."
    namespace_sources = [
        (
            "classes",
            [
                o
                for s, o in state.cur.execute(
                    "SELECT DISTINCT subject, object FROM triples WHERE predicate = ? AND is_literal = 0",
                    (rdf_type_str,),
                ).fetchall()
                if not is_meta_uri(o)
            ],
        ),
        (
            "predicates",
            [
                r[0]
                for r in state.cur.execute(
                    "SELECT DISTINCT predicate FROM triples"
                ).fetchall()
                if not is_meta_uri(r[0])
            ],
        ),
        (
            "subjects",
            [
                r[0]
                for r in state.cur.execute(
                    "SELECT DISTINCT subject FROM triples"
                ).fetchall()
                if not is_meta_uri(r[0])
            ],
        ),
    ]
    namespace_counter = Counter()
    for _, uris in namespace_sources:
        for uri in uris:
            ns = (
                uri.rsplit("#", 1)[0] + "#"
                if "#" in uri
                else uri.rsplit("/", 1)[0] + "/"
                if "/" in uri
                else uri.rsplit(":", 1)[0] + ":"
                if uri.startswith("urn:")
                else ""
            )
            if (
                ns
                and (
                    not any(
                        (ns.startswith(pfx) for pfx in standard_vocabulary_prefixes)
                    )
                )
                and (not is_meta_uri(ns))
            ):
                namespace_counter[ns] += 1
    state.detected_namespace: str = (
        namespace_counter.most_common(1)[0][0]
        if namespace_counter
        else "http://example.org/domain#"
    )
    state.log(f"Detected Namespace: {state.detected_namespace}")


def name_concepts(state: PipelineState) -> None:
    "Name provisional signature groups in the pipeline namespace."
    existing_class_uris = {o for _, o in state.active_type_rows}
    used_class_uris = set(existing_class_uris)
    used_class_uris.update(
        (
            str(term)
            for triple in state.training_graph
            for term in triple
            if isinstance(term, URIRef)
        )
    )
    state.induced_classes, state.induced_class_uris = ({}, set())
    pascal_case_sanitize = lambda s: "".join(
        (part.capitalize() for part in re.findall("[A-Za-z0-9]+", s))
    )
    for cluster in state.consolidated_clusters:
        entities, core = (cluster["entities"], cluster["core_preds"])
        tokens = [
            word
            for p in sorted(core)
            for word in re.findall(
                "[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\\d|\\b)", local_name(p)
            )
        ]
        name = (
            pascal_case_sanitize(" ".join(tokens[:3]))
            or f"Concept{cluster['hash'][:6]}"
        )
        cq = f"Which entities have the observed property signature {sorted(map(local_name, core))}?"
        candidates = [name, name + "Entity", "Domain" + name]
        answers = state.transport.ask(
            {"properties": sorted(core), "candidates": candidates},
            {
                "name": {
                    "type": "choice",
                    "instructions": "Select a descriptive class name.",
                    "criteria": {c: c for c in candidates},
                }
            },
            "concept_naming",
        )
        answer = answers.get("name", {})
        choice = answer.get("choice") if isinstance(answer, dict) else None
        if choice in candidates:
            name = choice
        aligned = None
        uri = aligned or inferred_namespace + name
        suffix = 2
        while aligned is None and uri in used_class_uris:
            uri = inferred_namespace + name + f"_{suffix}"
            suffix += 1
        used_class_uris.add(uri)
        if aligned is None:
            state.induced_class_uris.add(uri)
        for entity in entities:
            state.cur.execute(
                "INSERT INTO triples VALUES (?, ?, ?, 0, NULL)",
                (entity, rdf_type_str, uri),
            )
        previous = state.induced_classes.get(uri, {}).get("entities", [])
        state.induced_classes[uri] = {
            "uri": uri,
            "name": local_name(uri),
            "cq": cq,
            "gloss": "Provisional grouping by observed property signature.",
            "core_preds": core,
            "entities": sorted(set(previous + entities)),
        }
        state.log(
            f"Cluster {cluster['hash']}: {local_name(uri)} ({len(entities)} instances)"
        )
    state.conn.commit()
