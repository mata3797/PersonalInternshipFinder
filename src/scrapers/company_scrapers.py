"""
Direct company career-page scrapers for well-known cybersecurity companies.

Each scraper targets the company's own careers website so that we return the
real company job-posting URL rather than a third-party aggregator.

Supported companies
-------------------
- CrowdStrike
- Palo Alto Networks
- Fortinet
- Splunk (Cisco)
- Rapid7
- Tenable
- SentinelOne
- Qualys
"""

import logging
import re
from typing import List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from src.models import Job
from src.scrapers import fetch_html, make_session

logger = logging.getLogger(__name__)

# Keywords used to decide whether a listing is summer-internship relevant
_INTERN_KEYWORDS = {"intern", "internship", "co-op", "coop"}
_CYBER_KEYWORDS = {
    "security",
    "cyber",
    "soc",
    "pentest",
    "penetration",
    "threat",
    "vulnerability",
    "forensic",
    "malware",
    "devsecops",
    "appsec",
    "infosec",
    "red team",
    "blue team",
    "iam",
    "identity",
    "siem",
    "incident response",
    "cryptograph",
    "cloud security",
    "network security",
}


def _is_cyber_intern(title: str) -> bool:
    """Return True if the title indicates an internship or a cybersecurity role.

    Company-level scrapers already target cybersecurity firms, so any
    internship role from them is relevant.  We also accept non-intern
    roles that explicitly mention cybersecurity so the caller can decide
    whether to include them.
    """
    title_lower = title.lower()
    has_intern = any(kw in title_lower for kw in _INTERN_KEYWORDS)
    has_cyber = any(kw in title_lower for kw in _CYBER_KEYWORDS)
    return has_intern or has_cyber


def _clean(text: Optional[str]) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# CrowdStrike — uses Workday ATS
# ---------------------------------------------------------------------------

