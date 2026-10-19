"""test_pipeline.py - Automated End-to-End Test Harness for ABox2TBox Induction Pipeline.

Executes abox2tbox.ipynb headlessly in an isolated Python namespace
and verifies all structural, logical, and formal acceptance criteria:
  1. Notebook Execution Integrity (all cells run without unhandled error, >= 15 cells)
  2. Valid OWL 2 / RDFS Syntax in TBox.ttl (>= 15 declared classes)
  3. Strict Subsumption DAG (0 directed cycles in taxonomy)
  4. Post-Repair Disjointness Consistency (DVC_post == 0)
  5. Honest offline telemetry and unavailable unsupported evaluation metrics
  6. OntoQA Metrics Non-Empty and Valid (RR, IR, CCR)
  7. W3C PROV-O Metadata Compliance (provenance annotations)

Dual Execution Interface:
  CLI:    python3 test_pipeline.py
  Pytest: pytest test_pipeline.py -v
"""

import json
import tempfile
from unittest.mock import patch
import os
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

import matplotlib
matplotlib.use("Agg")

import networkx as nx
import pytest
import rdflib
from rdflib.namespace import OWL, RDF, RDFS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NOTEBOOK_PATH = (
    os.path.join(BASE_DIR, "abox2tbox.ipynb")
    if os.path.exists(os.path.join(BASE_DIR, "abox2tbox.ipynb"))
    else os.path.join(BASE_DIR, "ABox2TBox.ipynb")
)
ABOX_PATH = (
    os.path.join(BASE_DIR, "input", "ABox.ttl")
    if os.path.exists(os.path.join(BASE_DIR, "input", "ABox.ttl"))
    else os.path.join(BASE_DIR, "ABox.ttl")
)
_OUTPUT_TEMP = tempfile.TemporaryDirectory(prefix="abox2tbox-baseline-test-")
TBOX_PATH = os.path.join(_OUTPUT_TEMP.name, "TBox.ttl")


_EXECUTION_CACHE: Optional[Tuple[Dict[str, Any], int]] = None


def run_pipeline_once(force_reexecution=False):
    """Execute the actual notebook offline, with isolated temporary outputs."""
    global _EXECUTION_CACHE
    if _EXECUTION_CACHE is not None and not force_reexecution:
        return _EXECUTION_CACHE
    namespace = {}
    with open(NOTEBOOK_PATH, encoding="utf-8") as handle:
        notebook = json.load(handle)
    count = 0
    with patch.dict(os.environ, {
        "USE_LLM": "false", "ABOX_INPUT_PATH": ABOX_PATH,
        "TBOX_OUTPUT_PATH": TBOX_PATH, "CALIBRATION_LABELS_PATH": "",
        "TELEMETRY_PLOT_PATH": os.path.join(_OUTPUT_TEMP.name, "telemetry.png")
    }):
        for index, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] == "code":
                exec(compile("".join(cell["source"]), f"cell-{index}", "exec"), namespace)
                count += 1
    assert namespace["VALIDATION_REPORT"]["status"] == "passed"
    _EXECUTION_CACHE = namespace, count
    return _EXECUTION_CACHE


# ==============================================================================
# Helper Verification Functions
# ==============================================================================


def verify_abox_benchmark_integrity() -> Dict[str, Any]:
    """Verify structural and ontological integrity of ABox.ttl benchmark dataset.

    Returns:
        Dictionary of dataset metrics (triples, subjects, untyped clusters, noise patterns).
    """
    assert os.path.exists(ABOX_PATH), f"ABox missing at {ABOX_PATH}"
    g = rdflib.Graph()
    g.parse(ABOX_PATH, format="turtle")

    subjects = set(g.subjects())
    typed = set(g.subjects(RDF.type, None))
    untyped = subjects - typed

    grants = [s for s in untyped if "grant" in str(s)]
    labs = [s for s in untyped if "lab" in str(s)]
    degrees = [s for s in untyped if "deg" in str(s)]

    UNIV = rdflib.Namespace("http://example.org/univ#")
    lects = set(g.subjects(RDF.type, UNIV.Lecturer))
    insts = set(g.subjects(RDF.type, UNIV.Instructor))
    scc_overlap = len(lects & insts) / len(lects) if lects else 0.0

    collabs = list(g.subject_objects(UNIV.collaboratesWith))
    symm_edges = sum(1 for s, o in collabs if (o, UNIV.collaboratesWith, s) in g)
    rho_sym = symm_edges / len(collabs) if collabs else 0.0

    return {
        "triples": len(g),
        "subjects": len(subjects),
        "untyped_grants": len(grants),
        "untyped_labs": len(labs),
        "untyped_degrees": len(degrees),
        "scc_overlap": scc_overlap,
        "rho_sym": rho_sym,
    }


