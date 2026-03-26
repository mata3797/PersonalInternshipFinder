"""Tests for the Job data model."""

import pytest
from src.models import Job


def make_job(**kwargs):
    defaults = dict(
        title="Security Intern",
        company="AcmeSec",
        location="Remote",
        url="https://acmesec.com/jobs/123",
    )
    defaults.update(kwargs)
    return Job(**defaults)


class TestJobModel:
    def test_to_dict_includes_all_fields(self):
        job = make_job(pay="$30/hr", published_date="1d")
        d = job.to_dict()
        assert d["title"] == "Security Intern"
        assert d["company"] == "AcmeSec"
        assert d["location"] == "Remote"
        assert d["pay"] == "$30/hr"
        assert d["published_date"] == "1d"
        assert d["url"] == "https://acmesec.com/jobs/123"

    def test_to_dict_pay_defaults_to_not_listed(self):
        job = make_job(pay=None)
        assert job.to_dict()["pay"] == "Not listed"

    def test_to_dict_published_date_defaults_to_not_listed(self):
        job = make_job(published_date=None)
        assert job.to_dict()["published_date"] == "Not listed"

    def test_is_cybersecurity_related_by_title(self):
        assert make_job(title="Security Analyst Intern").is_cybersecurity_related()
        assert make_job(title="Cyber Defense Intern").is_cybersecurity_related()
        assert make_job(title="AppSec Summer Intern").is_cybersecurity_related()

    def test_is_cybersecurity_related_by_company(self):
        assert make_job(title="Software Intern", company="CrowdStrike Security").is_cybersecurity_related()

    def test_not_cybersecurity_related(self):
        assert not make_job(title="Marketing Intern", company="ACME Retail").is_cybersecurity_related()