def scrape_crowdstrike(session: Optional[requests.Session] = None) -> List[Job]:
    """
    Scrape CrowdStrike Workday career page for intern roles.
    URL: https://crowdstrike.wd5.myworkdayjobs.com/crowdstrikecareers
    """
    if session is None:
        session = make_session()

    base = "https://crowdstrike.wd5.myworkdayjobs.com"
    search_url = (
        f"{base}/wday/cxs/crowdstrike/crowdstrikecareers/jobs"
        "?limit=50&offset=0&searchText=intern"
    )

    jobs: List[Job] = []
    try:
        resp = session.get(search_url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("jobPostings", []):
            title = _clean(item.get("title", ""))
            location_info = item.get("locationsText", "") or item.get("location", "")
            location = _clean(location_info)
            external_path = item.get("externalPath", "")
            url = urljoin(base, f"/crowdstrike/crowdstrikecareers/job/{external_path}") if external_path else ""
            if not url:
                continue
            jobs.append(
                Job(
                    title=title,
                    company="CrowdStrike",
                    location=location,
                    published_date=_clean(item.get("postedOn", "") or item.get("bulletFields", [""])[0] if item.get("bulletFields") else ""),
                    url=url,
                    source="CrowdStrike Careers",
                )
            )
    except Exception as exc:
        logger.warning("CrowdStrike scrape failed: %s", exc)

    return jobs


# ---------------------------------------------------------------------------
# Palo Alto Networks — uses Workday ATS
# ---------------------------------------------------------------------------

def scrape_palo_alto(session: Optional[requests.Session] = None) -> List[Job]:
    """
    Scrape Palo Alto Networks Workday career page for intern roles.
    """
    if session is None:
        session = make_session()

    base = "https://jobs.paloaltonetworks.com"
    search_url = (
        f"https://paloaltonetworks.wd3.myworkdayjobs.com"
        "/wday/cxs/paloaltonetworks/PAN_Careers/jobs"
        "?limit=50&offset=0&searchText=intern"
    )

    jobs: List[Job] = []
    try:
        resp = session.get(search_url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("jobPostings", []):
            title = _clean(item.get("title", ""))
            location = _clean(item.get("locationsText", "") or item.get("location", ""))
            external_path = item.get("externalPath", "")
            if external_path:
                url = (
                    "https://paloaltonetworks.wd3.myworkdayjobs.com"
                    f"/en-US/PAN_Careers/job/{external_path}"
                )
            else:
                continue
            jobs.append(
                Job(
                    title=title,
                    company="Palo Alto Networks",
                    location=location,
                    published_date=_clean(item.get("postedOn", "") or item.get("bulletFields", [""])[0] if item.get("bulletFields") else ""),
                    url=url,
                    source="Palo Alto Networks Careers",
                )
            )
    except Exception as exc:
        logger.warning("Palo Alto Networks scrape failed: %s", exc)

    return jobs


# ---------------------------------------------------------------------------
# Rapid7 — uses Greenhouse ATS
# ---------------------------------------------------------------------------

def scrape_rapid7(session: Optional[requests.Session] = None) -> List[Job]:
    """
    Scrape Rapid7 Greenhouse board for intern / cybersecurity roles.
    API: https://boards-api.greenhouse.io/v1/boards/rapid7/jobs
    """
    if session is None:
        session = make_session()

    api_url = "https://boards-api.greenhouse.io/v1/boards/rapid7/jobs?content=true"
    jobs: List[Job] = []
    try:
        resp = session.get(api_url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("jobs", []):
            title = _clean(item.get("title", ""))
            if not _is_cyber_intern(title):
                continue
            location = _clean(item.get("location", {}).get("name", ""))
            url = _clean(item.get("absolute_url", ""))
            if not url:
                continue
            jobs.append(
                Job(
                    title=title,
                    company="Rapid7",
                    location=location,
                    published_date=_clean(item.get("updated_at", "") or item.get("created_at", "")),
                    url=url,
                    source="Rapid7 Careers",
                )
            )
    except Exception as exc:
        logger.warning("Rapid7 scrape failed: %s", exc)

    return jobs


# ---------------------------------------------------------------------------
# Tenable — uses Greenhouse ATS
# ---------------------------------------------------------------------------

def scrape_tenable(session: Optional[requests.Session] = None) -> List[Job]:
    """
    Scrape Tenable Greenhouse board for intern / cybersecurity roles.
    """
    if session is None:
        session = make_session()

    api_url = "https://boards-api.greenhouse.io/v1/boards/tenable/jobs?content=true"
    jobs: List[Job] = []
    try:
        resp = session.get(api_url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("jobs", []):
            title = _clean(item.get("title", ""))
            if not _is_cyber_intern(title):
                continue
            location = _clean(item.get("location", {}).get("name", ""))
            url = _clean(item.get("absolute_url", ""))
            if not url:
                continue
            jobs.append(
                Job(
                    title=title,
                    company="Tenable",
                    location=location,
                    published_date=_clean(item.get("updated_at", "") or item.get("created_at", "")),
                    url=url,
                    source="Tenable Careers",
                )
            )
    except Exception as exc:
        logger.warning("Tenable scrape failed: %s", exc)

    return jobs


# ---------------------------------------------------------------------------
# SentinelOne — uses Greenhouse ATS
# ---------------------------------------------------------------------------

def scrape_sentinelone(session: Optional[requests.Session] = None) -> List[Job]:
    """
    Scrape SentinelOne Greenhouse board for intern / cybersecurity roles.
    """
    if session is None:
        session = make_session()

    api_url = "https://boards-api.greenhouse.io/v1/boards/sentinelone/jobs?content=true"
    jobs: List[Job] = []
    try:
        resp = session.get(api_url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("jobs", []):
            title = _clean(item.get("title", ""))
            if not _is_cyber_intern(title):
                continue
            location = _clean(item.get("location", {}).get("name", ""))
            url = _clean(item.get("absolute_url", ""))
            if not url:
                continue
            jobs.append(
                Job(
                    title=title,
                    company="SentinelOne",
                    location=location,
                    published_date=_clean(item.get("updated_at", "") or item.get("created_at", "")),
                    url=url,
                    source="SentinelOne Careers",
                )
            )
    except Exception as exc:
        logger.warning("SentinelOne scrape failed: %s", exc)

    return jobs


# ---------------------------------------------------------------------------
# Qualys — uses Lever ATS
# ---------------------------------------------------------------------------

def scrape_qualys(session: Optional[requests.Session] = None) -> List[Job]:
    """
    Scrape Qualys Lever board for intern / cybersecurity roles.
    API: https://api.lever.co/v0/postings/qualys?mode=json
    """
    if session is None:
        session = make_session()

    api_url = "https://api.lever.co/v0/postings/qualys?mode=json"
    jobs: List[Job] = []
    try:
        resp = session.get(api_url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        for item in data:
            title = _clean(item.get("text", ""))
            if not _is_cyber_intern(title):
                continue
            location = _clean(item.get("categories", {}).get("location", ""))
            url = _clean(item.get("hostedUrl", ""))
            if not url:
                continue
            jobs.append(
                Job(
                    title=title,
                    company="Qualys",
                    location=location,
                    published_date=_clean(item.get("createdAt", "") or item.get("updatedAt", "")),
                    url=url,
                    source="Qualys Careers",
                )
            )
    except Exception as exc:
        logger.warning("Qualys scrape failed: %s", exc)

    return jobs


# ---------------------------------------------------------------------------
# Fortinet — HTML scraping of careers page
# ---------------------------------------------------------------------------

def scrape_fortinet(session: Optional[requests.Session] = None) -> List[Job]:
    """
    Scrape Fortinet careers search for intern / security roles.
    """
    if session is None:
        session = make_session()

    search_url = "https://www.fortinet.com/corporate/careers/search-jobs?search=intern"
    jobs: List[Job] = []
    soup = fetch_html(search_url, session)
    if soup is None:
        return jobs

    # Fortinet renders jobs in <div class="career-listing"> elements (fallback: any <a> with intern in title)
    for link in soup.find_all("a", href=True):
        title = _clean(link.get_text())
        href = link["href"]
        if not _is_cyber_intern(title):
            continue
        if not href.startswith("http"):
            href = urljoin("https://www.fortinet.com", href)
        jobs.append(
            Job(
                title=title,
                company="Fortinet",
                location="",
                url=href,
                source="Fortinet Careers",
            )
        )

    return jobs


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

COMPANY_SCRAPERS = [
    scrape_crowdstrike,
    scrape_palo_alto,
    scrape_rapid7,
    scrape_tenable,
    scrape_sentinelone,
    scrape_qualys,
    scrape_fortinet,
]


def scrape_all_companies(session: Optional[requests.Session] = None) -> List[Job]:
    """Run all company scrapers and return combined results."""
    if session is None:
        session = make_session()
    all_jobs: List[Job] = []
    for scraper in COMPANY_SCRAPERS:
        try:
            results = scraper(session)
            logger.info("%s returned %d jobs", scraper.__name__, len(results))
            all_jobs.extend(results)
        except Exception as exc:
            logger.warning("Scraper %s raised an unexpected error: %s", scraper.__name__, exc)
    return all_jobs
