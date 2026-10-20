# Falsification audit and probability contract

## Steelman the pipeline

Repeated instances share type inclusions, property signatures, domains, ranges,
and relational implications. A compact ontology can express these regularities,
recover missing assertions, and help reuse data. Confirmation on unseen subjects
reduces selection effects. Explicit negatives and reasoning eliminate some wrong
proposals. This supports autonomous, useful schema induction.

It supports a fallible procedure, not a guarantee of intended meaning or agreement
among people. The following objections drive the implementation.

| Strongest argument | How it can be wrong | Implemented response | Remaining limitation |
|---|---|---|---|
| Every observed A is B, so A subclasses B. | All sampled employees happen to be adults; employment does not logically imply adulthood. | Separate confirmation, skeptical prior, target-prevalence comparison, negative veto. | Biased populations can repeat the same mistake across splits. |
| Hundreds of records are overwhelming evidence. | They are aliases, copied records, or correlated exports. | Deduplicate RDF; collapse explicit sameAs; count subjects rather than triples. | Unknown copying and correlation between subjects remain possible. |
| The model recognizes the concepts and agrees. | It follows misleading names or repeats a confident misconception. | Model opinion has zero Bayesian evidence weight and cannot authorize axioms. | Suggested names can still imply stronger meaning than a signature supports. |
| The TBox is consistent. | A false employee/adult rule can be consistent. An empty ontology is often consistent. | Logical and empirical checks are separate; positive fixtures require useful learned axioms. | Compatibility does not establish truth. |
| No overlap means disjointness. | Dual membership was never collected. | Withhold inferred disjointness. | Genuine disjointness cannot be recovered from absence alone. |
| One value per subject proves functionality. | A second value is unrecorded; two IRIs can denote one individual. | Withhold uniqueness; inspect explicitly distinct values. | Completeness and identity are usually unknown. |
| Identical extensions prove equivalence. | Temporary co-labeling explains equality. | No inferred equivalence; withhold reciprocal subclass directions together. | True equivalence may also be missed. |
| Random hold-outs prove generalization. | Source dependence and reporting bias span every partition. | Isolate discovery, confirmation, and final test subjects; inspect subject folds. | Cross-source and temporal generalization remain unmeasured. |
| A high Bayesian probability proves the axiom. | The probability concerns observation coverage, assuming exchangeability. | Record the target, priors, counts, and assumptions; universal truth remains unknown. | A posterior cannot repair an unidentified sampling process. |
| A small risk budget handles multiple comparisons. | Conditional posterior risk is not a frequentist guarantee under misspecification. | Allocate across the configured candidate cap, not just successful candidates. | The allowance is meaningful only within the model. |
| More expressive axioms are better. | Individually plausible restrictions and role rules conflict when combined. | Validate the complete graph; retract learned axioms if joint validation fails. | Vocabulary fallback sacrifices useful axioms; it is not optimal repair. |
| Supporting RDF formats makes conversion universal. | RDF Full, invalid literals, contradictory data, or an unmapped table may lack the intended OWL interpretation. | Explicit normalization and validation contract; preserve output on failure. | No finite implementation handles every encoding, scale, and meaning. |

## Conditions guaranteeing failure of a universal claim

Suppose the ABox says only `alice rdf:type Student` and
`alice rdf:type Employee`. Both “all students are employees” and “some students
are not employees” have models compatible with these observations. The intended
world cannot be identified from the ABox alone. An algorithm promising the one
universally correct answer must fail for at least one compatible world.

A predicate used for both resource and literal values cannot retain both roles
under the same IRI in an OWL 2 DL ontology. A normalization mapping or another
formalism is necessary. The notebook chooses a recorded normalization mapping.

An assertion and its negation, or equality and inequality of the same individuals,
cannot all be retained in a consistent classical ontology. The notebook rejects
inconsistent source data instead of claiming to have repaired domain truth.

## Exact probability model

For each eligible confirmation subject and proposed implication, let `Y=1` when
all tested consequents for that subject are observed; otherwise let `Y=0`. An
existential needs one observed witness. `Y=0` is an observation failure, not an OWL
negation. Known training types can be used for fillers; hidden test labels cannot.

Assuming conditionally exchangeable Bernoulli observations:

