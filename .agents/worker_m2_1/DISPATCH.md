# Task Assignment: Milestone 2 — Research-Grade Notebook Implementation (`ABox2TBox.ipynb`)

## Identity & Context
- Role: Notebook Implementation Worker (`teamwork_preview_worker`)
- Working Directory: `/home/miskat/ABOX2TBOX/.agents/worker_m2_1`
- Parent: Orchestrator (`0a10e674-c27e-47e5-ac70-e7b05332cf40`)
- Write Ownership: You exclusively own `/home/miskat/ABOX2TBOX/ABox2TBox.ipynb`. Do NOT edit or overwrite `ABox.ttl` or `test_pipeline.py`.

## Mandatory Inputs (Read these first)
1. `/home/miskat/ABOX2TBOX/.agents/ORIGINAL_REQUEST.md` (Authoritative user request)
2. `/home/miskat/ABOX2TBOX/software_requirements_specification_abox_to_tbox_induction_notebook.md` (Full SRS)
3. `/home/miskat/ABOX2TBOX/.agents/orchestrator_1/PROJECT.md` (Architecture, feature inventory, contracts)
4. `/home/miskat/ABOX2TBOX/.agents/spec_miner_survey_1/report.md` (Formal formulas, JSON schemas, repair algorithms)
5. `/home/miskat/ABOX2TBOX/.agents/explorer_env_1/report.md` (Client adapter, fallback architecture, host environment)
6. `/home/miskat/ABOX2TBOX/ABox.ttl` (Benchmark dataset to ingest and test against)
7. `/home/miskat/ABOX2TBOX/test_pipeline.py` (Test assertions and execution harness)

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Objective
Author a comprehensive, research-grade Jupyter Notebook `/home/miskat/ABOX2TBOX/ABox2TBox.ipynb` covering all 8 modular sections:

- **Section 0: Environment Setup, Hyperparameters & Reproducibility Seeds**
  * Seed configs, hyperparameter dictionary, headless matplotlib backend (`matplotlib.use('Agg')`).
  * `PAYLOAD_TOKEN_AUDIT_LOG = []` tracking all payload token counts.
  * Unified `NeuroSymbolicClient` adapter: tries Ollama `/api/generate` and `/v1/systemone` first, transparently falls back to deterministic calibrated statistical simulation when offline or returning 404/500 (per R3 and explorer_env_1 design).

- **Section 1: Scalable ABox Ingestion & Characteristic Set Profiling**
  * Streaming parse of `ABox.ttl` with `rdflib` and `sqlite3` relational index.
  * Separate instance assertions from schema triples.
  * Extract $CS(v) = \{p^+\} \cup \{p^-\} \cup \{\tau\}$.
  * Compute 64-bit signature hashes (`hashlib.blake2b` / `xxhash64`).
  * Equivalence clustering for untyped entities with Jaccard $\ge 0.85$.

- **Section 2: Open-Vocabulary Concept Induction for Untyped Entities**
  * Micro-prompt generation bounded to $\le 400$ input tokens, 5 sample instances/predicates.
  * `tinyllama:latest` / fallback synthesis producing `{"class_name": "...", "gloss": "..."}`.
  * Regex validation `^[A-Z][a-zA-Z0-9]+$` and deterministic TF-IDF predicate noun fallback.

- **Section 3: Candidate Axiom Generation & Graph Pruning (`networkx`)**
  * Candidate class pairs with $\text{conf}(C_i \sqsubseteq C_j) \ge 0.15$ or signature Jaccard $\ge 0.40$.
  * Disjointness candidate pairs where overlap ratio $\le 0.005$.
  * Property empirical metrics: $\rho_{\text{trans}}, \rho_{\text{sym}}, \rho_{\text{func}}$.
  * Literal datatype inspection mapping object literals to XSD types.

- **Section 4: Hierarchical Tournament & Batch Axiom Verification**
  * Payloads strictly $\le 1,500$ tokens ($O(1)$ scaling).
  * 5-way `choice` for taxonomic relations (`c1_sub_c2`, `c2_sub_c1`, `equivalent`, `disjoint`, `none`).
  * Parallel `noul` for 5 property characteristics (Transitive, Symmetric, Asymmetric, Functional, InvFunctional).
  * 4-level `score` rubric ($0-3$).
  * $k$-ary tournament tree ($b=15 + 1$ Thing) for high-cardinality candidate domains/ranges.
  * Calibrated acceptance gate: $\theta_{\text{prob}}=0.70, \theta_{\text{conf}}=0.65, \theta_{\text{score}}=1.80, \theta_{\text{noul}}=0.80, \delta_{\text{deadband}}=0.15$.

- **Section 5: Graph-Theoretic TBox Repair & Consistency Enforcement (`networkx`)**
  * Tarjan's SCC equivalence collapsing for mutual symmetric pairs with score $\ge 0.80$ into `owl:equivalentClass`.
  * Minimum Feedback Arc Set (MFAS) edge removal for remaining cycles to guarantee a strict DAG (0 directed cycles).
  * Transitive reduction (`nx.transitive_reduction`) for minimal Hasse diagram.
  * Disjointness-subsumption reachability conflict resolution pruning the lower-confidence assertion to guarantee $DVC_{\text{post}} = 0$.
  * Property characteristic mutex resolution.

- **Section 6: `TBox.ttl` Materialization with W3C PROV-O Metadata (`rdflib`)**
  * Serializes validated OWL 2 / RDFS classes, properties, domains/ranges, subClassOf, equivalentClass, disjointWith to `/home/miskat/ABOX2TBOX/TBox.ttl`.
  * Injects W3C PROV-O reification metadata with decision probabilities and ABox support counts when `EXPORT_STRICT_OWL2_DL = False`.

- **Section 7: Research Evaluation, Ablation & Calibration Diagnostics**
  * OntoQA metrics: Relationship Richness ($RR$), Inheritance Richness ($IR$), Class Coverage Ratio ($CCR$).
  * Soundness metrics: cycle elimination count, $DVC_{\text{pre}}$ vs $DVC_{\text{post}} = 0$.
  * Telemetry: token utilization distribution, confidence histograms, hierarchy tree plots rendered with matplotlib.
  * Namespace variables exported: `PAYLOAD_TOKEN_AUDIT_LOG`, `ONTOQA_METRICS`, `DVC_POST`, `EXPORT_STRICT_OWL2_DL`.

## Self-Verification
Execute:
`python3 test_pipeline.py`
and
`pytest test_pipeline.py -v`
Ensure all 7 acceptance assertions pass with 0 failures!

## Deliverable
Document your implementation, verification commands, and outputs in `/home/miskat/ABOX2TBOX/.agents/worker_m2_1/handoff.md`.
