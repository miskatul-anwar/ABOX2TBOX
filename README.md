# ABox-to-TBox induction

Run `abox2tbox.ipynb` from this directory, in cell order. Install the pinned Python
dependencies with `python -m pip install -r requirements.txt`. HermiT also requires
a working Java runtime. The notebook no longer installs or upgrades packages on
every execution.

The default input remains `input/agriAbox.ttl`. Paths and transport settings can
be overridden before starting the kernel:

```sh
export USE_LLM=false
export ABOX_INPUT_PATH="$PWD/input/ABox.ttl"
export TBOX_OUTPUT_PATH=/tmp/abox2tbox/TBox.ttl
export TELEMETRY_PLOT_PATH=/tmp/abox2tbox/telemetry.png
jupyter notebook abox2tbox.ipynb
```

For model-assisted induction, set `USE_LLM=true`, `OLLAMA_BASE_URL`, and
`MODEL_DECISION`. The notebook preserves the existing private-server default,
`http://100.75.221.29:11434`, but contacts only the configured endpoint. It probes
native `/v1/systemone`, then attempts actual JSON-chat adjudication via `/api/chat`.
It abstains if neither works. Naming uses deterministic candidate names with
optional model selection; there is no separate generative-model dependency.

## Interpretation and validation

- Offline mode produces provisional signature groups and conservative empirical
  subclass hypotheses. It does not turn non-overlap into disjointness, identical
  samples into equivalence, or missing two-hop observations into transitivity.
  Stronger axioms require explicit model confirmation. Model confirmation is
  evidence for a hypothesis, not proof of domain truth.
- Role rules use PCA statistics; restrictions use one-step coverage scoring.
  Taxonomic cycle repair is a greedy algorithm, not MaxSAT. Signature containment
  is not a full formal-concept lattice implementation.
- OWL annotations distinguish empirical support from model probabilities and
  record the actual source. Graph repair includes equivalences and propagates
  non-simple properties through subproperty/inverse relationships. Chain checking
  is conservative and can reject legal recursive chains.
- The complete round-tripped TBox is checked by HermiT for unsatisfiable named
  classes, then checked with **training assertions only** for inconsistency.
  Failed validation or an unavailable reasoner stops execution before replacing
  the output. This is not a substitute for a comprehensive external OWL profile
  checker or expert review of the induced semantics.
- Type and role hold-outs are deterministic and inaccessible to induction.
  Positive-only hold-outs report recovery recall and sample counts. Precision
  and F1 are `None`, since absent assertions are not labeled negatives.
- Recovery uses subclass/equivalence closure, domains/ranges, subproperties,
  inverses, chains, symmetry, reflexivity, and transitivity. It does not implement
  full OWL entailment, existential witnesses, restriction-based type inference,
  or equality reasoning. Recall describes this rule fragment.

## Calibration and request budgets

Calibration is unavailable unless directed model probabilities and independent
binary labels overlap. Set `CALIBRATION_LABELS_PATH` to a JSON file such as:

```json
[
  {"sub": "https://example.org/Student", "super": "https://example.org/Person", "label": 1},
  {"sub": "https://example.org/Person", "super": "https://example.org/Student", "label": 0}
]
```

Labels must be independently established, include indirect subclass entailment,
and represent the population whose calibration is being assessed. They are read
only after induction and export. ECE includes probability 1.0 and omits empty
bins; no self-generated taxonomy is used as ground truth.

`MAX_DECISION_PAIRS` and `MAX_LLM_PAIRS` bound decision attempts across stages.
Requests are sent one candidate at a time. `MAX_PAYLOAD_TOKENS` gates a conservative
UTF-8 byte estimate plus a framing reserve; without the server's exact tokenizer
this is not a guarantee of the server token count. Oversized requests abstain.
Reported token counts are recorded separately from estimates; a reported overrun
disables further model calls. Errors open a shared circuit breaker after
`LLM_MAX_CONSECUTIVE_ERRORS` consecutive failures. Audit entries identify errors
and skipped requests. Offline execution records zero network calls.

## Tests and regeneration

Install pytest to run:

```sh
python -m pytest test_complete_v3.py test_pipeline.py test_cross_domain.py -q
```

Tests use temporary outputs, restore environment settings, and perform no model
requests. They cover the actual notebook, five bundled domains, logical failures,
hold-out isolation, deterministic splitting, and mocked native/chat transports.
The regression suite replaces the previous copied pipeline in
`test_complete_v3.py`, which executed obsolete code at import time.

`build_notebook.py` contains the synchronized, output-free notebook cells and
regenerates `abox2tbox.ipynb`. Update both when editing cells; a regression test
checks that their sources match. `pipeline_support.py` contains the shared
transport, validation, closure, and calibration functions.