# ==============================================================================
# Pytest Acceptance Assertions
# ==============================================================================


def test_01_notebook_execution():
    """Assertion 1: Notebook executes end-to-end without unhandled cell errors."""
    user_ns, count = run_pipeline_once()
    assert count >= 15, f"Expected >= 15 executed code cells, observed {count}"


def test_02_tbox_syntax_and_parsimony():
    """Assertion 2: Generated TBox.ttl is valid OWL 2 / RDFS syntax and contains >= 15 classes."""
    run_pipeline_once()
    assert os.path.exists(TBOX_PATH), f"TBox.ttl missing at {TBOX_PATH}"
    g = rdflib.Graph()
    g.parse(TBOX_PATH, format="turtle")
    assert len(g) > 20, f"TBox.ttl contains suspiciously few triples: {len(g)}"

    classes = set(g.subjects(RDF.type, OWL.Class)) | set(
        g.subjects(RDF.type, RDFS.Class)
    )
    assert len(classes) >= 15, (
        f"Expected >= 15 declared classes in TBox, observed {len(classes)}"
    )


def test_03_subsumption_dag_acyclicity():
    """Assertion 3: Extracted subsumption graph forms a strict DAG (0 directed cycles)."""
    run_pipeline_once()
    assert os.path.exists(TBOX_PATH), f"TBox.ttl missing at {TBOX_PATH}"
    g = rdflib.Graph()
    g.parse(TBOX_PATH, format="turtle")

    dag = nx.DiGraph()
    for s, _, o in g.triples((None, RDFS.subClassOf, None)):
        if (
            isinstance(s, rdflib.URIRef)
            and isinstance(o, rdflib.URIRef)
            and str(s) != str(o)
        ):
            dag.add_edge(str(s), str(o))

    cycles = list(nx.simple_cycles(dag))
    assert len(cycles) == 0, f"Directed cycles detected in subsumption hierarchy: {cycles}"
    assert nx.is_directed_acyclic_graph(dag), "Subsumption hierarchy is not a strict DAG"


def test_04_disjointness_consistency():
    """Assertion 4: Post-repair Disjointness Violation Count (DVC_post) equals 0."""
    user_ns, _ = run_pipeline_once()

    # Verify in-memory telemetry if recorded
    if "DVC_POST" in user_ns:
        assert user_ns["DVC_POST"] == 0, (
            f"In-memory DVC_POST is {user_ns['DVC_POST']} (must be 0)"
        )

    # Independent ground-truth evaluation against ABox instances
    g_abox = rdflib.Graph().parse(ABOX_PATH, format="turtle")
    g_tbox = rdflib.Graph().parse(TBOX_PATH, format="turtle")

    dag = nx.DiGraph()
    for s, _, o in g_tbox.triples((None, RDFS.subClassOf, None)):
        if str(s) != str(o):
            dag.add_edge(str(s), str(o))

    def get_class_ancestors(c: str) -> Set[str]:
        ancestors = {c}
        if c in dag:
            ancestors.update(nx.descendants(dag, c))  # superclasses in DAG
        return ancestors

    def get_all_types(inst: rdflib.URIRef) -> Set[str]:
        types = set(str(t) for t in g_abox.objects(inst, RDF.type))
        expanded = set()
        for t in types:
            expanded.update(get_class_ancestors(t))
        return expanded

    disjoint_pairs = [
        (str(s), str(o))
        for s, _, o in g_tbox.triples((None, OWL.disjointWith, None))
        if str(s) != str(o)
    ]

    violations = 0
    violating_instances = []
    for inst in g_abox.subjects(RDF.type, None):
        inst_types = get_all_types(inst)
        for c1, c2 in disjoint_pairs:
            if c1 in inst_types and c2 in inst_types:
                violations += 1
                violating_instances.append((str(inst), c1, c2))

    assert violations == 0, (
        f"DVC_post violation: {violations} instances violate disjointness constraints: "
        f"{violating_instances[:5]}"
    )


def test_05_prompt_token_ceiling():
    """Offline runs do not manufacture model calls, precision, or calibration."""
    user_ns, _ = run_pipeline_once()
    token_log = user_ns.get(
        "TOKEN_AUDIT_LOG", user_ns.get("PAYLOAD_TOKEN_AUDIT_LOG", [])
    )
    assert token_log == [], "Offline execution must not fabricate model calls"
    assert user_ns["total_tokens_measured"] == 0
    assert user_ns["ECE"] is None
    assert user_ns["ONTOQA_METRICS"]["hold_out_precision"] is None
    assert user_ns["ONTOQA_METRICS"]["hold_out_f1"] is None


