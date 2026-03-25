# PersonalInternshipFinder

A web-scraping agent that automatically finds **cybersecurity summer internships** and returns the job title, company, location, pay, and a **direct link to the company's own job posting** (not LinkedIn or Indeed).

---

## Features

- 🔍 **Multi-source scraping** — pulls from the [SimplifyJobs Summer 2026 Internships](https://github.com/SimplifyJobs/Summer2026-Internships) GitHub repo (1,800+ listings) and direct company career pages
- 🏢 **Real company links** — UTM tracking parameters are stripped; aggregator links (LinkedIn, Simplify, Indeed) are skipped in favour of the direct ATS URL
- 🛡️ **Cybersecurity filter** — keeps only roles whose title contains cybersecurity keywords (security, cyber, SOC, appsec, threat intel, cryptography, …) OR that come from a well-known security company (CrowdStrike, Palo Alto Networks, Leidos, Booz Allen, …)
- 🧹 **Deduplication** — removes duplicate listings across sources
- 📊 **Rich table output** — formatted terminal table with colour; also supports `--json` and `--output` flags

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the agent

```bash
# Pretty table in the terminal
python -m src.main

# JSON output (stdout)
python -m src.main --json

# Save results to a file
python -m src.main --output jobs.json

# Verbose logging (useful for debugging)
python -m src.main -v
```

---

## Project Structure

```
PersonalInternshipFinder/
├── requirements.txt
├── src/
│   ├── agent.py                 # Orchestrator: runs scrapers, filters, deduplicates
│   ├── main.py                  # CLI entry point
│   ├── models/
│   │   └── __init__.py          # Job data model
│   └── scrapers/
│       ├── __init__.py          # Shared HTTP session / fetch helpers
│       ├── github_simplify.py   # Scraper for SimplifyJobs GitHub repo
│       └── company_scrapers.py  # Direct company career-page scrapers
└── tests/
    ├── test_agent.py
    ├── test_company_scrapers.py
    ├── test_github_scraper.py
    └── test_models.py
```

---

## Running Tests

```bash
python -m pytest tests/ -v
```

---

## Data Sources

| Source | Method | Notes |
|--------|--------|-------|
| [SimplifyJobs/Summer2026-Internships](https://github.com/SimplifyJobs/Summer2026-Internships) | HTML table parsing | Primary source — updated daily |
| CrowdStrike | Workday JSON API | Direct company ATS |
| Palo Alto Networks | Workday JSON API | Direct company ATS |
| Rapid7 | Greenhouse JSON API | Direct company ATS |
| Tenable | Greenhouse JSON API | Direct company ATS |
| SentinelOne | Greenhouse JSON API | Direct company ATS |
| Qualys | Lever JSON API | Direct company ATS |
| Fortinet | HTML scraping | Direct company careers page |

---

## Cybersecurity Keywords

The agent matches roles whose **title** contains any of:

`security`, `cyber`, `soc`, `pentest`, `penetration`, `red team`, `blue team`, `threat`, `vulnerability`, `forensic`, `malware`, `devsecops`, `appsec`, `infosec`, `iam`, `identity`, `siem`, `incident response`, `cryptograph`, `cloud security`, `network security`

…or whose **company** is one of ~30 known cybersecurity firms (CrowdStrike, Palo Alto Networks, Snyk, Leidos, Booz Allen, CACI, Peraton, etc.).
