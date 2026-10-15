"""test_cross_domain.py - Automated Cross-Domain Verification Harness (Milestone 3).

Executes ABox2TBox.ipynb across all 5 benchmark domains in complete isolation:
  1. University Baseline (input/ABox.ttl)
  2. E-Commerce / Retail (input/ecommerce_abox.ttl)
  3. Hospital / Biomedical (input/hospital_abox.ttl)
  4. Corporate / Enterprise (input/enterprise_abox.ttl)
  5. Financial / Banking (input/banking_abox.ttl)

For every domain, verifies the 7 formal acceptance assertions:
  - Assertion 1: Notebook execution integrity (>= 15 code cells, no unhandled exceptions)
  - Assertion 2: Valid OWL 2 / RDFS syntax with >= 15 declared classes
  - Assertion 3: Subsumption hierarchy forms a strict DAG (0 directed cycles)
  - Assertion 4: Post-repair disjointness violations DVC_post == 0
  - Assertion 5: Strict prompt token ceiling (maximum payload <= 1,500 tokens)
  - Assertion 6: OntoQA metrics within mathematical bounds (0 < RR <= 1.0, IR > 0, 0.5 <= CCR <= 1.0)
  - Assertion 7: W3C PROV-O reification metadata present and valid

Dual Execution Interface:
  CLI:    python3 test_cross_domain.py
  Pytest: pytest test_cross_domain.py -v
"""

import argparse
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

import matplotlib
matplotlib.use("Agg")

from IPython.core.interactiveshell import InteractiveShell
import networkx as nx
import pytest
import rdflib
from rdflib.namespace import OWL, RDF, RDFS

# ==============================================================================
# Configuration & Domain Benchmarks Specification
# ==============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NOTEBOOK_PATH = os.path.join(BASE_DIR, "ABox2TBox.ipynb")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

DOMAINS: Dict[str, Dict[str, Any]] = {
    "baseline": {
        "key": "baseline",
        "name": "University Baseline",
        "abox_path": (
            os.path.join(BASE_DIR, "input", "ABox.ttl")
            if os.path.exists(os.path.join(BASE_DIR, "input", "ABox.ttl"))
            else os.path.join(BASE_DIR, "ABox.ttl")
        ),
        "tbox_path": os.path.join(OUTPUT_DIR, "TBox.ttl"),
        "plot_path": os.path.join(OUTPUT_DIR, "telemetry_diagnostics.png"),
        "namespace": "http://example.org/univ#",
    },
    "ecommerce": {
        "key": "ecommerce",
        "name": "E-Commerce / Retail",
        "abox_path": os.path.join(BASE_DIR, "input", "ecommerce_abox.ttl"),
        "tbox_path": os.path.join(OUTPUT_DIR, "ecommerce_tbox.ttl"),
        "plot_path": os.path.join(OUTPUT_DIR, "ecommerce_telemetry.png"),
        "namespace": "http://example.org/ecommerce#",
    },
    "hospital": {
        "key": "hospital",
        "name": "Hospital / Biomedical",
        "abox_path": os.path.join(BASE_DIR, "input", "hospital_abox.ttl"),
        "tbox_path": os.path.join(OUTPUT_DIR, "hospital_tbox.ttl"),
        "plot_path": os.path.join(OUTPUT_DIR, "hospital_telemetry.png"),
        "namespace": "http://example.org/hospital#",
    },
    "enterprise": {
        "key": "enterprise",
        "name": "Corporate / Enterprise",
        "abox_path": os.path.join(BASE_DIR, "input", "enterprise_abox.ttl"),
        "tbox_path": os.path.join(OUTPUT_DIR, "enterprise_tbox.ttl"),
        "plot_path": os.path.join(OUTPUT_DIR, "enterprise_telemetry.png"),
        "namespace": "http://example.org/enterprise#",
    },
    "banking": {
        "key": "banking",
        "name": "Financial / Banking",
        "abox_path": os.path.join(BASE_DIR, "input", "banking_abox.ttl"),
        "tbox_path": os.path.join(OUTPUT_DIR, "banking_tbox.ttl"),
        "plot_path": os.path.join(OUTPUT_DIR, "banking_telemetry.png"),
        "namespace": "http://example.org/banking#",
    },
}

