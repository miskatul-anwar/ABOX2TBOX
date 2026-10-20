"""Discovery-only taxonomy and role candidate mining."""

from __future__ import annotations
from collections import defaultdict
from typing import Any
import json
from rdflib.namespace import RDF
from .utils import (
    is_meta_uri,
    local_name,
    wilson_lower,
    celoe_heuristic,
    lexical_similarity,
    rdf_type_str,
)
from .state import PipelineState


def mine_taxonomy(state: PipelineState) -> None:
    "Propose subclass candidates using discovery observations only."
    state.class_instances: dict[str, set[str]] = defaultdict(set)
    for s, o in state.cur.execute(
        "SELECT subject, object FROM triples WHERE predicate = ? AND is_literal = 0",
        (rdf_type_str,),
    ).fetchall():
        if not is_meta_uri(o):
            state.class_instances[o].add(s)
    state.entity_direct_types: dict[str, set[str]] = defaultdict(set)
    for c_uri, insts in state.class_instances.items():
        for inst in insts:
            state.entity_direct_types[inst].add(c_uri)
    state.class_core_predicates: dict[str, set[str]] = defaultdict(set)
    for c_uri, inst_set in state.class_instances.items():
        if not inst_set:
            continue
        p_tally: dict[str, int] = defaultdict(int)
        for inst in inst_set:
            for p_row in state.cur.execute(
                "SELECT DISTINCT predicate FROM triples WHERE subject = ?", (inst,)
            ).fetchall():
                if not is_meta_uri(p_row[0]):
                    p_tally[p_row[0]] += 1
            for p_row in state.cur.execute(
                "SELECT DISTINCT predicate FROM triples WHERE object = ? AND is_literal = 0",
                (inst,),
            ).fetchall():
                if not is_meta_uri(p_row[0]):
                    p_tally["IN:" + p_row[0]] += 1
        for p_id, count_val in p_tally.items():
            if count_val >= 0.5 * len(inst_set):
                state.class_core_predicates[c_uri].add(p_id)
    state.all_universe_classes: list[str] = sorted(state.class_instances.keys())
    state.all_universe_classes = sorted(
        set(state.all_universe_classes)
        | {str(c) for c in state.training_graph.objects(None, RDF.type)}
    )
    mining_classes = sorted(
        state.class_instances, key=lambda c: (-len(state.class_instances[c]), c)
    )[: state.config["MAX_MINING_CLASSES"]]
    state.MINING_REPORT = {
        "classes_considered": len(mining_classes),
        "classes_omitted_from_search": max(
            0, len(state.class_instances) - len(mining_classes)
        ),
    }
    tau_sub: float = float(state.config["TAU_SUB"])
    tau_sig: float = float(state.config["TAU_SIG"])
    wilson_z: float = float(state.config["WILSON_Z"])
    tau_intensional_sub: float = float(state.config["TAU_INTENSIONAL_SUB"])
    state.candidate_taxonomic_pairs: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()
    for i in range(len(mining_classes)):
        for j in range(i + 1, len(mining_classes)):
            c1: str = mining_classes[i]
            c2: str = mining_classes[j]
            set1: set[str] = state.class_instances[c1]
            set2: set[str] = state.class_instances[c2]
            overlap: set[str] = set1 & set2
            if not overlap:
                continue
            p_c2_given_c1: float = len(overlap) / len(set1)
            p_c1_given_c2: float = len(overlap) / len(set2)
            jaccard: float = len(overlap) / len(set1 | set2)
            w_12: float = wilson_lower(len(overlap), len(set1), wilson_z)
            w_21: float = wilson_lower(len(overlap), len(set2), wilson_z)
            jw_sim: float = lexical_similarity(local_name(c1), local_name(c2))
            if max(p_c2_given_c1, p_c1_given_c2) >= tau_sub or jaccard >= tau_sig:
                seen_pairs.add((c1, c2))
                state.candidate_taxonomic_pairs.append(
                    {
                        "c1": c1,
                        "c2": c2,
                        "c1_name": local_name(c1),
                        "c2_name": local_name(c2),
                        "c1_count": len(set1),
                        "c2_count": len(set2),
                        "overlap": len(overlap),
                        "p_c2_c1": p_c2_given_c1,
                        "p_c1_c2": p_c1_given_c2,
                        "w_12": w_12,
                        "w_21": w_21,
                        "jaccard": jaccard,
                        "jw_sim": jw_sim,
                        "mining_mode": "extensional",
                        "shared_core_preds": sorted(
                            [
                                local_name(p)
                                for p in state.class_core_predicates[c1]
                                & state.class_core_predicates[c2]
                            ]
                        ),
                    }
                )
    for i in range(len(mining_classes)):
        for j in range(i + 1, len(mining_classes)):
            c1 = mining_classes[i]
            c2 = mining_classes[j]
            if (c1, c2) in seen_pairs:
                continue
            if (
                c1 in state.induced_class_uris or c2 in state.induced_class_uris
            ) and len(state.class_instances[c1] & state.class_instances[c2]) == 0:
                core1: set[str] = state.class_core_predicates[c1]
                core2: set[str] = state.class_core_predicates[c2]
                inter_core: set[str] = core1 & core2
                s_int_12: float = len(inter_core) / len(core2) if core2 else 0.0
                s_int_21: float = len(inter_core) / len(core1) if core1 else 0.0
                jw_sim = lexical_similarity(local_name(c1), local_name(c2))
                if (
                    max(s_int_12, s_int_21) >= tau_intensional_sub or jw_sim >= 0.7
                ) and len(inter_core) >= 1:
                    seen_pairs.add((c1, c2))
                    state.candidate_taxonomic_pairs.append(
                        {
                            "c1": c1,
                            "c2": c2,
                            "c1_name": local_name(c1),
                            "c2_name": local_name(c2),
                            "c1_count": len(state.class_instances[c1]),
                            "c2_count": len(state.class_instances[c2]),
                            "overlap": 0,
                            "p_c2_c1": s_int_12,
                            "p_c1_c2": s_int_21,
                            "w_12": 0.0,
                            "w_21": 0.0,
                            "jaccard": len(inter_core) / max(1, len(core1 | core2)),
                            "jw_sim": jw_sim,
                            "mining_mode": "signature_containment",
                            "shared_core_preds": sorted(
                                [local_name(p) for p in inter_core]
                            ),
                        }
                    )
    state.log(f"Taxonomic candidate pairs: {len(state.candidate_taxonomic_pairs)}")
    state.candidate_taxonomic_pairs.sort(
        key=lambda p: (-p["overlap"], p["c1"], p["c2"])
    )
    state.candidate_taxonomic_pairs = state.candidate_taxonomic_pairs[
        : int(state.config["MAX_DECISION_PAIRS"])
    ]


