# Project: Multi-Domain ABox-to-TBox Induction Pipeline Generalization & Hardening

## Architecture
The system realizes a generalized, domain-agnostic neuro-symbolic ontology induction pipeline that extracts formal OWL 2 / RDFS terminological boxes (`TBox.ttl`) from arbitrary RDF knowledge graphs (`ABox.ttl`):

1. **Environment Configuration & Parametric I/O**:
   - Dynamic resolution of input/output paths via environment variables with backward-compatible defaults:
     * `ABOX_INPUT_PATH`: defaults to `/home/miskat/ABOX2TBOX/input/ABox.ttl`
     * `TBOX_OUTPUT_PATH`: defaults to `/home/miskat/ABOX2TBOX/output/TBox.ttl`
     * `TELEMETRY_PLOT_PATH`: defaults to `/home/miskat/ABOX2TBOX/output/telemetry_diagnostics.png`
   - Dynamic ontology URI and namespace extraction from input ABox triples (detecting base prefix or constructing generic `http://example.org/domain#` dynamically).

2. **Domain-Agnostic Scalable Ingestion & Characteristic Set Profiling**:
   - Streaming RDF parsing into an in-memory or SQLite relational index (`triples` table with indexed subject, predicate, object).
   - Characteristic Set computation $CS(v) = \{p^+\} \cup \{p^-\}$ and 64-bit hashing via `hashlib.sha256(signature).hexdigest()[:16]`.
   - Equivalence clustering for untyped entities reducing clusters to prototype representations.

3. **Domain-Agnostic Concept Synthesis for Untyped Clusters**:
   - Removal of all domain-specific hardcoded keywords (e.g., "grant", "funding", "lab", "room", "degree", "credits").
   - Purely statistical, open-vocabulary concept naming:
     * Predicate local name tokenization (camelCase and snake_case regex splitting).
     * Stopword filtering and frequency-weighted ranking of salient predicate nouns.
     * Deterministic synthesis of valid PascalCase class identifiers (`^[A-Z][a-zA-Z0-9]+$`).
     * Fallback to `Induced<Noun1><Noun2>` or `Cluster_<hash[:8]>` ensuring valid ontology identifiers.
     * Micro-prompting bounded to $\le 400$ input tokens and 64 output tokens for Ollama (`tinyllama:latest`) with deterministic fallback.

4. **Statistical Candidate Mining & Domain-Agnostic Disjointness Detection**:
   - Conditional subsumption inclusion mining $\text{conf}(C_i \sqsubseteq C_j) = |C_i \cap C_j| / |C_i|$ filtered by $\tau_{sub}=0.15$ or Jaccard $\ge \tau_{sig}=0.40$.
   - Elimination of lexical hardcoded disjointness regexes (`Course`, `Student`, `Faculty`, `Professor`, `Staff`).
   - Domain-agnostic disjointness candidate mining:
     * Two non-empty classes $C_1, C_2$ are disjoint candidates if instance overlap ratio $|C_1 \cap C_2| / \min(|C_1|, |C_2|) \le \epsilon_{disj}$ ($0.005$) and conditional containment is near zero ($\max(conf_{12}, conf_{21}) < \tau_{sub}$).
   - Property empirical characteristic extraction: transitivity $\rho_{\text{trans}}$, symmetry $\rho_{\text{sym}}$, functionality $\rho_{\text{func}}$, inverse functionality $\rho_{\text{invfunc}}$.

5. **Calibrated Axiom Adjudication & Tournament Selection**:
   - Bounded payloads strictly $\le 1,500$ tokens ($O(1)$ scaling relative to KB size).
   - 5-way choice for taxonomic relations, property characteristic gating ($\theta_{noul} = 0.80$, $\delta_{deadband} = 0.15$).
   - $k$-ary tournament tree ($b=15$) for property domain/range selection.

6. **Graph-Theoretic TBox Repair**:
   - Tarjan SCC equivalence collapsing for mutual symmetric subsumptions ($\ge 0.80$) into `owl:equivalentClass`.
   - Minimum Feedback Arc Set (MFAS) cycle breaking for directed cycles to guarantee a strict DAG (0 directed cycles).
   - Transitive reduction (`nx.transitive_reduction`) for minimal Hasse diagram.
   - Disjointness-subsumption conflict pruning via DAG reachability to guarantee $DVC_{post} = 0$.
   - Property characteristic mutex enforcement.

7. **Materialization & Provenance**:
   - OWL 2 / RDFS serialization in Turtle format.
   - Dynamic W3C PROV-O reification predicates (`f"{namespace}decisionProbability"`, `f"{namespace}confidenceScore"`, `f"{namespace}aboxSupportCount"`).

