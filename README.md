# ABox-to-TBox Python pipeline

The maintained implementation is the `abox2tbox` package in `src/abox2tbox/`.
It autonomously discovers schema candidates, tries to falsify them, validates the
surviving ontology, and writes a TBox plus an evidence ledger. No notebook or
human/model decisions are required to run it.

Use **uv** for dependency management and execution. Requirements: uv, Python 3.12+
(the existing project environment uses 3.14), and a working Java runtime for HermiT.

```sh
uv sync --locked
uv run --locked abox2tbox input/ABox.ttl --output output/TBox.ttl --offline
uv run --locked pytest -q
```

`pyproject.toml` declares the package and development tools; `uv.lock` pins the
resolved dependencies. `uv sync --locked` installs the package in editable mode
and includes the `dev` group. For a runtime-only environment, use
`uv sync --locked --no-dev` and `uv run --locked --no-dev abox2tbox ...`.

The default input is `input/agriAbox.ttl`. Output paths can be supplied explicitly:

```sh
uv run --locked abox2tbox --input input/ABox.ttl --output /tmp/abox2tbox/TBox.ttl \
  --plot /tmp/abox2tbox/telemetry.png --offline --json
uv run --locked abox2tbox input/ABox.ttl -o /tmp/abox2tbox/TBox.ttl --no-plot
uv run --locked abox2tbox --help
```

The evidence ledger is written beside the TBox as `TBox.evidence.json`. With no
path overrides, the TBox and telemetry default to `output/TBox.ttl` and
`output/telemetry_diagnostics.png`. `--no-plot` skips plotting. Stage diagnostics
from `--verbose` go to stderr; `--json` writes a result summary to stdout.
Failures return a nonzero status. Input, TBox, ledger, and plot paths must be distinct.

Python callers use the same pipeline:

```python
from abox2tbox import run_pipeline

result = run_pipeline(
    "input/ABox.ttl",
    "/tmp/abox2tbox/TBox.ttl",
    config={"USE_LLM": False},
    plot=False,
)
print(result.validation)
print(result.metrics)
print(result.evidence["status_counts"])
```

Explicit API arguments override the `config` mapping, which overrides environment
settings. Each run owns its graphs, audit log, and SQLite store. The store closes
on success or failure. Importing the package performs no induction or model requests.
Package version 4.1 retains the v4.0 evidence and ontology format.

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

## Code inventory and verification

All maintained runtime code is under `src/abox2tbox/`:

| Module | Responsibility |
|---|---|
| `pipeline.py`, `state.py` | Public API, result object, explicit stage ordering, per-run resources |
| `config.py`, `cli.py`, `__main__.py`, `__init__.py` | Settings, CLI, package entry points |
| `data.py` | Input partitioning, SQLite discovery store, signature grouping and naming |
| `mining.py` | Taxonomy, role-rule, and restriction candidates |
| `adjudication.py`, `transport.py` | Independent confirmation and optional model critique |
| `ontology.py` | Structural repair, annotated OWL construction, validated export |
| `evaluation.py` | Positive hold-out recovery, calibration reporting, telemetry |
| `induction_evidence.py` | RDF normalization, counterexamples, Bayesian coverage evidence |
| `pipeline_support.py`, `utils.py` | Reasoner integration, transport, closure, numerical/vocabulary helpers |

```sh
uv run --locked pytest -q
uv run --locked ruff format --check src tests scripts
uv run --locked python -m tests.test_multi_inputs_harness
```

Tests call the production API and stage functions directly. They cover five
small bundled domains, RDF serializations, sparse/empty inputs, semantic
counterexamples, positive evidence admitting a hierarchy, and fresh evidence
withdrawing one. API/CLI tests also check isolated repeated runs, closed database
connections after failures, output protection, and execution without any notebook.
The migration was separately compared with the previous notebook on all five
small domains: RDF graphs, candidate evidence, and metrics matched.

`ABOX2TBOX.ipynb` is an optional short API example. It contains no independent
pipeline implementation and is not read by the package or its tests. Regenerate
it with `uv run --locked python scripts/build_notebook.py`. A Jupyter kernel used
for that optional example must have the package installed.

`scripts/run_pipeline.py` is a thin source-checkout CLI launcher. The historical
PDF guide describes the earlier notebook implementation.

`requirements.txt` is a compatibility export, not a second dependency source.
After intentionally changing dependencies, update the lock and export with:

```sh
uv lock
uv export --locked --no-dev --no-emit-project --no-hashes --output-file requirements.txt
```

## Download and test public ABoxes sequentially

```sh
uv run --locked python scripts/benchmark_online.py
uv run --locked python scripts/benchmark_online.py --only dbpedia-leipzig
```

The source manifest is `benchmarks/online_sources.json`. The runner downloads and
tests each source before moving to the next. It saves original RDF snapshots and
SHA-256 provenance under `input/online/`, then runs the installed CLI in a fresh
subprocess with models disabled and a 180-second per-input timeout. No triples
are removed and no datatype is weakened to make a source pass.

Each run writes `report.json` and `report.md` under
`output/online_benchmarks/<timestamp>/`. Original snapshots and per-source TBoxes,
logs, and plots remain local; source manifests and aggregate reports are versioned.
Cached snapshots are reused only when their checksum matches. Use `--refresh` to
fetch current publisher responses. A run returns nonzero if any download or
pipeline test fails, while continuing sequentially with the remaining sources.

The [2026-10-20 online report](output/online_benchmarks/2026-10-20/report.md) records
eight attempted sources: seven RDF downloads, two successful pipeline runs, five
pipeline failures, and one publisher returning HTML. Both successful runs produced
vocabulary-only ontologies. The failures expose discovery join limits and HermiT
datatype limitations; these are distinct from proving a source inconsistent.
