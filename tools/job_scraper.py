"""
Job scraping tool — wraps JobSpy for multi-board aggregation.
"""
import logging
import time
from urllib.parse import quote_plus, urljoin
from config.constants import (
    DEFAULT_BOARDS,
    JOBSPY_BOARDS,
    NICHE_JOB_PLATFORMS,
    SCRAPE_DELAY_SECONDS,
    SUPPORTED_BOARDS,
)

logger = logging.getLogger(__name__)


def scrape_jobs(
    search_term: str,
    location: str = "",
    boards: list[str] | None = None,
    results_wanted: int = 50,
    hours_old: int = 72,
    job_type: str | None = None,
    is_remote: bool = False,
) -> list[dict]:
    """
    Scrape job postings from multiple boards using JobSpy.

    Returns a list of dicts with keys:
        title, company, location, description, job_url, source, date_posted, salary
    """
    if boards is None:
        boards = DEFAULT_BOARDS

    # Filter to supported boards
    boards = [b for b in boards if b in SUPPORTED_BOARDS]
    if not boards:
        logger.warning("No valid boards specified. Using defaults.")
        boards = DEFAULT_BOARDS

    jobspy_boards = [b for b in boards if b in JOBSPY_BOARDS]
    niche_boards = [b for b in boards if b in NICHE_JOB_PLATFORMS]
    jobs = []

    if jobspy_boards:
        jobs.extend(_scrape_jobspy(
            search_term=search_term,
            location=location,
            boards=jobspy_boards,
            results_wanted=results_wanted,
            hours_old=hours_old,
            job_type=job_type,
            is_remote=is_remote,
        ))

    for board in niche_boards:
        jobs.extend(_scrape_niche_platform(
            platform_key=board,
            search_term=search_term,
            results_wanted=results_wanted,
        ))

    logger.info(f"Scraped {len(jobs)} jobs with descriptions for '{search_term}'")
    return jobs


def _scrape_jobspy(
    search_term: str,
    location: str,
    boards: list[str],
    results_wanted: int,
    hours_old: int,
    job_type: str | None,
    is_remote: bool,
) -> list[dict]:
    """Scrape JobSpy-supported boards."""
    from jobspy import scrape_jobs as _scrape

    logger.info(f"Scraping '{search_term}' from {boards} (max {results_wanted} each)")

    try:
        jobs_df = _scrape(
            site_name=boards,
            search_term=search_term,
            location=location if location else None,
            results_wanted=results_wanted,
            hours_old=hours_old,
            job_type=job_type,
            is_remote=is_remote,
            linkedin_fetch_description=True,
            country_indeed="USA",
        )

        if jobs_df is None or jobs_df.empty:
            logger.info(f"No jobs found for '{search_term}'")
            return []

        jobs = []
        for _, row in jobs_df.iterrows():
            description = str(row.get("description", ""))
            if not description or description == "nan" or len(description) < 50:
                continue  # Skip jobs with no/tiny description

            job = {
                "title": str(row.get("title", "")),
                "company": str(row.get("company_name", row.get("company", ""))),
                "location": str(row.get("location", "")),
                "description": description,
                "job_url": str(row.get("job_url", row.get("link", ""))),
                "source": str(row.get("site", row.get("source", ""))),
                "date_posted": str(row.get("date_posted", "")),
                "salary": str(row.get("min_amount", "")) if row.get("min_amount") else None,
            }
            # Clean up nan values
            for k, v in job.items():
                if v == "nan" or v == "None":
                    job[k] = "" if k != "salary" else None
            jobs.append(job)

        logger.info(f"Scraped {len(jobs)} jobs with descriptions for '{search_term}'")

        # Polite delay
        time.sleep(SCRAPE_DELAY_SECONDS)
        return jobs

    except Exception as e:
        logger.error(f"Scraping failed for '{search_term}': {e}")
        return []


def _scrape_niche_platform(
    platform_key: str,
    search_term: str,
    results_wanted: int,
) -> list[dict]:
    """
    Search niche tech portals from the curated platform table.

    Many of these sites are dynamic and do not expose a stable public API, so this
    intentionally extracts conservative title/link candidates from the search page
    and lets the downstream matcher decide whether they clear the 95% threshold.
    """
    import requests
    from bs4 import BeautifulSoup
    from config.constants import DEFAULT_HEADERS

    platform = NICHE_JOB_PLATFORMS[platform_key]
    search_url = platform["search_url"].format(query=quote_plus(search_term))
    logger.info(f"Scraping '{search_term}' from {platform['name']}: {search_url}")

    try:
        response = requests.get(search_url, headers=DEFAULT_HEADERS, timeout=15)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Scraping failed for {platform['name']} '{search_term}': {e}")
        return []

    soup = BeautifulSoup(response.text, "lxml")
    jobs: list[dict] = []
    seen_urls: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        if len(jobs) >= results_wanted:
            break

        title = " ".join(anchor.get_text(" ", strip=True).split())
        href = anchor.get("href", "")
        if not _looks_like_job_link(title, href, search_term):
            continue

        job_url = urljoin(search_url, href)
        if job_url in seen_urls:
            continue
        seen_urls.add(job_url)

        container = anchor.find_parent(["article", "li", "section", "div"])
        snippet = ""
        if container:
            snippet = " ".join(container.get_text(" ", strip=True).split())
        if len(snippet) < len(title):
            snippet = title

        description = (
            f"{title}\n"
            f"Search query: {search_term}\n"
            f"Platform focus: {platform['best_for']}.\n"
            f"Platform signal: {platform['why_better']}.\n"
            f"Listing snippet: {snippet[:1200]}"
        )

        jobs.append({
            "title": title[:160],
            "company": platform["name"],
            "location": "Any",
            "description": description,
            "job_url": job_url,
            "source": platform["name"],
            "date_posted": "",
            "salary": None,
        })

    logger.info(f"Scraped {len(jobs)} candidate links from {platform['name']}")
    time.sleep(SCRAPE_DELAY_SECONDS)
    return jobs


def _looks_like_job_link(title: str, href: str, search_term: str) -> bool:
    """Return True when an anchor is plausibly an individual job result."""
    if not title or len(title) < 4:
        return False

    lowered = f"{title} {href}".lower()
    blocked = ("login", "sign", "privacy", "terms", "blog", "about", "pricing")
    if any(token in lowered for token in blocked):
        return False

    job_tokens = (
        "job", "role", "career", "opening", "engineer", "developer", "scientist",
        "analyst", "data", "machine learning", "ai", "ml", "software",
    )
    query_tokens = [t for t in search_term.lower().replace("-", " ").split() if len(t) > 2]
    return any(token in lowered for token in job_tokens) or any(t in lowered for t in query_tokens)


def scrape_jobs_multi_query(
    queries: list[str],
    location: str = "",
    boards: list[str] | None = None,
    results_per_query: int = 50,
) -> list[dict]:
    """
    Scrape with multiple search queries and deduplicate results.
    """
    all_jobs: dict[str, dict] = {}  # keyed by job_url for dedup

    for query in queries:
        jobs = scrape_jobs(
            search_term=query,
            location=location,
            boards=boards,
            results_wanted=results_per_query,
        )
        for job in jobs:
            url = job.get("job_url", "")
            if url and url not in all_jobs:
                all_jobs[url] = job

        # Delay between queries to avoid rate limiting
        time.sleep(SCRAPE_DELAY_SECONDS)

    logger.info(f"Total unique jobs after dedup: {len(all_jobs)}")
    return list(all_jobs.values())
