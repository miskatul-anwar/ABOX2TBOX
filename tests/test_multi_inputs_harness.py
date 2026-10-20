"""test_multi_inputs_harness.py - Comprehensive Multi-Input Verification for the Python API.

Tests the Python API against:
  1. Standard Domains: Baseline (University), E-Commerce, Hospital, Enterprise, Banking
  2. Diverse RDF Formats: Turtle, N-Triples, JSON-LD, RDF/XML, TriG, N-Quads, Notation3, TriX
  3. Semantic & Structural Variants: Empty ABox, Sparse Single-Instance, Mixed-property,
     Blank-Node Untyped Graph, Inconsistent ABox (Falsification), and Over-Limit Guard.
"""

from abox2tbox import run_pipeline
from collections import defaultdict
import io
import json
import os
import shutil
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import patch

import matplotlib

matplotlib.use("Agg")
import networkx as nx
import rdflib
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def execute_pipeline_on_input(
    input_path: str,
    rdf_format: Optional[str] = None,
    extra_env: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Execute the production pipeline against the specified input file."""
    temp_dir = tempfile.mkdtemp(prefix="abox2tbox-test-")
    tbox_out = os.path.join(temp_dir, "TBox.ttl")
    plot_out = os.path.join(temp_dir, "telemetry.png")

    env = {
        "USE_LLM": "false",
        "ABOX_INPUT_PATH": os.path.abspath(input_path),
        "TBOX_OUTPUT_PATH": tbox_out,
        "TELEMETRY_PLOT_PATH": plot_out,
        "CALIBRATION_LABELS_PATH": "",
    }
    if rdf_format:
        env["ABOX_FORMAT"] = rdf_format
    if extra_env:
        env.update(extra_env)

    ns: Dict[str, Any] = {}
    stdout_capture = io.StringIO()
    start_time = time.time()
    exception_raised = None
    stages_completed = 0

    try:
        with patch.dict(os.environ, env):
            with patch("sys.stdout", stdout_capture):
                result = run_pipeline(
                    input_path, tbox_out, plot_path=plot_out, rdf_format=rdf_format
                )
                ns = vars(result.state)
                stages_completed = len(result.state.completed_stages)
    except Exception as e:
        exception_raised = e

    elapsed = time.time() - start_time

    # Inspect outputs
    tbox_exists = os.path.exists(tbox_out)
    tbox_size = os.path.getsize(tbox_out) if tbox_exists else 0
    tbox_triples = 0
    classes_count = 0
    subclass_count = 0
    disjoint_count = 0
    is_dag = False
    cycles = []

    if tbox_exists and tbox_size > 0:
        try:
            g = Graph().parse(tbox_out, format="turtle")
            tbox_triples = len(g)
            classes = set(g.subjects(RDF.type, OWL.Class)) | set(
                g.subjects(RDF.type, RDFS.Class)
            )
            classes_count = len(classes)
            subclass_triples = list(g.triples((None, RDFS.subClassOf, None)))
            subclass_count = len(subclass_triples)
            disjoint_triples = list(g.triples((None, OWL.disjointWith, None)))
            disjoint_count = len(disjoint_triples)

            dag = nx.DiGraph()
            for s, _, o in subclass_triples:
                if str(s) != str(o):
                    dag.add_edge(str(s), str(o))
            cycles = list(nx.simple_cycles(dag))
            is_dag = len(cycles) == 0
        except Exception:
            pass

    validation = ns.get("VALIDATION_REPORT", {})
    ontoqa = ns.get("ONTOQA_METRICS", {})
    tokens_used = ns.get("total_tokens_measured", 0)

    # Clean up temp dir
    shutil.rmtree(temp_dir, ignore_errors=True)

    return {
        "input_path": input_path,
        "elapsed_s": round(elapsed, 2),
        "stages_completed": stages_completed,
        "exception": str(exception_raised) if exception_raised else None,
        "tbox_exists": tbox_exists,
        "tbox_size": tbox_size,
        "tbox_triples": tbox_triples,
        "classes_count": classes_count,
        "subclass_count": subclass_count,
        "disjoint_count": disjoint_count,
        "is_dag": is_dag,
        "cycles_detected": len(cycles),
        "validation_status": validation.get("status"),
        "tbox_coherent": validation.get("tbox_coherent"),
        "abox_consistent": validation.get("training_abox_consistent"),
        "ontoqa_rr": ontoqa.get("relationship_richness"),
        "ontoqa_ir": ontoqa.get("inheritance_richness"),
        "ontoqa_ccr": ontoqa.get("class_coverage_ratio"),
        "tokens_used": tokens_used,
    }


def main():
    print("=" * 80)
    print("ABOX2TBOX PYTHON API MULTI-INPUT VERIFICATION SUITE")
    print("=" * 80)

    results = []

    # --------------------------------------------------------------------------
    # Group 1: Five Benchmark Domains
    # --------------------------------------------------------------------------
    benchmark_domains = [
        ("Baseline (University)", "input/ABox.ttl", "turtle"),
        ("E-Commerce / Retail", "input/ecommerce_abox.ttl", "turtle"),
        ("Hospital / Biomedical", "input/hospital_abox.ttl", "turtle"),
        ("Corporate / Enterprise", "input/enterprise_abox.ttl", "turtle"),
        ("Financial / Banking", "input/banking_abox.ttl", "turtle"),
    ]

    print("\n--- 1. Testing Benchmark Domains ---")
    for name, rel_path, fmt in benchmark_domains:
        path = os.path.join(BASE_DIR, rel_path)
        print(f"Running domain: {name} ({rel_path})...")
        res = execute_pipeline_on_input(path, fmt)
        res["test_name"] = name
        res["category"] = "Benchmark Domain"
        results.append(res)
        print(
            f"  -> Done in {res['elapsed_s']}s | Classes: {res['classes_count']} | "
            f"Subclasses: {res['subclass_count']} | DAG: {res['is_dag']} | "
            f"Validation: {res['validation_status']}"
        )

    # --------------------------------------------------------------------------
    # Group 2: Multiple Serialization Formats
    # --------------------------------------------------------------------------
    print("\n--- 2. Testing Multiple RDF Serialization Formats ---")
    # Generate multi-format files from baseline ABox
    base_g = Graph().parse(os.path.join(BASE_DIR, "input/ABox.ttl"), format="turtle")
    formats_to_test = [
        ("N-Triples", "nt", "nt"),
        ("JSON-LD", "json-ld", "jsonld"),
        ("RDF/XML", "xml", "xml"),
        ("TriG", "trig", "trig"),
        ("N-Quads", "nquads", "nq"),
        ("Notation3", "n3", "n3"),
        ("TriX", "trix", "trix"),
    ]

    with tempfile.TemporaryDirectory(prefix="abox2tbox-formats-") as fmt_dir:
        for fmt_name, rdflib_fmt, ext in formats_to_test:
            target_file = os.path.join(fmt_dir, f"baseline.{ext}")
            try:
                if rdflib_fmt in ("trig", "nquads", "trix"):
                    ds = rdflib.Dataset()
                    for s, p, o in base_g:
                        ds.add((s, p, o, ds.default_context))
                    ds.serialize(target_file, format=rdflib_fmt)
                else:
                    base_g.serialize(target_file, format=rdflib_fmt)

                print(f"Running format: {fmt_name} (extension: .{ext})...")
                res = execute_pipeline_on_input(target_file, rdflib_fmt)
                res["test_name"] = f"Format: {fmt_name}"
                res["category"] = "RDF Serialization"
                results.append(res)
                print(
                    f"  -> Done in {res['elapsed_s']}s | Classes: {res['classes_count']} | "
                    f"Subclasses: {res['subclass_count']} | DAG: {res['is_dag']} | "
                    f"Validation: {res['validation_status']}"
                )
            except Exception as e:
                print(f"  -> Format {fmt_name} serialization/execution error: {e}")

    # --------------------------------------------------------------------------
    # Group 3: Edge Cases, Semantic Challenges & Falsification
    # --------------------------------------------------------------------------
    print("\n--- 3. Testing Semantic Edge Cases & Falsification ---")
    with tempfile.TemporaryDirectory(prefix="abox2tbox-edge-") as edge_dir:
        # 3.1 Empty ABox
        empty_file = os.path.join(edge_dir, "empty.ttl")
        with open(empty_file, "w") as f:
            f.write("")
        print("Running: Empty ABox (0 triples)...")
        res = execute_pipeline_on_input(empty_file, "turtle")
        res["test_name"] = "Empty ABox"
        res["category"] = "Semantic Edge Case"
        results.append(res)
        print(
            f"  -> Done in {res['elapsed_s']}s | TBox Size: {res['tbox_size']} bytes | "
            f"Validation: {res['validation_status']} | Coherent: {res['tbox_coherent']}"
        )

        # 3.2 Sparse Single Instance
        sparse_file = os.path.join(edge_dir, "sparse.ttl")
        with open(sparse_file, "w") as f:
            f.write(
                "@prefix ex: <http://example.org/> .\n ex:john a ex:Person ; ex:age 30 .\n"
            )
        print("Running: Sparse Single-Instance ABox...")
        res = execute_pipeline_on_input(sparse_file, "turtle")
        res["test_name"] = "Sparse Single-Instance"
        res["category"] = "Semantic Edge Case"
        results.append(res)
        print(
            f"  -> Done in {res['elapsed_s']}s | Classes: {res['classes_count']} | "
            f"Validation: {res['validation_status']}"
        )

        # 3.3 Blank Nodes and Untyped Instances
        bnode_file = os.path.join(edge_dir, "bnode.ttl")
        with open(bnode_file, "w") as f:
            f.write("""
            @prefix ex: <http://example.org/> .
            _:b1 ex:parentOf _:b2 .
            _:b2 ex:parentOf _:b3 .
            _:b1 ex:name "Grandparent" .
            _:b2 ex:name "Parent" .
            _:b3 ex:name "Child" .
            """)
        print("Running: Blank Nodes & Untyped Graph...")
        res = execute_pipeline_on_input(bnode_file, "turtle")
        res["test_name"] = "Blank Nodes Untyped"
        res["category"] = "Semantic Edge Case"
        results.append(res)
        print(
            f"  -> Done in {res['elapsed_s']}s | Classes: {res['classes_count']} | "
            f"Validation: {res['validation_status']}"
        )

        # 3.4 Mixed Datatype / Object Property
        mixed_file = os.path.join(edge_dir, "mixed.ttl")
        with open(mixed_file, "w") as f:
            f.write("""
            @prefix ex: <http://example.org/> .
            ex:inst1 a ex:Entity ; ex:hasCode "ABC123" .
            ex:inst2 a ex:Entity ; ex:hasCode ex:CodeResource .
            ex:CodeResource a ex:CodeDefinition .
            """)
        print("Running: Mixed Datatype/Object Predicate Normalization...")
        res = execute_pipeline_on_input(mixed_file, "turtle")
        res["test_name"] = "Mixed Predicate Normalization"
        res["category"] = "Semantic Edge Case"
        results.append(res)
        print(
            f"  -> Done in {res['elapsed_s']}s | Validation: {res['validation_status']}"
        )

        # 3.5 Contradictory Input (Inconsistent sameAs + differentFrom)
        inconsistent_file = os.path.join(edge_dir, "inconsistent.ttl")
        with open(inconsistent_file, "w") as f:
            f.write("""
            @prefix ex: <http://example.org/> .
            @prefix owl: <http://www.w3.org/2002/07/owl#> .
            ex:entityA owl:sameAs ex:entityB .
            ex:entityA owl:differentFrom ex:entityB .
            """)
        print("Running: Contradictory Input (sameAs + differentFrom)...")
        res = execute_pipeline_on_input(inconsistent_file, "turtle")
        res["test_name"] = "Contradictory Input (Fail-Closed)"
        res["category"] = "Falsification / Safety"
        results.append(res)
        print(
            f"  -> Correctly raised exception: {bool(res['exception'])} | "
            f"Error: {res['exception'][:60] if res['exception'] else 'None'}"
        )

        # 3.6 Over-Limit Input Guard (Exceeding MAX_INPUT_TRIPLES)
        overlimit_file = os.path.join(edge_dir, "overlimit.ttl")
        with open(overlimit_file, "w") as f:
            lines = ["@prefix ex: <http://example.org/> .\n"]
            for i in range(150):
                lines.append(f"ex:s{i} a ex:C{i % 5} .\n")
            f.writelines(lines)
        print("Running: Over-Limit Input Guard (configured limit=50, input=150)...")
        res = execute_pipeline_on_input(
            overlimit_file, "turtle", extra_env={"MAX_INPUT_TRIPLES": "50"}
        )
        res["test_name"] = "Over-Limit Triples Guard"
        res["category"] = "Falsification / Safety"
        results.append(res)
        print(
            f"  -> Correctly raised exception: {bool(res['exception'])} | "
            f"Error: {res['exception'][:60] if res['exception'] else 'None'}"
        )

    # Output detailed JSON report
    report_path = os.path.join(BASE_DIR, "output", "multi_input_test_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved comprehensive test report to {report_path}")

    return results


if __name__ == "__main__":
    main()


# ==============================================================================
# Pytest Interface
# ==============================================================================

import pytest


@pytest.mark.parametrize(
    "domain_name,rel_path",
    [
        ("Baseline (University)", "input/ABox.ttl"),
        ("E-Commerce / Retail", "input/ecommerce_abox.ttl"),
        ("Hospital / Biomedical", "input/hospital_abox.ttl"),
        ("Corporate / Enterprise", "input/enterprise_abox.ttl"),
        ("Financial / Banking", "input/banking_abox.ttl"),
    ],
)
def test_pytest_benchmark_domain(domain_name, rel_path):
    path = os.path.join(BASE_DIR, rel_path)
    res = execute_pipeline_on_input(path, "turtle")
    assert res["exception"] is None, f"Failed on {domain_name}: {res['exception']}"
    assert res["validation_status"] == "passed"
    assert res["is_dag"] is True
    assert res["classes_count"] >= 15


@pytest.mark.parametrize(
    "fmt_name,rdflib_fmt,ext",
    [
        ("N-Triples", "nt", "nt"),
        ("JSON-LD", "json-ld", "jsonld"),
        ("RDF/XML", "xml", "xml"),
        ("TriG", "trig", "trig"),
        ("N-Quads", "nquads", "nq"),
        ("Notation3", "n3", "n3"),
        ("TriX", "trix", "trix"),
    ],
)
def test_pytest_serialization_formats(tmp_path, fmt_name, rdflib_fmt, ext):
    base_g = Graph().parse(os.path.join(BASE_DIR, "input/ABox.ttl"), format="turtle")
    target_file = str(tmp_path / f"test.{ext}")
    if rdflib_fmt in ("trig", "nquads", "trix"):
        ds = rdflib.Dataset()
        for s, p, o in base_g:
            ds.add((s, p, o, ds.default_context))
        ds.serialize(target_file, format=rdflib_fmt)
    else:
        base_g.serialize(target_file, format=rdflib_fmt)
    res = execute_pipeline_on_input(target_file, rdflib_fmt)
    assert res["exception"] is None, f"Format {fmt_name} failed: {res['exception']}"
    assert res["validation_status"] == "passed"
    assert res["classes_count"] == 57


def test_pytest_empty_input(tmp_path):
    p = tmp_path / "empty.ttl"
    p.write_text("")
    res = execute_pipeline_on_input(str(p), "turtle")
    assert res["exception"] is None
    assert res["validation_status"] == "passed"
    assert res["tbox_exists"] is True


def test_pytest_inconsistent_fails_closed(tmp_path):
    p = tmp_path / "inconsistent.ttl"
    p.write_text("""@prefix ex: <http://example.org/> .
                    @prefix owl: <http://www.w3.org/2002/07/owl#> .
                    ex:a owl:sameAs ex:b ; owl:differentFrom ex:b .""")
    res = execute_pipeline_on_input(str(p), "turtle")
    assert res["exception"] is not None
    assert "validation failed" in res["exception"]