_EXECUTION_CACHE: Dict[str, Tuple[Dict[str, Any], int]] = {}
_METRICS_CACHE: Dict[str, Dict[str, Any]] = {}


# ==============================================================================
# Pipeline Execution Engine
# ==============================================================================


def run_pipeline_for_domain(
    domain_key: str, force_reexecution: bool = False, verbose: bool = False
) -> Tuple[Dict[str, Any], int]:
    """Execute ABox2TBox.ipynb in complete isolation for a specific benchmark domain.

    Injects domain-specific environment variables (`ABOX_INPUT_PATH`,
    `TBOX_OUTPUT_PATH`, `TELEMETRY_PLOT_PATH`) and executes within a fresh
    `InteractiveShell` instance with cleared memory and relational state.

    Args:
        domain_key: Identifier key in DOMAINS dictionary.
        force_reexecution: If True, bypass execution cache and rerun.
        verbose: If True, stream cell stdout/stderr directly.

    Returns:
        Tuple containing (user_namespace, executed_cell_count).

    Raises:
        KeyError: If domain_key is not in DOMAINS.
        FileNotFoundError: If notebook or ABox file is missing.
        RuntimeError: If any notebook code cell fails.
    """
    global _EXECUTION_CACHE
    if domain_key in _EXECUTION_CACHE and not force_reexecution:
        return _EXECUTION_CACHE[domain_key]

    if domain_key not in DOMAINS:
        raise KeyError(
            f"Unknown domain '{domain_key}'. Available: {list(DOMAINS.keys())}"
        )

    cfg = DOMAINS[domain_key]
    abox_path = cfg["abox_path"]
    tbox_path = cfg["tbox_path"]
    plot_path = cfg["plot_path"]

    if not os.path.exists(NOTEBOOK_PATH):
        raise FileNotFoundError(
            f"Notebook artifact not found at {NOTEBOOK_PATH}."
        )

    if not os.path.exists(abox_path):
        raise FileNotFoundError(
            f"Benchmark ABox dataset for '{domain_key}' not found at {abox_path}."
        )

    os.makedirs(os.path.dirname(tbox_path), exist_ok=True)
    os.makedirs(os.path.dirname(plot_path), exist_ok=True)

    # Invalidate existing output artifacts to guarantee fresh materialization
    if force_reexecution:
        if os.path.exists(tbox_path):
            try:
                os.remove(tbox_path)
            except OSError:
                pass
        if os.path.exists(plot_path):
            try:
                os.remove(plot_path)
            except OSError:
                pass

    # Inject isolated environment parameters
    os.environ["ABOX_INPUT_PATH"] = abox_path
    os.environ["TBOX_OUTPUT_PATH"] = tbox_path
    os.environ["TELEMETRY_PLOT_PATH"] = plot_path

    # Instantiate fresh isolated InteractiveShell
    InteractiveShell.clear_instance()
    shell = InteractiveShell.instance()

    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
        nb = json.load(f)

    captured_output = io.StringIO()
    executed_count = 0

    for idx, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") == "code":
            source = "".join(cell.get("source", []))
            if not source.strip():
                continue

            if verbose:
                res = shell.run_cell(source)
            else:
                with redirect_stdout(captured_output), redirect_stderr(
                    captured_output
                ):
                    res = shell.run_cell(source)

            if not res.success:
                err = res.error_in_exec or RuntimeError(
                    f"Domain '{domain_key}' notebook cell {idx} failed execution."
                )
                if not verbose:
                    print(
                        f"[-] Execution failure in domain '{domain_key}' cell {idx}:\n"
                        f"{captured_output.getvalue()}",
                        file=sys.stderr,
                    )
                raise err
            executed_count += 1

    _EXECUTION_CACHE[domain_key] = (shell.user_ns, executed_count)
    return _EXECUTION_CACHE[domain_key]


