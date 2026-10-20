"""Try to falsify induction, including situations where abstention is the answer."""

import json
from pathlib import Path

import pytest
from abox2tbox import run_pipeline
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD

from abox2tbox.induction_evidence import (
    EvidenceGate,
    beta_tail,
    coverage_belief,
    load_abox,
    split_assertions,
    term_key,
)

EX = Namespace("urn:challenge:")
ROOT = Path(__file__).resolve().parent.parent


def population(n=240, missing=0):
    graph = Graph()
    for i in range(n):
        graph.add((EX[f"a{i}"], RDF.type, EX.A))
        if i >= missing:
            graph.add((EX[f"a{i}"], RDF.type, EX.B))
    # A generic target covering everyone is a competing explanation, not hierarchy evidence.
    for i in range(n):
        graph.add((EX[f"other{i}"], RDF.type, EX.Other))
    return graph


def gate(graph, context=None, subjects=None, **config):
    return EvidenceGate(
        graph,
        context if context is not None else Graph(),
        subjects if subjects is not None else {term_key(s) for s in graph.subjects()},
        config,
    )


def subclass(engine):
    return engine.assess("subclass", {"sub": str(EX.A), "super": str(EX.B)})


def negative_type(subject, cls):
    graph, expression = Graph(), BNode()
    graph.add((subject, RDF.type, expression))
    graph.add((expression, OWL.complementOf, cls))
    return graph


def test_beta_probability_is_exact_for_uniform_prior_and_updates_both_ways():
    assert beta_tail(1, 1, 0.9) == pytest.approx(0.1)
    assert beta_tail(2, 1, 0.9) == pytest.approx(1 - 0.9**2)
    assert beta_tail(1, 2, 0.9) == pytest.approx(0.1**2)
    first = coverage_belief(20, 0)
    more = coverage_belief(40, 0)
    missing = coverage_belief(20, 20)
    assert missing["posterior_mean"] < first["posterior_mean"] < more["posterior_mean"]
    assert (
        missing["probability_coverage_exceeds_threshold"]
        < first["probability_coverage_exceeds_threshold"]
        < more["probability_coverage_exceeds_threshold"]
    )


def test_strong_independent_support_can_be_accepted_without_a_model():
    result = subclass(gate(population()))
    assert result["status"] == "accepted", result["reasons"]
    assert result["support_subjects"] == 240
    assert result["human_agreement"] is None
    assert result["universal_truth_probability"] is None


def test_missing_type_is_unknown_but_can_withdraw_observed_regularity():
    original = subclass(gate(population()))
    updated = subclass(gate(population(n=400, missing=160)))
    assert original["status"] == "accepted"
    assert updated["status"] == "withheld"
    assert updated["counterexample_count"] == 0
    assert updated["unobserved_subjects"] == 160
    assert updated["belief"]["posterior_mean"] < original["belief"]["posterior_mean"]


def test_one_explicit_counterexample_vetoes_hundreds_of_confirmations():
    graph = population()
    graph.add((EX.exception, RDF.type, EX.A))
    result = subclass(gate(graph, negative_type(EX.exception, EX.B)))
    assert result["status"] == "rejected"
    assert result["counterexample_count"] == 1
    assert result["counterexamples"][0]["subject"] == str(EX.exception)


def test_disjoint_type_supplies_a_real_counterexample():
    graph, context = population(), Graph()
    graph.add((EX.exception, RDF.type, EX.A))
    graph.add((EX.exception, RDF.type, EX.C))
    context.add((EX.B, OWL.disjointWith, EX.C))
    assert subclass(gate(graph, context))["status"] == "rejected"


def test_training_overlap_is_not_independent_confirmation():
    assert subclass(gate(population(), subjects=set()))["status"] == "withheld"


def test_repeated_rdf_and_repeated_assessment_do_not_inflate_support():
    graph = population()
    for _ in range(50):
        graph.add((EX.a0, RDF.type, EX.A))
        graph.add((EX.a0, RDF.type, EX.B))
    engine = gate(graph)
    first = subclass(engine)
    assert subclass(engine) is first
    assert len(engine.records) == 1
    assert first["support_subjects"] == 240


