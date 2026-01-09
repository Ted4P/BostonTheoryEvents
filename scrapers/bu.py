#!/usr/bin/env python3
"""
Scraper for BU Algorithms and Theory Seminar.
Source: Google Calendar (iCal feed)
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

CALENDAR_ID = "hmaqnavg6bjvd84ib0qjk07hcg@group.calendar.google.com"
URL = f"https://calendar.google.com/calendar/ical/{CALENDAR_ID}/public/basic.ics"
SERIES_NAME = "BU Theory Seminar"
SERIES_URL = "https://www.bu.edu/cs/research-groups/theory/algorithms-and-theory-seminar/"


def fetch_ical() -> str:
    """Fetch the iCal feed."""
    headers = {
        "User-Agent": "BostonTheoryEvents/1.0 (academic seminar aggregator)"
    }
    response = requests.get(URL, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def parse_ical(ical_text: str) -> list:
    """Parse iCal format into list of events."""
    events = []

    # Split into events
    event_blocks = re.split(r"BEGIN:VEVENT", ical_text)[1:]  # Skip header

    for block in event_blocks:
        event = parse_event_block(block)
        if event and event.get("date"):
            events.append(event)

    return events


def parse_event_block(block: str) -> dict:
    """Parse a single VEVENT block."""
    event = {
        "series": SERIES_NAME,
        "series_url": SERIES_URL,
    }

    # Extract fields using regex
    # DTSTART
    dtstart_match = re.search(r"DTSTART[^:]*:(\d{8}T\d{6}Z?)", block)
    if dtstart_match:
        dt_str = dtstart_match.group(1)
        event["date"], event["time"] = parse_ical_datetime(dt_str)

    # SUMMARY (title + speaker usually)
    summary_match = re.search(r"SUMMARY:(.+?)(?:\r?\n(?! )|\Z)", block, re.DOTALL)
    if summary_match:
        summary = unfold_ical(summary_match.group(1))
        event["title"], event["speaker"] = parse_summary(summary)

    # LOCATION
    location_match = re.search(r"LOCATION:(.+?)(?:\r?\n(?! )|\Z)", block, re.DOTALL)
    if location_match:
        location = unfold_ical(location_match.group(1))
        if location and not location.lower().startswith("bu "):
            location = f"BU {location}"
        event["location"] = location

    # DESCRIPTION (may contain abstract and bio)
    desc_match = re.search(r"DESCRIPTION:(.+?)(?:\r?\n(?! )|\Z)", block, re.DOTALL)
    if desc_match:
        desc = unfold_ical(desc_match.group(1))
        # Don't store full description, just extract speaker if not found
        if not event.get("speaker"):
            bio_match = re.search(r"<b>Bio:</b>\s*<a[^>]*>([^<]+)</a>", desc)
            if bio_match:
                event["speaker"] = bio_match.group(1).strip()

    return event


def unfold_ical(text: str) -> str:
    """Unfold iCal line continuations and unescape."""
    # iCal folds long lines with \r\n followed by space
    text = re.sub(r"\r?\n ", "", text)
    # Unescape
    text = text.replace("\\n", "\n")
    text = text.replace("\\,", ",")
    text = text.replace("\\;", ";")
    text = text.replace("\\\\", "\\")
    return text.strip()


def parse_ical_datetime(dt_str: str) -> tuple:
    """Parse iCal datetime like '20240923T163000Z' to date and time."""
    # Remove trailing Z if present
    dt_str = dt_str.rstrip("Z")

    try:
        dt = datetime.strptime(dt_str, "%Y%m%dT%H%M%S")
        # Assume UTC, convert to Eastern
        # For simplicity, just subtract 5 hours (EST) or 4 (EDT)
        # In production, use proper timezone handling
        dt = dt.replace(tzinfo=timezone.utc)
        # Rough conversion to Eastern
        from datetime import timedelta
        dt = dt - timedelta(hours=5)

        return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
    except ValueError:
        return "", ""


def parse_summary(summary: str) -> tuple:
    """Parse summary into title and speaker."""
    # Common patterns:
    # "Speaker Name: Talk Title"
    # "Talk Title (Speaker Name)"
    # Just "Talk Title"

    summary = summary.strip()

    # Try "Speaker: Title" pattern
    if ":" in summary:
        parts = summary.split(":", 1)
        if len(parts) == 2:
            potential_speaker = parts[0].strip()
            potential_title = parts[1].strip()
            # Check if first part looks like a name (not too long, no special chars)
            if len(potential_speaker) < 50 and not any(c in potential_speaker for c in "()[]{}"):
                return potential_title, potential_speaker

    # Try "(Speaker)" at end pattern
    paren_match = re.search(r"^(.+?)\s*\(([^)]+)\)\s*$", summary)
    if paren_match:
        return paren_match.group(1).strip(), paren_match.group(2).strip()

    # Just return as title
    return summary, ""


def main():
    """Main entry point."""
    print(f"Scraping BU Theory Seminar...")

    try:
        ical_text = fetch_ical()
        events = parse_ical(ical_text)
    except requests.RequestException as e:
        print(f"Error fetching calendar: {e}")
        return

    # Filter to recent/upcoming events
    current_year = datetime.now().year
    events = [e for e in events if e.get("date") and int(e["date"][:4]) >= current_year - 2]

    # Sort by date
    events.sort(key=lambda e: e.get("date", ""))

    print(f"Found {len(events)} events")

    # Create output directory
    output_dir = Path(__file__).parent / "scraped"
    output_dir.mkdir(exist_ok=True)

    # Write output
    output_file = output_dir / "bu.json"
    with open(output_file, "w") as f:
        json.dump(events, f, indent=2)

    print(f"Wrote events to {output_file}")

    # Print summary
    for event in events[:5]:
        speaker = event.get("speaker", "")[:20] or "TBA"
        title = event.get("title", "TBA")[:35]
        print(f"  - {event.get('date')}: {speaker} - {title}")
    if len(events) > 5:
        print(f"  ... and {len(events) - 5} more")


if __name__ == "__main__":
    main()
