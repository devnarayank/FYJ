"""
Job discovery entry points built on the pluggable provider layer.

``tools.job_sources`` owns the per-board scraping logic; this module keeps the
public API used by the agents and orchestrates the sources for one or many
search queries.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from config.constants import (
    DEFAULT_BOARDS,
    JOBSPY_BOARDS,
    SCRAPE_DELAY_SECONDS,
    SUPPORTED_BOARDS,
)
from tools.job_sources import (
    CutShortSource,
    HttpClient,
    JobSource,
    JobSpySource,
    SourceHealth,
    WellfoundSource,
    collect_jobs,
)

logger = logging.getLogger(__name__)

__all__ = [
    "scrape_jobs",
    "scrape_jobs_multi_query",
    "build_sources",
]


def _settings() -> Any:
    """Load application settings, falling back to defaults when unavailable."""
    try:
        from config.settings import get_settings

        return get_settings()
    except Exception as exc:  # pragma: no cover - configuration problems must not kill scraping
        logger.debug("Using default search configuration (%s).", exc)
        return None


def _proxies() -> list[str] | None:
    settings = _settings()
    raw = getattr(settings, "jobspy_proxies", "") or ""
    if not raw:
        return None
    return [item.strip() for item in raw.split(",") if item.strip()]


def build_sources(
    boards: list[str] | None = None,
    hours_old: int = 72,
    job_type: str | None = None,
    is_remote: bool = False,
) -> list[JobSource]:
    """Instantiate the providers for the requested boards."""
    settings = _settings()
    selected = [board for board in (boards or DEFAULT_BOARDS) if board in SUPPORTED_BOARDS]
    if not selected:
        selected = list(DEFAULT_BOARDS)

    max_details = int(getattr(settings, "max_detail_fetches", 20) or 20)
    max_workers = int(getattr(settings, "max_concurrent_fetches", 6) or 6)
    timeout = int(getattr(settings, "request_timeout_seconds", 20) or 20)
    client = HttpClient(timeout=timeout)
    proxies = _proxies()

    sources: list[JobSource] = []
    for board in selected:
        if board in JOBSPY_BOARDS:
            sources.append(
                JobSpySource(
                    board,
                    hours_old=hours_old,
                    proxies=proxies,
                    job_type=job_type,
                    is_remote=is_remote,
                )
            )
        elif board == "wellfound":
            sources.append(WellfoundSource(client, max_detail_fetches=max_details, max_workers=max_workers))
        elif board == "cutshort":
            sources.append(CutShortSource(client, max_detail_fetches=max_details, max_workers=max_workers))
        else:
            logger.info("Ignoring unknown job source '%s'.", board)
    return sources


def scrape_jobs(
    search_term: str,
    location: str = "",
    boards: list[str] | None = None,
    results_wanted: int = 50,
    hours_old: int = 72,
    job_type: str | None = None,
    is_remote: bool = False,
    health: SourceHealth | None = None,
) -> list[dict[str, Any]]:
    """
    Search the configured job sources.

    Returns a list of dicts with keys:
        title, company, location, description, job_url, source, date_posted, salary
    """
    settings = _settings()
    threshold = int(getattr(settings, "source_failure_threshold", 3) or 3)
    min_chars = int(getattr(settings, "min_description_chars", 80) or 80)
    health = health or SourceHealth(failure_threshold=threshold)

    sources = build_sources(boards, hours_old=hours_old, job_type=job_type, is_remote=is_remote)
    try:
        postings = collect_jobs(
            sources=sources,
            query=search_term,
            location=location,
            limit=results_wanted,
            health=health,
            min_description_chars=min_chars,
        )
    finally:
        for source in sources:
            source.close()

    logger.info("Found %s job(s) with descriptions for '%s'", len(postings), search_term)
    return [posting.to_dict() for posting in postings]


def scrape_jobs_multi_query(
    queries: list[str],
    location: str = "",
    boards: list[str] | None = None,
    results_per_query: int = 50,
    hours_old: int = 72,
) -> list[dict[str, Any]]:
    """
    Scrape with multiple search queries and deduplicate results.

    A single health tracker is shared across the queries so a source that
    keeps failing is disabled for the remainder of the run.
    """
    settings = _settings()
    threshold = int(getattr(settings, "source_failure_threshold", 3) or 3)
    health = SourceHealth(failure_threshold=threshold)

    all_jobs: dict[str, dict[str, Any]] = {}
    for query in queries:
        try:
            jobs = scrape_jobs(
                search_term=query,
                location=location,
                boards=boards,
                results_wanted=results_per_query,
                hours_old=hours_old,
                health=health,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Search for '%s' failed (%s) - continuing.", query, exc)
            continue

        for job in jobs:
            url = job.get("job_url", "")
            if url and url not in all_jobs:
                all_jobs[url] = job

        time.sleep(SCRAPE_DELAY_SECONDS)

    logger.info("Total unique jobs after dedup: %s", len(all_jobs))
    return list(all_jobs.values())
