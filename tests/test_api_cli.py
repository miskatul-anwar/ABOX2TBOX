"""Exercise the public codebase without any notebook or working-directory coupling."""

import ast
import json
import os
from pathlib import Path
import random
import shutil
import sqlite3
import subprocess
import sys

import pytest
from rdflib import Graph, Namespace
from rdflib.namespace import RDF

from abox2tbox import create_state, run_pipeline
from abox2tbox.config import load_config
from abox2tbox.pipeline import STAGES

ROOT = Path(__file__).resolve().parents[1]
EX = Namespace("urn:api:")


def input_file(tmp_path):
    source = tmp_path / "input.ttl"
    source.write_text('@prefix e: <urn:api:> . e:a a e:A ; e:label "one" .')
    return source


def test_two_api_runs_are_isolated_and_preserve_process_state(tmp_path):
    source = input_file(tmp_path)
    original = source.read_bytes()
    environment = dict(os.environ)
    rng_state = random.getstate()
    first = run_pipeline(source, tmp_path / "first.ttl", plot=False)
    second = run_pipeline(source, tmp_path / "second.ttl", plot=False)
    assert first.validation["status"] == second.validation["status"] == "passed"
    assert first.state is not second.state
    assert first.state.evidence_gate is not second.state.evidence_gate
    assert first.state.config is not second.state.config
    assert (
        first.state.payload_token_audit_log is not second.state.payload_token_audit_log
    )
    first.tbox.add((EX.only_first, RDF.type, EX.Extra))
    assert (EX.only_first, RDF.type, EX.Extra) not in second.tbox
    assert source.read_bytes() == original
    assert os.environ == environment
    assert random.getstate() == rng_state
    assert first.plot_path is None
    assert first.state.completed_stages == [s.__name__ for s in STAGES[:-1]]
    for result in (first, second):
        with pytest.raises(sqlite3.ProgrammingError):
            result.state.conn.execute("SELECT 1")
        ledger = json.loads(result.evidence_path.read_text())
        import hashlib

        assert (
            ledger["output_sha256"]
            == hashlib.sha256(result.output_path.read_bytes()).hexdigest()
        )


def test_failure_closes_database_and_preserves_prior_outputs(tmp_path, monkeypatch):
    from abox2tbox import data, ontology

    source = input_file(tmp_path)
    output = tmp_path / "TBox.ttl"
    ledger = output.with_suffix(".evidence.json")
    output.write_text("previous ontology")
    ledger.write_text("previous ledger")
    connections = []
    connect = sqlite3.connect

    def tracked_connect(*args, **kwargs):
        connection = connect(*args, **kwargs)
        connections.append(connection)
        return connection

    def unavailable(*args, **kwargs):
        raise RuntimeError("reasoner unavailable")

    monkeypatch.setattr(data.sqlite3, "connect", tracked_connect)
    monkeypatch.setattr(ontology, "validate_export", unavailable)
    with pytest.raises(RuntimeError, match="reasoner unavailable"):
        run_pipeline(source, output, plot=False)
    assert connections
    for connection in connections:
        with pytest.raises(sqlite3.ProgrammingError):
            connection.execute("SELECT 1")
    assert output.read_text() == "previous ontology"
    assert ledger.read_text() == "previous ledger"


@pytest.mark.parametrize("collision", ["input", "plot", "ledger"])
def test_output_collisions_fail_before_replacing_anything(tmp_path, collision):
    source = input_file(tmp_path)
    original = source.read_bytes()
    output = source if collision == "input" else tmp_path / "TBox.ttl"
    plot_path = output if collision == "plot" else output.with_suffix(".evidence.json")
    with pytest.raises(ValueError, match="distinct paths"):
        run_pipeline(source, output, plot_path=plot_path, plot=collision != "input")
    assert source.read_bytes() == original
    if output != source:
        assert not output.exists()


def test_output_symlink_cannot_hide_a_ledger_input_collision(tmp_path):
    source = tmp_path / "out.evidence.json"
    source.write_text("@prefix e: <urn:api:> . e:a a e:A .")
    original = source.read_bytes()
    previous = tmp_path / "previous.ttl"
    previous.write_text("previous ontology")
    target = tmp_path / "out.ttl"
    target.symlink_to(previous)
    with pytest.raises(ValueError, match="distinct paths"):
        run_pipeline(source, target, rdf_format="turtle", plot=False)
    assert source.read_bytes() == original
    assert target.is_symlink()
    assert previous.read_text() == "previous ontology"


def test_config_precedence_validation_and_no_environment_mutation(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("MAX_INPUT_TRIPLES", "99")
    env = dict(os.environ)
    assert load_config()["MAX_INPUT_TRIPLES"] == 99
    assert load_config({"MAX_INPUT_TRIPLES": 123})["MAX_INPUT_TRIPLES"] == 123
    assert os.environ == env
    assert load_config(environ={}, base_dir=tmp_path)["ABOX_PATH"] == str(
        tmp_path / "input/agriAbox.ttl"
    )
    with pytest.raises(ValueError, match="Unknown configuration"):
        load_config({"MISSPELLED_BUDGET": 12})
    with pytest.raises(ValueError, match="positive integer"):
        load_config({"MAX_INPUT_TRIPLES": 0})
    with pytest.raises(ValueError, match="lie in"):
        load_config({"CONFIRMATION_FRACTION": float("nan")})
    with pytest.raises(ValueError, match="seed must"):
        create_state(seed=True)


def test_cli_runs_without_a_notebook_from_another_directory(tmp_path):
    # Copy only package sources. No repository notebook, tests, or generator exists.
    isolated = tmp_path / "standalone"
    shutil.copytree(
        ROOT / "src/abox2tbox",
        isolated / "abox2tbox",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    source = input_file(tmp_path)
    output = tmp_path / "cli.ttl"
    env = {**os.environ, "PYTHONPATH": str(isolated)}
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "abox2tbox",
            str(source),
            "--output",
            str(output),
            "--offline",
            "--no-plot",
            "--json",
        ],
        cwd=isolated,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    summary = json.loads(completed.stdout)
    assert summary["validation"]["status"] == "passed"
    assert summary["plot_path"] is None
    assert len(Graph().parse(output)) == summary["tbox_triples"]
    assert not list(isolated.rglob("*.ipynb"))


def test_cli_failure_has_nonzero_status_and_keeps_output(tmp_path):
    source = tmp_path / "conflict.ttl"
    source.write_text("""@prefix e: <urn:api:> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        e:a owl:sameAs e:b ; owl:differentFrom e:b .""")
    output = tmp_path / "existing.ttl"
    output.write_text("previous output")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/run_pipeline.py"),
            str(source),
            "-o",
            str(output),
            "--offline",
            "--no-plot",
            "--json",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 1
    assert "sameAs/differentFrom contradiction" in result.stderr
    assert not result.stdout
    assert output.read_text() == "previous output"


def test_all_source_modules_parse_and_have_no_notebook_runtime():
    package = ROOT / "src/abox2tbox"
    expected = {
        "__init__",
        "__main__",
        "config",
        "cli",
        "state",
        "pipeline",
        "data",
        "mining",
        "adjudication",
        "ontology",
        "evaluation",
        "transport",
        "utils",
        "induction_evidence",
        "pipeline_support",
    }
    assert {p.stem for p in package.glob("*.py")} == expected
    for path in package.glob("*.py"):
        source = path.read_text()
        tree = ast.parse(source, filename=str(path))
        assert ".ipynb" not in source, path
        assert not any(
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id in {"exec", "eval", "compile"}
            for n in ast.walk(tree)
        ), path