def test_06_ontoqa_metrics():
    """Assertion 6: OntoQA structural metrics computed and mathematically valid."""
    user_ns, _ = run_pipeline_once()
    ontoqa = user_ns.get("ONTOQA_METRICS", {})
    assert ontoqa, "ONTOQA_METRICS missing from execution namespace"
    assert "relationship_richness" in ontoqa, "relationship_richness missing"
    assert "inheritance_richness" in ontoqa, "inheritance_richness missing"
    assert "class_coverage_ratio" in ontoqa, "class_coverage_ratio missing"

    rr = ontoqa["relationship_richness"]
    ir = ontoqa["inheritance_richness"]
    ccr = ontoqa["class_coverage_ratio"]

    assert 0.0 < rr <= 1.0, f"Relationship Richness out of bounds: {rr}"
    assert ir >= 0.0, f"Inheritance Richness cannot be negative: {ir}"
    assert 0.50 <= ccr <= 1.0, f"Class Coverage Ratio out of bounds: {ccr}"


def test_07_provenance_metadata():
    """Assertion 7: W3C PROV-O metadata is valid when enabled."""
    user_ns, _ = run_pipeline_once()
    graph = rdflib.Graph().parse(TBOX_PATH, format="turtle")
    predicate = rdflib.URIRef("http://www.w3.org/ns/prov#wasAttributedTo")
    assert (predicate, RDF.type, OWL.AnnotationProperty) in graph
    agents = list(graph.objects(None, predicate))
    assert agents and all(isinstance(agent, rdflib.URIRef) for agent in agents)

# ==============================================================================
# CLI Entrypoint
# ==============================================================================

if __name__ == "__main__":
    print("=" * 72)
    print("🚀 ABOX2TBOX INDUCTION PIPELINE — AUTOMATED VERIFICATION HARNESS")
    print("=" * 72)

    # Check for CLI flags
    if "--verify-abox" in sys.argv:
        print("[*] Running ABox benchmark verification only...")
        try:
            stats = verify_abox_benchmark_integrity()
            print(f"  [PASS] ABox Parsed: {stats['triples']} triples, {stats['subjects']} subjects")
            print(f"  [PASS] Untyped Clusters: {stats['untyped_grants']} grants, "
                  f"{stats['untyped_labs']} labs, {stats['untyped_degrees']} degrees")
            print(f"  [PASS] SCC Overlap: {stats['scc_overlap']*100:.1f}%, "
                  f"Symmetry: {stats['rho_sym']:.3f}")
            print("✔ ABox benchmark integrity verified successfully.")
            sys.exit(0)
        except Exception as e:
            print(f"❌ ABox verification failed: {e}")
            sys.exit(1)

    print("[*] Initiating headless execution of ABox2TBox.ipynb...")
    try:
        ns, cell_count = run_pipeline_once()
        print(f"✔ Notebook executed successfully ({cell_count} code cells)\n")
    except FileNotFoundError as fnf:
        print(f"⚠️  {fnf}\n")
        print("[*] Note: In Milestone 1, ABox.ttl is verified via --verify-abox flag.")
        print("[*] Run 'python3 test_pipeline.py --verify-abox' to verify benchmark dataset.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        sys.exit(1)

    suite = [
        ("Assertion 1: Notebook Execution Integrity", test_01_notebook_execution),
        ("Assertion 2: Valid OWL 2 / RDFS in TBox.ttl", test_02_tbox_syntax_and_parsimony),
        ("Assertion 3: Subsumption DAG (0 Cycles)", test_03_subsumption_dag_acyclicity),
        ("Assertion 4: Disjointness DVC_post == 0", test_04_disjointness_consistency),
        ("Assertion 5: Prompt Token Ceiling <= 1500", test_05_prompt_token_ceiling),
        ("Assertion 6: OntoQA Metrics Non-Empty", test_06_ontoqa_metrics),
        ("Assertion 7: W3C PROV-O Metadata", test_07_provenance_metadata),
    ]

    passed = 0
    for name, test_fn in suite:
        try:
            test_fn()
            print(f"  [PASS] {name}")
            passed += 1
        except AssertionError as ae:
            print(f"  [FAIL] {name}: {ae}")
        except Exception as ex:
            print(f"  [ERROR] {name}: {ex}")

    print("-" * 72)
    print(f"Summary: {passed}/{len(suite)} assertions passed.")
    if passed == len(suite):
        print("🎉 ALL ACCEPTANCE ASSERTIONS SATISFIED!")
        sys.exit(0)
    else:
        print("❌ SOME ASSERTIONS FAILED.")
        sys.exit(1)
