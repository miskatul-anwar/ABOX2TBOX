"""Keep validation runs independent of the caller's model and input settings."""

import pytest


@pytest.fixture(autouse=True)
def isolate_pipeline_environment(monkeypatch):
    for key in (
        "USE_LLM",
        "OLLAMA_BASE_URL",
        "MODEL_DECISION",
        "LLM_TIMEOUT_S",
        "LLM_MAX_CONSECUTIVE_ERRORS",
        "SYSTEMONE_BATCH_SIZE",
        "MAX_DECISION_PAIRS",
        "MAX_LLM_PAIRS",
        "MAX_PAYLOAD_TOKENS",
        "ABOX_FORMAT",
        "ABOX_INPUT_PATH",
        "TBOX_OUTPUT_PATH",
        "TELEMETRY_PLOT_PATH",
        "CALIBRATION_LABELS_PATH",
        "CONFIRMATION_FRACTION",
        "MIN_OBSERVED_COVERAGE",
        "MAX_EVIDENCE_CANDIDATES",
        "MAX_INPUT_TRIPLES",
        "MAX_JOIN_EDGES",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("USE_LLM", "false")