def test_ubiquitous_label_is_a_competing_explanation():
    graph = population()
    for subject in list(graph.subjects()):
        graph.add((subject, RDF.type, EX.B))
    result = subclass(gate(graph))
    assert result["status"] == "withheld"
    assert "ubiquitous_target_explains_overlap" in result["reasons"]


def test_disjointness_and_global_reflexivity_cannot_be_proved_by_nonoverlap():
    engine = gate(population())
    result = engine.assess("disjoint", {"c1": str(EX.A), "c2": str(EX.Other)})
    assert result["status"] == "withheld"
    assert "nonoverlap_is_not_negative_evidence" in result["reasons"]
    assert engine.assess("Reflexive", {"property": str(EX.p)})["status"] == "withheld"


def test_unique_names_are_not_assumed_for_functionality():
    graph = Graph()
    graph.add((EX.subject, EX.p, EX.left))
    graph.add((EX.subject, EX.p, EX.right))
    result = gate(graph).assess("Functional", {"property": str(EX.p)})
    assert result["status"] == "withheld"
    assert result["counterexample_count"] == 0
    context = Graph()
    context.add((EX.left, OWL.differentFrom, EX.right))
    result = gate(graph, context).assess("Functional", {"property": str(EX.p)})
    assert result["status"] == "rejected"


def test_negative_property_assertion_vetoes_an_implication():
    graph, context, node = Graph(), Graph(), BNode()
    graph.add((EX.a, EX.p, EX.b))
    for p, o in [
        (RDF.type, OWL.NegativePropertyAssertion),
        (OWL.sourceIndividual, EX.a),
        (OWL.assertionProperty, EX.q),
        (OWL.targetIndividual, EX.b),
    ]:
        context.add((node, p, o))
    result = gate(graph, context).assess(
        "subproperty", {"sub": str(EX.p), "super": str(EX.q)}
    )
    assert result["status"] == "rejected"
    assert result["counterexample_count"] == 1


def test_all_fillers_are_checked_and_missing_existential_is_not_falsity():
    graph = Graph()
    graph.add((EX.a, RDF.type, EX.A))
    graph.add((EX.a, EX.p, EX.good))
    graph.add((EX.good, RDF.type, EX.B))
    graph.add((EX.a, EX.p, EX.bad))
    engine = gate(graph, negative_type(EX.bad, EX.B))
    result = engine.assess(
        "restriction",
        {
            "class": str(EX.A),
            "property": str(EX.p),
            "filler": str(EX.B),
            "type": "allValuesFrom",
        },
    )
    assert result["status"] == "rejected"
    result = engine.assess(
        "restriction",
        {
            "class": str(EX.A),
            "property": str(EX.unknown),
            "filler": str(EX.B),
            "type": "someValuesFrom",
        },
    )
    assert result["status"] == "withheld"
    assert result["counterexample_count"] == 0


def test_join_budget_abstains_instead_of_truncating_evidence():
    graph = Graph()
    for i in range(5):
        graph.add((EX[f"s{i}"], EX.p, EX.middle))
        graph.add((EX.middle, EX.q, EX[f"o{i}"]))
    result = gate(graph, MAX_JOIN_EDGES=10).assess(
        "chain", {"chain": [str(EX.p), str(EX.q)], "super": str(EX.r)}
    )
    assert "join_budget_exceeded" in result["reasons"]
    assert result["status"] == "withheld"


@pytest.mark.parametrize(
    "fmt,extension",
    [
        ("turtle", "ttl"),
        ("nt", "nt"),
        ("xml", "rdf"),
        ("json-ld", "jsonld"),
        ("trig", "trig"),
        ("nquads", "nq"),
    ],
)
def test_input_serializations_preserve_terms(tmp_path, fmt, extension):
    from rdflib import Dataset

    graph = Graph()
    graph.add((EX.a, RDF.type, EX.A))
    graph.add((EX.a, EX.label, Literal("বাংলা", lang="bn")))
    graph.add((EX.a, EX.p, BNode("object_only")))
    path = tmp_path / ("input." + extension)
    if fmt in {"trig", "nquads"}:
        dataset = Dataset()
        for triple in graph:
            dataset.graph(EX.source).add(triple)
        dataset.serialize(path, format=fmt)
    else:
        graph.serialize(path, format=fmt)
    loaded, report = load_abox(path)
    assert len(loaded) == 3
    assert (EX.a, EX.label, Literal("বাংলা", lang="bn")) in loaded
    assert isinstance(loaded.value(EX.a, EX.p), BNode)
    assert report["format"] == fmt


