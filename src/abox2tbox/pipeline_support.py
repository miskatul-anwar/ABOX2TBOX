"""Shared, testable support for the ABox-to-TBox pipeline.

Candidate scores describe observations. They are never presented as calibrated
probabilities or proof that an OWL axiom holds.
"""

from collections import defaultdict
import json
import math
from pathlib import Path
import tempfile
import time
import urllib.request

import networkx as nx
import owlready2
from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS


class DecisionTransport:
    """Bounded requests, explicit abstentions, and a shared error circuit breaker.

    The byte budget is a conservative preflight estimate, not a tokenizer count.
    Server token usage, when available, is recorded separately. Oversized inputs
    are skipped; they are never truncated into a different question.
    """

    def __init__(self, config, audit, opener=None):
        self.config, self.audit = config, audit
        self.opener = opener or urllib.request.urlopen
        self.endpoint = str(config["OLLAMA_BASE_URL"]).rstrip("/")
        self.model = config["MODEL_DECISION"]
        self.tier = "statistical"
        self.errors = 0
        self.decisions = 0
        self.llm_decisions = 0
        for key in (
            "MAX_DECISION_PAIRS",
            "MAX_LLM_PAIRS",
            "MAX_PAYLOAD_TOKENS",
            "LLM_MAX_CONSECUTIVE_ERRORS",
            "SYSTEMONE_BATCH_SIZE",
        ):
            if int(config[key]) <= 0:
                raise ValueError(f"{key} must be positive")
        if float(config["LLM_TIMEOUT_S"]) <= 0:
            raise ValueError("LLM_TIMEOUT_S must be positive")

    def _request(self, route, payload, stage):
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
        estimate = len(body) + 128  # reserve for server prompt framing
        event = {
            "stage": stage,
            "endpoint": route,
            "model": payload.get("model"),
            "timestamp": time.time(),
            "estimated_input_tokens": estimate,
            "input_tokens": None,
            "status": "pending",
        }
        self.audit.append(event)
        if estimate > int(self.config["MAX_PAYLOAD_TOKENS"]):
            event["status"] = "skipped_budget"
            return None
        if self.errors >= int(self.config["LLM_MAX_CONSECUTIVE_ERRORS"]):
            event["status"] = "skipped_circuit_open"
            return None
        request = urllib.request.Request(
            self.endpoint + route,
            data=body,
            headers={"Content-Type": "application/json"},
        )
        try:
            with self.opener(
                request, timeout=float(self.config["LLM_TIMEOUT_S"])
            ) as response:
                result = json.loads(response.read().decode())
            if not isinstance(result, dict):
                raise ValueError("Response must be a JSON object")
            tokens = result.get("usage", {}).get(
                "input_tokens", result.get("prompt_eval_count")
            )
            if tokens is not None:
                tokens = int(tokens)
                if tokens < 0:
                    raise ValueError("Negative token usage")
                event["input_tokens"] = tokens
                if tokens > int(self.config["MAX_PAYLOAD_TOKENS"]):
                    self.errors = int(self.config["LLM_MAX_CONSECUTIVE_ERRORS"])
                    raise ValueError(
                        "Server token count exceeded budget; transport disabled"
                    )
            if route == "/api/chat":
                result = json.loads(result["message"]["content"])
            answers = result.get("answers")
            if not isinstance(answers, dict) or not answers:
                raise ValueError("Missing answers object")
            self.errors = 0
            event["status"] = "success"
            return answers
        except Exception as exc:
            self.errors += 1
            event.update(status="error", error=f"{type(exc).__name__}: {exc}")
            print(f"Decision transport abstained ({stage}): {event['error']}")
            return None

    def connect(self):
        if not self.config["USE_LLM"]:
            return
        questions = {
            "ready": {"type": "noul", "instructions": "Is this a readiness check?"}
        }
        payload = {"model": self.model, "state": {}, "questions": questions}
        answers = self._request("/v1/systemone", payload, "probe")
        if answers and isinstance(answers.get("ready"), dict):
            self.tier = "native_http"
            return
        answers = self._request("/api/chat", self._chat_payload({}, questions), "probe")
        if answers and isinstance(answers.get("ready"), dict):
            self.tier = "chat_emulated"

    def _chat_payload(self, state, questions):
        return {
            "model": self.model,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0, "seed": 42},
            "messages": [
                {
                    "role": "system",
                    "content": 'Return JSON {"answers":{key:answer}}. For choice return choice, '
                    "probabilities and confidence; for noul return noul in [0,1]; "
                    "for score return score in [0,3]. Abstain if evidence is insufficient.",
                },
                {
                    "role": "user",
                    "content": json.dumps({"state": state, "questions": questions}),
                },
            ],
        }

    def ask(self, state, questions, stage):
        if self.decisions >= int(self.config["MAX_DECISION_PAIRS"]):
            return {}
        self.decisions += 1
        if self.tier == "statistical" or self.llm_decisions >= int(
            self.config["MAX_LLM_PAIRS"]
        ):
            return {}
        if self.errors >= int(self.config["LLM_MAX_CONSECUTIVE_ERRORS"]):
            return {}
        self.llm_decisions += 1
        if self.tier == "native_http":
            payload = {"model": self.model, "state": state, "questions": questions}
            return self._request("/v1/systemone", payload, stage) or {}
        return (
            self._request("/api/chat", self._chat_payload(state, questions), stage)
            or {}
        )


