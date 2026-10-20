"""State owned by one pipeline run, including its disposable discovery store."""

from __future__ import annotations
from dataclasses import dataclass, field
import sqlite3
import sys
from typing import Any
from rdflib import Graph


@dataclass
class PipelineState:
    """Stage outputs live here rather than in notebook or module globals.

    Each stage creates its named outputs on this object. Internal mining stages
    are available for diagnostics; use run_pipeline for the supported public API.
    No state is reused between runs, and no database is opened during import.
    """

    config: dict[str, Any]
    seed_value: int = 42
    verbose: bool = False
    payload_token_audit_log: list[dict[str, Any]] = field(default_factory=list)
    training_graph: Graph = field(default_factory=Graph)
    semantic_context: Graph = field(default_factory=Graph)
    completed_stages: list[str] = field(default_factory=list)
    conn: sqlite3.Connection | None = None
    cur: sqlite3.Cursor | None = None

    def log(self, *values: object) -> None:
        if self.verbose:
            print(*values, file=sys.stderr)

    def close(self) -> None:
        """Release SQLite on success, failure, or cancellation; safe to repeat."""
        if self.conn is not None:
            self.conn.close()