# ==============================================================================
# Domain Assertion Verification Functions
# ==============================================================================


def verify_assertion_1_notebook_execution(domain_key: str) -> int:
    """Assertion 1: Notebook execution integrity (>= 15 code cells without error)."""
    user_ns, count = run_pipeline_for_domain(domain_key)
    assert count >= 15, (
        f"Domain '{domain_key}': Expected >= 15 executed code cells, observed {count}"
    )
    return count


def verify_assertion_2_tbox_syntax_and_classes(domain_key: str) -> int:
    """Assertion 2: Valid OWL 2 / RDFS syntax in TBox.ttl with >= 15 declared classes."""
    run_pipeline_for_domain(domain_key)
    cfg = DOMAINS[domain_key]
    tbox_path = cfg["tbox_path"]
    assert os.path.exists(tbox_path), (
        f"Domain '{domain_key}': TBox file missing at {tbox_path}"
    )

    g = rdflib.Graph()
    g.parse(tbox_path, format="turtle")
    assert len(g) > 20, (
        f"Domain '{domain_key}': TBox contains suspiciously few triples: {len(g)}"
    )

    classes = set(g.subjects(RDF.type, OWL.Class)) | set(
        g.subjects(RDF.type, RDFS.Class)
    )
    assert len(classes) >= 15, (
        f"Domain '{domain_key}': Expected >= 15 declared classes, observed {len(classes)}"
    )
    return len(classes)


def verify_assertion_3_subsumption_dag_acyclicity(
    domain_key: str,
) -> Tuple[bool, int]:
    """Assertion 3: Subsumption hierarchy forms a strict DAG (0 directed cycles)."""
    run_pipeline_for_domain(domain_key)
    cfg = DOMAINS[domain_key]
    tbox_path = cfg["tbox_path"]
    assert os.path.exists(tbox_path), (
        f"Domain '{domain_key}': TBox file missing at {tbox_path}"
    )

    g = rdflib.Graph()
    g.parse(tbox_path, format="turtle")

    dag = nx.DiGraph()
    for s, _, o in g.triples((None, RDFS.subClassOf, None)):
        if (
            isinstance(s, rdflib.URIRef)
            and isinstance(o, rdflib.URIRef)
            and str(s) != str(o)
        ):
            dag.add_edge(str(s), str(o))

    cycles = list(nx.simple_cycles(dag))
    assert len(cycles) == 0, (
        f"Domain '{domain_key}': Directed cycles detected in subsumption hierarchy: {cycles}"
    )
    assert nx.is_directed_acyclic_graph(dag), (
        f"Domain '{domain_key}': Subsumption hierarchy is not a strict DAG"
    )
    return True, dag.number_of_edges()


def verify_assertion_4_disjointness_consistency(domain_key: str) -> int:
    """Assertion 4: Post-repair disjointness violations DVC_post == 0."""
    user_ns, _ = run_pipeline_for_domain(domain_key)
    cfg = DOMAINS[domain_key]
    abox_path = cfg["abox_path"]
    tbox_path = cfg["tbox_path"]

    # Verify in-memory telemetry if recorded
    if "DVC_POST" in user_ns:
        assert user_ns["DVC_POST"] == 0, (
            f"Domain '{domain_key}': In-memory DVC_POST is {user_ns['DVC_POST']} (must be 0)"
        )

    # Independent ground-truth evaluation against ABox instances
    g_abox = rdflib.Graph().parse(abox_path, format="turtle")
    g_tbox = rdflib.Graph().parse(tbox_path, format="turtle")

    dag = nx.DiGraph()
    for s, _, o in g_tbox.triples((None, RDFS.subClassOf, None)):
        if str(s) != str(o):
            dag.add_edge(str(s), str(o))

    def get_class_ancestors(c: str) -> Set[str]:
        ancestors = {c}
        if c in dag:
            ancestors.update(nx.descendants(dag, c))
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
        f"Domain '{domain_key}': DVC_post violation: {violations} instances violate disjointness: "
        f"{violating_instances[:5]}"
    )
    return violations