def test_mixed_property_normalization_preserves_every_fact_and_mapping(tmp_path):
    path = tmp_path / "mixed.ttl"
    path.write_text('@prefix e: <urn:ex:> . e:a e:p e:b, "b".')
    first, report = load_abox(path)
    second, again = load_abox(path)
    assert set(first) == set(second)
    assert report == again
    assert len(first) == 2
    (mapping,) = report["mixed_properties"]
    assert mapping["original"] == "urn:ex:p"
    assert (URIRef("urn:ex:a"), URIRef(mapping["object"]), URIRef("urn:ex:b")) in first
    assert (URIRef("urn:ex:a"), URIRef(mapping["data"]), Literal("b")) in first


def test_sameas_collapse_prevents_alias_evidence_inflation(tmp_path):
    graph = population(n=1)
    for i in range(30):
        graph.add((EX[f"alias{i}"], OWL.sameAs, EX.a0))
        graph.add((EX[f"alias{i}"], RDF.type, EX.A))
        graph.add((EX[f"alias{i}"], RDF.type, EX.B))
    path = tmp_path / "aliases.ttl"
    graph.serialize(path, format="turtle")
    normalized, report = load_abox(path)
    data, context = split_assertions(normalized)
    assert subclass(gate(data, context))["support_subjects"] == 1
    assert len(report["equality_aliases"]) == 30


def test_remote_context_is_rejected_before_any_network_access(tmp_path):
    path = tmp_path / "remote.jsonld"
    path.write_text(json.dumps({"@context": "https://example.invalid/context"}))
    with pytest.raises(ValueError, match="inline context"):
        load_abox(path)


def execute(path, tmp_path, monkeypatch):
    monkeypatch.setenv("USE_LLM", "false")
    monkeypatch.setenv("ABOX_INPUT_PATH", str(path))
    monkeypatch.setenv("TBOX_OUTPUT_PATH", str(tmp_path / "TBox.ttl"))
    monkeypatch.setenv("TELEMETRY_PLOT_PATH", str(tmp_path / "telemetry.png"))
    monkeypatch.setenv("CALIBRATION_LABELS_PATH", "")
    result = run_pipeline(
        path, tmp_path / "TBox.ttl", plot_path=tmp_path / "telemetry.png"
    )
    return vars(result.state)


@pytest.mark.parametrize(
    "content",
    [
        "",
        "@prefix e: <urn:ex:> . e:a a e:A .",
        '@prefix e: <urn:ex:> . e:a e:p e:b, "b" ; e:label "বাংলা"@bn .',
        '@prefix e: <urn:ex:> . [] e:p [e:q "value"] .',
    ],
)
def test_pipeline_handles_empty_sparse_mixed_and_blank_node_aboxes(
    tmp_path, monkeypatch, content
):
    path = tmp_path / "input.ttl"
    path.write_text(content)
    ns = execute(path, tmp_path, monkeypatch)
    assert ns["VALIDATION_REPORT"]["status"] == "passed"
    output = Graph().parse(tmp_path / "TBox.ttl")
    assert len(output) > 0
    assert not list(output.triples((None, OWL.disjointWith, None)))
    ledger = json.loads((tmp_path / "TBox.evidence.json").read_text())
    assert ledger["validation"]["status"] == "passed"
    assert ns["payload_token_audit_log"] == []


