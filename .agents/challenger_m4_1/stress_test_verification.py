#!/usr/bin/env python3
"""stress_test_verification.py - Standalone Adversarial Verification Suite.

Author: challenger_m4_1 (teamwork_preview_challenger)
Role: critic, specialist

Performs rigorous empirical stress testing across all benchmark domains:
1. DAG Acyclicity Stress-Test:
   - Tarjan SCC analysis (0 components with size > 1)
   - Johnson's elementary cycle enumeration (nx.simple_cycles(G) == 0)
   - Reflexivity / self-loop check (0 self-loops)
2. Transitive Reduction Minimality:
   - nx.transitive_reduction(G) edge identity check
   - Manual alternative path enumeration (0 transitive shortcuts)
3. Disjointness Consistency Stress-Test:
   - Full instance type expansion via DAG ancestors
   - owl:disjointWith axiom conflict cross-checking
   - Verification of DVC_post == 0 across all benchmark domains
   - Adversarial full-closure expansion (DAG + owl:equivalentClass)
"""

import json
import os
import sys
from typing import Any, Dict, List, Set, Tuple

import networkx as nx
import rdflib
from rdflib.namespace import OWL, RDF, RDFS

PROJECT_ROOT = "/home/miskat/ABOX2TBOX"

DOMAINS = [
    {
        "key": "baseline",
        "name": "University Baseline",
        "abox": os.path.join(PROJECT_ROOT, "input", "ABox.ttl"),
        "tbox": os.path.join(PROJECT_ROOT, "output", "TBox.ttl"),
    },
    {
        "key": "ecommerce",
        "name": "E-Commerce / Retail",
        "abox": os.path.join(PROJECT_ROOT, "input", "ecommerce_abox.ttl"),
        "tbox": os.path.join(PROJECT_ROOT, "output", "ecommerce_tbox.ttl"),
    },
    {
        "key": "hospital",
        "name": "Hospital / Biomedical",
        "abox": os.path.join(PROJECT_ROOT, "input", "hospital_abox.ttl"),
        "tbox": os.path.join(PROJECT_ROOT, "output", "hospital_tbox.ttl"),
    },
    {
        "key": "enterprise",
        "name": "Corporate / Enterprise",
        "abox": os.path.join(PROJECT_ROOT, "input", "enterprise_abox.ttl"),
        "tbox": os.path.join(PROJECT_ROOT, "output", "enterprise_tbox.ttl"),
    },
    {
        "key": "banking",
        "name": "Financial / Banking",
        "abox": os.path.join(PROJECT_ROOT, "input", "banking_abox.ttl"),
        "tbox": os.path.join(PROJECT_ROOT, "output", "banking_tbox.ttl"),
    },
]


def run_dag_acyclicity_test(tbox_path: str) -> Dict[str, Any]:
    """Execute Tarjan SCC and Johnson simple_cycles on subsumption graph."""
    g = rdflib.Graph().parse(tbox_path, format="turtle")
    G = nx.DiGraph()
    self_loops = []

    for s, p, o in g.triples((None, RDFS.subClassOf, None)):
        if isinstance(s, rdflib.URIRef) and isinstance(o, rdflib.URIRef):
            s_str, o_str = str(s), str(o)
            if s_str == o_str:
                self_loops.append(s_str)
            G.add_edge(s_str, o_str)

    # Tarjan's Strongly Connected Components
    sccs = list(nx.strongly_connected_components(G))
    non_trivial_sccs = [list(c) for c in sccs if len(c) > 1]

    # Johnson's elementary cycle enumeration
    simple_cycles = list(nx.simple_cycles(G))

    is_dag = nx.is_directed_acyclic_graph(G)
    longest_path_len = nx.dag_longest_path_length(G) if len(G) > 0 and is_dag else 0
    longest_path = [n.split("#")[-1] for n in nx.dag_longest_path(G)] if len(G) > 0 and is_dag else []

    roots = [n.split("#")[-1] for n, d in G.out_degree() if d == 0]
    leaves = [n.split("#")[-1] for n, d in G.in_degree() if d == 0]

    return {
        "nodes_count": G.number_of_nodes(),
        "edges_count": G.number_of_edges(),
        "self_loops_count": len(self_loops),
        "self_loops": self_loops,
        "is_dag": is_dag,
        "tarjan_total_sccs": len(sccs),
        "tarjan_non_trivial_sccs_count": len(non_trivial_sccs),
        "tarjan_non_trivial_sccs": non_trivial_sccs,
        "johnson_simple_cycles_count": len(simple_cycles),
        "johnson_simple_cycles": simple_cycles,
        "max_taxonomic_depth": longest_path_len,
        "longest_path_sample": longest_path,
        "roots_count": len(roots),
        "leaves_count": len(leaves),
        "passed": (is_dag and len(simple_cycles) == 0 and len(non_trivial_sccs) == 0 and len(self_loops) == 0),
    }