8. **Automated Cross-Domain Test Harness (`test_cross_domain.py`)**:
   - Parameterized headless execution across 3-4 distinct domain benchmark datasets.
   - Execution isolation ensuring clean states and independent outputs.
   - Comprehensive assertions: 100% valid syntax, 0 cycles (DAG), $DVC_{post} == 0$, token limit <= 1500, OntoQA metrics within mathematical bounds ($0 < RR \le 1.0$, $IR > 0.0$, $0.5 \le CCR \le 1.0$).
   - Formatted cross-domain comparison matrix.

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F1 | Retail/E-Commerce Benchmark Dataset | Synthetic ABox with products, orders, customers, reviews, untyped clusters, disjointness, and intentional noise | M1 | R1 |
| F2 | Hospital/Biomedical Benchmark Dataset | Synthetic ABox with patients, diagnoses, treatments, medications, untyped clusters, disjointness, and noise | M1 | R1 |
| F3 | Enterprise Organization Benchmark Dataset | Synthetic ABox with employees, projects, departments, assets, budgets, untyped clusters, disjointness, and noise | M1 | R1 |
| F4 | Financial/Banking Benchmark Dataset | Synthetic ABox with accounts, transactions, loans, branches, untyped clusters, disjointness, and noise | M1 | R1 |
| F5 | Parametric I/O Configuration | Allow ABOX_INPUT_PATH and TBOX_OUTPUT_PATH override via environment variables | M2 | R2 |
| F6 | Dynamic Namespace Derivation | Infer ontology URI and base namespace dynamically from input triples | M2 | R2 |
| F7 | Domain-Agnostic Concept Synthesis | Statistical/TF-IDF predicate noun extraction, eliminating keyword rules | M2 | R2 |
| F8 | Domain-Agnostic Disjointness Mining | Pure statistical overlap ratio disjointness mining, eliminating lexical regex rules | M2 | R2 |
| F9 | Provenance URI Generalization | Dynamic namespace for PROV-O reification annotations | M2 | R2 |
| F10 | Cross-Domain Test Runner | Execution harness running notebook headlessly per benchmark dataset with isolated outputs | M3 | R3 |
| F11 | Cross-Domain Assertion Suite | Verify OWL 2 Turtle syntax, strict DAG, DVC_post==0, token <= 1500, OntoQA bounds per domain | M3 | R3 |
| F12 | Cross-Domain Comparison & Reporting | Formatted comparative table of metrics across all benchmark domains | M3 | R3 |
| F13 | Regression Verification Suite | Verify test_pipeline.py passes all 7/7 acceptance assertions | M3 | R3, Non-Regression |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Multi-Domain Benchmark Datasets Generation | Author 4 synthetic benchmark datasets: `input/ecommerce_abox.ttl`, `input/hospital_abox.ttl`, `input/enterprise_abox.ttl`, `input/banking_abox.ttl` | none | DONE |
| M2 | Domain-Agnostic Pipeline Refactor | Refactor `ABox2TBox.ipynb` to remove all hardcoded university terms, implement statistical concept synthesis, statistical disjointness mining, dynamic namespaces, and parametric I/O | none | DONE |
| M3 | Automated Cross-Domain Verification Harness | Implement `test_cross_domain.py` executing notebook across all benchmarks, verifying all assertions, generating comparison table, and checking non-regression | M1, M2 | DONE |
| M4 | Comprehensive Multi-Agent Quality Gate | Run Reviewers, Challengers, and Forensic Auditor for full verification and integrity validation | M1, M2, M3 | DONE |

---

## Interface Contracts

### Benchmark Datasets Contract (`input/*_abox.ttl`)
- **Format**: Valid W3C Turtle (`text/turtle`), parseable by `rdflib.Graph().parse()`.
- **Target Files**:
  1. `input/ecommerce_abox.ttl` (prefix `: <http://example.org/ecommerce#>`)
  2. `input/hospital_abox.ttl` (prefix `: <http://example.org/hospital#>`)
  3. `input/enterprise_abox.ttl` (prefix `: <http://example.org/enterprise#>`)
  4. `input/banking_abox.ttl` (prefix `: <http://example.org/banking#>`)
- **Volume & Content**:
  - 500 – 1500 RDF triples per dataset.
  - Multi-level class hierarchy ($\ge 3$ levels deep).
  - Explicit classes with instances.
  - At least 2–3 distinct untyped entity clusters with rich incoming/outgoing property signatures.
  - Disjointness boundaries (e.g. PhysicalProduct vs DigitalService; Inpatient vs Outpatient; FullTime vs Contractor; CheckingAccount vs LoanAccount).
  - Algebraic property characteristics (transitive, symmetric, functional).
