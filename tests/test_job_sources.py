"""Offline tests for the pluggable job-source layer.

No network access is required: every provider interaction is either stubbed or
exercised against an inline HTML fixture.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.job_sources import (  # noqa: E402
    CutShortSource,
    HttpClient,
    JobPosting,
    JobSpySource,
    SourceHealth,
    SourceUnavailable,
    WellfoundSource,
    collect_jobs,
    extract_jobposting,
    extract_jobposting_ldjson,
    extract_jobposting_next_data,
    html_to_text,
    jobposting_to_posting,
    query_tokens,
)

WELLFOUND_NODE = {
    "@context": "http://schema.org/",
    "@type": "JobPosting",
    "title": "Senior Software Engineer",
    "description": (
        "<p>Build <b>Python</b> services with FastAPI and AWS.</p>"
        "<p>You will own APIs, data pipelines and mentor juniors.</p>"
    ),
    "datePosted": "2026-06-16",
    "employmentType": "FULL_TIME",
    "hiringOrganization": {"@type": "Organization", "name": "Example AI"},
    "jobLocation": [
        {
            "@type": "Place",
            "address": {"addressLocality": "Berlin", "addressCountry": "Germany"},
        }
    ],
    "baseSalary": {"value": {"minValue": 80000, "maxValue": 110000, "currency": "EUR"}},
}

WELLFOUND_DETAIL = (
    "<html><head><script type=\"application/ld+json\">"
    + json.dumps(WELLFOUND_NODE)
    + "</script></head><body></body></html>"
)

CUTSHORT_PAYLOAD = {
    "props": {
        "pageProps": {
            "dehydratedState": {
                "queries": [
                    {
                        "state": {
                            "data": {
                                "data": {
                                    "seoData": {
                                        "jsonlds": [
                                            {"@context": "https://schema.org", "@type": "BreadcrumbList"},
                                            {
                                                "@context": "https://schema.org",
                                                "@type": "JobPosting",
                                                "title": "Machine Learning Engineer",
                                                "description": (
                                                    "<p>We are looking for a Machine Learning "
                                                    "Engineer with strong Python and PyTorch "
                                                    "experience building recommendation systems.</p>"
                                                ),
                                                "datePosted": "2026-07-01",
                                                "hiringOrganization": {
                                                    "@type": "Organization",
                                                    "name": "Acme AI",
                                                },
                                                "jobLocation": {
                                                    "@type": "Place",
                                                    "address": {"addressLocality": "Remote"},
                                                },
                                            },
                                        ]
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }
    }
}

CUTSHORT_DETAIL = (
    "<html><body><script id=\"__NEXT_DATA__\" type=\"application/json\">"
    + json.dumps(CUTSHORT_PAYLOAD)
    + "</script></body></html>"
)

WELLFOUND_SEARCH = """
<html><body>
  <a href="/jobs/1234-senior-software-engineer">Senior Software Engineer</a>
  <a href="/jobs/1234-senior-software-engineer">Senior Software Engineer</a>
  <a href="/company/acme">Acme</a>
  <a href="/jobs/5678-machine-learning-engineer">Machine Learning Engineer</a>
