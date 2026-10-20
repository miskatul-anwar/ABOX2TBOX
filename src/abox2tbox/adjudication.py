"""Counterexample-first confirmation of proposed schema axioms."""

from __future__ import annotations
from collections import defaultdict
import itertools
from .state import PipelineState
from .transport import assess_candidate


def adjudicate_taxonomy(state: PipelineState) -> None:
    "Test directed taxonomy candidates and withhold ambiguous directions."
    state.adjudicated_subsumptions, state.adjudicated_equivalences = ([], [])
    state.taxonomic_predictions = {}
    for pair in state.candidate_taxonomic_pairs:
        if pair["mining_mode"] != "extensional":
            for sub, sup in [(pair["c1"], pair["c2"]), (pair["c2"], pair["c1"])]:
                assess_candidate(state, "subclass", {"sub": sub, "super": sup})
            continue
        for sub, sup in [(pair["c1"], pair["c2"]), (pair["c2"], pair["c1"])]:
            result = assess_candidate(state, "subclass", {"sub": sub, "super": sup})
            if result["status"] == "accepted":
                state.adjudicated_subsumptions.append(
                    {
                        "sub": sub,
                        "super": sup,
                        "conf": result["belief"][
                            "probability_coverage_exceeds_threshold"
                        ],
                        "supp": result["support_subjects"],
                        "mode": "independent_confirmation",
                        "source": "subject_confirmation_with_skeptical_prior",
                        "support_fraction": result["support_subjects"]
                        / (result["support_subjects"] + result["unobserved_subjects"]),
                        "evidence_id": result["id"],
                    }
                )
    directions = {(e["sub"], e["super"]) for e in state.adjudicated_subsumptions}
    ambiguous = {(a, b) for a, b in directions if (b, a) in directions}
    for record in state.evidence_gate.records:
        if (
            record["family"] == "subclass"
            and (record["candidate"]["sub"], record["candidate"]["super"]) in ambiguous
        ):
            record["status"] = "withheld"
            record["reasons"].append(
                "bidirectional_observations_do_not_identify_taxonomy"
            )
    state.adjudicated_subsumptions = [
        e
        for e in state.adjudicated_subsumptions
        if (e["sub"], e["super"]) not in ambiguous
    ]
    state.log(
        f"Evidence-admitted subclass hypotheses: {len(state.adjudicated_subsumptions)}"
    )


def assess_disjointness(state: PipelineState) -> None:
    "Record non-overlap without turning absence into disjointness."
    state.candidate_disjoint_pairs, state.adjudicated_disjoint_pairs = ([], [])
    for c1, c2 in itertools.islice(
        itertools.combinations(state.all_universe_classes, 2),
        state.config["MAX_DECISION_PAIRS"],
    ):
        if min(
            len(state.class_instances[c1]), len(state.class_instances[c2])
        ) >= 5 and (not state.class_instances[c1] & state.class_instances[c2]):
            candidate = {"c1": c1, "c2": c2}
            state.candidate_disjoint_pairs.append(candidate)
            assess_candidate(state, "disjoint", candidate)
    state.log(
        f"Withheld {len(state.candidate_disjoint_pairs)} disjointness proposals: absence is not negation"
    )


def adjudicate_roles(state: PipelineState) -> None:
    "Apply independent confirmation to expressive candidate families."
    state.adjudicated_property_characteristics = defaultdict(list)
    state.characteristic_metrics = {
        "Functional": "rho_func",
        "InverseFunctional": "rho_invfunc",
        "Transitive": "rho_trans",
        "Symmetric": "rho_sym",
        "Asymmetric": "rho_asym",
        "Reflexive": "rho_refl",
        "Irreflexive": "rho_irrefl",
    }
    for prop in state.all_domain_properties:
        profile = state.property_profiles[prop]
        for characteristic, metric in state.characteristic_metrics.items():
            if prop in state.datatype_props and characteristic != "Functional":
                continue
            if profile["support"] >= 5 and profile[metric] >= 0.9:
                result = assess_candidate(state, characteristic, {"property": prop})
                if result["status"] == "accepted":
                    state.adjudicated_property_characteristics[prop].append(
                        characteristic
                    )

    def evidence_candidates(candidates, family):
        return [
            c
            for c in candidates
            if assess_candidate(state, family, c)["status"] == "accepted"
        ]

    state.adjudicated_subproperties = evidence_candidates(
        state.candidate_subproperties, "subproperty"
    )
    state.adjudicated_inverses = evidence_candidates(
        state.candidate_inverses, "inverse"
    )
    state.adjudicated_chains = evidence_candidates(
        state.candidate_property_chains, "chain"
    )
    state.adjudicated_local_restrictions = evidence_candidates(
        state.candidate_local_restrictions, "restriction"
    )
    state.log("Evidence decisions:", state.evidence_gate.report()["status_counts"])


def infer_domains_ranges(state: PipelineState) -> None:
    "Confirm domain, resource-range, and literal-range proposals."
    state.property_domains: dict[str, str] = {}
    state.property_ranges: dict[str, str] = {}
    theta_dom_rng: float = float(state.config["THETA_DOMAIN_RANGE"])
    for p in state.all_domain_properties:
        s_insts = {s for s, o in state.edges_by_prop[p]}
        qualifying_doms = []
        for c_uri in state.all_universe_classes:
            c_insts = state.class_instances[c_uri]
            if (
                c_insts
                and len(s_insts & c_insts) / max(1, len(s_insts)) >= theta_dom_rng
            ):
                qualifying_doms.append((len(c_insts), c_uri))
        if qualifying_doms:
            qualifying_doms.sort(key=lambda x: x[0])
            chosen = qualifying_doms[0][1]
            if (
                assess_candidate(state, "domain", {"property": p, "class": chosen})[
                    "status"
                ]
                == "accepted"
            ):
                state.property_domains[p] = chosen
        if p in state.object_props:
            o_obj_insts = {o for s, o in state.edges_by_prop[p]}
            qualifying_rngs = []
            for c_uri in state.all_universe_classes:
                c_insts = state.class_instances[c_uri]
                if (
                    c_insts
                    and len(o_obj_insts & c_insts) / max(1, len(o_obj_insts))
                    >= theta_dom_rng
                ):
                    qualifying_rngs.append((len(c_insts), c_uri))
            if qualifying_rngs:
                qualifying_rngs.sort(key=lambda x: x[0])
                chosen = qualifying_rngs[0][1]
                if (
                    assess_candidate(state, "range", {"property": p, "class": chosen})[
                        "status"
                    ]
                    == "accepted"
                ):
                    state.property_ranges[p] = chosen
    state.property_datatype_ranges = {}
    for prop in state.datatype_props:
        counts = state.cur.execute(
            "SELECT datatype, COUNT(DISTINCT subject) FROM triples WHERE predicate=? AND is_literal=1 GROUP BY datatype ORDER BY COUNT(DISTINCT subject) DESC, datatype",
            (prop,),
        ).fetchall()
        if counts:
            datatype = counts[0][0]
            result = assess_candidate(
                state, "datatype_range", {"property": prop, "datatype": datatype}
            )
            if result["status"] == "accepted":
                state.property_datatype_ranges[prop] = datatype