def number(answer, key, upper=1.0):
    """Reject missing, malformed, nonfinite, and out-of-range model values."""
    if not isinstance(answer, dict):
        return None
    value = answer.get(key)
    if isinstance(value, bool):
        return None
    try:
        value = float(value)
    except (ValueError, TypeError):
        return None
    return value if math.isfinite(value) and 0 <= value <= upper else None


def confirm_axiom(transport, state, stage, threshold=0.9):
    answers = transport.ask(
        state,
        {
            "valid": {
                "type": "noul",
                "instructions": "Does this proposed axiom hold universally, beyond the observed sample?",
            },
            "necessity": {
                "type": "score",
                "instructions": "Rate necessity: 0 accidental, 1 empirical, 2 domain regularity, 3 logical necessity.",
            },
        },
        stage,
    )
    probability = number(answers.get("valid"), "noul")
    necessity = number(answers.get("necessity"), "score", 3)
    return (
        probability is not None
        and necessity is not None
        and probability >= threshold
        and necessity >= 2.5
    )


def class_closure(classes, edges, equivalences=()):
    graph = nx.DiGraph()
    graph.add_nodes_from(classes)
    graph.add_edges_from(edges)
    for left, right, *_ in equivalences:
        graph.add_edge(left, right)
        graph.add_edge(right, left)
    return {c: {c} | nx.descendants(graph, c) for c in graph}


def repair_roles(characteristics, subproperties, inverses, chains):
    """Conservative regularity check, then propagate non-simplicity.

    Reject chain dependencies that cycle after collapsing subproperty SCCs and
    inverse pairs. This sufficient condition intentionally rejects some legal
    recursive OWL chains. No claim of a complete OWL profile checker is made.
    """
    hierarchy = nx.DiGraph()
    hierarchy.add_nodes_from(characteristics)
    hierarchy.add_edges_from((r["sub"], r["super"]) for r in subproperties)
    for inv in inverses:
        hierarchy.add_edge(inv["p"], inv["q"])
        hierarchy.add_edge(inv["q"], inv["p"])
    for chain in chains:
        hierarchy.add_nodes_from(chain["chain"] + [chain["super"]])
    condensed = nx.condensation(hierarchy)
    component = condensed.graph["mapping"]
    accepted, rejected = [], []
    for chain in sorted(
        chains, key=lambda c: (-c.get("conf_pca", 0), c["super"], c["chain"])
    ):
        trial = condensed.copy()
        trial.add_edges_from(
            (component[p], component[chain["super"]]) for p in chain["chain"]
        )
        if nx.is_directed_acyclic_graph(trial):
            condensed = trial
            accepted.append(chain)
        else:
            rejected.append(chain)
    non_simple = {p for p, chars in characteristics.items() if "Transitive" in chars}
    non_simple.update(c["super"] for c in accepted)
    for p in tuple(non_simple):
        if p in hierarchy:
            non_simple.update(nx.descendants(hierarchy, p))
    forbidden = {"Functional", "InverseFunctional", "Asymmetric", "Irreflexive"}
    cleaned = {
        p: [c for c in chars if p not in non_simple or c not in forbidden]
        for p, chars in characteristics.items()
    }
    return cleaned, accepted, rejected


