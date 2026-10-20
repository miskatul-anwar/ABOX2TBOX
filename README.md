# ABox-to-TBox induction, v4.0

Run `ABOX2TBOX.ipynb` (or `abox2tbox.ipynb`) from this directory in cell order. It automatically discovers
schema candidates, tries to falsify them, validates the surviving ontology, and
writes a TBox plus an evidence ledger. No model or human decisions are required.

```sh
python -m pip install -r requirements.txt
# HermiT also requires a working Java runtime.
export ABOX_INPUT_PATH="$PWD/input/ABox.ttl"
export TBOX_OUTPUT_PATH=/tmp/abox2tbox/TBox.ttl
export TELEMETRY_PLOT_PATH=/tmp/abox2tbox/telemetry.png
jupyter notebook ABOX2TBOX.ipynb
```

The default input is `input/agriAbox.ttl`. Outputs default to `output/TBox.ttl`,
`output/TBox.evidence.json`, and `output/telemetry_diagnostics.png`.

## Meaning and evidence

The output is a **defeasible schema supported by observations**. A finite ABox
cannot identify a unique intended TBox: incompatible generalizations can explain
the same observations. Consistency and model agreement do not establish domain
truth or human consensus. See the [falsification audit](docs/falsification.md).

The pipeline:

- Separates discovery, confirmation, and final test subjects before mining;
  collapses explicit `sameAs` aliases before splitting.
- Searches available training assertions for counterexamples using negative
  property assertions, complemented types, disjoint types, and distinct fillers.
- Updates a Beta-Bernoulli model of **observable implication coverage** on
  confirmation subjects. Missing assertions reduce observed coverage without
  becoming logical negatives.
- Requires support across three subject folds and under uniform and skeptical
  priors. Subclass/domain proposals must beat a target-prevalence explanation.
- Withholds disjointness, uniqueness, global reflexivity, and equivalence claims
  that positive samples cannot identify. Bidirectional subclass proposals are
  withheld together instead of forcing an arbitrary direction.
- Validates the complete TBox and its compatibility with training assertions and
  supplied semantic context. Jointly invalid learned axioms are retracted and a
  vocabulary-only fallback is validated. Inconsistent input or unavailable
  reasoning stops execution before replacing the existing output.

The JSON ledger records decisions, reasons, posterior parameters, prior
sensitivity, fold results, observed failures, and contradiction witnesses.
Accepted evidence is also annotated in the ontology. The ledger includes the
SHA-256 of its Turtle export; the files are individually replaced atomically.

Append evidence and rerun to recompute beliefs from unique RDF facts. Old
posteriors are never recycled as new priors. Previously admitted claims can be
withdrawn. Empty or weak input can yield only vocabulary declarations.

## Input coverage

Automatic format detection supports Turtle, N-Triples, RDF/XML, JSON-LD with
inline contexts, TriG, N-Quads, N3 RDF triples, and TriX. Set `ABOX_FORMAT` for an
ambiguous extension. Named graphs are unioned, not treated as independent votes.
Unicode, language tags, datatypes, blank nodes, object-only resources, untyped
graphs, and mixed object/literal predicates are supported.

Mixed predicates are split into deterministic object and data property IRIs;
the ledger and ontology record the mapping. Input files are never rewritten.
The TBox applies to the **normalized** ABox; mixed source predicates require
that mapping before the TBox can be applied to them.

Supplied schema, negatives, and equality statements constrain validation rather
than count as newly discovered truth. Resolve remote JSON-LD contexts, XML DTDs,
and `owl:imports` locally first. Invalid literals, malformed RDF, and inconsistent
assertions fail explicitly. CSV, arbitrary JSON, images, and natural language
require an RDF mapping; their intended semantics cannot be guessed reliably.

## Settings and limits

| Environment setting | Default | Purpose |
|---|---:|---|
| `CONFIRMATION_FRACTION` | 0.35 | Confirmation share outside the final test subjects |
| `MIN_OBSERVED_COVERAGE` | 0.90 | Coverage threshold tested by the posterior |
| `MAX_EVIDENCE_CANDIDATES` | 1,000 | Maximum candidates fully assessed |
| `MAX_INPUT_TRIPLES` | 2,000,000 | Input graph size guard after parsing |
| `MAX_JOIN_EDGES` | 100,000 | Maximum materialized chain join |
| `USE_LLM` | false | Optional naming and advisory adversarial critique |

Admission requires at least 12 confirmation subjects, two subjects in each of
three folds, and each fold's coverage at least the configured threshold. The
posterior risk allowance is `0.05 / MAX_EVIDENCE_CANDIDATES`, under both Beta(1,1)
and Beta(1,3) priors. This is conditional model uncertainty, not a distribution-free
error guarantee. Admission usually needs substantially more than 12 subjects.

Discovery searches at most 256 classes and 64 object properties, ranked by
support, and records omissions. These limits bound search coverage, not every
runtime or memory cost. Parsing and reasoning remain in memory. Exceeding a
chain discovery join limit stops the run rather than silently truncating evidence.
Rare true axioms can be missed.

For optional model assistance, set `USE_LLM=true`, `OLLAMA_BASE_URL` (default
`http://localhost:11434`), and `MODEL_DECISION`. Native `/v1/systemone` and JSON
`/api/chat` retain bounded requests and circuit breakers. Model agreement never
raises a posterior or overrides a counterexample. Repeated model answers are
not independent evidence.

Final hold-outs report positive recovery recall within the supported rule
fragment. Precision, F1, universal-truth calibration, and human agreement remain
unavailable. Legacy subclass calibration labels cannot calibrate these new
observable-coverage probabilities: the prediction targets differ.

## Tests and regeneration

```sh
python -m pytest tests/ -q
python scripts/build_notebook.py
```

Tests execute the actual notebook with temporary outputs and no model calls.
They include five bundled small domains, six RDF serializations, sparse/empty
inputs, identity and open-world counterexamples, positive evidence admitting a
useful hierarchy, and evidence withdrawing a proposal.

- `src/induction_evidence.py` implements ingestion, canonicalization, and the evidence gate.
- `src/pipeline_support.py` implements transport, validation, and recovery.
- `scripts/build_notebook.py` is the synchronized, self-contained notebook generator.
- `tests/` contains the comprehensive test suite (falsification, cross-domain, pipeline, and multi-input harnesses).
The existing PDF guide describes the earlier implementation.
