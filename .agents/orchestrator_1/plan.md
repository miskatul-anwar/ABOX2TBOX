# Orchestrator Plan — ABox2TBox Ontology Induction

## Phase 0: Survey & Scope Mapping
- Dispatch 3 Explorers / Spec Miners:
  - Explorer 1 (Spec Miner): Deep-mine requirements from SRS (R1-R5, mathematical formulas, payload schemas, acceptance criteria).
  - Explorer 2: Analyze environment dependencies (python packages, rdflib, networkx, duckdb, sqlite3, requests, matplotlib, pandas, ollama service status and fallback strategies).
  - Explorer 3: Define synthetic university domain benchmark requirements (ABox.ttl) with ground truth taxonomies and intentional noise, plus test harness requirements (test_pipeline.py).
- Synthesize findings into `PROJECT.md` Feature Inventory & Architecture.

## Phase 1: Dual Track Decomposition & Execution
- **Track 1: Benchmark Dataset & Test Harness**
  - Worker writes `ABox.ttl` (synthetic academic domain, explicit + untyped clusters, disjointness ground truth, cycles, noisy transitivity/symmetry/functionality).
  - Worker writes `test_pipeline.py` (executes notebook cells or python equivalent, checks OWL 2 valid TBox.ttl, 0 cycles, DVC_post = 0, <= 1500 tokens payload bounds, OntoQA metrics).
  - Verification & Review.
- **Track 2: ABox2TBox.ipynb Implementation (Sections 0 to 7)**
  - Implement full 8 sections (0 to 7) per SRS with fallback simulations for Ollama `/v1/systemone` and `/api/generate`.
  - Review, Challenge, Forensic Audit.

## Phase 2: Full End-to-End Verification & Gate Approval
- Execute `test_pipeline.py` and inspect notebook execution.
- Reviewer, Challenger, and Forensic Auditor verdicts.
- When all pass, report completion to Sentinel.