def verify_assertion_5_prompt_token_ceiling(domain_key: str) -> int:
    """Assertion 5: Maximum recorded token payload <= 1,500 tokens."""
    user_ns, _ = run_pipeline_for_domain(domain_key)
    token_log = user_ns.get(
        "TOKEN_AUDIT_LOG", user_ns.get("PAYLOAD_TOKEN_AUDIT_LOG", [])
    )
    assert len(token_log) > 0, (
        f"Domain '{domain_key}': TOKEN_AUDIT_LOG is missing or empty"
    )
    max_tokens = max(entry.get("tokens", 0) for entry in token_log)
    assert max_tokens <= 1500, (
        f"Domain '{domain_key}': Token ceiling violation! Max payload was {max_tokens} > 1500 tokens."
    )
    return max_tokens


def verify_assertion_6_ontoqa_metrics(
    domain_key: str,
) -> Tuple[float, float, float]:
    """Assertion 6: OntoQA metrics within valid mathematical bounds."""
    user_ns, _ = run_pipeline_for_domain(domain_key)
    ontoqa = user_ns.get("ONTOQA_METRICS", {})
    assert ontoqa, (
        f"Domain '{domain_key}': ONTOQA_METRICS missing from execution namespace"
    )

    rr = float(
        ontoqa.get("relationship_richness", ontoqa.get("RelationshipRichness", 0.0))
    )
    ir = float(
        ontoqa.get("inheritance_richness", ontoqa.get("InheritanceRichness", 0.0))
    )
    ccr = float(
        ontoqa.get("class_coverage_ratio", ontoqa.get("ClassCoverageRatio", 0.0))
    )

    assert 0.0 < rr <= 1.0, (
        f"Domain '{domain_key}': Relationship Richness out of bounds: {rr}"
    )
    assert ir > 0.0, (
        f"Domain '{domain_key}': Inheritance Richness must be positive: {ir}"
    )
    assert 0.50 <= ccr <= 1.0, (
        f"Domain '{domain_key}': Class Coverage Ratio out of bounds: {ccr}"
    )
    return rr, ir, ccr


def verify_assertion_7_provenance_metadata(domain_key: str) -> int:
    """Assertion 7: W3C PROV-O reification metadata present and syntactically valid."""
    user_ns, _ = run_pipeline_for_domain(domain_key)
    cfg = DOMAINS[domain_key]
    strict_mode = user_ns.get("EXPORT_STRICT_OWL2_DL", False)
    tbox_path = cfg["tbox_path"]
    assert os.path.exists(tbox_path), (
        f"Domain '{domain_key}': TBox file missing at {tbox_path}"
    )

    g = rdflib.Graph().parse(tbox_path, format="turtle")
    prov_pred = rdflib.URIRef("http://www.w3.org/ns/prov#wasAttributedTo")
    prov_triples = list(g.triples((None, prov_pred, None)))
    axioms = list(g.subjects(RDF.type, OWL.Axiom))

    if not strict_mode:
        assert len(prov_triples) > 0, (
            f"Domain '{domain_key}': PROV-O wasAttributedTo triples missing in TBox"
        )
        assert len(axioms) > 0, (
            f"Domain '{domain_key}': OWL:Axiom reification instances missing in TBox"
        )
    return len(prov_triples)


# ==============================================================================
# Comparative Analytics & Metrics Extraction
# ==============================================================================