def run_transitive_reduction_test(tbox_path: str) -> Dict[str, Any]:
    """Verify that subsumption hierarchy equals its minimal Hasse diagram."""
    g = rdflib.Graph().parse(tbox_path, format="turtle")
    G = nx.DiGraph()

    for s, p, o in g.triples((None, RDFS.subClassOf, None)):
        if isinstance(s, rdflib.URIRef) and isinstance(o, rdflib.URIRef) and str(s) != str(o):
            G.add_edge(str(s), str(o))

    assert nx.is_directed_acyclic_graph(G), "Graph must be DAG for transitive reduction"
    G_tr = nx.transitive_reduction(G)

    redundant_edges = set(G.edges()) - set(G_tr.edges())

    # Exhaustive alternative path search
    alternative_path_violations = []
    for u, v in G.edges():
        G_temp = G.copy()
        G_temp.remove_edge(u, v)
        if nx.has_path(G_temp, u, v):
            paths = list(nx.all_simple_paths(G_temp, u, v))
            alternative_path_violations.append({
                "source": u.split("#")[-1],
                "target": v.split("#")[-1],
                "alternate_paths": [[x.split("#")[-1] for x in p] for p in paths]
            })

    return {
        "direct_edges_count": G.number_of_edges(),
        "hasse_edges_count": G_tr.number_of_edges(),
        "redundant_edges_count": len(redundant_edges),
        "redundant_edges": [f"{u.split('#')[-1]} -> {v.split('#')[-1]}" for u, v in redundant_edges],
        "alternative_path_shortcuts_count": len(alternative_path_violations),
        "alternative_path_shortcuts": alternative_path_violations,
        "passed": (len(redundant_edges) == 0 and len(alternative_path_violations) == 0),
    }


def run_disjointness_consistency_test(abox_path: str, tbox_path: str) -> Dict[str, Any]:
    """Cross-check expanded instance types against all owl:disjointWith axioms."""
    g_abox = rdflib.Graph().parse(abox_path, format="turtle")
    g_tbox = rdflib.Graph().parse(tbox_path, format="turtle")

    # Build DAG
    dag = nx.DiGraph()
    for s, p, o in g_tbox.triples((None, RDFS.subClassOf, None)):
        if isinstance(s, rdflib.URIRef) and isinstance(o, rdflib.URIRef) and str(s) != str(o):
            dag.add_edge(str(s), str(o))

    # Equivalent classes map
    eq_graph = nx.Graph()
    for s, p, o in g_tbox.triples((None, OWL.equivalentClass, None)):
        if isinstance(s, rdflib.URIRef) and isinstance(o, rdflib.URIRef) and str(s) != str(o):
            eq_graph.add_edge(str(s), str(o))

    # Disjoint pairs (canonical min, max)
    disjoint_pairs = set()
    for s, p, o in g_tbox.triples((None, OWL.disjointWith, None)):
        if isinstance(s, rdflib.URIRef) and isinstance(o, rdflib.URIRef) and str(s) != str(o):
            c1, c2 = str(s), str(o)
            disjoint_pairs.add((min(c1, c2), max(c1, c2)))

    # Instances and raw types
    raw_instance_types: Dict[str, Set[str]] = {}
    for s, p, o in g_abox.triples((None, RDF.type, None)):
        if isinstance(s, rdflib.URIRef) and isinstance(o, rdflib.URIRef):
            raw_instance_types.setdefault(str(s), set()).add(str(o))

    # Expansion Method 1: Standard DAG Ancestors (descendants in s -> o)
    def get_dag_ancestors(c: str) -> Set[str]:
        ans = {c}
        if c in dag:
            ans.update(nx.descendants(dag, c))
        return ans

    # Expansion Method 2: Full Equivalence + Subsumption Closure
    all_classes = set(dag.nodes()) | set(eq_graph.nodes())
    closure_cache: Dict[str, Set[str]] = {}
    for c in all_classes:
        cl = {c}
        if c in eq_graph:
            cl.update(nx.node_connected_component(eq_graph, c))
        changed = True
        while changed:
            old_len = len(cl)
            new_nodes = set()
            for x in cl:
                if x in dag:
                    for parent in dag.successors(x):
                        new_nodes.add(parent)
                        if parent in eq_graph:
                            new_nodes.update(nx.node_connected_component(eq_graph, parent))
            cl.update(new_nodes)
            changed = len(cl) > old_len
        closure_cache[c] = cl

    # Evaluate Violations
    dvc_dag = 0
    dvc_dag_violating_instances = []

    dvc_full_closure = 0
    dvc_full_closure_violating_instances = []

    for inst, types in raw_instance_types.items():
        # Expansion 1
        exp_dag = set()
        for t in types:
            exp_dag.update(get_dag_ancestors(t))

        inst_has_dag_violation = False
        for c1, c2 in disjoint_pairs:
            if c1 in exp_dag and c2 in exp_dag:
                dvc_dag += 1
                if not inst_has_dag_violation:
                    dvc_dag_violating_instances.append(inst.split("#")[-1])
                    inst_has_dag_violation = True

        # Expansion 2
        exp_full = set()
        for t in types:
            exp_full.update(closure_cache.get(t, {t}))

        inst_has_full_violation = False
        for c1, c2 in disjoint_pairs:
            if c1 in exp_full and c2 in exp_full:
                dvc_full_closure += 1
                if not inst_has_full_violation:
                    dvc_full_closure_violating_instances.append(inst.split("#")[-1])
                    inst_has_full_violation = True

    return {
        "instances_count": len(raw_instance_types),
        "disjoint_axioms_count": len(disjoint_pairs),
        "dvc_dag_ancestors": dvc_dag,
        "dvc_dag_violating_instances": dvc_dag_violating_instances,
        "dvc_full_closure": dvc_full_closure,
        "dvc_full_closure_violating_instances": dvc_full_closure_violating_instances,
        "passed_standard_contract": (dvc_dag == 0),
        "passed_full_closure": (dvc_full_closure == 0),
    }


