# Project: ABox-to-TBox Ontology Induction Pipeline

## Architecture
A scalable neuro-symbolic map-compress-adjudicate-repair architecture:
1. **Context-Invariant Ingestion & Profiling**:
   - Streaming RDF parsing via `rdflib` and relational indexing via `sqlite3`.
   - Characteristic Set computation $CS(v) = \{p^+\} \cup \{p^-\} \cup \{\tau\}$.
   - 64-bit signature hashing via `hashlib.blake2b` / `xxhash64`.
   - Equivalence clustering for untyped entities (Jaccard $\ge 0.85$).
2. **Lexical Concept Induction**:
   - Micro-prompting bounded to $\le 400$ input tokens, 64 output tokens.
   - Dual-mode client: live `tinyllama:latest` (/api/generate) with automatic fallback to deterministic TF-IDF predicate noun-phrase synthesis.
   - Regex validation (`^[A-Z][a-zA-Z0-9]+$`) and JSON schema compliance.
3. **Statistical Candidate Mining**:
   - Class co-occurrence matrices, empirical conditional inclusion $\text{conf}(C_i \sqsubseteq C_j)$, and signature Jaccard.
   - Disjointness candidate mining (overlap ratio $\le 0.005$).
   - Property empirical ratios: transitivity $\rho_{\text{trans}}$, symmetry $\rho_{\text{sym}}$, functionality $\rho_{\text{func}}$.
4. **Calibrated Axiom Adjudication**:
   - Bounded payloads strictly $\le 1,500$ tokens ($O(1)$ scaling relative to ABox triple count).
   - Dual-mode client: live `tev1:0.8b` (/v1/systemone) with automatic fallback to deterministic statistical simulation engine.
   - 5-way `choice` for taxonomic relations, parallel `noul` for 5 property characteristics, 4-level `score` rubric.
   - $k$-ary tournament tree ($b=15 + 1$ Thing) for high-cardinality candidate domains/ranges.
   - Acceptance thresholds: $\theta_{\text{prob}} = 0.70$, $\theta_{\text{conf}} = 0.65$, $\theta_{\text{score}} = 1.80$, $\theta_{\text{noul}} = 0.80$, $\delta_{\text{deadband}} = 0.15$.
5. **Graph-Theoretic TBox Repair**:
   - Tarjan's SCC equivalence collapsing for mutual symmetric subsumption pairs ($\ge 0.80$).
   - Minimum Feedback Arc Set (MFAS) cycle breaking for remaining directed cycles to ensure a strict DAG.
   - Transitive reduction (`nx.transitive_reduction`) for minimal Hasse diagram.
   - Disjointness-subsumption conflict pruning via DAG reachability to guarantee $DVC_{\text{post}} = 0$.
   - Property characteristic mutex enforcement (e.g. Symmetric vs. Asymmetric).
6. **Materialization & Provenance**:
   - Serialization to standard OWL 2 / RDFS Turtle in `TBox.ttl`.
   - Optional W3C PROV-O reification metadata with decision probabilities and ABox support counts.
