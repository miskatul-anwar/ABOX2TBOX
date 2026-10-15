# Plan: Multi-Domain Generalization & Hardening

## Objective
Evaluate, generalize, and iteratively harden the ABox-to-TBox ontology induction pipeline across diverse multi-domain benchmarks to prevent overfitting and ensure structural and logical validity.

## Phases

### Phase 0: Survey & Codebase Investigation (Parallel Exploration)
- **Explorer 1 (Codebase & Notebook Analyzer)**: Inspect `ABox2TBox.ipynb` for any hardcoded university-specific terms (Course, Student, Faculty, Grant, etc.), heuristics, fallbacks, concept induction rules, and disjointness logic.
- **Explorer 2 (Benchmark Domain Designer)**: Investigate structural requirements for 3-4 distinct synthetic benchmark datasets (`ABox.ttl` in E-Commerce/Retail, Hospital/Biomedical, Enterprise/Corporate domains), including explicitly typed instances, untyped characteristic set clusters, multi-level class hierarchies, disjointness boundaries, and realistic statistical noise.
- **Spec Miner 3 (Harness & Metrics Architect)**: Analyze verification requirements for the automated cross-domain test harness (`test_cross_domain.py`), OntoQA metrics boundaries, regression checking against `test_pipeline.py`, DAG enforcement, DVC=0, token ceiling.

### Phase 1: Architecture & Decomposition Synthesis
- Synthesize explorer findings into `/home/miskat/ABOX2TBOX/.agents/orchestrator_2/PROJECT.md`.
- Establish Feature Inventory, Milestones, Interface Contracts, and Code Layout.

### Phase 2: Milestone Execution (Dual Track)
- **Milestone 1 (Worker M1)**: Generate 3-4 distinct synthetic benchmark datasets (`input/ecommerce_abox.ttl`, `input/hospital_abox.ttl`, `input/enterprise_abox.ttl`, etc.).
- **Milestone 2 (Worker M2)**: Refactor `ABox2TBox.ipynb` to be completely domain-agnostic with robust statistical heuristics and open-vocabulary concept induction.
- **Milestone 3 (Test Writer / Worker M3)**: Implement automated cross-domain verification test harness (`test_cross_domain.py`).

### Phase 3: Verification, Hardening & Independent Quality Gate
- Run `test_pipeline.py` (ensure 7/7 passing backwards compatibility).
- Run `test_cross_domain.py` (ensure 100% pass across all multi-domain benchmarks).
- Multi-Agent Gate:
  - 2 Reviewers independently evaluating code quality, modularity, domain-agnosticism.
  - 2 Challengers empirically stress-testing boundary cases, DAG checks, DVC=0, and token limits.
  - 1 Forensic Auditor (`teamwork_preview_auditor`) running integrity forensics (no hardcoded answers, no fake tests, authentic execution).
- Gate Decision in `GATE_STATUS.md`.

### Phase 4: Final Reporting & Handoff
- Produce comprehensive final report with OntoQA comparison across domains, structural diagnostics, and verification proofs.
