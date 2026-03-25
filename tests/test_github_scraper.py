"""Tests for the GitHub SimplifyJobs scraper."""

import pytest
import responses as responses_lib

from src.scrapers import github_simplify
from src.scrapers.github_simplify import _REPO_URLS, _parse_html_tables, _strip_tracking_params


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_readme(rows_html: str) -> str:
    """Wrap row HTML in a minimal README table structure."""
    return f"""
# Summer 2026 Tech Internships

<table>
<thead>
<tr>
<th>Company</th>
<th>Role</th>
<th>Location</th>
<th>Application</th>
<th>Age</th>
</tr>
</thead>
<tbody>
{rows_html}
</tbody>
</table>
"""


_SAMPLE_ROWS = """
<tr>
<td><strong><a href="https://simplify.jobs/c/CrowdStrike">CrowdStrike</a></strong></td>
<td>Security Engineering Intern</td>
<td>Austin, TX</td>
<td><div align="center">
  <a href="https://crowdstrike.wd5.myworkdayjobs.com/crowdstrikecareers/job/123?utm_source=Simplify&amp;ref=Simplify"><img src="apply.png" alt="Apply"></a>
  <a href="https://simplify.jobs/p/abc123"><img src="simplify.png" alt="Simplify"></a>
</div></td>
<td>1d</td>
</tr>
<tr>
<td><strong><a href="https://simplify.jobs/c/Acme">Acme Corp</a></strong></td>
<td>Software Engineering Intern</td>
<td>Remote</td>
<td><div align="center">
  <a href="https://acme.com/jobs/456?utm_source=Simplify&amp;ref=Simplify"><img src="apply.png" alt="Apply"></a>
</div></td>
<td>2d</td>
</tr>
<tr>
<td>↳</td>
<td>Data Engineering Intern</td>
<td>NYC</td>
<td><div align="center">
  <a href="https://acme.com/jobs/789?utm_source=Simplify&amp;ref=Simplify"><img src="apply.png" alt="Apply"></a>
</div></td>
<td>2d</td>
</tr>
"""

SAMPLE_README = _make_readme(_SAMPLE_ROWS)


# ---------------------------------------------------------------------------
# Unit tests for the HTML table parser
# ---------------------------------------------------------------------------

class TestHTMLTableParser:
    def test_parses_expected_number_of_jobs(self):
        jobs = _parse_html_tables(SAMPLE_README)
        assert len(jobs) == 3

    def test_job_fields_populated(self):
        jobs = _parse_html_tables(SAMPLE_README)
        job = jobs[0]
        assert job.company == "CrowdStrike"
        assert "Security" in job.title
        assert job.location == "Austin, TX"
        assert "crowdstrike" in job.url.lower()

    def test_sub_entry_inherits_company_name(self):
        jobs = _parse_html_tables(SAMPLE_README)
        assert jobs[2].company == "Acme Corp"
        assert jobs[2].title == "Data Engineering Intern"

    def test_tracking_params_stripped_from_url(self):
        jobs = _parse_html_tables(SAMPLE_README)
        assert "utm_source" not in jobs[0].url
        assert "ref=" not in jobs[0].url

    def test_simplify_links_not_used_as_primary(self):
        jobs = _parse_html_tables(SAMPLE_README)
        assert "simplify.jobs" not in jobs[0].url

    def test_source_set(self):
        jobs = _parse_html_tables(SAMPLE_README)
        assert all(j.source == "SimplifyJobs GitHub" for j in jobs)

    def test_empty_html_returns_empty(self):
        assert _parse_html_tables("") == []

    def test_html_without_table_returns_empty(self):
        assert _parse_html_tables("<p>No table here.</p>") == []


class TestStripTrackingParams:
    def test_removes_utm_source(self):
        url = "https://example.com/jobs/1?utm_source=Simplify&ref=Simplify"
        clean = _strip_tracking_params(url)
        assert "utm_source" not in clean
        assert "ref=" not in clean
        assert "example.com/jobs/1" in clean

    def test_preserves_non_tracking_params(self):
        url = "https://example.com/jobs?id=123&gh_jid=456"
        clean = _strip_tracking_params(url)
        assert "id=123" in clean
        assert "gh_jid=456" in clean


# ---------------------------------------------------------------------------
# Integration-style tests using `responses` to mock HTTP
# ---------------------------------------------------------------------------

@responses_lib.activate
def test_scrape_uses_first_url_on_success():
    responses_lib.add(
        responses_lib.GET,
        _REPO_URLS[0],
        body=SAMPLE_README,
        status=200,
    )
    jobs = github_simplify.scrape()
    assert len(jobs) == 3


@responses_lib.activate
def test_scrape_falls_back_to_second_url():
    responses_lib.add(
        responses_lib.GET,
        _REPO_URLS[0],
        status=404,
    )
    responses_lib.add(
        responses_lib.GET,
        _REPO_URLS[1],
        body=SAMPLE_README,
        status=200,
    )
    jobs = github_simplify.scrape()
    assert len(jobs) == 3


@responses_lib.activate
def test_scrape_returns_empty_when_all_fail():
    for url in _REPO_URLS:
        responses_lib.add(responses_lib.GET, url, status=500)
    jobs = github_simplify.scrape()
    assert jobs == []