def mine_roles_and_restrictions(state: PipelineState) -> None:
    "Mine role implications and score local restriction proposals."
    state.object_props: list[str] = sorted(
        list(
            {
                r[0]
                for r in state.cur.execute(
                    "SELECT DISTINCT predicate FROM triples WHERE is_literal = 0 AND predicate != ?",
                    (rdf_type_str,),
                ).fetchall()
                if not is_meta_uri(r[0])
            }
        )
    )
    state.datatype_props: list[str] = sorted(
        list(
            {
                r[0]
                for r in state.cur.execute(
                    "SELECT DISTINCT predicate FROM triples WHERE is_literal = 1"
                ).fetchall()
                if not is_meta_uri(r[0])
            }
        )
    )
    state.all_domain_properties: list[str] = sorted(
        list(set(state.object_props + state.datatype_props))
    )
    if set(state.object_props) & set(state.datatype_props):
        raise ValueError(
            f"Mixed object/literal property usage requires normalization: {set(state.object_props) & set(state.datatype_props)}"
        )
    state.property_profiles: dict[str, dict[str, Any]] = {}
    state.edges_by_prop: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for s, p, o, is_lit, _ in state.cur.execute(
        "SELECT subject, predicate, object, is_literal, datatype FROM triples WHERE predicate != ?",
        (rdf_type_str,),
    ).fetchall():
        state.edges_by_prop[p].add((s, o))
    for p in state.all_domain_properties:
        p_edges = state.edges_by_prop[p]
        s_set = {s for s, o in p_edges}
        o_set = {o for s, o in p_edges}
        e_cnt = max(1, len(p_edges))
        func_val = len(s_set) / e_cnt
        ifunc_val = len(o_set) / e_cnt
        if p in state.object_props and len(p_edges) >= 2:
            successors = defaultdict(set)
            for source, target in p_edges:
                successors[source].add(target)
            two_hops = {(x, z) for x, y in p_edges for z in successors[y]}
            trans_hits = len(two_hops & p_edges)
            rho_trans = trans_hits / len(two_hops) if two_hops else 0.0
            recip_hits = sum((1 for x, y in p_edges if (y, x) in p_edges))
            rho_sym = recip_hits / e_cnt
            rho_asym = 1.0 - rho_sym
            refl_hits = sum((1 for x, y in p_edges if x == y))
            rho_refl = refl_hits / max(1, len(s_set))
            rho_irrefl = 1.0 - rho_refl
        else:
            rho_trans = 0.0
            rho_sym = 0.0
            rho_asym = 1.0
            rho_refl = 0.0
            rho_irrefl = 1.0
        state.property_profiles[p] = {
            "uri": p,
            "name": local_name(p),
            "is_object": p in state.object_props,
            "support": len(p_edges),
            "func": func_val,
            "ifunc": ifunc_val,
            "rho_func": func_val,
            "rho_invfunc": ifunc_val,
            "rho_trans": rho_trans,
            "rho_sym": rho_sym,
            "rho_asym": rho_asym,
            "rho_refl": rho_refl,
            "rho_irrefl": rho_irrefl,
        }
    state.candidate_subproperties: list[dict[str, Any]] = []
    state.candidate_inverses: list[dict[str, Any]] = []
    state.candidate_property_chains: list[dict[str, Any]] = []
    amie_min_hc: float = float(state.config["AMIE_MIN_HC"])
    amie_min_pca_conf: float = float(state.config["AMIE_MIN_PCA_CONF"])
    mining_object_props = sorted(
        state.object_props, key=lambda p: (-len(state.edges_by_prop[p]), p)
    )[: state.config["MAX_MINING_PROPERTIES"]]
    if hasattr(state, "MINING_REPORT"):
        state.MINING_REPORT["properties_omitted_from_role_search"] = len(
            state.object_props
        ) - len(mining_object_props)
    for p in mining_object_props:
        for q in mining_object_props:
            if p == q:
                continue
            sub_supp = len(state.edges_by_prop[p] & state.edges_by_prop[q])
            if sub_supp >= 5:
                hc = sub_supp / len(state.edges_by_prop[q])
                s_q = {x for x, y in state.edges_by_prop[q]}
                o_q = {y for x, y in state.edges_by_prop[q]}
                pca_den = (
                    len({(x, y) for x, y in state.edges_by_prop[p] if x in s_q})
                    if state.property_profiles[q]["func"]
                    >= state.property_profiles[q]["ifunc"]
                    else len({(x, y) for x, y in state.edges_by_prop[p] if y in o_q})
                )
                conf_pca = sub_supp / pca_den if pca_den > 0 else 0.0
                if hc >= amie_min_hc and conf_pca >= amie_min_pca_conf:
                    state.candidate_subproperties.append(
                        {
                            "sub": p,
                            "super": q,
                            "supp": sub_supp,
                            "hc": hc,
                            "conf_pca": conf_pca,
                        }
                    )
            inv_supp = len(
                {
                    (x, y)
                    for x, y in state.edges_by_prop[q]
                    if (y, x) in state.edges_by_prop[p]
                }
            )
            if inv_supp >= 5:
                hc_inv = inv_supp / len(state.edges_by_prop[q])
                s_q = {x for x, y in state.edges_by_prop[q]}
                pca_inv_den = len(
                    {(y, x) for y, x in state.edges_by_prop[p] if x in s_q}
                )
                conf_pca_inv = inv_supp / pca_inv_den if pca_inv_den > 0 else 0.0
                if hc_inv >= amie_min_hc and conf_pca_inv >= 0.7:
                    state.candidate_inverses.append(
                        {
                            "p": p,
                            "q": q,
                            "supp": inv_supp,
                            "hc": hc_inv,
                            "conf_pca": conf_pca_inv,
                        }
                    )
    for p1 in mining_object_props:
        for p2 in mining_object_props:
            z_to_y = defaultdict(set)
            for z, y in state.edges_by_prop[p2]:
                z_to_y[z].add(y)
            two_hop_edges = set()
            for x, z in state.edges_by_prop[p1]:
                for y in z_to_y.get(z, ()):
                    two_hop_edges.add((x, y))
                    if len(two_hop_edges) > state.config["MAX_JOIN_EDGES"]:
                        raise ValueError(
                            "Property-chain join exceeds MAX_JOIN_EDGES; output preserved"
                        )
            if len(two_hop_edges) < 5:
                continue
            for p3 in mining_object_props:
                if p3 == p1 or p3 == p2:
                    continue
                chain_supp = len(two_hop_edges & state.edges_by_prop[p3])
                if chain_supp >= 5:
                    hc_chain = chain_supp / len(state.edges_by_prop[p3])
                    s_p3 = {x for x, y in state.edges_by_prop[p3]}
                    o_p3 = {y for x, y in state.edges_by_prop[p3]}
                    pca_chain_den = (
                        len({(x, y) for x, y in two_hop_edges if x in s_p3})
                        if state.property_profiles[p3]["func"]
                        >= state.property_profiles[p3]["ifunc"]
                        else len({(x, y) for x, y in two_hop_edges if y in o_p3})
                    )
                    conf_pca_chain = (
                        chain_supp / pca_chain_den if pca_chain_den > 0 else 0.0
                    )
                    if hc_chain >= amie_min_hc and conf_pca_chain >= 0.8:
                        state.candidate_property_chains.append(
                            {
                                "chain": [p1, p2],
                                "super": p3,
                                "p1": p1,
                                "p2": p2,
                                "p3": p3,
                                "supp": chain_supp,
                                "hc": hc_chain,
                                "conf_pca": conf_pca_chain,
                            }
                        )
    all_domain_instances: set[str] = (
        set.union(*state.class_instances.values()) if state.class_instances else set()
    )
    state.candidate_local_restrictions: list[dict[str, Any]] = []
    for c_uri in sorted(
        state.class_instances, key=lambda c: (-len(state.class_instances[c]), c)
    )[: state.config["MAX_MINING_CLASSES"]]:
        pos_instances = state.class_instances[c_uri]
        if len(pos_instances) < 3:
            continue
        neg_instances = all_domain_instances - pos_instances
        q_parent_baseline = 0.5
        for r_prop in mining_object_props:
            fillers_by_class: dict[str, set[tuple[str, str]]] = defaultdict(set)
            for s_inst in pos_instances:
                for (o_inst,) in state.cur.execute(
                    "SELECT object FROM triples WHERE subject = ? AND predicate = ? AND is_literal = 0",
                    (s_inst, r_prop),
                ).fetchall():
                    for (o_type,) in state.cur.execute(
                        "SELECT object FROM triples WHERE subject = ? AND predicate = ? AND is_literal = 0",
                        (o_inst, rdf_type_str),
                    ):
                        if not is_meta_uri(o_type):
                            fillers_by_class[o_type].add((s_inst, o_inst))
            for target_class, edges_matched in fillers_by_class.items():
                pos_cov_set = {s for s, o in edges_matched}
                pos_cov = len(pos_cov_set) / len(pos_instances)
                neg_cov_set = set()
                for neg_inst in neg_instances:
                    for (o_neg,) in state.cur.execute(
                        "SELECT object FROM triples WHERE subject = ? AND predicate = ? AND is_literal = 0",
                        (neg_inst, r_prop),
                    ).fetchall():
                        for (ot_neg,) in state.cur.execute(
                            "SELECT object FROM triples WHERE subject = ? AND predicate = ? AND is_literal = 0",
                            (o_neg, rdf_type_str),
                        ):
                            if ot_neg == target_class:
                                neg_cov_set.add(neg_inst)
                tp_val = len(pos_cov_set)
                fp_val = len(neg_cov_set)
                fn_val = len(pos_instances) - tp_val
                prec_val = tp_val / (tp_val + fp_val) if tp_val + fp_val > 0 else 0.0
                rec_val = tp_val / (tp_val + fn_val) if tp_val + fn_val > 0 else 0.0
                f1_quality = (
                    2.0 * prec_val * rec_val / (prec_val + rec_val)
                    if prec_val + rec_val > 0
                    else 0.0
                )
                phi_celoe = celoe_heuristic(
                    q_parent_baseline,
                    f1_quality,
                    3,
                    float(state.config["CELOE_LAMBDA"]),
                    float(state.config["CELOE_BETA"]),
                )
                total_r_edges = state.cur.execute(
                    "SELECT subject, object FROM triples WHERE subject IN ({}) AND predicate = ? AND is_literal = 0".format(
                        ",".join("?" * len(pos_instances))
                    ),
                    (*pos_instances, r_prop),
                ).fetchall()
                purity = (
                    len(edges_matched) / len(total_r_edges) if total_r_edges else 0.0
                )
                if (
                    phi_celoe >= float(state.config["THETA_LOCAL_RESTRICTION"])
                    and pos_cov >= 0.5
                ):
                    state.candidate_local_restrictions.append(
                        {
                            "type": "someValuesFrom",
                            "class": c_uri,
                            "property": r_prop,
                            "filler": target_class,
                            "phi_celoe": phi_celoe,
                            "coverage": pos_cov,
                            "verbalization": f"Every instance of {local_name(c_uri)} is linked via {local_name(r_prop)} to at least one instance of {local_name(target_class)}",
                        }
                    )
                if purity >= 0.95 and len(edges_matched) >= 3:
                    state.candidate_local_restrictions.append(
                        {
                            "type": "allValuesFrom",
                            "class": c_uri,
                            "property": r_prop,
                            "filler": target_class,
                            "phi_celoe": phi_celoe,
                            "coverage": purity,
                            "verbalization": f"Every instance of {local_name(c_uri)} linked via {local_name(r_prop)} has only fillers of type {local_name(target_class)}",
                        }
                    )
    state.log(
        f"Scored restriction candidates: {len(state.candidate_local_restrictions)}, property chains: {len(state.candidate_property_chains)}"
    )
    for candidates in (
        state.candidate_subproperties,
        state.candidate_inverses,
        state.candidate_property_chains,
        state.candidate_local_restrictions,
    ):
        candidates.sort(
            key=lambda c: (
                -c.get("supp", c.get("coverage", 0)),
                json.dumps(c, sort_keys=True),
            )
        )
        del candidates[state.config["MAX_EVIDENCE_CANDIDATES"] :]
