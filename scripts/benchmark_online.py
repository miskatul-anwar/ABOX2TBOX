"""Download publisher RDF snapshots and test the real pipeline strictly sequentially.

Network access is needed only for acquisition. Each pipeline run uses the
installed package in an isolated subprocess with all model requests disabled.
Failures remain in the report; no triples are removed to make a source pass.
"""

from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".pending")
    temporary.write_text(
        json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def acquire(source, directory, timeout, max_bytes, refresh):
    """Save original response bytes and provenance; never parse remote RDF in-process."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / ("source." + source["extension"])
    provenance_path = directory / "download.json"
    if not refresh and path.exists() and provenance_path.exists():
        provenance = json.loads(provenance_path.read_text())
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        if (
            provenance["requested_url"] == source["url"]
            and checksum == provenance["sha256"]
        ):
            return path, {**provenance, "cached": True}
    accept = "application/rdf+xml" if source["format"] == "xml" else "text/turtle"
    request = urllib.request.Request(
        source["url"],
        headers={
            "Accept": accept,
            "User-Agent": "abox2tbox/4.1 (public RDF compatibility benchmark)",
        },
    )
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        body = response.read(max_bytes + 1)
        resolved_url = response.geturl()
        http_status = response.status
        etag = response.headers.get("ETag")
        last_modified = response.headers.get("Last-Modified")
    if len(body) > max_bytes:
        raise ValueError(f"Download exceeds {max_bytes} bytes")
    if not body:
        raise ValueError("Publisher returned an empty response")
    if "text/html" in content_type.lower() or body.lstrip().lower().startswith(
        (b"<!doctype html", b"<html")
    ):
        raise ValueError(
            f"Publisher returned HTML rather than RDF ({content_type}; {resolved_url})"
        )
    provenance = {
        "requested_url": source["url"],
        "resolved_url": resolved_url,
        "retrieved_at": utc_now(),
        "content_type": content_type,
        "http_status": http_status,
        "etag": etag,
        "last_modified": last_modified,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "download_seconds": round(time.monotonic() - started, 3),
        "preprocessing": "none; original publisher response bytes",
    }
    pending = path.with_suffix(path.suffix + ".pending")
    pending.write_bytes(body)
    pending.replace(path)
    write_json(provenance_path, provenance)
    return path, {**provenance, "cached": False}


def evaluate(source, input_path, destination, timeout):
    destination.mkdir(parents=True, exist_ok=True)
    output_path = destination / "TBox.ttl"
    summary_path = destination / "result.json"
    log_path = destination / "pipeline.log"
    command = [
        sys.executable,
        "-m",
        "abox2tbox",
        str(input_path),
        "--output",
        str(output_path),
        "--plot",
        str(destination / "telemetry.png"),
        "--format",
        source["format"],
        "--offline",
        "--json",
        "--verbose",
    ]
    env = {
        **os.environ,
        "USE_LLM": "false",
        "ABOX_FORMAT": source["format"],
        "CALIBRATION_LABELS_PATH": "",
        "MAX_INPUT_TRIPLES": "2000000",
        "MAX_JOIN_EDGES": "100000",
        "MAX_EVIDENCE_CANDIDATES": "1000",
        "CONFIRMATION_FRACTION": "0.35",
        "MIN_OBSERVED_COVERAGE": "0.90",
        "MAX_DECISION_PAIRS": "1000",
        "MAX_LLM_PAIRS": "1000",
        "MPLCONFIGDIR": str(destination / "matplotlib-cache"),
    }
    started = time.monotonic()
    status = "pipeline_error"
    with summary_path.open("w") as stdout, log_path.open("w") as stderr:
        process = subprocess.Popen(
            command, stdout=stdout, stderr=stderr, env=env, start_new_session=True
        )
        try:
            returncode = process.wait(timeout=timeout)
            status = "passed" if returncode == 0 else "pipeline_error"
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            returncode = process.returncode
            status = "timeout"
    result = {
        "status": status,
        "runtime_seconds": round(time.monotonic() - started, 3),
        "returncode": returncode,
        "timeout_seconds": timeout,
        "output_directory": str(destination.relative_to(ROOT))
        if destination.is_relative_to(ROOT)
        else str(destination),
        "command": command,
        "pipeline_summary": None,
        "input": None,
        "accepted_families": {},
        "counterexamples_found": 0,
    }
    if status == "passed":
        result["pipeline_summary"] = json.loads(summary_path.read_text())
        evidence = json.loads(output_path.with_suffix(".evidence.json").read_text())
        result["input"] = evidence["input"]
        records = evidence["candidates"]
        result["accepted_families"] = dict(
            Counter(c["family"] for c in records if c["status"] == "accepted")
        )
        result["counterexamples_found"] = sum(
            c.get("counterexample_count", 0) for c in records
        )
        result["rejection_reasons"] = dict(
            Counter(reason for c in records for reason in c.get("reasons", []))
        )
        result["models_enabled"] = False
    else:
        result["error_tail"] = log_path.read_text(errors="replace")[-12000:]
        write_json(
            summary_path,
            {
                "status": status,
                "returncode": returncode,
                "diagnostic_log": log_path.name,
            },
        )
    enrich_result(result, log_path.read_text(errors="replace"))
    return result


def enrich_result(result, log=""):
    """Describe observed failures without calling them inconsistent source data."""
    result.pop("network_model_calls", None)
    result["models_enabled"] = False
    if result["status"] != "passed":
        result["accepted_families"] = None
        result["counterexamples_found"] = None
    loaded = re.search(r"Loaded (\d+) triples; training=(\d+)", log)
    if loaded:
        result["normalized_triples_loaded"] = int(loaded[1])
    diagnostic = result.get("error", result.get("error_tail", ""))
    if "Property-chain join exceeds MAX_JOIN_EDGES" in diagnostic:
        result["failure_category"] = "discovery_join_budget_exceeded"
    elif "UnsupportedDatatypeException" in diagnostic:
        result["failure_category"] = "reasoner_unsupported_datatype"
        match = re.search(r"The datatype '([^']+)'", diagnostic)
        if match:
            result["unsupported_datatype"] = match[1]
    elif "returned HTML rather than RDF" in diagnostic:
        result["failure_category"] = "publisher_returned_html"


def save_reports(report, directory):
    report["status_counts"] = dict(Counter(r["status"] for r in report["results"]))
    write_json(directory / "report.json", report)
    lines = [
        "# Sequential online ABox benchmark",
        "",
        f"Started: {report['started_at']}",
        "",
        "Original publisher responses; one subprocess at a time; models disabled.",
        "Pass means execution and logical validation, not domain truth or human consensus.",
        "",
        "| Dataset | Result | Normalized triples | Pipeline seconds | Accepted | Withheld | Type / role recall |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in report["results"]:
        summary = row.get("pipeline_summary") or {}
        decisions = summary.get("decisions", {})
        metrics = summary.get("metrics", {})
        recalls = [
            "n/a" if metrics.get(k) is None else f"{metrics[k]:.3f}"
            for k in ("hold_out_recall", "hold_out_role_recall")
        ]
        triples = (row.get("input") or {}).get(
            "normalized_triples", row.get("normalized_triples_loaded", "—")
        )
        seconds = f"{row['runtime_seconds']:.2f}" if "runtime_seconds" in row else "—"
        accepted = decisions.get("accepted", 0) if summary else "—"
        withheld = decisions.get("withheld", 0) if summary else "—"
        lines.append(
            f"| [{row['name']}]({row['url']}) | {row['status']} | "
            f"{triples} | {seconds} | {accepted} | {withheld} | {' / '.join(recalls)} |"
        )
    lines += ["", "## Failure details", ""]
    for row in report["results"]:
        if row["status"] != "passed":
            lines += [
                f"### {row['name']}",
                "",
                "```text",
                row.get("error", row.get("error_tail", "No diagnostic available")),
                "```",
                "",
            ]
    lines += [
        "## Scope",
        "",
        "This is a small, deliberately varied convenience sample. Resource descriptions",
        "and standards fixtures are usually too small or too sparsely typed to establish",
        "universal axioms. Missing hold-out denominators and zero recovery are preserved.",
        "Download failures are distinct from pipeline failures; no source was cleaned to pass.",
        "An accepted count of zero means vocabulary-only output, even when validation passed.",
        "Acquisition URLs, timestamps, sizes, and SHA-256 hashes are recorded in report.json.",
    ]
    markdown = "\n".join(line.rstrip() for line in "\n".join(lines).splitlines())
    (directory / "report.md").write_text(markdown + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest", type=Path, default=ROOT / "benchmarks/online_sources.json"
    )
    parser.add_argument("--input-dir", type=Path, default=ROOT / "input/online")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument(
        "--only", action="append", help="Run only this source ID (repeatable)"
    )
    parser.add_argument("--download-timeout", type=float, default=45)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--max-download-mb", type=int, default=16)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    for value in (args.download_timeout, args.timeout, args.max_download_mb):
        if value <= 0:
            parser.error("Timeouts and download size must be positive")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory = (args.output_dir or ROOT / "output/online_benchmarks" / stamp).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    sources = json.loads(args.manifest.read_text())
    if args.only:
        unknown = set(args.only) - {s["id"] for s in sources}
        if unknown:
            parser.error(f"Unknown source IDs: {sorted(unknown)}")
        sources = [s for s in sources if s["id"] in args.only]
    report = {
        "started_at": utc_now(),
        "manifest": str(args.manifest),
        "execution": "strictly sequential; offline pipeline; no cleaning or sampling",
        "configuration": {
            "max_input_triples": 2000000,
            "max_join_edges": 100000,
            "max_evidence_candidates": 1000,
            "pipeline_timeout_s": args.timeout,
        },
        "results": [],
    }
    for index, source in enumerate(sources, 1):
        print(f"[{index}/{len(sources)}] Downloading {source['name']}", flush=True)
        row = dict(source)
        try:
            input_path, provenance = acquire(
                source,
                args.input_dir.resolve() / source["id"],
                args.download_timeout,
                args.max_download_mb * 1024**2,
                args.refresh,
            )
            row["download"] = provenance
            print(
                f"[{index}/{len(sources)}] Testing {source['id']} ({provenance['bytes']} bytes)",
                flush=True,
            )
            row.update(
                evaluate(source, input_path, directory / source["id"], args.timeout)
            )
        except Exception as exc:
            row.update(
                status="download_error" if "download" not in row else "harness_error",
                error=f"{type(exc).__name__}: {exc}",
            )
        enrich_result(row)
        report["results"].append(row)
        save_reports(report, directory)
        print(f"[{index}/{len(sources)}] {row['status']}: {source['id']}", flush=True)
    report["finished_at"] = utc_now()
    save_reports(report, directory)
    print(f"Reports: {directory / 'report.md'}", flush=True)
    print(json.dumps(report["status_counts"], sort_keys=True), flush=True)
    return 0 if all(r["status"] == "passed" for r in report["results"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