def validate_export(tbox, training_abox=None):
    """Fail closed on profile problems, unsatisfiable classes, or inconsistency.

    Validate a copy: reasoner inferences must not alter the evaluated export.
    TBox coherence and consistency with training assertions are separate checks.
    """
    object_props = set(tbox.subjects(RDF.type, OWL.ObjectProperty))
    data_props = set(tbox.subjects(RDF.type, OWL.DatatypeProperty))
    if object_props & data_props:
        raise ValueError(
            f"Properties used as both object and data properties: {object_props & data_props}"
        )
    hierarchy = nx.DiGraph()
    hierarchy.add_nodes_from(object_props)
    hierarchy.add_edges_from(tbox.subject_objects(RDFS.subPropertyOf))
    for left, right in tbox.subject_objects(OWL.inverseOf):
        hierarchy.add_edge(left, right)
        hierarchy.add_edge(right, left)
    for left, right in tbox.subject_objects(OWL.equivalentProperty):
        hierarchy.add_edge(left, right)
        hierarchy.add_edge(right, left)
    non_simple = set(tbox.subjects(RDF.type, OWL.TransitiveProperty))
    non_simple.update(tbox.subjects(OWL.propertyChainAxiom, None))
    for prop in tuple(non_simple):
        if prop in hierarchy:
            non_simple.update(nx.descendants(hierarchy, prop))
    for prop in non_simple:
        for characteristic in (
            OWL.FunctionalProperty,
            OWL.InverseFunctionalProperty,
            OWL.AsymmetricProperty,
            OWL.IrreflexiveProperty,
        ):
            if (prop, RDF.type, characteristic) in tbox:
                raise ValueError(
                    f"Non-simple property {prop} cannot have characteristic {characteristic}"
                )
    for label, abox in (("TBox", None), ("TBox + training ABox", training_abox)):
        if label != "TBox" and abox is None:
            continue
        graph = Graph()
        graph += tbox
        if abox is not None:
            graph += abox
            # OWLReady's RDF loader can omit assertions on undeclared individuals.
            # Check explicit identity clashes before translating, and declare the
            # observed vocabulary so those assertions reach HermiT.
            equality = nx.Graph()
            equality.add_edges_from(graph.subject_objects(OWL.sameAs))
            components = {
                node: index
                for index, group in enumerate(nx.connected_components(equality))
                for node in group
            }
            for left, right in graph.subject_objects(OWL.differentFrom):
                if left == right or (
                    left in components and components.get(right) == components[left]
                ):
                    raise RuntimeError(
                        f"Complete export validation failed ({label}): sameAs/differentFrom contradiction"
                    )
            individuals = set()
            meta = (str(RDF), str(RDFS), str(OWL))
            from rdflib import Literal

            for subject, predicate, obj in list(abox):
                if (
                    predicate == RDF.type
                    and isinstance(obj, URIRef)
                    and not str(obj).startswith(meta)
                ):
                    graph.add((obj, RDF.type, OWL.Class))
                    individuals.add(subject)
                elif (
                    not str(predicate).startswith(meta)
                    and (predicate, RDF.type, OWL.AnnotationProperty) not in graph
                ):
                    graph.add(
                        (
                            predicate,
                            RDF.type,
                            OWL.DatatypeProperty
                            if isinstance(obj, Literal)
                            else OWL.ObjectProperty,
                        )
                    )
                    individuals.add(subject)
                    if not isinstance(obj, Literal):
                        individuals.add(obj)
                elif predicate in (OWL.sameAs, OWL.differentFrom):
                    individuals.update((subject, obj))
                elif predicate in (OWL.sourceIndividual, OWL.targetIndividual):
                    individuals.add(obj)
            for individual in individuals:
                graph.add((individual, RDF.type, OWL.NamedIndividual))
            for node in abox.subjects(RDF.type, OWL.NegativePropertyAssertion):
                prop = abox.value(node, OWL.assertionProperty)
                if prop is not None:
                    kind = (
                        OWL.DatatypeProperty
                        if abox.value(node, OWL.targetValue) is not None
                        else OWL.ObjectProperty
                    )
                    graph.add((prop, RDF.type, kind))
        with tempfile.TemporaryDirectory(prefix="abox2tbox-reasoner-") as directory:
            path = Path(directory) / "ontology.owl"
            graph.serialize(path, format="xml")
            world = owlready2.World()
            try:
                world.get_ontology(path.as_uri()).load()
                owlready2.sync_reasoner_hermit(world, debug=0)
                unsatisfiable = sorted(
                    c.iri
                    for c in world.inconsistent_classes()
                    if c.iri != str(OWL.Nothing)
                )
                if unsatisfiable:
                    raise ValueError(f"{label}: unsatisfiable classes: {unsatisfiable}")
            except Exception as exc:
                raise RuntimeError(
                    f"Complete export validation failed ({label}): {exc}"
                ) from exc
            finally:
                world.close()
    return {
        "status": "passed",
        "tbox_coherent": True,
        "training_abox_consistent": training_abox is not None,
    }


