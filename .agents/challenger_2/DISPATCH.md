# Task Assignment: Challenger 2 — Adversarial Empirical Verifier (Token Ceiling, Ingestion & Metrics)

## Identity & Context
- Role: Empirical Challenger (`teamwork_preview_challenger`)
- Working Directory: `/home/miskat/ABOX2TBOX/.agents/challenger_2`
- Parent: Orchestrator (`0a10e674-c27e-47e5-ac70-e7b05332cf40`)

## Mandatory Inputs (Read these first)
1. `/home/miskat/ABOX2TBOX/.agents/ORIGINAL_REQUEST.md` (Authoritative user request)
2. `/home/miskat/ABOX2TBOX/software_requirements_specification_abox_to_tbox_induction_notebook.md` (Full SRS)
3. `/home/miskat/ABOX2TBOX/.agents/orchestrator_1/PROJECT.md` (Project specifications and interface contracts)
4. `/home/miskat/ABOX2TBOX/ABox2TBox.ipynb` (Notebook implementation to challenge)
5. `/home/miskat/ABOX2TBOX/ABox.ttl` (Benchmark dataset)
6. `/home/miskat/ABOX2TBOX/TBox.ttl` (Materialized ontology)
7. `/home/miskat/ABOX2TBOX/test_pipeline.py` (Test harness)

## Objective
Empirically and adversarially test prompt token bounds, characteristic set compression scaling, and metric calculation rigor:
1. Write and run Python test scripts to verify:
   - Every single prompt recorded in `PAYLOAD_TOKEN_AUDIT_LOG` is $\le 1,500$ tokens (test maximum, mean, 95th percentile).
   - Characteristic set hashing algorithm produces deterministic 64-bit signatures and groups instances with identical predicate signatures into exact single prototypes.
   - Micro-prompt inputs are bounded to $\le 400$ input tokens and synthesize valid PascalCase class names.
   - Mathematical calculations of OntoQA metrics: Relationship Richness ($RR$), Inheritance Richness ($IR$), and Class Coverage Ratio ($CCR$) match manual graph recalculations.
2. Render an explicit verdict in your handoff: `APPROVE` or `REJECT`.

## Deliverable
Write your empirical test script, test output, and verdict to `/home/miskat/ABOX2TBOX/.agents/challenger_2/handoff.md`. Notify parent when done.

## 2026-10-14T18:15:00Z
You are Challenger 2 for the ABox-to-TBox ontology induction project.
Your assigned working directory is /home/miskat/ABOX2TBOX/.agents/challenger_2.
Read /home/miskat/ABOX2TBOX/.agents/challenger_2/DISPATCH.md.
Read /home/miskat/ABOX2TBOX/.agents/ORIGINAL_REQUEST.md and /home/miskat/ABOX2TBOX/software_requirements_specification_abox_to_tbox_induction_notebook.md.
Empirically and adversarially test token bounds, characteristic set compression, and OntoQA metric calculations:
Write and execute Python test scripts to verify all prompt payloads <= 1,500 tokens, 64-bit signature hash determinism, and independent calculation of Relationship Richness, Inheritance Richness, and Class Coverage Ratio.
Render an explicit verdict: APPROVE or REJECT.
Save your report and handoff to /home/miskat/ABOX2TBOX/.agents/challenger_2/handoff.md and notify parent (0a10e674-c27e-47e5-ac70-e7b05332cf40).

