"""
Scraper for the SimplifyJobs/Summer2026-Internships GitHub repository.

The repo maintains an HTML table of internship listings that includes:
  - Company name
  - Role / title
  - Location
  - Application link (first link in the cell is the direct company URL)

The README is stored as a Markdown file that embeds raw HTML tables.

Raw URL:
  https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/README.md

Fallback to Summer2025 if 2026 is not yet available.
"""

import logging
import re
from typing import List, Optional
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

import requests
from bs4 import BeautifulSoup

from src.models import Job
from src.scrapers import make_session

logger = logging.getLogger(__name__)

_REPO_URLS = [
    "https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/README.md",
    "https://raw.githubusercontent.com/SimplifyJobs/Summer2025-Internships/dev/README.md",
]

# UTM / tracking params we strip from company URLs
_TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "ref"}

# Skip these domains — they are aggregator / redirect pages, not real company pages
_SKIP_DOMAINS = {"simplify.jobs", "linkedin.com", "indeed.com", "glassdoor.com"}


def _strip_tracking_params(url: str) -> str:
    """Remove common UTM / tracking query parameters from *url*."""
    try:
        parsed = urlparse(url)
        qs = {k: v for k, v in parse_qs(parsed.query).items() if k not in _TRACKING_PARAMS}
        clean_query = urlencode(qs, doseq=True)
        return urlunparse(parsed._replace(query=clean_query))
    except Exception:
        return url


def _is_aggregator(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lstrip("www.")
        return any(host.endswith(d) for d in _SKIP_DOMAINS)
    except Exception:
        return False


def _first_company_link(td) -> Optional[str]:
    """
    Return the first non-aggregator href found inside an application <td>.
    The SimplifyJobs table embeds two links per cell:
      1. Direct company career page (Workday / Greenhouse / Lever / etc.)
      2. simplify.jobs redirect
    We want the first one.
    """
    for a in td.find_all("a", href=True):
        href = a["href"].strip()
        if not href.startswith("http"):
            continue
        if not _is_aggregator(href):
            return _strip_tracking_params(href)
    return None


def _row_is_sub_entry(tds) -> bool:
    """
    Rows that continue a previous company entry start with '↳' in the first cell.
    We still want to parse them — just reuse the last seen company name.
    """
    if not tds:
        return False
    text = tds[0].get_text(strip=True)
    return text.startswith("↳") or text == ""


def _parse_location(td) -> str:
    """
    Extract a human-readable location string from a location <td>.

    The SimplifyJobs table sometimes embeds multiple location spans separated
    by <br> tags, and prefixes multi-location rows with "N locations".
    This helper normalises those into a clean comma-separated string.
    """
    # Replace <br> tags with ", " so they become natural separators
    for br in td.find_all("br"):
        br.replace_with(", ")

    text = td.get_text(separator=" ", strip=True)

    # Remove leading "N locations" prefix (e.g. "9 locations Boston, MA …")
    text = re.sub(r"^\d+\s+locations?\s*", "", text, flags=re.IGNORECASE)

    # Collapse internal runs of commas / spaces
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"\s{2,}", " ", text).strip(", ")

    return text


def _parse_html_tables(html: str) -> List[Job]:
    """Parse all HTML tables in the SimplifyJobs README and return Job objects."""
    soup = BeautifulSoup(html, "lxml")
    jobs: List[Job] = []
    last_company = ""

    for table in soup.find_all("table"):
        # Only process tables with the expected headers
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        if "company" not in headers or "role" not in headers:
            continue

        col = {name: idx for idx, name in enumerate(headers)}
        company_idx = col.get("company", 0)
        role_idx = col.get("role", 1)
        location_idx = col.get("location", 2)
        application_idx = col.get("application", 3)
        age_idx = col.get("age")

        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if not tds or len(tds) < 3:
                continue

            # Determine company name
            if _row_is_sub_entry(tds):
                company = last_company
            else:
                company = tds[company_idx].get_text(separator=" ", strip=True)
                # Strip emoji/flags and leading symbols
                company = re.sub(r"^[\U0001F000-\U0001FFFF🔥🛂🇺🇸🔒🎓\s]+", "", company).strip()
                if company:
                    last_company = company
                else:
                    company = last_company

            if not company:
                continue

            title = tds[role_idx].get_text(strip=True) if role_idx < len(tds) else ""
            location = _parse_location(tds[location_idx]) if location_idx < len(tds) else ""
            published_date = _clean(tds[age_idx].get_text()) if age_idx is not None and age_idx < len(tds) else ""

            url = None
            if application_idx < len(tds):
                url = _first_company_link(tds[application_idx])

            if not title or not url:
                continue

            jobs.append(
                Job(
                    title=title,
                    company=company,
                    location=location,
                    published_date=published_date,
                    url=url,
                    source="SimplifyJobs GitHub",
                )
            )

    return jobs


def scrape(session: Optional[requests.Session] = None) -> List[Job]:
    """
    Download and parse the SimplifyJobs internship README.

    Returns a list of *all* jobs found; the agent layer is responsible for
    filtering to cybersecurity-relevant roles.
    """
    if session is None:
        session = make_session()

    for url in _REPO_URLS:
        try:
            response = session.get(url, timeout=20)
            response.raise_for_status()
            logger.info("Fetched SimplifyJobs README from %s (%d bytes)", url, len(response.text))
            jobs = _parse_html_tables(response.text)
            logger.info("Parsed %d total job listings", len(jobs))
            return jobs
        except requests.RequestException as exc:
            logger.warning("Could not fetch %s: %s", url, exc)

    logger.error("All SimplifyJobs URLs failed.")
    return []
