"""Configuration defaults, environment loading, and explicit API overrides."""

from __future__ import annotations
from collections.abc import Mapping
from pathlib import Path
from typing import Any
import math
import os


def load_config(
    overrides: Mapping[str, Any] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Resolve a fresh configuration without mutating environment or global state."""
    env = os.environ if environ is None else environ
    base_dir = str(Path.cwd() if base_dir is None else base_dir)
    config: dict[str, Any] = {
        "OLLAMA_BASE_URL": env.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        "MODEL_DECISION": env.get("MODEL_DECISION", "clef-flash:latest"),
        "USE_LLM": env.get("USE_LLM", "false").lower() in ("1", "true", "yes"),
        "LLM_TIMEOUT_S": float(env.get("LLM_TIMEOUT_S", "20.0")),
        "LLM_MAX_CONSECUTIVE_ERRORS": int(env.get("LLM_MAX_CONSECUTIVE_ERRORS", "3")),
        "SYSTEMONE_BATCH_SIZE": int(env.get("SYSTEMONE_BATCH_SIZE", "16")),
        "MAX_DECISION_PAIRS": int(env.get("MAX_DECISION_PAIRS", "1000")),
        "MAX_LLM_PAIRS": int(env.get("MAX_LLM_PAIRS", "1000")),
        "MAX_PAYLOAD_TOKENS": int(env.get("MAX_PAYLOAD_TOKENS", "1500")),
        "ABOX_FORMAT": env.get("ABOX_FORMAT") or None,
        "CONFIRMATION_FRACTION": float(env.get("CONFIRMATION_FRACTION", "0.35")),
        "MIN_OBSERVED_COVERAGE": float(env.get("MIN_OBSERVED_COVERAGE", "0.90")),
        "MIN_CONFIRMATION_SUBJECTS": 12,
        "POSTERIOR_RISK_BUDGET": 0.05,
        "MAX_EVIDENCE_CANDIDATES": int(env.get("MAX_EVIDENCE_CANDIDATES", "1000")),
        "MAX_INPUT_TRIPLES": int(env.get("MAX_INPUT_TRIPLES", "2000000")),
        "MAX_JOIN_EDGES": int(env.get("MAX_JOIN_EDGES", "100000")),
        "MAX_MINING_CLASSES": 256,
        "MAX_MINING_PROPERTIES": 64,
        "TAU_MERGE_JACCARD": 0.65,
        "TAU_INTENSIONAL_SUB": 0.5,
        "TAU_SUB": 0.15,
        "TAU_SIG": 0.35,
        "WILSON_Z": 1.28,
        "AMIE_MIN_HC": 0.05,
        "AMIE_MIN_PCA_CONF": 0.75,
        "CELOE_LAMBDA": 0.2,
        "CELOE_BETA": 0.03,
        "JARO_WINKLER_THRESHOLD": 0.8,
        "THETA_PROB": 0.7,
        "THETA_CONF": 0.55,
        "THETA_SCORE": 1.8,
        "THETA_NOUL": 0.8,
        "THETA_DOMAIN_RANGE": 0.9,
        "THETA_LOCAL_RESTRICTION": 0.7,
        "HOLD_OUT_FRACTION": 0.2,
        "ROLE_HOLD_OUT_FRACTION": 0.15,
        "CALIBRATION_LABELS_PATH": env.get("CALIBRATION_LABELS_PATH"),
        "EXPORT_STRICT_OWL2_DL": True,
        "ABOX_PATH": env.get(
            "ABOX_INPUT_PATH", os.path.join(base_dir, "input", "agriAbox.ttl")
        ),
        "TBOX_PATH": env.get(
            "TBOX_OUTPUT_PATH", os.path.join(base_dir, "output", "TBox.ttl")
        ),
        "PLOT_PATH": env.get(
            "TELEMETRY_PLOT_PATH",
            os.path.join(base_dir, "output", "telemetry_diagnostics.png"),
        ),
    }

    if overrides:
        unknown = set(overrides) - config.keys()
        if unknown:
            raise ValueError(f"Unknown configuration keys: {sorted(unknown)}")
        config.update(
            {key: value for key, value in overrides.items() if value is not None}
        )
    validate_config(config)
    return config


def validate_config(config: Mapping[str, Any]) -> None:
    """Reject invalid budgets and fractions before opening input or transport."""
    for key in (
        "MAX_EVIDENCE_CANDIDATES",
        "MAX_INPUT_TRIPLES",
        "MAX_JOIN_EDGES",
        "MAX_MINING_CLASSES",
        "MAX_MINING_PROPERTIES",
        "MAX_DECISION_PAIRS",
        "MAX_LLM_PAIRS",
        "MAX_PAYLOAD_TOKENS",
        "LLM_MAX_CONSECUTIVE_ERRORS",
        "SYSTEMONE_BATCH_SIZE",
        "MIN_CONFIRMATION_SUBJECTS",
    ):
        value = config[key]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{key} must be a positive integer")
    for key in (
        "CONFIRMATION_FRACTION",
        "MIN_OBSERVED_COVERAGE",
        "POSTERIOR_RISK_BUDGET",
    ):
        if not 0 < config[key] < 1:
            raise ValueError(f"{key} must lie in (0,1)")
    for key in ("HOLD_OUT_FRACTION", "ROLE_HOLD_OUT_FRACTION"):
        if not 0 <= config[key] < 1:
            raise ValueError(f"{key} must lie in [0,1)")
    if not isinstance(config["USE_LLM"], bool):
        raise ValueError("USE_LLM must be a boolean")
    if not math.isfinite(config["LLM_TIMEOUT_S"]) or config["LLM_TIMEOUT_S"] <= 0:
        raise ValueError("LLM_TIMEOUT_S must be finite and positive")
