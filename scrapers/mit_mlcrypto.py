#!/usr/bin/env python3
"""
Scraper for ML+Cryptography seminars.
Source: https://mlcrypto.github.io/seminar/index.html
"""

import json
import re
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://mlcrypto.github.io/seminar/index.html"
SERIES_NAME = "ML+Cryptography Seminar"
SERIES_URL = "https://mlcrypto.github.io/seminar/index.html"
DEFAULT_LOCATION = "MIT"  # Location varies


def fetch_page(url: str) -> str:
    """Fetch the HTML content of the page."""
    headers = {
        "User-Agent": "BostonTheoryEvents/1.0 (academic seminar aggregator)"
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def parse_date(date_str: str) -> str | None:
    """Parse date string to ISO format."""
    date_str = date_str.strip()

    # Skip TBD dates
    if "TBD" in date_str.upper():
        return None

    # Try full date: "November 18, 2025"
    try:
        dt = datetime.strptime(date_str, "%B %d, %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # Try: "November 18th, 2025"
    date_str_clean = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_str)
    try:
        dt = datetime.strptime(date_str_clean, "%B %d, %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    return None


def parse_speaker(text: str) -> tuple[str, str]:
    """Parse speaker string like 'Name (Affiliation)' into components."""
    match = re.match(r"(.+?)\s*\((.+?)\)\s*$", text)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return text.strip(), ""


def scrape_events() -> list:
    """Scrape events from the ML+Crypto page."""
    html = fetch_page(URL)
    soup = BeautifulSoup(html, "html.parser")

    events = []
    current_year = datetime.now().year
    cutoff_year = current_year - 1

    for h3 in soup.find_all("h3"):
        title = h3.get_text(strip=True)
        if not title:
            continue

        event = {
            "series": SERIES_NAME,
            "series_url": SERIES_URL,
            "location": DEFAULT_LOCATION,
            "title": title,
        }

        # Get speaker and date from next siblings
        siblings = []
        for sib in h3.next_siblings:
            if hasattr(sib, "get_text"):
                text = sib.get_text(strip=True)
                if text:
                    siblings.append(text)
                    if len(siblings) >= 2:
                        break
            elif hasattr(sib, "name") and sib.name in ["h2", "h3"]:
                break

        if siblings:
            speaker, affiliation = parse_speaker(siblings[0])
            event["speaker"] = speaker
            if affiliation:
                event["affiliation"] = affiliation

        if len(siblings) >= 2:
            date = parse_date(siblings[1])
            if date:
                event["date"] = date
                # Only include recent events
                year = int(date[:4])
                if year >= cutoff_year:
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

    output_file = output_dir / "mit_mlcrypto.json"
    with open(output_file, "w") as f:
        json.dump(events, f, indent=2)

    print(f"Wrote events to {output_file}")

    for event in events[:5]:
        print(f"  - {event.get('date')}: {event.get('speaker', 'TBA')} - {event.get('title', 'TBA')[:40]}")
    if len(events) > 5:
        print(f"  ... and {len(events) - 5} more")


if __name__ == "__main__":
    main()
