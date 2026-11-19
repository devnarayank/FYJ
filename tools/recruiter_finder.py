"""
Lightweight HTTP-based recruiter/contact finder.
Uses requests + BeautifulSoup instead of Playwright to save RAM.
"""
import logging
import re

import requests
from bs4 import BeautifulSoup

from config.constants import DEFAULT_HEADERS
from models.schemas import ContactInfo

logger = logging.getLogger(__name__)


def find_recruiter(job_url: str, company_name: str) -> ContactInfo:
    """
    Attempt to find recruiter/hiring manager contact info.
    Falls back gracefully to generic contact.
    """
    contact = ContactInfo(source="generic")

    # Strategy 1: Parse the job posting page itself
    contact = _try_job_page(job_url, contact)
    if contact.email:
        return contact

    # Strategy 2: Check company careers page
    domain = _extract_company_domain(company_name)
    if domain:
        contact = _try_careers_page(domain, contact)
        if contact.email:
            return contact

        # Strategy 3: Infer common email patterns
        contact = _infer_email(domain, contact)

    return contact


def _try_job_page(job_url: str, contact: ContactInfo) -> ContactInfo:
    """Try to extract recruiter info from the job posting page."""
    if not job_url:
        return contact

    try:
        resp = requests.get(job_url, headers=DEFAULT_HEADERS, timeout=10)
        if resp.status_code != 200:
            return contact

        soup = BeautifulSoup(resp.text, "lxml")
        text = soup.get_text(" ", strip=True)

        # Look for recruiter name patterns
        name_patterns = [
            r"[Pp]osted\s+by[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)",
            r"[Rr]ecruiter[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)",
            r"[Hh]iring\s+[Mm]anager[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)",
            r"[Cc]ontact[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)",
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                contact.name = match.group(1).strip()
                contact.source = "job_posting"
                break

        # Look for email in page
        email_match = re.search(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            text,
        )
        if email_match:
            email = email_match.group(0)
            # Filter out common non-recruiter emails
            skip = ["noreply", "no-reply", "support", "info@example", "test@"]
            if not any(s in email.lower() for s in skip):
                contact.email = email
                contact.source = "job_posting"

    except Exception as e:
        logger.debug(f"Job page scrape failed: {e}")

    return contact


def _try_careers_page(domain: str, contact: ContactInfo) -> ContactInfo:
    """Try to find contact info on a company's careers page."""
    careers_urls = [
        f"https://{domain}/careers",
        f"https://{domain}/jobs",
        f"https://careers.{domain}",
    ]

    for url in careers_urls:
        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=8)
            if resp.status_code != 200:
                continue

            text = resp.text
            email_match = re.search(
                r"[a-zA-Z0-9._%+-]+@" + re.escape(domain),
                text,
            )
            if email_match:
                contact.email = email_match.group(0)
                contact.source = "career_page"
                return contact

        except Exception:
            continue

    return contact


def _infer_email(domain: str, contact: ContactInfo) -> ContactInfo:
    """Infer a generic contact email from company domain."""
    common_prefixes = ["careers", "jobs", "hr", "recruiting", "talent", "hiring"]
    for prefix in common_prefixes:
        inferred = f"{prefix}@{domain}"
        if _check_email_deliverable(inferred):
            contact.email = inferred
            contact.source = "inferred"
            return contact

    # Ultimate fallback
    contact.email = f"careers@{domain}"
    contact.source = "inferred"
    return contact


def _extract_company_domain(company_name: str) -> str | None:
    """Guess the company's domain from its name."""
    if not company_name:
        return None
    # Clean company name
    name = company_name.lower().strip()
    name = re.sub(r"[,.\s]+(inc|llc|ltd|corp|co|gmbh|plc)\.?$", "", name)
    name = re.sub(r"[^a-z0-9]", "", name)
    if name:
        return f"{name}.com"
    return None


def _check_email_deliverable(email: str) -> bool:
    """Quick check if email domain has MX records."""
    try:
        import dns.resolver
        domain = email.split("@")[1]
        dns.resolver.resolve(domain, "MX")
        return True
    except Exception:
        return False  # Can't verify, assume it might work