def main():
    print("=" * 80)
    print("🔬 EMPIRICAL ADVERSARIAL STRESS TEST HARNESS — CHALLENGER M4-1")
    print("=" * 80)

    overall_results = {}
    all_passed = True

    for dom in DOMAINS:
        key = dom["key"]
        name = dom["name"]
        abox = dom["abox"]
        tbox = dom["tbox"]

        print(f"\n[*] Evaluating Domain: {name} ({key})")
        print(f"    ABox: {abox}")
        print(f"    TBox: {tbox}")

        if not os.path.exists(tbox):
            print(f"    [FAIL] TBox file missing at {tbox}")
            all_passed = False
            continue

        dag_res = run_dag_acyclicity_test(tbox)
        tr_res = run_transitive_reduction_test(tbox)
        disj_res = run_disjointness_consistency_test(abox, tbox)

        dom_passed = dag_res["passed"] and tr_res["passed"] and disj_res["passed_standard_contract"]
        if not dom_passed:
            all_passed = False

        overall_results[key] = {
            "name": name,
            "dag_acyclicity": dag_res,
            "transitive_reduction": tr_res,
            "disjointness_consistency": disj_res,
            "overall_passed": dom_passed,
        }

        print(f"    [DAG Acyclicity] Nodes={dag_res['nodes_count']}, Edges={dag_res['edges_count']}, "
              f"Cycles={dag_res['johnson_simple_cycles_count']}, Non-trivial SCCs={dag_res['tarjan_non_trivial_sccs_count']} "
              f"-> {'PASS' if dag_res['passed'] else 'FAIL'}")
        print(f"    [Transitive Reduction] Direct Edges={tr_res['direct_edges_count']}, Hasse Edges={tr_res['hasse_edges_count']}, "
              f"Redundant Edges={tr_res['redundant_edges_count']} -> {'PASS' if tr_res['passed'] else 'FAIL'}")
        print(f"    [Disjointness Consistency] Instances={disj_res['instances_count']}, Disjoint Pairs={disj_res['disjoint_axioms_count']}, "
              f"DVC_post (DAG)={disj_res['dvc_dag_ancestors']} -> {'PASS' if disj_res['passed_standard_contract'] else 'FAIL'}")
        print(f"    [Adversarial Equiv Probe] DVC_post (Full Closure)={disj_res['dvc_full_closure']}")

    output_json_path = os.path.join(os.path.dirname(__file__), "stress_test_results.json")
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(overall_results, f, indent=2)

    print("\n" + "=" * 80)
    print("VERDICT SUMMARY")
    print("=" * 80)
    print(f"All Domains Satisfied Formal Acceptance Criteria: {all_passed}")
    verdict = "APPROVE" if all_passed else "CHALLENGE_FAILED"
    print(f"FINAL CHALLENGER VERDICT: {verdict}")
    print(f"Saved full JSON results to: {output_json_path}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
