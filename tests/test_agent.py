"""Tests for the agent orchestrator."""

import pytest

from src.agent import CybersecurityInternshipAgent, _is_relevant, _deduplicate
from src.models import Job


def _job(title, company="AcmeSec", url="https://acmesec.com/jobs/1", location="Remote"):
    return Job(title=title, company=company, location=location, url=url)


class TestIsRelevant:
    def test_cyber_intern_is_relevant(self):
        assert _is_relevant(_job("Cybersecurity Intern"))

    def test_security_intern_is_relevant(self):
        assert _is_relevant(_job("Security Engineering Intern"))

    def test_threat_intel_intern_is_relevant(self):
        assert _is_relevant(_job("Threat Intelligence Intern"))

    def test_appsec_intern_is_relevant(self):
        assert _is_relevant(_job("AppSec Intern"))

    def test_fulltime_security_not_relevant(self):
        # Full-time roles without intern keyword should be excluded
        assert not _is_relevant(_job("Security Engineer"))

    def test_marketing_intern_not_relevant(self):
        assert not _is_relevant(_job("Marketing Intern"))

    def test_crowdstrike_intern_is_relevant(self):
        # Intern at a known cyber company → relevant even without "security" in title
        assert _is_relevant(_job("Software Intern", company="CrowdStrike"))

    def test_soc_not_matched_in_associate(self):
        # "soc" must not match as a substring of "associate"
        assert not _is_relevant(_job("Associate Intern", company="Acme Retail"))

    def test_iam_not_matched_in_team(self):
        # "iam" must not match as a substring of "team"
        assert not _is_relevant(_job("Team Intern", company="Acme Retail"))


class TestDeduplicate:
    def test_removes_exact_duplicates(self):
        j = _job("Security Intern")
        result = _deduplicate([j, j])
        assert len(result) == 1

    def test_keeps_different_jobs(self):
        j1 = _job("Security Intern", url="https://a.com/1")
        j2 = _job("Network Security Intern", url="https://b.com/2")
        result = _deduplicate([j1, j2])
        assert len(result) == 2

    def test_deduplication_is_case_insensitive_on_company_and_title(self):
        j1 = _job("Security Intern", company="CrowdStrike", url="https://cs.com/1")
        j2 = _job("security intern", company="crowdstrike", url="https://cs.com/1")
        result = _deduplicate([j1, j2])
        assert len(result) == 1


class TestAgentToJson:
    def test_to_json_returns_valid_json(self):
        import json
        agent = CybersecurityInternshipAgent.__new__(CybersecurityInternshipAgent)
        jobs = [Job(
            title="Security Intern",
            company="AcmeSec",
            location="Remote",
            url="https://acmesec.com/1",
            pay="$30/hr",
        )]
        output = agent.to_json(jobs)
        data = json.loads(output)
        assert len(data) == 1
        assert data[0]["title"] == "Security Intern"
        assert data[0]["pay"] == "$30/hr"
