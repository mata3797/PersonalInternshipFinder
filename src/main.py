"""
CLI entry point for the Cybersecurity Internship Finder Agent.

Usage
-----
  python -m src.main              # print results as a rich table
  python -m src.main --json       # print raw JSON
  python -m src.main --output jobs.json   # save JSON to a file
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich import box

from src.agent import CybersecurityInternshipAgent

console = Console()


def _build_table(jobs) -> Table:
    table = Table(
        title="[bold cyan]Cybersecurity Summer Internships[/bold cyan]",
        box=box.ROUNDED,
        show_lines=True,
        highlight=True,
    )
    table.add_column("#", style="dim", width=4, no_wrap=True)
    table.add_column("Company", style="bold green", min_width=18)
    table.add_column("Title", style="white", min_width=28)
    table.add_column("Location", style="yellow", min_width=18)
    table.add_column("Published", style="cyan", min_width=12)
    table.add_column("Pay", style="magenta", min_width=12)
    table.add_column("Link", style="blue", min_width=35)

    for i, job in enumerate(jobs, start=1):
        table.add_row(
            str(i),
            job.company,
            job.title,
            job.location or "—",
            job.published_date or "Not listed",
            job.pay or "Not listed",
            job.url,
        )
    return table


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="internship-finder",
        description="Find cybersecurity summer internships from company career pages.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of a formatted table.",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Save JSON results to FILE (implies --json).",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    with console.status("[bold green]Searching for cybersecurity internships…[/bold green]"):
        agent = CybersecurityInternshipAgent()
        jobs = agent.run()

    if not jobs:
        console.print("[bold red]No cybersecurity internships found.[/bold red]")
        sys.exit(0)

    if args.output or args.json:
        payload = json.dumps([j.to_dict() for j in jobs], indent=2)
        if args.output:
            Path(args.output).write_text(payload, encoding="utf-8")
            console.print(f"[green]Saved {len(jobs)} jobs to {args.output}[/green]")
        else:
            print(payload)
    else:
        console.print(_build_table(jobs))
        console.print(f"\n[bold]Total:[/bold] {len(jobs)} cybersecurity internships found.")


if __name__ == "__main__":
    main()