def compute_domain_metrics(domain_key: str) -> Dict[str, Any]:
    """Compute and compile comprehensive verification metrics for a domain."""
    global _METRICS_CACHE
    if domain_key in _METRICS_CACHE:
        return _METRICS_CACHE[domain_key]

    cfg = DOMAINS[domain_key]
    user_ns, cell_count = run_pipeline_for_domain(domain_key)
    abox_path = cfg["abox_path"]
    tbox_path = cfg["tbox_path"]

    g_abox = rdflib.Graph().parse(abox_path, format="turtle")
    g_tbox = rdflib.Graph().parse(tbox_path, format="turtle")

    classes = set(g_tbox.subjects(RDF.type, OWL.Class)) | set(
        g_tbox.subjects(RDF.type, RDFS.Class)
    )

    dag = nx.DiGraph()
    for s, _, o in g_tbox.triples((None, RDFS.subClassOf, None)):
        if (
            isinstance(s, rdflib.URIRef)
            and isinstance(o, rdflib.URIRef)
            and str(s) != str(o)
        ):
            dag.add_edge(str(s), str(o))

    is_dag = nx.is_directed_acyclic_graph(dag)
    cycles = list(nx.simple_cycles(dag))
    dag_status = "DAG (0 cyc)" if is_dag and len(cycles) == 0 else f"CYC ({len(cycles)})"

    # Evaluate disjointness
    def get_class_ancestors(c: str) -> Set[str]:
        ancestors = {c}
        if c in dag:
            ancestors.update(nx.descendants(dag, c))
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
    for inst in g_abox.subjects(RDF.type, None):
        inst_types = get_all_types(inst)
        for c1, c2 in disjoint_pairs:
            if c1 in inst_types and c2 in inst_types:
                violations += 1

    token_log = user_ns.get(
        "TOKEN_AUDIT_LOG", user_ns.get("PAYLOAD_TOKEN_AUDIT_LOG", [])
    )
    max_tokens = max((e.get("tokens", 0) for e in token_log), default=0)

    ontoqa = user_ns.get("ONTOQA_METRICS", {})
    rr = float(
        ontoqa.get("relationship_richness", ontoqa.get("RelationshipRichness", 0.0))
    )
    ir = float(
        ontoqa.get("inheritance_richness", ontoqa.get("InheritanceRichness", 0.0))
    )
    ccr = float(
        ontoqa.get("class_coverage_ratio", ontoqa.get("ClassCoverageRatio", 0.0))
    )

    prov_triples = list(
        g_tbox.triples((None, rdflib.URIRef("http://www.w3.org/ns/prov#wasAttributedTo"), None))
    )

    # Check if all 7 acceptance criteria pass
    passed = (
        cell_count >= 15
        and len(classes) >= 15
        and is_dag
        and len(cycles) == 0
        and violations == 0
        and max_tokens <= 1500
        and 0.0 < rr <= 1.0
        and ir > 0.0
        and 0.50 <= ccr <= 1.0
        and len(prov_triples) > 0
    )

    metrics = {
        "key": domain_key,
        "domain": cfg["name"],
        "abox_triples": len(g_abox),
        "tbox_triples": len(g_tbox),
        "classes": len(classes),
        "hasse_edges": dag.number_of_edges(),
        "dag_status": dag_status,
        "dvc_post": violations,
        "max_tokens": max_tokens,
        "rr": rr,
        "ir": ir,
        "ccr": ccr,
        "prov_triples": len(prov_triples),
        "status": "PASS" if passed else "FAIL",
    }
    _METRICS_CACHE[domain_key] = metrics
    return metrics