def recover_assertions(
    direct_types,
    role_edges,
    closure,
    subproperties,
    inverses,
    chains,
    characteristics,
    domains,
    ranges,
):
    """Materialize the supported named-type and role rules for recall evaluation.

    Existential witnesses and equality reasoning are deliberately not scored as
    recovered named edges. This is a bounded rule fragment, not an OWL reasoner.
    """
    edges = defaultdict(set, {p: set(values) for p, values in role_edges.items()})
    individuals = set(direct_types)
    individuals.update(
        entity for values in edges.values() for edge in values for entity in edge
    )
    for prop, chars in characteristics.items():
        if "Reflexive" in chars:
            edges[prop].update((entity, entity) for entity in individuals)
    changed = True
    while changed:
        before = sum(map(len, edges.values()))
        for rule in subproperties:
            edges[rule["super"]].update(edges[rule["sub"]])
        for rule in inverses:
            p, q = rule["p"], rule["q"]
            edges[q].update((o, s) for s, o in tuple(edges[p]))
            edges[p].update((o, s) for s, o in tuple(edges[q]))
        active_chains = list(chains)
        for p, chars in characteristics.items():
            if "Symmetric" in chars:
                edges[p].update((o, s) for s, o in tuple(edges[p]))
            if "Transitive" in chars:
                active_chains.append({"chain": [p, p], "super": p})
        for chain in active_chains:
            composed = set(edges[chain["chain"][0]])
            for prop in chain["chain"][1:]:
                targets = defaultdict(set)
                for s, o in edges[prop]:
                    targets[s].add(o)
                composed = {(s, o) for s, middle in composed for o in targets[middle]}
            edges[chain["super"]].update(composed)
        changed = before != sum(map(len, edges.values()))
    types = defaultdict(set, {s: set(values) for s, values in direct_types.items()})
    for p, values in edges.items():
        for s, o in values:
            if p in domains:
                types[s].add(domains[p])
            if p in ranges:
                types[o].add(ranges[p])
    for s, values in types.items():
        types[s] = (
            set().union(*(closure.get(c, {c}) for c in values)) if values else set()
        )
    return types, edges


def calibration_metrics(predictions, gold):
    """Score directed model predictions against independent binary gold labels.

    Missing ground truth yields unavailable metrics, never a synthetic score.
    """
    pairs = [(float(p), gold[key]) for key, p in predictions.items() if key in gold]
    for probability, label in pairs:
        if (
            not math.isfinite(probability)
            or not 0 <= probability <= 1
            or label not in (0, 1)
        ):
            raise ValueError(
                "Calibration requires probabilities in [0,1] and binary labels"
            )
    if not pairs:
        return {"ece": None, "brier": None, "count": 0, "bins": []}
    bins = []
    ece = 0.0
    for i in range(10):
        values = [(p, y) for p, y in pairs if min(int(p * 10), 9) == i]
        if not values:
            continue
        confidence = sum(p for p, _ in values) / len(values)
        accuracy = sum(y for _, y in values) / len(values)
        ece += len(values) / len(pairs) * abs(confidence - accuracy)
        bins.append(
            {"confidence": confidence, "accuracy": accuracy, "count": len(values)}
        )
    return {
        "ece": ece,
        "brier": sum((p - y) ** 2 for p, y in pairs) / len(pairs),
        "count": len(pairs),
        "bins": bins,
    }