7. **Research Evaluation & Diagnostics**:
   - OntoQA metrics: Relationship Richness ($RR$), Inheritance Richness ($IR$), Class Coverage Ratio ($CCR$).
   - Logical soundness: cycle elimination count, Disjointness Violation Count ($DVC$).
   - Telemetry: token utilization distribution, confidence histograms, hierarchy tree plots.

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Reproducibility & Seeds | Seed setting (random, numpy), hyperparameter config dictionary | M2 | SRS §3 |
| 2 | Unified Client Adapter | HTTP client with automatic fallback simulation for Ollama | M2 | R3, SRS §4.4 |
| 3 | Streaming RDF Ingestion | Chunked streaming Turtle ingestion via rdflib | M2 | R2, SRS FR-1.1 |
| 4 | Relational Triple Index | Out-of-core SQLite store for entity and triple indexing | M2 | R2, SRS FR-1.1 |
| 5 | URI Lexical Tokenizer | Namespace splitting, camelCase/snake_case token normalization | M2 | SRS FR-1.2 |
| 6 | Characteristic Set Profiler | In/out-predicate extraction and 64-bit signature hashing | M2 | R2, SRS FR-1.3 |
| 7 | Equivalence Clustering | Jaccard clustering ($\ge 0.85$) reducing untyped entities to prototypes | M2 | R2, SRS FR-1.3 |
| 8 | Micro-Prompt Constructor | Bound prompt payload to $\le 400$ input tokens, 5 sample instances/predicates | M2 | R3, SRS FR-2.2 |
| 9 | Lexical Concept Synthesis | tinyllama /api/generate invocation with num_predict=64, JSON output | M2 | R3, SRS FR-2.2 |
| 10 | Regex Sanitization & Fallback | Regex validation `^[A-Z][a-zA-Z0-9]+$` and TF-IDF predicate noun fallback | M2 | R3, SRS FR-2.3 |
| 11 | Subsumption Matrix Mining | Compute $\text{conf}(C_i \sqsubseteq C_j)$ and filter by $\tau_{\text{sub}}=0.15$ or $\tau_{\text{sig}}=0.40$ | M2 | SRS FR-3.1 |
| 12 | Disjointness Candidate Mining | Detect candidate disjoint pairs where overlap ratio $\le 0.005$ | M2 | SRS FR-3.2 |
| 13 | Property Empirical Metrics | Calculate $\rho_{\text{trans}}, \rho_{\text{sym}}, \rho_{\text{func}}$ from instance graph | M2 | SRS FR-3.3 |
| 14 | Datatype Property Profiler | Literal regex inspection mapping object literals to XSD types | M2 | SRS FR-4.4 |
| 15 | Payload Token Guard | Enforce state + question tokens $\le 1,500$ across all adjudication calls | M2 | NFR-1, SRS FR-4.1 |
| 16 | 5-Way Taxonomic Choice | Adjudicate `c1_sub_c2`, `c2_sub_c1`, `equivalent`, `disjoint`, `none` | M2 | SRS FR-4.2 |
| 17 | Property Characteristic Noul | Parallel noul queries for Transitive, Symmetric, Asymmetric, Functional, InvFunctional | M2 | SRS FR-4.3 |
| 18 | Quality Scoring | 4-level rubric scoring ($0-3$) for candidate axioms | M2 | SRS FR-4.5 |
| 19 | Tournament Tree Partitioning | $k$-ary tournament tree ($b=15 + 1$ Thing) for high-cardinality domains/ranges | M2 | SRS FR-5.1-2 |
| 20 | Calibrated Acceptance Gate | Gate rule using $\theta_{\text{prob}}=0.70, \theta_{\text{conf}}=0.65, \theta_{\text{score}}=1.80, \theta_{\text{noul}}=0.80$ | M2 | SRS §6.2 |
| 21 | Tarjan SCC Equivalence Collapse | Collapse mutual subsumptions with score $\ge 0.80$ into `owl:equivalentClass` | M2 | R4, SRS FR-6.1 |
| 22 | Minimum Feedback Arc Set | Remove minimum-weight cycle edges to guarantee strict DAG (0 cycles) | M2 | R4, SRS FR-6.1 |
| 23 | Transitive Reduction (Hasse) | Remove redundant transitive subsumption edges via networkx | M2 | R4, SRS FR-6.2 |
| 24 | Disjointness Conflict Repair | Prune conflicting subsumptions or disjointness to enforce $DVC_{\text{post}} = 0$ | M2 | R4, SRS FR-6.3 |
| 25 | Property Mutex Enforcement | Resolve contradictory property declarations (Symmetric vs Asymmetric, etc.) | M2 | SRS FR-6.4 |
| 26 | OWL 2 / RDFS Serialization | Materialize classes, hierarchies, properties, and domains/ranges in TBox.ttl | M2 | R1, SRS §3.6 |
| 27 | W3C PROV-O Annotation Injection | Optional axiom reification recording probabilities, confidence, ABox support | M2 | NFR-3, SRS §3.6 |
| 28 | OntoQA Metric Suite | Compute Relationship Richness ($RR$), Inheritance Richness ($IR$), Class Coverage ($CCR$) | M2 | R1, SRS §7.1 |
| 29 | Soundness & Telemetry Suite | Report cycle elimination count, $DVC_{\text{pre}}$ vs $DVC_{\text{post}}$, token histograms | M2 | R1, SRS §7.2-3 |
| 30 | Hierarchy Visualization | Render matplotlib hierarchy tree using Agg backend | M2 | R1, SRS §7.3 |
| 31 | University Benchmark Dataset | Synthetic ABox.ttl with explicit/untyped entities, deep taxonomy, and intentional noise | M1 | R5, SRS §4 |
| 32 | Automated Test Harness | test_pipeline.py executing notebook programmatically and checking all 7 assertions | M1 | R5, Acceptance |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Benchmark Dataset & Automated Test Harness | Author synthetic benchmark `ABox.ttl` and automated headless test harness `test_pipeline.py` | none | IN_PROGRESS |
| M2 | Research-Grade Induction Notebook (`ABox2TBox.ipynb`) | Implement complete 8-section notebook (Sections 0-7) with full algorithmic repair, dual-mode client adapter, and diagnostics | none (parallel with M1) | IN_PROGRESS |
| M3 | End-to-End Integration, Test Verification & Quality Gates | Execute `test_pipeline.py` against `ABox2TBox.ipynb` and `ABox.ttl`, run Reviewer, Challenger, and Forensic Auditor reviews to pass all gate criteria | M1, M2 | PLANNED |