def render_comparative_table(metrics_list: List[Dict[str, Any]]) -> str:
    """Render a formatted ASCII comparative analytics table."""
    headers = [
        "Domain",
        "ABox Triples",
        "TBox Triples",
        "Declared Classes",
        "Hasse Edges",
        "DAG Status",
        "DVC_post",
        "Max Tokens",
        "RR",
        "IR",
        "CCR",
        "Status",
    ]

    rows = []
    for m in metrics_list:
        rows.append(
            [
                m["domain"],
                str(m["abox_triples"]),
                str(m["tbox_triples"]),
                str(m["classes"]),
                str(m["hasse_edges"]),
                m["dag_status"],
                str(m["dvc_post"]),
                str(m["max_tokens"]),
                f"{m['rr']:.4f}",
                f"{m['ir']:.4f}",
                f"{m['ccr']:.4f}",
                m["status"],
            ]
        )

    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(val))

    def make_border(char="-", cross="+"):
        return cross + cross.join(char * (w + 2) for w in widths) + cross

    def make_line(values):
        cells = [f" {val.ljust(widths[i])} " for i, val in enumerate(values)]
        return "|" + "|".join(cells) + "|"

    border = make_border("-", "+")
    header_line = make_line(headers)
    rendered_rows = [make_line(row) for row in rows]

    return "\n".join([border, header_line, border] + rendered_rows + [border])


# ==============================================================================
# Pytest Parameterized Test Suite
# ==============================================================================

DOMAIN_KEYS = list(DOMAINS.keys())


@pytest.mark.parametrize("domain_key", DOMAIN_KEYS)
def test_01_notebook_execution(domain_key: str):
    """Assertion 1: Notebook execution integrity (>= 15 cells, no exceptions)."""
    verify_assertion_1_notebook_execution(domain_key)


@pytest.mark.parametrize("domain_key", DOMAIN_KEYS)
def test_02_tbox_syntax_and_parsimony(domain_key: str):
    """Assertion 2: Valid OWL 2 / RDFS syntax in TBox.ttl with >= 15 declared classes."""
    verify_assertion_2_tbox_syntax_and_classes(domain_key)


@pytest.mark.parametrize("domain_key", DOMAIN_KEYS)
def test_03_subsumption_dag_acyclicity(domain_key: str):
    """Assertion 3: Subsumption hierarchy forms a strict DAG (0 directed cycles)."""
    verify_assertion_3_subsumption_dag_acyclicity(domain_key)


@pytest.mark.parametrize("domain_key", DOMAIN_KEYS)
def test_04_disjointness_consistency(domain_key: str):
    """Assertion 4: Post-repair disjointness violations DVC_post == 0."""
    verify_assertion_4_disjointness_consistency(domain_key)


@pytest.mark.parametrize("domain_key", DOMAIN_KEYS)
def test_05_prompt_token_ceiling(domain_key: str):
    """Assertion 5: Strict prompt token ceiling (maximum payload <= 1,500 tokens)."""
    verify_assertion_5_prompt_token_ceiling(domain_key)


@pytest.mark.parametrize("domain_key", DOMAIN_KEYS)
def test_06_ontoqa_metrics(domain_key: str):
    """Assertion 6: OntoQA metrics within valid mathematical bounds."""
    verify_assertion_6_ontoqa_metrics(domain_key)


@pytest.mark.parametrize("domain_key", DOMAIN_KEYS)
def test_07_provenance_metadata(domain_key: str):
    """Assertion 7: W3C PROV-O reification metadata present and syntactically valid."""
    verify_assertion_7_provenance_metadata(domain_key)


def test_08_comparative_summary_matrix():
    """Assertion 8: Formatted comparative summary matrix compiles across all 5 domains."""
    metrics_list = [compute_domain_metrics(k) for k in DOMAIN_KEYS]
    table = render_comparative_table(metrics_list)
    print("\n" + table)

    # Verify all domains passed
    failed_domains = [m["domain"] for m in metrics_list if m["status"] != "PASS"]
    assert len(failed_domains) == 0, (
        f"The following benchmark domains failed verification: {failed_domains}"
    )


# ==============================================================================
# CLI Entrypoint
# ==============================================================================


