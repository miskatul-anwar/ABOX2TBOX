"""Counterexample-first evidence for autonomous, defeasible schema induction.

The probability below concerns *observable implication coverage*, conditional on
exchangeable subject observations. It is NOT P(OWL axiom is universally true).
Absent assertions are unknown in OWL, even when they lower observed coverage.
No repeated model opinion is counted as an independent observation.
"""

from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path

from rdflib import BNode, Dataset, Graph, Literal, URIRef
from rdflib.compare import to_canonical_graph
from rdflib.namespace import OWL, RDF, RDFS, XSD
from rdflib.util import guess_format


def term_key(term):
    """Keep blank nodes distinct from IRIs with the same lexical spelling."""
    return term.n3() if isinstance(term, (BNode, Literal)) else str(term)


def bucket(value, count=10000, salt="confirmation-v4"):
    digest = hashlib.sha256((salt + "\0" + value).encode()).digest()
    return int.from_bytes(digest[:8], "big") % count


def _local_jsonld(value):
    """Reject external JSON-LD contexts/imports before RDFLib can fetch them."""
    if isinstance(value, list):
        for item in value:
            _local_jsonld(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            if key == "@import":
                raise ValueError(
                    "External JSON-LD @import is unsupported; supply an inline context"
                )
            if key == "@context":
                contexts = item if isinstance(item, list) else [item]
                if any(isinstance(context, str) for context in contexts):
                    raise ValueError(
                        "External JSON-LD @context is unsupported; supply an inline context"
                    )
            _local_jsonld(item)


def load_abox(path, rdf_format=None, max_triples=2000000):
    """Read local RDF, normalize equality and mixed predicates, retain an audit.

    Named graphs are explicitly unioned. They are not claimed to be independent
    sources. Normalized mixed predicates have deterministic, collision-free IRIs.
    OWL imports are rejected rather than fetched or silently trusted.
    """
    path = Path(path)
    fmt = rdf_format or guess_format(path.name)
    fmt = {
        "json": "json-ld",
        "ttl": "turtle",
        "rdf": "xml",
        "nq": "nquads",
        "nt": "nt",
    }.get(fmt, fmt)
    if fmt not in {"turtle", "nt", "xml", "json-ld", "trig", "nquads", "n3", "trix"}:
        raise ValueError(
            "Unknown RDF format. Set ABOX_FORMAT to turtle, nt, xml, json-ld, trig, nquads, n3, or trix"
        )
    if fmt == "json-ld":
        _local_jsonld(json.loads(path.read_text(encoding="utf-8")))
    if fmt in {"xml", "trix"} and b"<!DOCTYPE" in path.read_bytes().upper():
        raise ValueError("XML DTDs are unsupported; provide RDF/XML without a DTD")
    graph = Graph()
    contexts = 1
    if fmt in {"trig", "nquads", "trix"}:
        dataset = Dataset()
        dataset.parse(path, format=fmt)
        contexts = sum(bool(len(g)) for g in dataset.graphs())
        for s, p, o, _ in dataset.quads():
            graph.add((s, p, o))
    else:
        graph.parse(path, format=fmt)
    if len(graph) > max_triples:
        raise ValueError(
            f"Input has {len(graph)} triples; MAX_INPUT_TRIPLES={max_triples}"
        )
    if any(graph.triples((None, OWL.imports, None))):
        raise ValueError("Resolve owl:imports into local RDF before induction")
    for s, p, o in graph:
        if (
            not isinstance(s, (URIRef, BNode))
            or not isinstance(p, URIRef)
            or not isinstance(o, (URIRef, BNode, Literal))
        ):
            raise ValueError(f"Unsupported generalized RDF triple: {(s, p, o)}")
        if isinstance(o, Literal) and getattr(o, "ill_typed", False):
            raise ValueError(f"Ill-typed literal: {o.n3()}")
    if any(isinstance(s, BNode) or isinstance(o, BNode) for s, _, o in graph):
        graph = to_canonical_graph(graph)
    report = {
        "format": fmt,
        "input_triples": len(graph),
        "named_graph_policy": "union",
        "nonempty_contexts": contexts,
        "mixed_properties": [],
        "equality_aliases": {},
    }
    parent = {}

    def root(x):
        parent.setdefault(x, x)
        while x != parent[x]:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in sorted(
        graph.subject_objects(OWL.sameAs), key=lambda pair: tuple(map(term_key, pair))
    ):
        if isinstance(b, Literal):
            raise ValueError("owl:sameAs requires resource terms")
        a, b = root(a), root(b)
        if a != b:
            # Prefer named IRIs, then lexical order; never depend on input ordering.
            a, b = sorted((a, b), key=lambda x: (isinstance(x, BNode), term_key(x)))
            parent[b] = a
    normalized = Graph()
    for s, p, o in graph:
        meta_predicate = str(p).startswith((str(RDF), str(RDFS), str(OWL), str(XSD)))
        if (
            p == RDF.type
            and isinstance(o, URIRef)
            and not str(o).startswith((str(RDF), str(RDFS), str(OWL), str(XSD)))
        ):
            # OWL punning: equality of individuals does not equate class names.
            normalized.add((root(s), p, o))
        elif not meta_predicate or p in (OWL.sameAs, OWL.differentFrom):
            normalized.add((root(s), p, root(o) if not isinstance(o, Literal) else o))
        elif p in (OWL.sourceIndividual, OWL.targetIndividual):
            normalized.add((s, p, root(o)))
        elif p == RDF.type and isinstance(o, BNode):
            normalized.add((root(s), p, o))
        else:
            normalized.add((s, p, o))
    report["equality_aliases"] = {
        term_key(x): term_key(root(x)) for x in parent if x != root(x)
    }
    kinds = defaultdict(set)
    for s, p, o in normalized:
        if not str(p).startswith((str(RDF), str(RDFS), str(OWL), str(XSD))):
            kinds[p].add("data" if isinstance(o, Literal) else "object")
    used = {
        str(term)
        for triple in normalized
        for term in triple
        if isinstance(term, URIRef)
    }
    for prop in sorted((p for p, kinds_ in kinds.items() if len(kinds_) > 1), key=str):
        mapping = {}
        for kind in ("object", "data"):
            base = (
                "urn:abox2tbox:normalized:"
                + hashlib.sha256(str(prop).encode()).hexdigest()
                + ":"
                + kind
            )
            name, suffix = base, 0
            while name in used:
                suffix += 1
                name = base + ":" + str(suffix)
            used.add(name)
            mapping[kind] = URIRef(name)
        for s, o in list(normalized.subject_objects(prop)):
            normalized.remove((s, prop, o))
            normalized.add(
                (s, mapping["data" if isinstance(o, Literal) else "object"], o)
            )
        # Preserve a negative assertion's connection to its normalized predicate.
        for node in list(normalized.subjects(OWL.assertionProperty, prop)):
            kind = (
                "data"
                if normalized.value(node, OWL.targetValue) is not None
                else "object"
            )
            normalized.set((node, OWL.assertionProperty, mapping[kind]))
        report["mixed_properties"].append(
            {"original": str(prop), **{k: str(v) for k, v in mapping.items()}}
        )
    report["normalized_triples"] = len(normalized)
    return normalized, report


def split_assertions(graph):
    """Separate observed assertions from schema/negative/equality context."""
    data, context = Graph(), Graph()
    meta = (str(RDF), str(RDFS), str(OWL), str(XSD))
    annotations = set(graph.subjects(RDF.type, OWL.AnnotationProperty))
    structural = set(graph.subjects(RDF.type, OWL.NegativePropertyAssertion))
    structural.update(graph.subjects(OWL.complementOf, None))
    structural.update(graph.subjects(RDF.type, OWL.Restriction))
    for s, p, o in graph:
        if (
            s not in structural
            and p not in annotations
            and (
                (
                    p == RDF.type
                    and isinstance(o, URIRef)
                    and not str(o).startswith(meta)
                )
                or not str(p).startswith(meta)
            )
        ):
            data.add((s, p, o))
        else:
            context.add((s, p, o))
    return data, context


def beta_tail(alpha, beta, threshold):
    """P(theta >= threshold) for integer Beta parameters, via binomial identity."""
    if alpha < 1 or beta < 1 or int(alpha) != alpha or int(beta) != beta:
        raise ValueError("Beta parameters must be positive integers")
    if not 0 < threshold < 1:
        raise ValueError("Coverage threshold must be in (0,1)")
    n = alpha + beta - 1
    logs = [
        math.lgamma(n + 1)
        - math.lgamma(j + 1)
        - math.lgamma(n - j + 1)
        + j * math.log(threshold)
        + (n - j) * math.log1p(-threshold)
        for j in range(alpha)
    ]
    top = max(logs)
    return min(1.0, math.exp(top) * math.fsum(math.exp(x - top) for x in logs))


def coverage_belief(supported, unobserved, threshold=0.9, prior=(1, 1)):
    """Update once per distinct subject; unknown outcomes aren't logical negatives."""
    if any(
        isinstance(n, bool) or not isinstance(n, int) or n < 0
        for n in (supported, unobserved)
    ):
        raise ValueError("Evidence counts must be nonnegative integers")
    a, b = prior
    return {
        "prior_alpha": a,
        "prior_beta": b,
        "posterior_alpha": a + supported,
        "posterior_beta": b + unobserved,
        "posterior_mean": (a + supported) / (a + b + supported + unobserved),
        "coverage_threshold": threshold,
        "probability_coverage_exceeds_threshold": beta_tail(
            a + supported, b + unobserved, threshold
        ),
    }


class EvidenceGate:
    """Use untouched confirmation subjects; search all training data for vetoes."""

    def __init__(self, training, context, confirmation_subjects, config=None):
        self.config = config or {}
        self.training, self.context = training, context
        self.confirmation_subjects = set(confirmation_subjects)
        self.types, self.edges = defaultdict(set), defaultdict(set)
        self.literal_datatypes = {}
        self.literal_terms = {}
        for s, p, o in training:
            if p == RDF.type:
                self.types[term_key(s)].add(str(o))
            else:
                self.edges[str(p)].add((term_key(s), term_key(o)))
                if isinstance(o, Literal):
                    self.literal_datatypes[term_key(o)] = str(
                        o.datatype or (RDF.langString if o.language else XSD.string)
                    )
                    self.literal_terms[term_key(o)] = o
        self.members = defaultdict(set)
        for s, types in self.types.items():
            for cls in types:
                self.members[cls].add(s)
        self.not_types = defaultdict(set)
        for s, expression in context.subject_objects(RDF.type):
            for cls in context.objects(expression, OWL.complementOf):
                self.not_types[term_key(s)].add(str(cls))
        self.disjoint = set()
        for a, b in context.subject_objects(OWL.disjointWith):
            self.disjoint.update(((str(a), str(b)), (str(b), str(a))))
        for s, types in self.types.items():
            for a, b in self.disjoint:
                if a in types:
                    self.not_types[s].add(b)
        self.negative_edges = defaultdict(set)
        for node in context.subjects(RDF.type, OWL.NegativePropertyAssertion):
            s, p = (
                context.value(node, OWL.sourceIndividual),
                context.value(node, OWL.assertionProperty),
            )
            o = context.value(node, OWL.targetIndividual)
            if o is None:
                o = context.value(node, OWL.targetValue)
            if s is not None and p is not None and o is not None:
                self.negative_edges[str(p)].add((term_key(s), term_key(o)))
        self.different = set()
        for a, b in context.subject_objects(OWL.differentFrom):
            self.different.update(
                ((term_key(a), term_key(b)), (term_key(b), term_key(a)))
            )
        self.records, self.cache = [], {}

    def _observations(self, family, spec):
        """Return subject-level observational tests and actual contradiction witnesses."""
        outcomes, contradictions = defaultdict(list), []

        def typed(s, target, subject=None):
            subject = s if subject is None else subject
            outcomes[subject].append(target in self.types[s])
            if target in self.not_types[s]:
                contradictions.append(
                    {"subject": subject, "target": s, "negated_class": target}
                )

        def edge(s, o, prop, subject=None):
            subject = s if subject is None else subject
            outcomes[subject].append((s, o) in self.edges[prop])
            if (s, o) in self.negative_edges[prop]:
                contradictions.append({"subject": s, "property": prop, "object": o})

        if family == "subclass":
            for s in sorted(self.members[spec["sub"]]):
                typed(s, spec["super"])
        elif family in {"domain", "range"}:
            for s, o in sorted(self.edges[spec["property"]]):
                typed(s if family == "domain" else o, spec["class"], s)
        elif family == "datatype_range":
            for s, o in sorted(self.edges[spec["property"]]):
                outcomes[s].append(self.literal_datatypes.get(o) == spec["datatype"])
        elif family == "subproperty":
            for s, o in sorted(self.edges[spec["sub"]]):
                edge(s, o, spec["super"])
        elif family == "inverse":
            for s, o in sorted(self.edges[spec["p"]]):
                edge(o, s, spec["q"], s)
            for s, o in sorted(self.edges[spec["q"]]):
                edge(o, s, spec["p"], s)
        elif family in {"chain", "Transitive"}:
            chain = spec["chain"] if family == "chain" else [spec["property"]] * 2
            head = spec["super"] if family == "chain" else spec["property"]
            composed = set(self.edges[chain[0]])
            limit = int(self.config.get("MAX_JOIN_EDGES", 100000))
            for prop in chain[1:]:
                targets = defaultdict(set)
                for s, o in self.edges[prop]:
                    targets[s].add(o)
                result = set()
                for s, middle in sorted(composed):
                    for o in sorted(targets[middle]):
                        result.add((s, o))
                        if len(result) > limit:
                            return {}, [], "join_budget_exceeded"
                composed = result
            for s, o in sorted(composed):
                edge(s, o, head)
        elif family == "Symmetric":
            for s, o in sorted(self.edges[spec["property"]]):
                edge(o, s, spec["property"], s)
        elif family == "restriction":
            fillers = defaultdict(set)
            for s, o in self.edges[spec["property"]]:
                fillers[s].add(o)
            for s in sorted(self.members[spec["class"]]):
                values = fillers[s]
                if spec["type"] == "someValuesFrom":
                    outcomes[s].append(
                        any(spec["filler"] in self.types[o] for o in values)
                    )
                    # No observed witness is not proof that no witness exists.
                else:
                    outcomes[s].append(
                        bool(values)
                        and all(spec["filler"] in self.types[o] for o in values)
                    )
                    for o in sorted(values):
                        if spec["filler"] in self.not_types[o]:
                            contradictions.append(
                                {
                                    "subject": s,
                                    "filler": o,
                                    "negated_class": spec["filler"],
                                }
                            )
        elif family in {"Functional", "InverseFunctional"}:
            values = defaultdict(set)
            for s, o in self.edges[spec["property"]]:
                values[o if family == "InverseFunctional" else s].add(
                    s if family == "InverseFunctional" else o
                )
            for s, objects in sorted(values.items()):
                for a in objects:
                    for b in objects:
                        if (a, b) in self.different:
                            contradictions.append(
                                {"subject": s, "distinct_values": sorted((a, b))}
                            )
                        elif (
                            a < b
                            and a in self.literal_terms
                            and b in self.literal_terms
                        ):
                            left, right = self.literal_terms[a], self.literal_terms[b]
                            # Value equality, not lexical inequality: "01"^^integer
                            # and "1"^^integer denote the same value.
                            try:
                                unequal = left.eq(right) is False
                            except (TypeError, ValueError):
                                unequal = False
                            if unequal:
                                contradictions.append(
                                    {"subject": s, "distinct_literal_values": [a, b]}
                                )
            # Single observed values cannot distinguish uniqueness from incompleteness.
            return (
                outcomes,
                contradictions,
                "uniqueness_not_identifiable_without_completeness",
            )
        elif family == "disjoint":
            contradictions = [
                {"subject": s, "classes": [spec["c1"], spec["c2"]]}
                for s in sorted(self.members[spec["c1"]] & self.members[spec["c2"]])
            ]
            return outcomes, contradictions, "nonoverlap_is_not_negative_evidence"
        elif family in {"Asymmetric", "Irreflexive", "Reflexive"}:
            prop = spec["property"]
            for s, o in sorted(self.edges[prop]):
                if (family == "Asymmetric" and (o, s) in self.edges[prop]) or (
                    family == "Irreflexive" and s == o
                ):
                    contradictions.append({"subject": s, "property": prop, "object": o})
            if family == "Reflexive":
                contradictions.extend(
                    {"subject": s, "negative_self_edge": prop}
                    for s, o in sorted(self.negative_edges[prop])
                    if s == o
                )
            return outcomes, contradictions, "global_or_negative_claim_not_identifiable"
        else:
            return outcomes, contradictions, "unsupported_evidence_family"
        return {s: all(values) for s, values in outcomes.items()}, contradictions, None

    def assess(self, family, spec):
        key = json.dumps([family, spec], sort_keys=True)
        if key in self.cache:
            return self.cache[key]
        if len(self.records) >= int(self.config.get("MAX_EVIDENCE_CANDIDATES", 1000)):
            record = {
                "id": hashlib.sha256(key.encode()).hexdigest()[:24],
                "family": family,
                "candidate": spec,
                "status": "withheld",
                "reasons": ["candidate_budget_exceeded"],
            }
            self.records.append(record)
            self.cache[key] = record
            return record
        outcomes, contradictions, limitation = self._observations(family, spec)
        confirmation = {
            s: value for s, value in outcomes.items() if s in self.confirmation_subjects
        }
        support = sum(confirmation.values())
        missing = len(confirmation) - support
        threshold = float(self.config.get("MIN_OBSERVED_COVERAGE", 0.9))
        belief = coverage_belief(support, missing, threshold)
        skeptical = coverage_belief(support, missing, threshold, prior=(1, 3))
        folds = []
        for i in range(3):
            values = [
                v for s, v in confirmation.items() if bucket(s, 3, "stability-v4") == i
            ]
            folds.append(
                {
                    "fold": i,
                    "subjects": len(values),
                    "observed_coverage": sum(values) / len(values) if values else None,
                }
            )
        stable = all(
            f["subjects"] >= 2 and f["observed_coverage"] >= threshold for f in folds
        )
        population = set(self.types) | {
            s for values in self.edges.values() for s, _ in values
        }
        population &= self.confirmation_subjects
        target_class = (
            spec.get("super")
            if family == "subclass"
            else spec.get("class")
            if family == "domain"
            else None
        )
        baseline = (
            len(self.members[target_class] & population) / len(population)
            if population and target_class
            else None
        )
        # Observable lift is a competing explanation check, not a causal test.
        observed = support / len(confirmation) if confirmation else 0
        discriminative = baseline is None or observed - baseline >= 0.05
        reasons = []
        if contradictions:
            reasons.append("explicit_counterexample")
        if limitation:
            reasons.append(limitation)
        if len(confirmation) < int(self.config.get("MIN_CONFIRMATION_SUBJECTS", 12)):
            reasons.append("insufficient_independent_confirmation_subjects")
        if not stable:
            reasons.append("unstable_or_underpowered_subject_folds")
        if not discriminative:
            reasons.append("ubiquitous_target_explains_overlap")
        risk = float(self.config.get("POSTERIOR_RISK_BUDGET", 0.05))
        # Allocated across the configured candidate budget, not just successful candidates.
        allowed_risk = risk / int(self.config.get("MAX_EVIDENCE_CANDIDATES", 1000))
        probability = min(
            belief["probability_coverage_exceeds_threshold"],
            skeptical["probability_coverage_exceeds_threshold"],
        )
        if 1 - probability > allowed_risk:
            reasons.append("posterior_risk_or_prior_sensitivity")
        record = {
            "id": hashlib.sha256(key.encode()).hexdigest()[:24],
            "family": family,
            "candidate": spec,
            "status": "rejected"
            if contradictions
            else "withheld"
            if reasons
            else "accepted",
            "reasons": reasons,
            "support_subjects": support,
            "unobserved_subjects": missing,
            "counterexample_count": len(contradictions),
            "counterexamples": contradictions[:10],
            "unobserved_examples": sorted(s for s, v in confirmation.items() if not v)[
                :10
            ],
            "probability_target": "observable implication coverage, not universal axiom truth",
            "belief": belief,
            "skeptical_prior_belief": skeptical,
            "stability_folds": folds,
            "competing_baseline_coverage": baseline,
            "allocated_posterior_risk": allowed_risk,
            "universal_truth_probability": None,
            "human_agreement": None,
        }
        self.records.append(record)
        self.cache[key] = record
        return record

    def report(self):
        return {
            "version": "4.0",
            "probability_contract": (
                "Beta-Bernoulli posterior for observed consequent coverage on untouched confirmation "
                "subjects. Unknown consequents lower observation coverage, not logical truth. "
                "Subject exchangeability is an assumption; correlated sources can violate it. "
                "Three folds and two priors are sensitivity checks, not independent votes."
            ),
            "status_counts": dict(Counter(r["status"] for r in self.records)),
            "candidates": self.records,
        }
