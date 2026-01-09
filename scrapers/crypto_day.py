#!/usr/bin/env python3
"""
Scraper for Charles River Crypto Day.
Source: https://bostoncryptoday.wordpress.com/feed/ (RSS)
"""

import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests

RSS_URL = "https://bostoncryptoday.wordpress.com/feed/"
SERIES_NAME = "Charles River Crypto Day"
SERIES_URL = "https://bostoncryptoday.wordpress.com/"


def fetch_rss() -> str:
    """Fetch the RSS feed."""
    headers = {
        "User-Agent": "BostonTheoryEvents/1.0 (academic seminar aggregator)"
    }
    response = requests.get(RSS_URL, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def scrape_events() -> list:
    """Scrape all events from the RSS feed."""
    xml_text = fetch_rss()
    root = ET.fromstring(xml_text)

    events = []

    for item in root.findall(".//item"):
        event = parse_rss_item(item)
        if event and event.get("date"):
            events.append(event)

    return events


def parse_rss_item(item) -> dict:
    """Parse a single RSS item into an event."""
    title_elem = item.find("title")
    pub_date_elem = item.find("pubDate")
    link_elem = item.find("link")
    desc_elem = item.find("description")

    if title_elem is None or pub_date_elem is None:
        return {}

    title_text = title_elem.text or ""
    pub_date_text = pub_date_elem.text or ""

    # Parse the publication date to get the year
    try:
        pub_datetime = parsedate_to_datetime(pub_date_text)
    except (ValueError, TypeError):
        return {}

    # Extract event date from title: "Friday, November 14 at MIT"
    date_match = re.search(
        r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+"
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2})",
        title_text, re.I
    )

    if not date_match:
        return {}

    # Determine year: event is usually in the same year as pub date,
    # or the following year if pub is late in year and event is early
    event_date_str = date_match.group(1)
    event_month = parse_month(event_date_str)
    pub_month = pub_datetime.month

    if event_month >= pub_month:
        # Event is same year as publication
        event_year = pub_datetime.year
    else:
        # Event month is earlier than pub month - event is next year
        event_year = pub_datetime.year + 1

    date_str = parse_date(event_date_str, event_year)
    if not date_str:
        return {}

    # Extract location from title
    location_match = re.search(r"(?:at|@)\s+(.+)$", title_text, re.I)
    location = location_match.group(1).strip() if location_match else "TBD"

    # Parse description for more details
    description = ""
    if desc_elem is not None and desc_elem.text:
        description = desc_elem.text

    # Extract speakers from description
    speakers = extract_speakers(description)

    event = {
        "title": "Charles River Crypto Day",
        "date": date_str,
        "time": "09:30",
        "location": location,
        "series": SERIES_NAME,
        "series_url": SERIES_URL,
        "url": link_elem.text if link_elem is not None else SERIES_URL,
    }

    if speakers:
        event["speaker"] = ", ".join(speakers[:3])
        if len(speakers) > 3:
            event["speaker"] += f" + {len(speakers) - 3} more"

    return event


def parse_month(date_str: str) -> int:
    """Extract month number from date string."""
    month_str = date_str.split()[0][:3].lower()
    months = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
              "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
    return months.get(month_str, 1)


def parse_date(date_str: str, year: int) -> str:
    """Parse date string like 'November 14' to YYYY-MM-DD."""
    date_str = date_str.strip()

    # Expand abbreviated months
    abbrevs = {
        "Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April",
        "May": "May", "Jun": "June", "Jul": "July", "Aug": "August",
        "Sep": "September", "Oct": "October", "Nov": "November", "Dec": "December"
    }
    for abbr, full in abbrevs.items():
        date_str = re.sub(rf"\b{abbr}\.?\b", full, date_str)

    try:
        dt = datetime.strptime(f"{date_str} {year}", "%B %d %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return ""


def extract_speakers(description: str) -> list:
    """Extract speaker names from HTML description."""
    speakers = []

    # Pattern: "Name (Affiliation)"
    pattern = r"([A-Z][a-z]+ [A-Z][a-z]+(?:-[A-Z][a-z]+)?)\s*\(([^)]+)\)"
    matches = re.findall(pattern, description)

    for name, affiliation in matches:
        if name.lower() not in ["coffee welcome", "lunch break", "star room", "hewlett room"]:
            speakers.append(name)

    return speakers


def main():
    """Main entry point."""
    print(f"Scraping {RSS_URL}...")

    try:
        events = scrape_events()
    except requests.RequestException as e:
        print(f"Error fetching feed: {e}")
        return

    # Filter to recent events (last 2 years)
    current_year = datetime.now().year
    events = [e for e in events if e.get("date") and int(e["date"][:4]) >= current_year - 2]

    print(f"Found {len(events)} events")

    # Create output directory
    output_dir = Path(__file__).parent / "scraped"
    output_dir.mkdir(exist_ok=True)

    # Write output
    output_file = output_dir / "crypto_day.json"
    with open(output_file, "w") as f:
        json.dump(events, f, indent=2)

    print(f"Wrote events to {output_file}")

    # Print summary
    for event in events[:5]:
        print(f"  - {event.get('date')}: {event.get('title')} @ {event.get('location', 'TBD')[:30]}")


if __name__ == "__main__":
    main()
