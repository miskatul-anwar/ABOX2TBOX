"""Test benchmark acquisition provenance without live network dependencies."""

import hashlib
import io
import json
from pathlib import Path

import pytest

from scripts import benchmark_online as benchmark

SOURCE = {"url": "https://example.org/data.ttl", "format": "turtle", "extension": "ttl"}
BODY = b'@prefix e: <urn:test:> . e:a e:p "value" .'


class Response(io.BytesIO):
    status = 200

    def __init__(self, body=BODY, content_type="text/turtle"):
        super().__init__(body)
        self.headers = {"Content-Type": content_type}

    def geturl(self):
        return SOURCE["url"]


def test_snapshot_cache_checks_hash_and_redownloads_tampered_files(
    tmp_path, monkeypatch
):
    requests = []

    def opener(request, timeout):
        requests.append(request.full_url)
        return Response()

    monkeypatch.setattr(benchmark.urllib.request, "urlopen", opener)
    path, metadata = benchmark.acquire(SOURCE, tmp_path, 1, 1024, False)
    assert path.read_bytes() == BODY
    assert metadata["sha256"] == hashlib.sha256(BODY).hexdigest()
    _, cached = benchmark.acquire(SOURCE, tmp_path, 1, 1024, False)
    assert cached["cached"]
    assert len(requests) == 1
    path.write_bytes(b"modified content")
    _, refreshed = benchmark.acquire(SOURCE, tmp_path, 1, 1024, False)
    assert not refreshed["cached"]
    assert len(requests) == 2
    assert path.read_bytes() == BODY


@pytest.mark.parametrize(
    "body,content_type,error",
    [
        (b"<html>Not a dataset</html>", "text/html", "rather than RDF"),
        (b"", "text/turtle", "empty response"),
        (BODY * 50, "text/turtle", "exceeds"),
    ],
)
def test_failed_refresh_preserves_existing_snapshot(
    tmp_path, monkeypatch, body, content_type, error
):
    target = tmp_path / "source.ttl"
    target.write_bytes(BODY)
    monkeypatch.setattr(
        benchmark.urllib.request,
        "urlopen",
        lambda *a, **k: Response(body, content_type),
    )
    with pytest.raises(ValueError, match=error):
        benchmark.acquire(SOURCE, tmp_path, 1, 1024, True)
    assert target.read_bytes() == BODY


def test_failure_report_preserves_unknown_metrics_and_actual_reason(tmp_path):
    row = {
        "name": "Publisher",
        "url": SOURCE["url"],
        "status": "download_error",
        "error": "Publisher returned HTML rather than RDF",
    }
    benchmark.enrich_result(row)
    report = {"started_at": "2026-10-20T00:00:00Z", "results": [row]}
    benchmark.save_reports(report, tmp_path)
    loaded = json.loads((tmp_path / "report.json").read_text())
    assert loaded["status_counts"] == {"download_error": 1}
    assert loaded["results"][0]["failure_category"] == "publisher_returned_html"
    markdown = (tmp_path / "report.md").read_text()
    assert "| download_error | — | — | — | — | n/a / n/a |" in markdown
    assert "Publisher returned HTML rather than RDF" in markdown
