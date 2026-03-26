import re
from dataclasses import dataclass, field
from typing import Optional

_CYBER_MODEL_KEYWORDS = {
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
    "encryption",
}

# Leading word-boundary patterns prevent false positives like
# "soc" matching "associate" or "iam" matching "teamwork".
_CYBER_MODEL_PATTERNS = [
    re.compile(r"\b" + re.escape(kw), re.IGNORECASE)
    for kw in _CYBER_MODEL_KEYWORDS
]


@dataclass
class Job:
    """Represents a cybersecurity internship listing."""

    title: str
    company: str
    location: str
    url: str
    pay: Optional[str] = None
    published_date: Optional[str] = None
    source: str = ""

    def is_cybersecurity_related(self) -> bool:
        """Return True if the job title or company is cybersecurity-related.

        Uses leading word-boundary matching to avoid false positives such as
        'soc' matching 'associate'.
        """
        combined = (self.title + " " + self.company).lower()
        return any(p.search(combined) for p in _CYBER_MODEL_PATTERNS)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "pay": self.pay or "Not listed",
            "published_date": self.published_date or "Not listed",
            "url": self.url,
            "source": self.source,
        }
