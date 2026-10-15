# Task Assignment: Synthetic Benchmark & Test Architecture Survey

## Identity & Context
- Role: Dataset & Test Architect Explorer (`teamwork_preview_explorer`)
- Working Directory: `/home/miskat/ABOX2TBOX/.agents/explorer_dataset_test_1`
- Parent: Orchestrator (`0a10e674-c27e-47e5-ac70-e7b05332cf40`)

## Mandatory Inputs (Read these first)
1. `/home/miskat/ABOX2TBOX/.agents/ORIGINAL_REQUEST.md` (Authoritative user request)
2. `/home/miskat/ABOX2TBOX/software_requirements_specification_abox_to_tbox_induction_notebook.md` (SRS Sections 4, 5, 7)

## Objective
Design the specifications for:
1. `ABox.ttl` synthetic university domain benchmark dataset:
   - What classes, instances, object properties, and data properties should be present?
   - How to incorporate explicit types AND untyped entity clusters needing concept induction?
   - What ground-truth subsumption hierarchies should exist (e.g. Professor -> FacultyMember -> AcademicStaff -> Person)?
   - What ground-truth disjointness pairs should exist (e.g. Course disjointWith Department, Student disjointWith Professor)?
   - What intentional noise should be injected (e.g. accidental cyclic assertions, noisy symmetric/transitive property assertions) to rigorously test Section 5 graph repair?
2. `test_pipeline.py` programmatic verification script:
   - How to execute `ABox2TBox.ipynb` programmatically end-to-end.
   - What automated assertions to verify (valid OWL 2 / RDFS in `TBox.ttl`, 0 directed cycles in subsumption DAG, $DVC_{\text{post}} = 0$, prompt token bounds $\le 1500$, OntoQA metrics present and non-empty, PROV-O annotations).

## Deliverable
Write your findings to `/home/miskat/ABOX2TBOX/.agents/explorer_dataset_test_1/report.md` and deliver `handoff.md`. Notify parent when done.

## 2026-10-14T17:36:03Z
You are the Dataset & Test Architect Explorer for the ABox-to-TBox ontology induction project. Your assigned working directory is /home/miskat/ABOX2TBOX/.agents/explorer_dataset_test_1. Read /home/miskat/ABOX2TBOX/.agents/explorer_dataset_test_1/DISPATCH.md, /home/miskat/ABOX2TBOX/.agents/ORIGINAL_REQUEST.md, and /home/miskat/ABOX2TBOX/software_requirements_specification_abox_to_tbox_induction_notebook.md. Analyze and design the benchmark dataset ABox.ttl (university domain, ground truth hierarchies, untyped clusters, intentional noise) and test_pipeline.py automated test harness (end-to-end execution, strict DAG, DVC_post = 0, <= 1500 token ceiling, OntoQA metrics). Save your report in /home/miskat/ABOX2TBOX/.agents/explorer_dataset_test_1/report.md, maintain your progress.md, and write handoff.md upon completion. When done, send a message to parent (0a10e674-c27e-47e5-ac70-e7b05332cf40).
