#!/usr/bin/env python3
"""
Scraper for MIT CIS (Cryptography and Information Security) seminars.
Source: https://cis.csail.mit.edu/
"""

import json
import re
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://cis.csail.mit.edu/"
SERIES_NAME = "MIT CIS Seminar"
SERIES_URL = "https://cis.csail.mit.edu/"
DEFAULT_LOCATION = "MIT 32-G882"
DEFAULT_TIME = "10:30"


def fetch_page(url: str) -> str:
    """Fetch the HTML content of the page."""
    headers = {
        "User-Agent": "BostonTheoryEvents/1.0 (academic seminar aggregator)"
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def parse_date(date_str: str, semester_year: int) -> str | None:
    """Parse date string like 'September 5, 2025' to ISO format."""
    date_str = date_str.strip()

    # Try full date with year
    try:
        dt = datetime.strptime(date_str, "%B %d, %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # Try date without year (use semester year)
    try:
        dt = datetime.strptime(date_str, "%B %d")
        return f"{semester_year}-{dt.month:02d}-{dt.day:02d}"
    except ValueError:
        pass

    return None


def parse_speaker(text: str) -> tuple[str, str]:
    """Parse speaker string like 'Name (Affiliation)' into components."""
    match = re.match(r"(.+?)\s*\((.+?)\)\s*$", text)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return text.strip(), ""


def get_semester_year(h2_text: str) -> int | None:
    """Extract year from semester heading like 'Fall 2025'."""
    match = re.search(r"(\d{4})", h2_text)
    if match:
        return int(match.group(1))
    return None


def scrape_events() -> list:
    """Scrape events from the MIT CIS page."""
    html = fetch_page(URL)
    soup = BeautifulSoup(html, "html.parser")

    events = []
    current_year = datetime.now().year
    cutoff_year = current_year - 1  # Only include recent events

    current_semester_year = current_year

    # Process all h2 (semester) and h3 (event) elements in order
    for elem in soup.find_all(["h2", "h3"]):
        if elem.name == "h2":
            # Semester heading
            year = get_semester_year(elem.get_text())
            if year:
                current_semester_year = year
            continue

        # Skip old events
        if current_semester_year < cutoff_year:
            continue

        # h3 = event title
        title = elem.get_text(strip=True)
        if not title:
            continue

        event = {
            "series": SERIES_NAME,
            "series_url": SERIES_URL,
            "location": DEFAULT_LOCATION,
            "time": DEFAULT_TIME,
            "title": title,
        }

        # Get speaker and date from next siblings
        siblings = []
        for sib in elem.next_siblings:
            if hasattr(sib, "get_text"):
                text = sib.get_text(strip=True)
                if text:
                    siblings.append(text)
                    if len(siblings) >= 2:
                        break
            elif hasattr(sib, "name") and sib.name in ["h2", "h3"]:
                break

        if siblings:
            # First sibling is speaker
            speaker, affiliation = parse_speaker(siblings[0])
            event["speaker"] = speaker
            if affiliation:
                event["affiliation"] = affiliation

        if len(siblings) >= 2:
            # Second sibling is date
            date = parse_date(siblings[1], current_semester_year)
            if date:
                event["date"] = date

        if event.get("date"):
            events.append(event)

    return events


def main():
    """Main entry point."""
    print(f"Scraping {URL}...")

    try:
        events = scrape_events()
    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        return

    print(f"Found {len(events)} events")

    output_dir = Path(__file__).parent / "scraped"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "mit_cis.json"
    with open(output_file, "w") as f:
        json.dump(events, f, indent=2)

    print(f"Wrote events to {output_file}")

    for event in events[:5]:
        print(f"  - {event.get('date')}: {event.get('speaker', 'TBA')} - {event.get('title', 'TBA')[:40]}")
    if len(events) > 5:
        print(f"  ... and {len(events) - 5} more")


if __name__ == "__main__":
    main()