def test_pipeline_produces_nonvacuous_taxonomy_on_large_independent_evidence(
    tmp_path, monkeypatch
):
    path = tmp_path / "input.ttl"
    graph = population(n=1200)
    for i in range(600):
        graph.add((EX[f"b_only{i}"], RDF.type, EX.B))
    graph.serialize(path, format="turtle")
    ns = execute(path, tmp_path, monkeypatch)
    output = Graph().parse(tmp_path / "TBox.ttl")
    assert (EX.A, RDFS.subClassOf, EX.B) in output
    assert ns["ONTOQA_METRICS"]["hold_out_recall"] > 0
    # Test subjects are never discovery or confirmation subjects.
    discovery_subjects = {term_key(s) for s in ns["discovery_graph"].subjects()}
    assert not discovery_subjects & ns["test_subjects"]
    assert not ns["confirmation_subjects"] & ns["test_subjects"]
    assert not discovery_subjects & ns["confirmation_subjects"]


def test_large_identical_extensions_do_not_force_an_arbitrary_taxonomy(
    tmp_path, monkeypatch
):
    path = tmp_path / "identical.ttl"
    population(n=1200).serialize(path, format="turtle")
    ns = execute(path, tmp_path, monkeypatch)
    assert ns["G_reduced"].number_of_edges() == 0
    assert not ns["adjudicated_equivalences"]
    assert any(
        "bidirectional_observations_do_not_identify_taxonomy" in r["reasons"]
        for r in ns["evidence_gate"].records
    )


def test_individual_equality_does_not_merge_punned_classes(tmp_path):
    path = tmp_path / "punning.ttl"
    path.write_text("""@prefix e: <urn:ex:> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        e:A a owl:Class ; owl:sameAs e:B .
        e:B a owl:Class . e:x a e:A . e:y a e:B .""")
    graph, _ = load_abox(path)
    assert (URIRef("urn:ex:x"), RDF.type, URIRef("urn:ex:A")) in graph
    assert (URIRef("urn:ex:y"), RDF.type, URIRef("urn:ex:B")) in graph
    assert (URIRef("urn:ex:B"), RDF.type, OWL.Class) in graph


def test_inconsistent_input_preserves_previous_export(tmp_path, monkeypatch):
    path = tmp_path / "input.ttl"
    path.write_text("""@prefix e: <urn:ex:> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        e:a owl:sameAs e:b ; owl:differentFrom e:b .""")
    target = tmp_path / "TBox.ttl"
    target.write_text("previous output")
    with pytest.raises(RuntimeError, match="validation failed"):
        execute(path, tmp_path, monkeypatch)
    assert target.read_text() == "previous output"


def test_joint_domain_conflict_retracts_learned_axioms_automatically(
    tmp_path, monkeypatch
):
    graph = Graph()
    graph.add((EX.A, OWL.disjointWith, EX.B))
    for i in range(1200):
        for cls, prop in [(EX.A, EX.p), (EX.B, EX.q)]:
            subject = URIRef(str(cls) + str(i))
            graph.add((subject, RDF.type, cls))
            graph.add((subject, prop, Literal("value")))
    # Neither individual domain hypothesis has an explicit local counterexample.
    # Together they force this untyped subject into disjoint classes.
    graph.add((EX.ambiguous, EX.p, Literal("value")))
    graph.add((EX.ambiguous, EX.q, Literal("value")))
    path = tmp_path / "joint-conflict.ttl"
    graph.serialize(path, format="turtle")
    ns = execute(path, tmp_path, monkeypatch)
    assert ns["VALIDATION_REPORT"]["status"] == "passed"
    assert ns["VALIDATION_REPORT"]["repaired"]
    assert not ns["property_domains"]
    assert any(
        "withdrawn_after_joint_reasoner_failure" in r["reasons"]
        for r in ns["evidence_gate"].records
    )
    output = Graph().parse(tmp_path / "TBox.ttl")
    assert not list(output.triples((None, RDFS.domain, None)))


def test_datatype_functionality_uses_value_equality():
    graph = Graph()
    graph.add((EX.a, EX.p, Literal("01", datatype=XSD.integer, normalize=False)))
    graph.add((EX.a, EX.p, Literal("1", datatype=XSD.integer, normalize=False)))
    result = gate(graph).assess("Functional", {"property": str(EX.p)})
    assert result["counterexample_count"] == 0
    graph.add((EX.a, EX.p, Literal("2", datatype=XSD.integer)))
    assert (
        gate(graph).assess("Functional", {"property": str(EX.p)})["status"]
        == "rejected"
    )
