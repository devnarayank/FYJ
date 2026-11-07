"""
Pluggable job-discovery providers.

Design notes
------------
* Every provider returns :class:`JobPosting` records that carry the *real* job
  description taken from the posting itself. Nothing is synthesised from a
  search-result snippet: a listing without a genuine description is dropped
  rather than faked, because the matching pipeline scores a candidate against
  genuine job requirements.
* Providers are isolated behind :class:`JobSource` so another board - or a
  research/crawling backend such as Firecrawl, Crawl4AI or an open deep-research
  pipeline - can be added later without touching the matching logic.
* Expected, recoverable problems (blocked hosts, missing pages, DNS failures,
  TLS problems, rate limits) are raised as :class:`SourceUnavailable` and
  handled by :class:`SourceHealth`, which disables a failing source for the
  rest of the run instead of flooding the log with errors.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Shared HTTP behaviour
# ──────────────────────────────────────────────

BROWSER_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

#: Words that carry no signal when matching a query against a job slug.
_STOP_TOKENS = frozenset(
    {
        "job", "jobs", "role", "roles", "position", "positions", "opening",
        "openings", "and", "the", "for", "with", "senior", "junior", "mid",
        "level", "midlevel", "remote", "hybrid", "onsite", "fulltime",
        "parttime", "contract", "intern", "internship", "engineer", "engineers",
        "developer", "developers", "manager", "specialist", "fresher",
    }
)


class SourceUnavailable(RuntimeError):
    """A source could not be reached or refused to serve results."""


class _LogCapture(logging.Handler):
    """Collect log messages emitted by a third-party logger."""

    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.messages.append(record.getMessage())
        except Exception:  # pragma: no cover - defensive
            pass


def _jobspy_logger_name(board: str) -> str:
    """Mirror JobSpy's own logger naming so a logger can be muted up front."""
    cap_name = board.capitalize()
    return "ZipRecruiter" if cap_name == "Zip_recruiter" else cap_name


def _mute_logger(name: str) -> None:
    target = logging.getLogger(name)
    target.setLevel(logging.CRITICAL)
    for handler in list(target.handlers):
        target.removeHandler(handler)
    target.addHandler(logging.NullHandler())
    target.propagate = False


def _install_capture(board: str) -> _LogCapture:
    """Capture what JobSpy reports about a board instead of printing it."""
    target = logging.getLogger(f"JobSpy:{_jobspy_logger_name(board)}")
    capture = _LogCapture()
    for handler in list(target.handlers):
        target.removeHandler(handler)
    target.addHandler(capture)
    target.setLevel(logging.WARNING)
    target.propagate = False
    return capture


def _restore_mute(board: str) -> None:
    _mute_logger(f"JobSpy:{_jobspy_logger_name(board)}")


_BLOCKED_PATTERNS: tuple[tuple[str, str], ...] = (
    ("403", "access refused (HTTP 403)"),
    ("401", "access refused (HTTP 401)"),
    ("406", "access refused (HTTP 406)"),
    ("429", "rate limited (HTTP 429)"),
    ("recaptcha", "blocked by a recaptcha challenge"),
    ("forbidden", "access refused (forbidden)"),
    ("bad response status code", "access refused by the board"),
    ("error fetching jobs", "the board refused the request"),
)


def _blocked_reason(messages: Sequence[str]) -> str | None:
    """Translate a third-party error message into a short reason."""
    for message in messages:
        lowered = message.lower()
        for needle, reason in _BLOCKED_PATTERNS:
            if needle in lowered:
                return reason
    return None


def silence_jobspy_logging(boards: Iterable[str] | None = None) -> None:
    """Mute JobSpy's private log stream.

    JobSpy installs its own stderr handler and reports blocked boards at ERROR
    level. The provider layer surfaces those conditions itself through
    :class:`SourceHealth`, so the third-party stream is muted to keep the
    pipeline output readable.

    Loggers for the given boards are pre-created because JobSpy only
    configures a logger when it has finished scraping, which is too late to
    stop the accompanying status line from being printed.
    """
    for board in boards or ():
        _mute_logger(f"JobSpy:{_jobspy_logger_name(board)}")

    for name in list(logging.root.manager.loggerDict):
        if not name.startswith("JobSpy"):
            continue
        _mute_logger(name)


