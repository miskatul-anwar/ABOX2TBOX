# Task Assignment: Specification Mining for ABox-to-TBox Induction

## Identity & Context
- Role: Specification Investigator (`teamwork_preview_spec_miner`)
- Working Directory: `/home/miskat/ABOX2TBOX/.agents/spec_miner_survey_1`
- Parent: Orchestrator (`0a10e674-c27e-47e5-ac70-e7b05332cf40`)

## Mandatory Inputs (Read these first)
1. `/home/miskat/ABOX2TBOX/.agents/ORIGINAL_REQUEST.md` (Authoritative user request)
2. `/home/miskat/ABOX2TBOX/software_requirements_specification_abox_to_tbox_induction_notebook.md` (Full SRS)

## Objective
Thoroughly extract and formalize every requirement, constraint, mathematical formula, data schema, API contract, and acceptance criterion for the ABox-to-TBox ontology induction notebook project.

Specifically document:
- Breakdown of all 8 notebook sections (0 to 7) and their exact inputs/outputs.
- Formal definitions of Characteristic Sets ($CS$), xxhash64 signatures, equivalence clustering.
- Micro-prompt specifications for `tinyllama:latest` (/api/generate, token budgets <= 400 in, 64 out, JSON schema, PascalCase regex, fallback naming).
- Axiom adjudication specifications for `tev1:0.8b` (/v1/systemone: choice, noul, score, k-ary tournament trees, payload <= 1500 tokens).
- Decision acceptance thresholds (theta_prob, theta_conf, theta_score, theta_noul, delta_deadband).
- Graph repair algorithms: Tarjan's SCC for owl:equivalentClass, Minimum Feedback Arc Set for strict DAG, transitive reduction (Hasse diagram), disjointness-subsumption consistency.
- TBox.ttl serialization requirements and optional W3C PROV-O annotations.
- Section 7 research evaluation metrics (RR, IR, CCR, DVC, token utilization).

## Deliverable
Write your comprehensive analysis to `/home/miskat/ABOX2TBOX/.agents/spec_miner_survey_1/report.md` and deliver `handoff.md`. Notify parent when done.

## 2026-10-14T17:36:02Z
You are the Specification Investigator for the ABox-to-TBox ontology induction project. Your assigned working directory is /home/miskat/ABOX2TBOX/.agents/spec_miner_survey_1. Read /home/miskat/ABOX2TBOX/.agents/spec_miner_survey_1/DISPATCH.md, /home/miskat/ABOX2TBOX/.agents/ORIGINAL_REQUEST.md, and /home/miskat/ABOX2TBOX/software_requirements_specification_abox_to_tbox_induction_notebook.md. Thoroughly extract all requirements, constraints, mathematical formulas, data schemas, API contracts, thresholds, and acceptance criteria. Save your comprehensive report in /home/miskat/ABOX2TBOX/.agents/spec_miner_survey_1/report.md, maintain your progress.md, and write handoff.md upon completion. When done, send a message to parent (0a10e674-c27e-47e5-ac70-e7b05332cf40).