```
theta ~ Beta(a, b)
theta | evidence ~ Beta(a + supported_subjects, b + unobserved_subjects)
```

The reported probability is `P(theta >= 0.90 | evidence)`, with a configurable
coverage threshold. Evaluate under `(a,b)=(1,1)` and `(1,3)` and use the less
favorable probability. Admission requires posterior risk no greater than
`0.05 / MAX_EVIDENCE_CANDIDATES`, enough subjects, sufficient coverage in all
three deterministic subject folds, and no explicit counterexample or other veto.
Priors and folds are sensitivity analyses of the SAME evidence, never independent
expert votes whose probabilities can be multiplied.

Subclass/domain coverage must also exceed target prevalence in the confirmation
subject population by at least 0.05. This can withhold broad, true superclasses
that cannot be distinguished from an uninformative generic label. The comparison
has no causal interpretation.

Missingness, wrong labels, source correlation, and concept drift can violate this
model. Universal-truth probability and human agreement remain `null`. Explicit
contradictions force rejection regardless of the coverage posterior. Observed
coverage probabilities cannot be calibrated against labels for a different event,
such as universal subclass truth.

## Evidence separation and updates

1. Canonicalize blank nodes and explicit individual aliases. Preserve term kinds
   and the distinction between individual equality and OWL class punning.
2. Reserve final test subjects and mask selected type/role assertions.
3. Hash other subjects into discovery and confirmation. Mine discovery only.
   Confirmation-only vocabulary may be declared but supplies no discovery instances.
4. Assess confirmation subjects and search available training data and supplied
   negative context for contradictions.
5. Repair structural conflicts and validate the complete output and training data.
   Write only after successful validation.
6. Measure final positive recovery afterward, seeded by known test features.

Adding evidence and rerunning replaces counts instead of compounding them. The
ledger records posterior parameters and concrete failures. It never recycles an
old posterior as a new prior. Blank-node canonicalization and changes to eligible
subjects may change partitions on evolving data; cross-run split stability is not
guaranteed for anonymous resources.

Synthetic signature-class memberships never supply their own confirmation
instances. Supplied schema constrains validation but is not presented as an
empirical discovery. Mixed-predicate normalization changes the target vocabulary
and is recorded explicitly.

## Validation boundaries and executable challenges

HermiT checks TBox coherence and compatibility with training assertions and
supplied context. The integration checks explicit identity clashes and declares
observed individuals/predicates before loading them. This addresses an actual
case where the former integration missed a contradiction. It is not a complete
profile checker for arbitrary RDF-to-OWL mappings. The conservative chain check
can reject legal recursive chains. Recall uses a named-type/role rule fragment,
not full OWL entailment or anonymous existential witnesses.

Named graphs are unioned, not counted as independent sources. Search caps and
parsing/reasoner resources limit scale. Joining past the discovery budget stops
execution instead of pretending truncated evidence is complete. Output files
are individually replaced atomically; their SHA-256 linkage detects a mismatched
Turtle/ledger pair after an interrupted write.

`test_falsification.py` tests posterior updates in both directions, explicit
negative vetoes, missing information, duplicate observations, isolated
confirmation, generic targets, absence of unique names, negative role assertions,
restriction fillers, join budgets, six serializations, mixed predicates,
individual aliases, class punning, remote contexts, empty/sparse inputs,
inconsistent data, and large samples that must either yield a useful taxonomy
or abstain from an arbitrary one. The older tests execute the real notebook and
five bundled domains. Neither suite measures human agreement or guarantees an
unseen domain.

## Observed verification results

On 2026-10-20, all 105 regression and falsification tests passed. The bundled
agriculture input also completed offline with HermiT validation: 381,770 source
triples became 381,720 triples after equality normalization. The evidence gate
admitted three hypotheses (one restriction and two datatype ranges) and withheld
171 candidates. Type recovery was 0/1 and role recovery was 0/8,295. These results
support execution and compatibility on that input, while providing **no evidence
of useful held-out recovery** there. They do not establish human agreement.

Semantic basis: [W3C OWL 2 Primer](https://www.w3.org/TR/owl-primer/),
[W3C RDF 1.1 Concepts](https://www.w3.org/TR/rdf11-concepts/), and
[RDFLib security considerations](https://rdflib.readthedocs.io/en/stable/security_considerations.html).
