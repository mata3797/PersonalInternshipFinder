"""Tests for the company career-page scrapers."""

import json
import pytest
import responses as responses_lib

from src.scrapers.company_scrapers import (
    scrape_rapid7,
    scrape_tenable,
    scrape_sentinelone,
    scrape_qualys,
)


def _greenhouse_payload(jobs):
    return json.dumps({"jobs": jobs})


def _lever_payload(jobs):
    return json.dumps(jobs)


def _make_greenhouse_job(title, location="Remote", url="https://boards.greenhouse.io/company/jobs/1"):
    return {
        "title": title,
        "location": {"name": location},
        "absolute_url": url,
        "updated_at": "2026-03-24T00:00:00Z",
    }


def _make_lever_job(title, location="Remote", url="https://jobs.lever.co/company/1"):
    return {
        "text": title,
        "categories": {"location": location},
        "hostedUrl": url,
        "createdAt": "2026-03-23T00:00:00Z",
    }


class TestRapid7Scraper:
    @responses_lib.activate
    def test_returns_intern_security_jobs(self):
        responses_lib.add(
            responses_lib.GET,
            "https://boards-api.greenhouse.io/v1/boards/rapid7/jobs",
            body=_greenhouse_payload([
                _make_greenhouse_job("Security Intern", "Boston, MA", "https://boards.greenhouse.io/rapid7/jobs/1"),
                _make_greenhouse_job("Full-Time Software Engineer", "Remote", "https://boards.greenhouse.io/rapid7/jobs/2"),
            ]),
            status=200,
        )
        jobs = scrape_rapid7()
        assert len(jobs) == 1
        assert jobs[0].title == "Security Intern"
        assert jobs[0].company == "Rapid7"
        assert jobs[0].published_date == "2026-03-24T00:00:00Z"
        assert "rapid7" in jobs[0].url

    @responses_lib.activate
    def test_returns_empty_on_http_error(self):
        responses_lib.add(
            responses_lib.GET,
            "https://boards-api.greenhouse.io/v1/boards/rapid7/jobs",
            status=503,
        )
        jobs = scrape_rapid7()
        assert jobs == []


class TestTenableScraper:
    @responses_lib.activate
    def test_returns_cyber_intern_jobs(self):
        responses_lib.add(
            responses_lib.GET,
            "https://boards-api.greenhouse.io/v1/boards/tenable/jobs",
            body=_greenhouse_payload([
                _make_greenhouse_job("Cyber Security Intern", "Columbia, MD", "https://boards.greenhouse.io/tenable/jobs/3"),
            ]),
            status=200,
        )
        jobs = scrape_tenable()
        assert len(jobs) == 1
        assert jobs[0].company == "Tenable"
        assert jobs[0].published_date == "2026-03-24T00:00:00Z"

    @responses_lib.activate
    def test_filters_non_matching_jobs(self):
        responses_lib.add(
            responses_lib.GET,
            "https://boards-api.greenhouse.io/v1/boards/tenable/jobs",
            body=_greenhouse_payload([
                _make_greenhouse_job("Marketing Manager", "Remote"),
            ]),
            status=200,
        )
        jobs = scrape_tenable()
        assert jobs == []


class TestSentinelOneScraper:
    @responses_lib.activate
    def test_returns_intern_jobs(self):
        responses_lib.add(
            responses_lib.GET,
            "https://boards-api.greenhouse.io/v1/boards/sentinelone/jobs",
            body=_greenhouse_payload([
                _make_greenhouse_job("Threat Intelligence Intern", "Mountain View, CA", "https://boards.greenhouse.io/sentinelone/jobs/5"),
            ]),
            status=200,
        )
        jobs = scrape_sentinelone()
        assert len(jobs) == 1
        assert jobs[0].company == "SentinelOne"
        assert jobs[0].published_date == "2026-03-24T00:00:00Z"


class TestQualysScraper:
    @responses_lib.activate
    def test_returns_security_intern_jobs(self):
        responses_lib.add(
            responses_lib.GET,
            "https://api.lever.co/v0/postings/qualys",
            body=_lever_payload([
                _make_lever_job("Security Intern", "Foster City, CA", "https://jobs.lever.co/qualys/abc"),
                _make_lever_job("Finance Director", "Remote", "https://jobs.lever.co/qualys/def"),
            ]),
            status=200,
        )
        jobs = scrape_qualys()
        assert len(jobs) == 1
        assert jobs[0].company == "Qualys"
        assert jobs[0].published_date == "2026-03-23T00:00:00Z"
        assert jobs[0].url == "https://jobs.lever.co/qualys/abc"