- **Challenge Structures / Injected Noise**:
  - Mutual subsumption cycle (e.g., $A \sqsubseteq B$ and $B \sqsubseteq A$) for Tarjan SCC testing.
  - Directed cycle back-edge (e.g., $Root \sqsubseteq Leaf$) for MFAS DAG testing.
  - Redundant transitive edge (e.g., $Leaf \sqsubseteq Root$) for Hasse reduction testing.
  - Injected disjointness violation instance for conflict repair testing ($DVC_{pre} > 0 \rightarrow DVC_{post} == 0$).
  - Property empirical noise (e.g. near-symmetric ~0.90, near-transitive ~0.08).

### Refactored Notebook Contract (`ABox2TBox.ipynb`)
- **Input / Output**:
  - Reads `os.environ.get("ABOX_INPUT_PATH", "/home/miskat/ABOX2TBOX/input/ABox.ttl")`.
  - Writes to `os.environ.get("TBOX_OUTPUT_PATH", "/home/miskat/ABOX2TBOX/output/TBox.ttl")`.
  - Writes plot to `os.environ.get("TELEMETRY_PLOT_PATH", "/home/miskat/ABOX2TBOX/output/telemetry_diagnostics.png")`.
- **Generalization**:
  - 0 occurrences of hardcoded university terms in concept induction or disjointness mining.
  - Open-vocabulary TF-IDF / statistical noun extraction for untyped entity clusters.
  - Pure statistical overlap ratio for disjointness candidate detection.
  - Dynamic namespace derivation for ontology URI, labels, and PROV-O reification.
- **Constraints**:
  - Subsumption graph forms a strict DAG (0 directed cycles).
  - $DVC_{post} == 0$ against the input benchmark dataset.
  - All prompt payloads strictly $\le 1,500$ tokens.
  - OntoQA metrics computed: $0 < RR \le 1.0$, $IR > 0.0$, $0.5 \le CCR \le 1.0$.

### Cross-Domain Test Harness Contract (`test_cross_domain.py`)
- **Invocation**: `python3 test_cross_domain.py` (CLI, exit code 0 on success) or `pytest test_cross_domain.py -v`.
- **Execution**:
  - Iterates through all benchmark datasets (`input/ABox.ttl`, `input/ecommerce_abox.ttl`, `input/hospital_abox.ttl`, `input/enterprise_abox.ttl`, `input/banking_abox.ttl`).
  - Executes notebook headlessly in isolated process or clean IPython shell with injected environment variables.
  - Outputs per domain: `output/<domain>_tbox.ttl` and `output/<domain>_telemetry.png`.
- **Verifications per Domain**:
  1. Notebook execution succeeds without cell failure.
  2. `TBox.ttl` parses as valid OWL 2 / RDFS in Turtle with $\ge 15$ classes.
  3. Strict DAG acyclicity (0 directed cycles).
  4. Post-repair disjointness violations $DVC_{post} == 0$.
  5. Maximum prompt payload $\le 1,500$ tokens.
  6. OntoQA metrics ($RR, IR, CCR$) non-empty and within mathematical bounds.
- **Reporting**:
  - Prints aggregated comparison table across all evaluated domains.

---

## Code Layout
- Workspace Root: `/home/miskat/ABOX2TBOX`
  - `ABox2TBox.ipynb`: General, domain-agnostic Jupyter Notebook.
  - `test_pipeline.py`: Existing baseline university benchmark test harness (MUST pass 7/7 assertions).
  - `test_cross_domain.py`: Multi-domain automated test harness.
  - `input/`:
    * `ABox.ttl`: Baseline university benchmark dataset.
    * `ecommerce_abox.ttl`: E-Commerce synthetic benchmark.
    * `hospital_abox.ttl`: Hospital/Biomedical synthetic benchmark.
    * `enterprise_abox.ttl`: Corporate/Enterprise synthetic benchmark.
    * `banking_abox.ttl`: Financial/Banking synthetic benchmark.
  - `output/`:
    * `TBox.ttl`: Default output TBox.
    * `ecommerce_tbox.ttl`, `hospital_tbox.ttl`, etc.: Per-domain materialized TBox files.
    * `telemetry_diagnostics.png`: Default diagnostic visualization.
    * `<domain>_telemetry.png`: Per-domain diagnostic visualizations.
- Metadata Directory: `/home/miskat/ABOX2TBOX/.agents/`
  - `orchestrator_2/`: Orchestrator state, plan, progress, PROJECT.md, GATE_STATUS.md.
  - Subagent working directories: `.agents/worker_m1_1/`, `.agents/worker_m2_1/`, etc.
