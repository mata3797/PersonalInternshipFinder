"""
Cybersecurity Internship Agent

Orchestrates multiple scrapers, deduplicates results, filters for
cybersecurity + summer-internship relevance, and presents findings.
"""

import json
import logging
import re
from typing import List, Optional

import requests

from src.models import Job
from src.scrapers import make_session
from src.scrapers import github_simplify
from src.scrapers.company_scrapers import scrape_all_companies

logger = logging.getLogger(__name__)

# Terms that indicate a role is a summer internship (vs full-time / part-time)
_SUMMER_TERMS = {"intern", "internship", "co-op", "coop", "summer"}

# Cybersecurity-specific title keywords (used with word-boundary matching)
_CYBER_TITLE_KEYWORDS = {
    "security",
    "cyber",
    "soc",
    "pentest",
    "penetration",
    "red team",
    "blue team",
    "threat",
    "vulnerability",
    "forensic",
    "malware",
    "devsecops",
    "appsec",
    "infosec",
    "iam",
    "identity",
    "siem",
    "incident response",
    "cryptograph",
    "cloud security",
    "network security",
}

# Well-known cybersecurity companies — any intern role from them counts
_CYBER_COMPANIES = {
    "crowdstrike",
    "palo alto",
    "fortinet",
    "rapid7",
    "tenable",
    "sentinelone",
    "qualys",
    "fireeye",
    "mandiant",
    "splunk",
    "symantec",
    "carbonblack",
    "darktrace",
    "cylance",
    "secureworks",
    "checkpoint",
    "watchguard",
    "trellix",
    "exabeam",
    "abnormal security",
    "lacework",
    "orca security",
    "wiz",
    "snyk",
    "veracode",
    "netspi",
    "coalfire",
    "optiv",
    "booz allen",
    "saic",
    "leidos",
    "peraton",
    "caci",
    "mitre",
    "offensive security",
    "hackthebox",
}

# Pre-compiled patterns for each keyword using a leading word boundary so that:
# - "cyber" matches "cybersecurity", "cyber defense", etc.
# - "soc" does NOT match "associate" (word boundary before 's' is required)
# - "iam" does NOT match "teamwork" (no word boundary before 'i' in "teamwork")
_CYBER_TITLE_PATTERNS = [re.compile(r"\b" + re.escape(kw), re.IGNORECASE) for kw in _CYBER_TITLE_KEYWORDS]
_CYBER_COMPANY_PATTERNS = [re.compile(r"\b" + re.escape(kw), re.IGNORECASE) for kw in _CYBER_COMPANIES]
_INTERN_PATTERNS = [re.compile(r"\b" + re.escape(t) + r"\b", re.IGNORECASE) for t in _SUMMER_TERMS]


def _matches_any(text: str, patterns: list) -> bool:
    return any(p.search(text) for p in patterns)


def _is_relevant(job: Job) -> bool:
    """
    Return True if the job is a cybersecurity-related summer internship.

    A job qualifies when:
      - Its title contains an internship keyword (intern / co-op / summer), AND
      - Either its title contains a cybersecurity keyword OR it comes from a
        well-known cybersecurity company.

    Word-boundary matching is used to avoid false positives such as
    "soc" in "associate" or "iam" in "team".
    """
    title_lower = job.title.lower()
    company_lower = job.company.lower()

    has_intern_term = _matches_any(title_lower, _INTERN_PATTERNS)
    has_cyber_title = _matches_any(title_lower, _CYBER_TITLE_PATTERNS)
    is_cyber_company = _matches_any(company_lower, _CYBER_COMPANY_PATTERNS)

    return has_intern_term and (has_cyber_title or is_cyber_company)


def _deduplicate(jobs: List[Job]) -> List[Job]:
    """Remove duplicates based on (company, title, url) identity."""
    seen: set = set()
    unique: List[Job] = []
    for job in jobs:
        key = (job.company.lower(), job.title.lower(), job.url)
        if key not in seen:
            seen.add(key)
            unique.append(job)
    return unique


class CybersecurityInternshipAgent:
    """Agent that searches for cybersecurity summer internships."""

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or make_session()

    def run(self) -> List[Job]:
        """
        Execute all scrapers, filter, deduplicate, and return results.
        """
        logger.info("Starting cybersecurity internship search …")

        all_jobs: List[Job] = []

        # --- Source 1: SimplifyJobs GitHub repo ---
        logger.info("Scraping SimplifyJobs GitHub repository …")
        github_jobs = github_simplify.scrape(self.session)
        logger.info("  → %d total listings found", len(github_jobs))
        all_jobs.extend(github_jobs)

        # --- Source 2: Direct company career pages ---
        logger.info("Scraping company career pages …")
        company_jobs = scrape_all_companies(self.session)
        logger.info("  → %d company listings found", len(company_jobs))
        all_jobs.extend(company_jobs)

        # Filter & deduplicate
        relevant = [j for j in all_jobs if _is_relevant(j)]
        unique = _deduplicate(relevant)

        logger.info(
            "Found %d relevant cybersecurity internships after deduplication (from %d total)",
            len(unique),
            len(all_jobs),
        )
        return unique

    def to_json(self, jobs: List[Job]) -> str:
        """Serialize job list to a JSON string."""
        return json.dumps([j.to_dict() for j in jobs], indent=2)