</body></html>
"""


# ── schema.org helpers ────────────────────────────────────────────────

def test_html_to_text_strips_markup():
    assert html_to_text("<p>Hello <b>world</b></p>") == "Hello world"
    assert html_to_text(None) == ""


def test_extract_jobposting_from_ldjson():
    node = extract_jobposting_ldjson(WELLFOUND_DETAIL)
    assert node is not None
    assert node["title"] == "Senior Software Engineer"


def test_extract_jobposting_from_next_data():
    node = extract_jobposting_next_data(CUTSHORT_DETAIL)
    assert node is not None
    assert node["title"] == "Machine Learning Engineer"


def test_extract_jobposting_handles_both_shapes():
    assert extract_jobposting(WELLFOUND_DETAIL)["@type"] == "JobPosting"
    assert extract_jobposting(CUTSHORT_DETAIL)["@type"] == "JobPosting"
    assert extract_jobposting("<html></html>") is None


def test_jobposting_to_posting_normalizes_fields():
    node = extract_jobposting_ldjson(WELLFOUND_DETAIL)
    posting = jobposting_to_posting(node, "wellfound", fallback_url="https://wellfound.com/jobs/1")
    assert posting is not None
    assert posting.title == "Senior Software Engineer"
    assert posting.company == "Example AI"
    assert posting.location == "Berlin, Germany"
    assert posting.source == "wellfound"
    assert "FastAPI" in posting.description
    assert "<b>" not in posting.description
    assert posting.salary is not None and "80000" in posting.salary


def test_jobposting_without_description_is_rejected():
    node = {"@type": "JobPosting", "title": "Ghost", "description": ""}
    assert jobposting_to_posting(node, "test") is None


# ── query helpers ─────────────────────────────────────────────────────

def test_query_tokens_drops_stop_words():
    tokens = query_tokens("mid-level software engineer AI/ML Python FastAPI")
    assert "python" in tokens
    assert "fastapi" in tokens
    assert "engineer" not in tokens
    assert "level" not in tokens


def test_query_tokens_keeps_technical_tokens():
    assert "python" in query_tokens("python")
    assert query_tokens("go") == set()


# ── source health ────────────────────────────────────────────────────

def test_source_health_disables_after_threshold():
    health = SourceHealth(failure_threshold=3)
    assert health.record_failure("glassdoor", "blocked") is False
    assert health.record_failure("glassdoor", "blocked") is False
    assert health.record_failure("glassdoor", "blocked") is True
    assert health.is_disabled("glassdoor")
    health.record_success("glassdoor")
    assert health.is_disabled("glassdoor"), "a disabled source stays disabled for the run"


def test_source_health_resets_after_success():
    health = SourceHealth(failure_threshold=2)
    health.record_failure("indeed", "timeout")
    health.record_success("indeed")
    assert not health.is_disabled("indeed")
    assert health.record_failure("indeed", "timeout") is False


# ── collection behaviour ─────────────────────────────────────────────

class _FailingSource:
    name = "always_fails"

    def search(self, query, location, limit):
        raise SourceUnavailable("access refused (HTTP 403)")


class _BrokenSource:
    name = "explodes"

    def search(self, query, location, limit):
        raise RuntimeError("boom")


class _EmptySource:
    name = "no_descriptions"

    def search(self, query, location, limit):
        return [JobPosting("A", "B", "C", "too short", "u", "no_descriptions")]


class _GoodSource:
    name = "good"

    def search(self, query, location, limit):
        return [
            JobPosting(
                "Python Engineer",
                "Acme",
                "Remote",
                "We need a Python engineer with FastAPI, Docker and AWS experience. " * 2,
                "https://example.com/1",
                "good",
            )
        ]


def test_collect_jobs_skips_unavailable_source(caplog):
    health = SourceHealth(failure_threshold=1)
    with caplog.at_level("WARNING"):
        postings = collect_jobs([_FailingSource()], "python", "", 10, health)
    assert postings == []
    assert not any(record.levelname == "ERROR" for record in caplog.records)
    assert health.is_disabled("always_fails")


def test_collect_jobs_survives_provider_bug(caplog):
    health = SourceHealth(failure_threshold=3)
    with caplog.at_level("WARNING"):
        postings = collect_jobs([_BrokenSource()], "python", "", 10, health)
    assert postings == []
    assert not any(record.levelname == "ERROR" for record in caplog.records)


def test_collect_jobs_drops_listings_without_real_description():
    health = SourceHealth(failure_threshold=3)
    postings = collect_jobs([_EmptySource()], "python", "", 10, health)
    assert postings == []


def test_collect_jobs_keeps_real_descriptions():
    health = SourceHealth(failure_threshold=3)
    postings = collect_jobs([_GoodSource()], "python", "", 10, health)
    assert len(postings) == 1
    assert postings[0].source == "good"
    assert postings[0].to_dict()["job_url"] == "https://example.com/1"


def test_collect_jobs_skips_disabled_sources():
    health = SourceHealth(failure_threshold=1)
    health.record_failure("good", "blocked")
    postings = collect_jobs([_GoodSource()], "python", "", 10, health)
    assert postings == []


# ── providers ────────────────────────────────────────────────────────

class _StubClient:
    """Return canned HTML per URL and record the calls."""

    def __init__(self, pages: dict[str, str]):
        self.pages = pages
        self.calls: list[str] = []

    def get_text(self, url, params=None):
        self.calls.append(url)
        if url in self.pages:
            return self.pages[url]
        for key in sorted(self.pages, key=len, reverse=True):
            if key in url:
                return self.pages[key]
        raise SourceUnavailable(f"page not found (HTTP 404, {url})")


def test_wellfound_source_collects_unique_links():
    client = _StubClient(
        {
            "https://wellfound.com/jobs": WELLFOUND_SEARCH,
            "https://wellfound.com/jobs/": WELLFOUND_DETAIL,
        }
    )
    source = WellfoundSource(client, max_detail_fetches=5, max_workers=2)
    postings = source.search("python", "", 10)
    assert postings
    assert postings[0].title == "Senior Software Engineer"
    assert postings[0].source == "wellfound"
    # the duplicate link is only fetched once
    assert client.calls.count("https://wellfound.com/jobs/1234-senior-software-engineer") == 1


def test_cutshort_source_filters_sitemap_by_query_tokens(monkeypatch):
    monkeypatch.setattr(
        CutShortSource,
        "_sitemap",
        classmethod(lambda cls: [
            "https://cutshort.io/job/Machine-Learning-Engineer-Acme-abc123",
            "https://cutshort.io/job/Sales-Manager-Globex-def456",
        ]),
    )
    client = _StubClient({"/job/": CUTSHORT_DETAIL})
    source = CutShortSource(client, max_detail_fetches=5, max_workers=1)
    postings = source.search("machine learning engineer", "", 10)
    assert len(postings) == 1
    assert postings[0].title == "Machine Learning Engineer"
    assert postings[0].company == "Acme AI"
    assert "PyTorch" in postings[0].description


def test_jobspy_source_maps_rows(monkeypatch):
    class _Frame:
        empty = False

        def iterrows(self):
            yield 0, {
                "title": "Data Engineer",
                "company_name": "Acme",
                "location": "Remote",
                "description": "Python, Spark, Airflow and strong SQL skills required.",
                "job_url": "https://example.com/job/1",
                "date_posted": "2026-07-02",
                "min_amount": 100000,
                "max_amount": 140000,
                "currency": "USD",
            }


    monkeypatch.setitem(
        sys.modules, "jobspy", type("M", (), {"scrape_jobs": staticmethod(lambda **kw: _Frame())})
    )
    postings = JobSpySource("indeed").search("python", "Remote", 5)
    assert len(postings) == 1
    assert postings[0].company == "Acme"
    assert postings[0].salary == "100000-140000 USD"


def test_http_client_translates_network_errors(monkeypatch):
    import requests

    client = HttpClient(timeout=1, retries=0)

    def _boom(*args, **kwargs):
        raise requests.exceptions.SSLError("handshake failure")

    monkeypatch.setattr(client._session, "get", _boom)
    with pytest.raises(SourceUnavailable) as exc:
        client.get_text("https://example.com")
    assert "TLS" in str(exc.value)


def test_http_client_translates_blocked_status(monkeypatch):

    client = HttpClient(timeout=1, retries=0)

    class _Response:
        status_code = 403
        text = ""

    monkeypatch.setattr(client._session, "get", lambda *a, **k: _Response())
    with pytest.raises(SourceUnavailable) as exc:
        client.get_text("https://example.com")
    assert "403" in str(exc.value)


# ── third-party log handling ─────────────────────────────────────────

def test_blocked_reason_translates_third_party_messages():
    from tools.job_sources import _blocked_reason

    assert _blocked_reason(["Glassdoor: bad response status code: 403"]) == "access refused (HTTP 403)"
    assert _blocked_reason(["Naukri API response status code 406 - recaptcha required"]) == (
        "access refused (HTTP 406)"
    )
    assert _blocked_reason(["all good"]) is None


def test_jobspy_source_reports_blocked_board(monkeypatch):
    from tools import job_sources

    class _EmptyFrame:
        empty = True

        def iterrows(self):
            return iter(())

    monkeypatch.setitem(
        sys.modules,
        "jobspy",
        type("M", (), {"scrape_jobs": staticmethod(lambda **kw: _EmptyFrame())}),
    )

    monkeypatch.setattr(job_sources, "_install_capture", lambda board: _CaptureWith("403"))

    with pytest.raises(SourceUnavailable) as exc:
        JobSpySource("glassdoor").search("python", "", 5)
    assert "403" in str(exc.value)


class _CaptureWith:
    """Minimal stand-in for the JobSpy log capture handler."""

    def __init__(self, message: str) -> None:
        self.messages = [message]