class HttpClient:
    """Small HTTP helper with retries, throttling and friendly failures."""

    def __init__(
        self,
        timeout: int = 20,
        retries: int = 2,
        min_interval: float = 0.4,
    ) -> None:
        self.timeout = timeout
        self._min_interval = min_interval
        self._last_request_at = 0.0
        self._lock = threading.Lock()
        self._session = requests.Session()
        retry = Retry(
            total=retries,
            connect=retries,
            read=retries,
            backoff_factor=0.8,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=16, pool_maxsize=16)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)
        self._session.headers.update(BROWSER_HEADERS)

    def _throttle(self) -> None:
        with self._lock:
            elapsed = time.monotonic() - self._last_request_at
            if self._last_request_at and elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_request_at = time.monotonic()

    def get_text(self, url: str, params: dict[str, str] | None = None) -> str:
        """Return the response body, or raise :class:`SourceUnavailable`."""
        self._throttle()
        try:
            response = self._session.get(url, params=params, timeout=self.timeout)
        except requests.exceptions.SSLError as exc:
            raise SourceUnavailable(f"TLS handshake failed ({_host_of(url)})") from exc
        except requests.exceptions.ConnectTimeout as exc:
            raise SourceUnavailable(f"connection timed out ({_host_of(url)})") from exc
        except requests.exceptions.ReadTimeout as exc:
            raise SourceUnavailable(f"read timed out ({_host_of(url)})") from exc
        except requests.exceptions.Timeout as exc:
            raise SourceUnavailable(f"request timed out ({_host_of(url)})") from exc
        except requests.exceptions.ConnectionError as exc:
            raise SourceUnavailable(f"host unreachable ({_host_of(url)})") from exc
        except requests.exceptions.RequestException as exc:
            raise SourceUnavailable(f"request failed ({_host_of(url)})") from exc

        status = response.status_code
        if status in (401, 403):
            raise SourceUnavailable(f"access refused (HTTP {status}, {_host_of(url)})")
        if status == 404:
            raise SourceUnavailable(f"page not found (HTTP 404, {_host_of(url)})")
        if status == 429:
            raise SourceUnavailable(f"rate limited (HTTP 429, {_host_of(url)})")
        if status >= 400:
            raise SourceUnavailable(f"unexpected response (HTTP {status}, {_host_of(url)})")
        return response.text

    def close(self) -> None:
        self._session.close()


def _host_of(url: str) -> str:
    try:
        return requests.utils.urlparse(url).netloc
    except Exception:  # pragma: no cover - defensive
        return url


# ──────────────────────────────────────────────
# Domain model
# ──────────────────────────────────────────────

