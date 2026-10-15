# Original User Request

## 2026-10-14T17:32:21Z

Implement a research-grade Jupyter Notebook (`ABox2TBox.ipynb`) that realizes a scalable neuro-symbolic ABox-to-TBox ontology induction pipeline, extracting formal OWL 2 / RDFS terminological boxes (`TBox.ttl`) from instance data (`ABox.ttl`) using graph mining, lexical LLM concept synthesis, and calibrated single-pass axiom adjudication.

Working directory: /home/miskat/ABOX2TBOX
Integrity mode: development

Reference specification: /home/miskat/ABOX2TBOX/software_requirements_specification_abox_to_tbox_induction_notebook.md

## Requirements

### R1. Eight-Section Interactive Jupyter Notebook
Implement `ABox2TBox.ipynb` covering all 8 modular sections defined in the SRS:
- Section 0: Environment Setup, Hyperparameters & Reproducibility Seeds
- Section 1: Scalable ABox Ingestion & Characteristic Set Profiling (`rdflib`, relational index)
- Section 2: Open-Vocabulary Concept Induction for Untyped Entities (`tinyllama:latest`)
- Section 3: Candidate Axiom Generation & Graph Pruning (`networkx`)
- Section 4: Hierarchical Tournament & Batch Axiom Verification (`tev1:0.8b` via `/v1/systemone`)
- Section 5: Graph-Theoretic TBox Repair & Consistency Enforcement (`networkx`)
- Section 6: `TBox.ttl` Materialization with W3C PROV-O Metadata (`rdflib`)
- Section 7: Research Evaluation, Ablation & Calibration Diagnostics (OntoQA metrics, ECE diagnostics, hierarchy plots)

### R2. Context-Invariant Ingestion & Characteristic Set Compression
Ingest `ABox.ttl` using streaming parsing and SQLite-backed relational indexing. Group entities lacking explicit types into equivalence clusters based on incoming/outgoing predicate signature hashes. Ensure that all downstream LLM prompt payloads scale as $O(1)$ with respect to KB size, strictly bounded to $\le 1,500$ tokens.

### R3. Dual-Model Neuro-Symbolic Integration with Resilient Fallback
- Integrate `tinyllama:latest` via `/api/generate` strictly for lexical class naming (`PascalCase`) and concise glosses of untyped clusters, protected by micro-prompt bounds ($\le 400$ tokens in, 64 tokens out), regex sanitization, and deterministic noun-phrase fallback.
- Integrate `tev1:0.8b` via `/v1/systemone` executing 5-way `choice` for taxonomic relations, `noul` for property characteristics, and $k$-ary tournament trees ($b=15$) for high-cardinality domain/range selection.
- Provide automatic simulation / deterministic heuristic fallback for `/v1/systemone` and `/api/generate` so the pipeline executes and tests reliably even when Ollama is offline or model weights are missing.

### R4. Graph-Theoretic Repair & Soundness
Construct the candidate subsumption graph in `networkx`. Apply Tarjan's Strongly Connected Components to collapse high-confidence mutual subsumptions into `owl:equivalentClass` clusters, eliminate residual cycles via Minimum Feedback Arc Set to yield a strict DAG, apply transitive reduction (Hasse diagram), and prune disjointness-subsumption conflicts.

### R5. Benchmark Dataset & Automated Test Harness
Provide a self-contained synthetic benchmark dataset (`ABox.ttl`) representing an academic university domain with ground-truth hierarchies and intentional noise. Provide a programmatic verification script (`test_pipeline.py` or equivalent test runner) that executes the notebook end-to-end and verifies structural and logical assertions.

## Acceptance Criteria

### Functional & Logical Consistency
- [ ] `ABox2TBox.ipynb` executes end-to-end without unhandled errors or notebook cell failures.
- [ ] Output `TBox.ttl` is valid OWL 2 / RDFS syntax parseable by `rdflib`.
- [ ] Subsumption hierarchy in `TBox.ttl` forms a strict Directed Acyclic Graph (0 directed cycles).
- [ ] Post-repair Disjointness Violation Count ($DVC_{\text{post}}$) equals 0 against the benchmark instances.
- [ ] Model request payloads remain strictly $\le 1,500$ tokens across all calls.
- [ ] Section 7 computes and displays OntoQA metrics (Relationship Richness, Inheritance Richness, Class Coverage Ratio) and renders hierarchy visualizations.
- [ ] Verification script runs automatically and reports all assertions passing.

## 2026-10-15T08:42:14Z

Evaluate, generalize, and iteratively harden the ABox-to-TBox ontology induction pipeline across diverse multi-domain benchmarks to prevent overfitting and ensure structural and logical validity.

Working directory: /home/miskat/ABOX2TBOX
Integrity mode: development
Requested team: Full multi-agent teamwork team

## Requirements

### R1. Multi-Domain Benchmark Dataset Generation
Generate 3–4 distinct synthetic RDF benchmark datasets (`ABox.ttl`) representing different real-world domains (e.g., E-Commerce/Retail catalog, Hospital/Biomedical records, Corporate/Enterprise organization). Each dataset must include explicitly typed instances, untyped characteristic set clusters, multi-level class hierarchies, disjointness boundaries, and realistic statistical noise.

### R2. Domain-Agnostic Pipeline Generalization
Refactor `ABox2TBox.ipynb` to eliminate domain-specific hardcoded assumptions (such as university-specific lexical rules for "Course", "Student", "Faculty", or "Grant"). Replace them with robust, generalizable heuristics and statistical pattern mining that induce valid concepts, taxonomies, and property axioms regardless of the input domain vocabulary.

### R3. Automated Cross-Domain Verification & Comparison Harness
Implement an automated multi-benchmark test harness that executes `ABox2TBox.ipynb` against each generated benchmark dataset, parses the resulting `TBox.ttl`, compares it against the input `ABox.ttl`, and verifies logical consistency and schema quality.

## Acceptance Criteria

### Generalization & Robustness
- [ ] Pipeline executes end-to-end on each benchmark dataset without code modifications between runs.
- [ ] No hardcoded domain-specific strings or class name rules remain in concept induction or disjointness filtering logic.

### Structural & Logical Validity
- [ ] 100% of generated `TBox.ttl` files parse as valid OWL 2 / RDFS in Turtle syntax.
- [ ] Every induced subsumption hierarchy forms a strict Directed Acyclic Graph (0 directed cycles).
- [ ] Exactly 0 post-repair disjointness violations ($DVC_{post} == 0$) across all benchmark datasets.
- [ ] 100% of LLM prompt payloads satisfy the strict <= 1,500 token ceiling.
- [ ] OntoQA metrics (Relationship Richness, Inheritance Richness, Class Coverage Ratio) are within valid mathematical bounds across all evaluated domains.

### Regression & Backward Compatibility
- [ ] The existing benchmark suite (`python3 test_pipeline.py`) continues to pass all 7/7 acceptance assertions.
- [ ] Code in `ABox2TBox.ipynb` remains modular, clean, and functional.

