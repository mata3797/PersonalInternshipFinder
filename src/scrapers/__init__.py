"""Shared HTTP session and helpers used by all scrapers."""

import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

REQUEST_TIMEOUT = 15


def make_session() -> requests.Session:
    """Return a requests.Session configured with default headers."""
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session


def fetch_html(url: str, session: Optional[requests.Session] = None) -> Optional[BeautifulSoup]:
    """
    Fetch *url* and return a BeautifulSoup document, or None on failure.
    """
    if session is None:
        session = make_session()
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")
    except requests.RequestException as exc:
        logger.warning("Failed to fetch %s: %s", url, exc)
        return None
