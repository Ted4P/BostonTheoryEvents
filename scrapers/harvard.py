#!/usr/bin/env python3
"""
Scraper for Harvard Theory of Computation Seminar.
Source: Google Doc linked from https://toc.seas.harvard.edu/toc-seminar
"""

import json
import re
from datetime import datetime
from pathlib import Path

import requests

# Google Doc export URL (plain text format)
DOC_ID = "1qBfsiK-NNe_dMIsShMSiJe5_Qsc2tmYJMSVzbsMw0RI"
URL = f"https://docs.google.com/document/d/{DOC_ID}/export?format=txt"
SERIES_NAME = "Harvard Theory Seminar"
SERIES_URL = "https://toc.seas.harvard.edu/toc-seminar"


def fetch_doc() -> str:
    """Fetch the Google Doc as plain text."""
    headers = {
        "User-Agent": "BostonTheoryEvents/1.0 (academic seminar aggregator)"
    }
    response = requests.get(URL, headers=headers, timeout=30, allow_redirects=True)
    response.raise_for_status()
    return response.text


def parse_date(date_str: str) -> str:
    """Parse date string like 'September 13, 2024' to YYYY-MM-DD."""
    date_str = date_str.strip()

    try:
        dt = datetime.strptime(date_str, "%B %d, %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # Try alternate format without comma
    try:
        dt = datetime.strptime(date_str, "%B %d %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    return ""


def parse_time(time_str: str) -> str:
    """Parse time string like '3:45–5:00 p.m.' to start time HH:MM."""
    time_str = time_str.strip().lower()

    # Extract start time
    match = re.search(r"(\d{1,2}):(\d{2})", time_str)
    if match:
        hour, minute = int(match.group(1)), match.group(2)

        # Check for PM
        if "p.m" in time_str or "pm" in time_str:
            if hour != 12:
                hour += 12
        elif "a.m" in time_str or "am" in time_str:
            if hour == 12:
                hour = 0

        return f"{hour:02d}:{minute}"

    return ""


def scrape_events() -> list:
    """Scrape all events from the Harvard Google Doc."""
    text = fetch_doc()
    events = []

    # Split by date pattern (e.g., "September 13, 2024")
    date_pattern = r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})"

    # Find all dates and their positions
    matches = list(re.finditer(date_pattern, text))

    for i, match in enumerate(matches):
        date_str = match.group(1)
        start_pos = match.end()

        # Get text until next date (or end of document)
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(text)

        event_text = text[start_pos:end_pos]
        event = parse_event_block(event_text, date_str)

        if event and event.get("date"):
            events.append(event)

    return events


def parse_event_block(text: str, date_str: str) -> dict:
    """Parse a single event block."""
    event = {
        "series": SERIES_NAME,
        "series_url": SERIES_URL,
        "date": parse_date(date_str),
    }

    lines = text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Speaker line: "Speaker: Name (Affiliation)" or "Speakers: ..."
        if line.lower().startswith("speaker"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                speaker_info = parts[1].strip()
                # Extract affiliation from parentheses
                affil_match = re.search(r"\(([^)]+)\)", speaker_info)
                if affil_match:
                    event["affiliation"] = affil_match.group(1)
                    event["speaker"] = speaker_info[:affil_match.start()].strip()
                else:
                    event["speaker"] = speaker_info

        # Title line: "Title: "..." or just the title in quotes
        elif line.lower().startswith("title"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                title = parts[1].strip().strip('"').strip("'")
                event["title"] = title

        # Time line: "Time: 3:45–5:00 p.m."
        elif line.lower().startswith("time"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                event["time"] = parse_time(parts[1])

        # Location line: "Location: SEC 3.301–3.303"
        elif line.lower().startswith("location"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                location = parts[1].strip()
                if location and not location.lower().startswith("harvard"):
                    location = f"Harvard {location}"
                event["location"] = location

    # If no title found, mark as TBA
    if not event.get("title"):
        event["title"] = "TBA"

    return event


def main():
    """Main entry point."""
    print(f"Scraping Harvard TOC Seminar...")

    try:
        events = scrape_events()
    except requests.RequestException as e:
        print(f"Error fetching document: {e}")
        return

    # Filter to recent/upcoming events (last 2 years + future)
    current_year = datetime.now().year
    events = [e for e in events if e.get("date") and int(e["date"][:4]) >= current_year - 2]

    print(f"Found {len(events)} events")

    # Create output directory
    output_dir = Path(__file__).parent / "scraped"
    output_dir.mkdir(exist_ok=True)

    # Write output
    output_file = output_dir / "harvard.json"
    with open(output_file, "w") as f:
        json.dump(events, f, indent=2)

    print(f"Wrote events to {output_file}")

    # Print summary
    for event in events[:5]:
        print(f"  - {event.get('date')}: {event.get('speaker', 'TBA')[:30]} - {event.get('title', 'TBA')[:30]}")
    if len(events) > 5:
        print(f"  ... and {len(events) - 5} more")


if __name__ == "__main__":
    main()