---

## Interface Contracts
### `ABox.ttl` Contract
- **Format**: Valid W3C Turtle (`text/turtle`), parseable by `rdflib.Graph().parse()`.
- **Domain**: University / Academic Knowledge Base.
- **Namespaces**: Default prefix `:` (`http://example.org/univ#`), `rdf:`, `rdfs:`, `owl:`, `xsd:`.
- **Entities**: Explicit classes (`Professor`, `Student`, `Department`, `Course`, etc.) and high-support untyped entities (`ResearchGrant`, `ResearchLaboratory`, `AcademicDegree`).
- **Injected Noise**:
  - Mutual subsumption cycle (`Lecturer` $\leftrightarrow$ `Instructor`).
  - Directed cycle back-edge (`Person` $\rightarrow$ `FullProfessor`).
  - Redundant transitive edge (`FullProfessor` $\rightarrow$ `Person`).
  - Disjointness violation instance (instance asserted with both `UndergraduateStudent` and `TenuredProfessor`).
  - Empirical property noise (e.g. `teaches` transitivity $\approx 0.05$, `collaboratesWith` symmetry $\approx 0.92$).

### `ABox2TBox.ipynb` Contract
- **Structure**: 8 sequential modular sections (0 through 7).
- **Execution**: Runs headlessly end-to-end via `IPython.core.interactiveshell.InteractiveShell` without throwing exceptions.
- **Output Artifacts**:
  - `TBox.ttl`: Valid OWL 2 / RDFS Turtle file written to working directory.
  - Formatted metrics dictionary/variables in notebook namespace for validation inspection.
- **Constraints**:
  - Subsumption graph must be a strict DAG (`nx.is_directed_acyclic_graph(G) == True`, 0 directed cycles).
  - Post-repair disjointness violation count $DVC_{\text{post}} == 0$.
  - All prompt payloads strictly $\le 1,500$ tokens.
  - Fallback engine activates automatically if Ollama daemon or model weights are unavailable.

### `test_pipeline.py` Contract
- **Invocation**: `python3 test_pipeline.py` (CLI, exit code 0 on success) or `pytest test_pipeline.py`.
- **Verification Assertions**:
  1. Notebook execution succeeds with 0 unhandled cell failures.
  2. Generated `TBox.ttl` parses without syntax errors and contains $\ge 15$ classes.
  3. Extracted subsumption graph from `TBox.ttl` has 0 directed cycles.
  4. Post-repair disjointness violations against `ABox.ttl` is exactly 0.
  5. Maximum recorded token payload length across all LLM queries is $\le 1,500$ tokens.
  6. OntoQA metrics ($RR, IR, CCR$) are computed, non-zero, and physically plausible ($0 < RR, IR, CCR \le 1.0$).
  7. Optional PROV-O reification metadata is syntactically valid when enabled.

---

## Code Layout
- Workspace Root: `/home/miskat/ABOX2TBOX`
  - `ABox.ttl`: Synthetic benchmark RDF dataset.
  - `ABox2TBox.ipynb`: Interactive research-grade Jupyter Notebook.
  - `test_pipeline.py`: Automated test harness and verification script.
  - `TBox.ttl`: Generated terminological ontology output.
  - `software_requirements_specification_abox_to_tbox_induction_notebook.md`: Reference SRS.
- Metadata Directory: `/home/miskat/ABOX2TBOX/.agents/`
  - `orchestrator_1/`: Orchestrator state, plan, progress, PROJECT.md, GATE_STATUS.md.
  - Worker/Reviewer/Challenger/Auditor directories: Isolated metadata directories for each subagent.
