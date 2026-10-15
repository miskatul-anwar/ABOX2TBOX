# Task Assignment: Milestone 1 — Synthetic Benchmark ABox.ttl & test_pipeline.py

## Identity & Context
- Role: Implementation Worker (`teamwork_preview_worker`)
- Working Directory: `/home/miskat/ABOX2TBOX/.agents/worker_m1_1`
- Parent: Orchestrator (`0a10e674-c27e-47e5-ac70-e7b05332cf40`)
- Write Ownership: You exclusively own `/home/miskat/ABOX2TBOX/ABox.ttl` and `/home/miskat/ABOX2TBOX/test_pipeline.py`. Do NOT write or edit any other project files.

## Mandatory Inputs (Read these first)
1. `/home/miskat/ABOX2TBOX/.agents/ORIGINAL_REQUEST.md` (Authoritative user request)
2. `/home/miskat/ABOX2TBOX/.agents/orchestrator_1/PROJECT.md` (Project specifications and interface contracts)
3. `/home/miskat/ABOX2TBOX/.agents/explorer_dataset_test_1/report.md` (Detailed blueprints for ABox.ttl and test_pipeline.py)
4. `/home/miskat/ABOX2TBOX/software_requirements_specification_abox_to_tbox_induction_notebook.md` (Reference SRS)

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Objective
Implement:
1. `/home/miskat/ABOX2TBOX/ABox.ttl`:
   - High-quality, valid Turtle dataset representing an academic university domain (~350–500 instances, ~2,500–3,500 triples).
   - Deep taxonomies: Person (Employee -> AcademicStaff -> FacultyMember -> Tenured/TenureTrack/Visiting/Adjunct; AdministrativeStaff; Student -> Undergrad/Grad/PhD/Master; TeachingAssistant multiple inheritance), Organization (AcademicUnit -> Department/Faculty/ResearchInstitute), Course (Undergrad/Grad), Publication (JournalArticle/ConferencePaper).
   - 3 distinct untyped entity clusters lacking explicit rdf:type (`ResearchGrant` with grantNumber, fundingAgency, fundingAmount, principalInvestigator, etc.; `ResearchLaboratory` with labDirector, locatedInRoom, affiliatedDepartment, etc.; `AcademicDegree` with degreeTitle, conferredBy, degreeLevel).
   - 5 intentional noise patterns for Section 5 graph repair testing:
     1. Mutual subsumption cycle (`Lecturer` <-> `Instructor` with >= 90% instance overlap).
     2. Directed cycle back-edge (`Person` -> `FullProfessor` with low support <= 2 instances).
     3. Redundant transitive edge (`FullProfessor` -> `Person`).
     4. Disjointness contradiction (1 instance asserted with both `UndergraduateStudent` and `TenuredProfessor`).
     5. Algebraic property noise (near-symmetric, near-transitive, near-functional relations).

2. `/home/miskat/ABOX2TBOX/test_pipeline.py`:
   - Headless notebook runner using `IPython.core.interactiveshell.InteractiveShell` (per blueprint in `explorer_dataset_test_1/report.md`).
   - 7 automated assertions:
     1. Notebook execution integrity (all cells run, >= 15 cells).
     2. Valid OWL 2 / RDFS in TBox.ttl (>= 15 classes).
     3. Strict subsumption DAG (0 directed cycles).
     4. Post-repair disjointness violations DVC_post == 0.
     5. Token ceiling <= 1,500 tokens across all model calls.
     6. OntoQA metrics present and non-empty (RR, IR, CCR).
     7. Valid PROV-O reification metadata when enabled.
   - Dual execution support: CLI `python3 test_pipeline.py` and Pytest `pytest test_pipeline.py`.

3. Self-Verification:
   - Run python verification commands to confirm `ABox.ttl` parses without syntax errors using `rdflib`.
   - Confirm entity counts, predicate signatures, untyped clusters, and noise patterns in `ABox.ttl`.
   - Test `test_pipeline.py` import and structure.

## Deliverable
Document your implementation, verification commands, and outputs in `/home/miskat/ABOX2TBOX/.agents/worker_m1_1/handoff.md`.

## 2026-10-14T17:44:18Z
You are the Implementation Worker for Milestone 1: Benchmark Dataset & Automated Test Harness.
Your assigned working directory is /home/miskat/ABOX2TBOX/.agents/worker_m1_1.
Read your dispatch assignment at /home/miskat/ABOX2TBOX/.agents/worker_m1_1/DISPATCH.md.
Read /home/miskat/ABOX2TBOX/.agents/ORIGINAL_REQUEST.md.
Read the architectural blueprint at /home/miskat/ABOX2TBOX/.agents/explorer_dataset_test_1/report.md and project spec at /home/miskat/ABOX2TBOX/.agents/orchestrator_1/PROJECT.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Implement:
1. /home/miskat/ABOX2TBOX/ABox.ttl per blueprint (~350-500 instances, ~2500-3500 triples, deep taxonomies, 3 untyped clusters, 5 intentional noise patterns).
2. /home/miskat/ABOX2TBOX/test_pipeline.py with InteractiveShell headless notebook executor, 7 acceptance assertions, dual CLI and pytest runners.

Verify your work with rdflib parsing and python tests, document verification results in /home/miskat/ABOX2TBOX/.agents/worker_m1_1/handoff.md, and send a completion message to parent (0a10e674-c27e-47e5-ac70-e7b05332cf40).