def main() -> int:
    """CLI Entrypoint for cross-domain verification harness."""
    parser = argparse.ArgumentParser(
        description="Automated Cross-Domain Verification Harness for ABox2TBox Induction Pipeline."
    )
    parser.add_argument(
        "--domain",
        choices=list(DOMAINS.keys()),
        default=None,
        help="Execute verification for a specific domain only.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Stream full stdout/stderr during notebook cell execution.",
    )
    args = parser.parse_args()

    target_domains = [args.domain] if args.domain else list(DOMAINS.keys())

    print("=" * 80)
    print("🚀 ABOX2TBOX MULTI-DOMAIN CROSS-VERIFICATION HARNESS (MILESTONE 3)")
    print("=" * 80)
    print(f"[*] Target Benchmark Domains ({len(target_domains)}):")
    for key in target_domains:
        cfg = DOMAINS[key]
        print(f"    - [{key}] {cfg['name']}: {cfg['abox_path']}")
    print("-" * 80)

    all_domain_metrics: List[Dict[str, Any]] = []
    total_assertions = 0
    passed_assertions = 0

    suite_assertions = [
        ("Assertion 1: Notebook Execution Integrity (>= 15 cells)", verify_assertion_1_notebook_execution),
        ("Assertion 2: Valid OWL 2 / RDFS Syntax (>= 15 classes)", verify_assertion_2_tbox_syntax_and_classes),
        ("Assertion 3: Subsumption DAG (0 Directed Cycles)", verify_assertion_3_subsumption_dag_acyclicity),
        ("Assertion 4: Post-Repair Disjointness (DVC_post == 0)", verify_assertion_4_disjointness_consistency),
        ("Assertion 5: Prompt Token Ceiling (<= 1,500 tokens)", verify_assertion_5_prompt_token_ceiling),
        ("Assertion 6: OntoQA Metrics in Valid Bounds", verify_assertion_6_ontoqa_metrics),
        ("Assertion 7: W3C PROV-O Reification Metadata", verify_assertion_7_provenance_metadata),
    ]

    for idx, domain_key in enumerate(target_domains, 1):
        cfg = DOMAINS[domain_key]
        print(f"\n[{idx}/{len(target_domains)}] Evaluating Domain: {cfg['name']} ({domain_key})")
        try:
            _, cell_count = run_pipeline_for_domain(domain_key, verbose=args.verbose)
            print(f"  ✔ Notebook executed successfully ({cell_count} code cells)")
        except Exception as e:
            print(f"  ❌ Notebook execution failed: {e}")
            all_domain_metrics.append({
                "key": domain_key,
                "domain": cfg["name"],
                "abox_triples": 0,
                "tbox_triples": 0,
                "classes": 0,
                "hasse_edges": 0,
                "dag_status": "FAILED",
                "dvc_post": -1,
                "max_tokens": -1,
                "rr": 0.0,
                "ir": 0.0,
                "ccr": 0.0,
                "status": "FAIL",
            })
            continue

        domain_passed = True
        for assert_name, assert_fn in suite_assertions:
            total_assertions += 1
            try:
                assert_fn(domain_key)
                print(f"  [PASS] {assert_name}")
                passed_assertions += 1
            except AssertionError as ae:
                print(f"  [FAIL] {assert_name}: {ae}")
                domain_passed = False
            except Exception as ex:
                print(f"  [ERROR] {assert_name}: {ex}")
                domain_passed = False

        metrics = compute_domain_metrics(domain_key)
        all_domain_metrics.append(metrics)

    print("\n" + "=" * 80)
    print("📊 CROSS-DOMAIN COMPARATIVE ANALYTICS & SUMMARY MATRIX")
    print("=" * 80)
    print(render_comparative_table(all_domain_metrics))
    print("-" * 80)

    failed_domains = [m["domain"] for m in all_domain_metrics if m["status"] != "PASS"]
    print(
        f"Summary: {len(all_domain_metrics) - len(failed_domains)}/{len(all_domain_metrics)} "
        f"domains passed all 7 acceptance assertions "
        f"({passed_assertions}/{total_assertions} assertions passed)."
    )

    if not failed_domains:
        print("🎉 ALL CROSS-DOMAIN ACCEPTANCE ASSERTIONS SATISFIED!")
        return 0
    else:
        print(f"❌ VERIFICATION FAILED for domains: {failed_domains}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