@dataclass
class JobPosting:
    """A single job posting with a genuine description."""

    title: str
    company: str
    location: str
    description: str
    job_url: str
    source: str
    date_posted: str = ""
    salary: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the mapping shape consumed by the matching pipeline."""
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "description": self.description,
            "job_url": self.job_url,
            "source": self.source,
            "date_posted": self.date_posted,
            "salary": self.salary,
        }


# ──────────────────────────────────────────────
# Provider contract
# ──────────────────────────────────────────────

class JobSource(ABC):
    """A source of job postings."""

    name: str = "source"

    @abstractmethod
    def search(self, query: str, location: str, limit: int) -> list[JobPosting]:
        """Return postings for ``query``; raise :class:`SourceUnavailable` on failure."""

    def close(self) -> None:  # pragma: no cover - default no-op
        """Release any network resources held by the source."""


# ──────────────────────────────────────────────
# Schema.org helpers
# ──────────────────────────────────────────────

_LD_JSON_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
_NEXT_DATA_RE = re.compile(
    r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")
_ENTITIES = {
    "&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">",
    "&quot;": '"', "&#39;": "'", "&apos;": "'",
}


def html_to_text(raw: str | None) -> str:
    """Convert an HTML fragment into readable plain text."""
    if not raw:
        return ""
    text = _TAG_RE.sub(" ", raw)
    for entity, char in _ENTITIES.items():
        text = text.replace(entity, char)
    text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n", text).strip()


def _iter_jsonld_nodes(payload: Any) -> Iterable[dict[str, Any]]:
    """Yield dict nodes from a JSON-LD payload (handles @graph wrappers)."""
    if isinstance(payload, list):
        for item in payload:
            yield from _iter_jsonld_nodes(item)
    elif isinstance(payload, dict):
        if "@graph" in payload:
            yield from _iter_jsonld_nodes(payload["@graph"])
        else:
            yield payload


def _jobposting_from_node(node: dict[str, Any]) -> dict[str, Any] | None:
    node_type = node.get("@type")
    types = node_type if isinstance(node_type, list) else [node_type]
    if not any(str(t).lower() == "jobposting" for t in types if t):
        return None
    return node


def extract_jobposting_ldjson(html: str) -> dict[str, Any] | None:
    """Return the first schema.org JobPosting embedded in ``html``."""
    for match in _LD_JSON_RE.finditer(html):
        try:
            payload = json.loads(match.group(1).strip())
        except (json.JSONDecodeError, TypeError):
            continue
        for node in _iter_jsonld_nodes(payload):
            posting = _jobposting_from_node(node)
            if posting:
                return posting
    return None


def extract_jobposting_next_data(html: str) -> dict[str, Any] | None:
    """Return the first schema.org JobPosting embedded in a Next.js payload."""
    match = _NEXT_DATA_RE.search(html)
    if not match:
        return None
    try:
        payload = json.loads(match.group(1).strip())
    except (json.JSONDecodeError, TypeError):
        return None

    found: list[dict[str, Any]] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            posting = _jobposting_from_node(node)
            if posting:
                found.append(posting)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(payload)
    return found[0] if found else None


def extract_jobposting(html: str) -> dict[str, Any] | None:
    """Return a schema.org JobPosting from either embedding style."""
    return extract_jobposting_ldjson(html) or extract_jobposting_next_data(html)


def _address_text(address: Any) -> str:
    if isinstance(address, list):
        parts = [_address_text(item) for item in address]
        return ", ".join(part for part in parts if part)
    if not isinstance(address, dict):
        return ""

    postal = address.get("address")
    if not isinstance(postal, dict):
        postal = address

    chunks = [
        postal.get("addressLocality") or "",
        postal.get("addressRegion") or "",
        postal.get("addressCountry") or "",
    ]
    return ", ".join(chunk for chunk in chunks if chunk)


def jobposting_to_posting(node: dict[str, Any], source: str, fallback_url: str = "") -> JobPosting | None:
    """Convert a schema.org JobPosting node into a :class:`JobPosting`."""
    description = html_to_text(node.get("description"))
    if not description:
        return None

    organization = node.get("hiringOrganization")
    if isinstance(organization, list):
        organization = organization[0] if organization else {}
    company = ""
    if isinstance(organization, dict):
        company = str(organization.get("name") or "")
    elif isinstance(organization, str):
        company = organization

    location = _address_text(node.get("jobLocation")) or _address_text(
        node.get("applicantLocationRequirements")
    )

    salary = None
    base_salary = node.get("baseSalary")
    if isinstance(base_salary, dict):
        value = base_salary.get("value")
        if isinstance(value, dict):
            low = value.get("minValue")
            high = value.get("maxValue")
            currency = value.get("currency") or ""
            if low or high:
                salary = f"{low or ''}-{high or ''} {currency}".strip(" -")
        elif isinstance(value, str):
            salary = value

    return JobPosting(
        title=html_to_text(str(node.get("title") or "")),
        company=company,
        location=location,
        description=description,
        job_url=str(node.get("url") or fallback_url or ""),
        source=source,
        date_posted=str(node.get("datePosted") or ""),
        salary=salary,
    )


# ──────────────────────────────────────────────
# Source health (circuit breaker)
# ──────────────────────────────────────────────

class SourceHealth:
    """Track consecutive source failures and disable a failing source."""

    def __init__(self, failure_threshold: int = 3) -> None:
        self._threshold = max(1, failure_threshold)
        self._failures: dict[str, int] = {}
        self._disabled: dict[str, str] = {}

    @property
    def failure_threshold(self) -> int:
        return self._threshold

    @property
    def disabled_sources(self) -> dict[str, str]:
        return dict(self._disabled)

    def is_disabled(self, name: str) -> bool:
        return name in self._disabled

    def record_failure(self, name: str, reason: str) -> bool:
        """Record a failure. Returns True when the source is now disabled."""
        count = self._failures.get(name, 0) + 1
        self._failures[name] = count
        if count >= self._threshold and name not in self._disabled:
            self._disabled[name] = reason
            return True
        return False

    def record_success(self, name: str) -> None:
        self._failures.pop(name, None)


# ──────────────────────────────────────────────
# Providers
# ──────────────────────────────────────────────

class JobSpySource(JobSource):
    """Job boards reached through the JobSpy scraper (Indeed, LinkedIn, ...)."""

    def __init__(
        self,
        board: str,
        hours_old: int = 72,
        proxies: list[str] | None = None,
        job_type: str | None = None,
        is_remote: bool = False,
    ) -> None:
        self.name = board
        self.hours_old = hours_old
        self.proxies = proxies
        self.job_type = job_type
        self.is_remote = is_remote

    def search(self, query: str, location: str, limit: int) -> list[JobPosting]:
        from jobspy import scrape_jobs

        capture = _install_capture(self.name)
        try:
            frame = scrape_jobs(
                site_name=[self.name],
                search_term=query,
                location=location or None,
                results_wanted=max(1, limit),
                hours_old=self.hours_old,
                job_type=self.job_type,
                is_remote=self.is_remote,
                linkedin_fetch_description=True,
                country_indeed="USA",
                proxies=self.proxies,
            )
        except Exception as exc:  # jobspy raises bare exceptions per board
            raise SourceUnavailable(f"{self.name} request failed: {exc}") from exc
        finally:
            _restore_mute(self.name)

        if frame is None or getattr(frame, "empty", True):
            reason = _blocked_reason(capture.messages)
            if reason:
                raise SourceUnavailable(reason)
            return []

        postings: list[JobPosting] = []
        for _, row in frame.iterrows():
            description = _clean_text(row.get("description"))
            if not description:
                continue
            postings.append(
                JobPosting(
                    title=_clean_text(row.get("title")),
                    company=_clean_text(row.get("company_name") or row.get("company")),
                    location=_clean_text(row.get("location")),
                    description=description,
                    job_url=_clean_text(row.get("job_url") or row.get("link")),
                    source=self.name,
                    date_posted=_clean_text(row.get("date_posted")),
                    salary=_row_salary(row),
                )
            )
        return postings


def _clean_text(value: Any) -> str:
    """Normalise a scraped cell into a usable string."""
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null", "nat"}:
        return ""
    return text


def _row_salary(row: Any) -> str | None:
    low = _clean_text(row.get("min_amount"))
    high = _clean_text(row.get("max_amount"))
    currency = _clean_text(row.get("currency"))
    if not low and not high:
        return None
    value = "-".join(part for part in (low, high) if part)
    return f"{value} {currency}".strip() if currency else (value or None)


class WellfoundSource(JobSource):
    """Wellfound (AngelList Talent) - schema.org JobPosting on every detail page."""

    name = "wellfound"
    _BASE = "https://wellfound.com"
    _SEARCH_URL = f"{_BASE}/jobs"
    _LINK_RE = re.compile(r'href="(/jobs/[^"#?]+)"')

    def __init__(
        self,
        client: HttpClient,
        max_detail_fetches: int = 20,
        max_workers: int = 6,
    ) -> None:
        self._client = client
        self._max_detail_fetches = max(1, max_detail_fetches)
        self._max_workers = max(1, max_workers)

    def search(self, query: str, location: str, limit: int) -> list[JobPosting]:
        params: dict[str, str] = {"q": query}
        if location:
            params["l"] = location
        html = self._client.get_text(self._SEARCH_URL, params=params)
        links = self._extract_links(html)
        if not links:
            return []
        selected = links[: self._max_detail_fetches]
        return self._fetch_details(selected)

    def _extract_links(self, html: str) -> list[str]:
        seen: set[str] = set()
        links: list[str] = []
        for path in self._LINK_RE.findall(html):
            if path in seen:
                continue
            seen.add(path)
            links.append(f"{self._BASE}{path}")
        return links

    def _fetch_details(self, urls: Sequence[str]) -> list[JobPosting]:
        postings: list[JobPosting] = []
        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            futures = [pool.submit(self._fetch_one, url) for url in urls]
            for future in futures:
                try:
                    posting = future.result()
                except SourceUnavailable as exc:
                    logger.debug("Wellfound listing skipped: %s", exc)
                    continue
                except Exception as exc:  # pragma: no cover - defensive
                    logger.debug("Wellfound listing failed: %s", exc)
                    continue
                if posting:
                    postings.append(posting)
        return postings

    def _fetch_one(self, url: str) -> JobPosting | None:
        html = self._client.get_text(url)
        node = extract_jobposting(html)
        if not node:
            return None
        return jobposting_to_posting(node, self.name, fallback_url=url)

    def close(self) -> None:
        self._client.close()


class CutShortSource(JobSource):
    """CutShort - job pages carry a schema.org JobPosting in the Next.js payload."""

    name = "cutshort"
    _SITEMAP_URL = (
        "https://cutshort-data.s3.amazonaws.com/cloudfront/public/jobs-sitemap.xml"
    )
    _LOC_RE = re.compile(r"<loc>(.*?)</loc>", re.IGNORECASE)
    _sitemap_lock = threading.Lock()
    _sitemap_urls: list[str] | None = None

    def __init__(
        self,
        client: HttpClient,
        max_detail_fetches: int = 20,
        max_workers: int = 6,
    ) -> None:
        self._client = client
        self._max_detail_fetches = max(1, max_detail_fetches)
        self._max_workers = max(1, max_workers)

    def search(self, query: str, location: str, limit: int) -> list[JobPosting]:
        candidates = self._candidates(query, limit)
        if not candidates:
            return []
        return self._fetch_details(candidates)

    # -- sitemap -------------------------------------------------------
    @classmethod
    def _sitemap(cls) -> list[str]:
        """Return (and cache) the CutShort job URL list."""
        with cls._sitemap_lock:
            if cls._sitemap_urls is None:
                client = HttpClient()
                try:
                    xml = client.get_text(cls._SITEMAP_URL)
                finally:
                    client.close()
                cls._sitemap_urls = [
                    url for url in cls._LOC_RE.findall(xml) if "/job/" in url
                ]
            return cls._sitemap_urls

    def _candidates(self, query: str, limit: int) -> list[str]:
        tokens = query_tokens(query)
        if not tokens:
            return []
        scored: list[tuple[int, str]] = []
        for url in self._sitemap():
            slug = url.rsplit("/", 1)[-1].lower()
            slug_tokens = set(re.split(r"[^a-z0-9#+.]+", slug))
            matched = tokens & slug_tokens
            if matched:
                scored.append((len(matched), url))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [url for _, url in scored[: self._max_detail_fetches]]

    # -- details -------------------------------------------------------
    def _fetch_details(self, urls: Sequence[str]) -> list[JobPosting]:
        postings: list[JobPosting] = []
        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            futures = [pool.submit(self._fetch_one, url) for url in urls]
            for future in futures:
                try:
                    posting = future.result()
                except SourceUnavailable as exc:
                    logger.debug("CutShort listing skipped: %s", exc)
                    continue
                except Exception as exc:  # pragma: no cover - defensive
                    logger.debug("CutShort listing failed: %s", exc)
                    continue
                if posting:
                    postings.append(posting)
        return postings

    def _fetch_one(self, url: str) -> JobPosting | None:
        html = self._client.get_text(url)
        node = extract_jobposting(html)
        if not node:
            return None
        return jobposting_to_posting(node, self.name, fallback_url=url)

    def close(self) -> None:
        self._client.close()


def query_tokens(query: str) -> set[str]:
    """Return the significant tokens of a search query."""
    raw = re.split(r"[^a-z0-9#+.]+", query.lower())
    return {
        token
        for token in raw
        if len(token) >= 3 and token not in _STOP_TOKENS and not token.isdigit()
    }


# ──────────────────────────────────────────────
# Orchestration
# ──────────────────────────────────────────────

def collect_jobs(
    sources: Sequence[JobSource],
    query: str,
    location: str,
    limit: int,
    health: SourceHealth,
    min_description_chars: int = 80,
) -> list[JobPosting]:
    """Query every enabled source, degrading gracefully when one misbehaves."""
    postings: list[JobPosting] = []
    for source in sources:
        if health.is_disabled(source.name):
            continue
        try:
            found = source.search(query, location, limit)
        except SourceUnavailable as exc:
            reason = str(exc)
            if health.record_failure(source.name, reason):
                logger.info(
                    "Source '%s' disabled for this run after %s consecutive failures (%s).",
                    source.name, health.failure_threshold, reason,
                )
            else:
                logger.warning("Source '%s' unavailable (%s) - skipping.", source.name, reason)
            continue
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Source '%s' failed (%s) - skipping.", source.name, exc)
            health.record_failure(source.name, str(exc))
            continue

        health.record_success(source.name)
        usable = [
            posting
            for posting in found
            if len(posting.description.strip()) >= min_description_chars
        ]
        dropped = len(found) - len(usable)
        if dropped:
            logger.info(
                "Source '%s': skipped %s listing(s) without a real job description.",
                source.name, dropped,
            )
        logger.info("Source '%s': %s job(s) with full descriptions.", source.name, len(usable))
        postings.extend(usable)
    return postings
