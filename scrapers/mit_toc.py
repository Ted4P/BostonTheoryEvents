#!/usr/bin/env python3
"""
Scraper for MIT CSAIL Theory of Computation seminars.
Source: https://www.csail.mit.edu/taxonomy/term/443
"""

import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://www.csail.mit.edu/taxonomy/term/443"
SERIES_NAME = "MIT Theory of Computation"
SERIES_URL = "https://www.csail.mit.edu/taxonomy/term/443"
DEFAULT_LOCATION = "MIT 32-G449"


def fetch_page(url: str) -> str:
    """Fetch the HTML content of the page."""
    headers = {
        "User-Agent": "BostonTheoryEvents/1.0 (academic seminar aggregator)"
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def scrape_events() -> list:
    """Scrape all events from the MIT TOC page."""
    html = fetch_page(URL)
    soup = BeautifulSoup(html, "html.parser")

    events = []

    # Find all event cards
    for card in soup.select(".event-card"):
        event = parse_event_card(card)
        if event and event.get("title") and event.get("date"):
            events.append(event)

    return events


def parse_event_card(card) -> dict:
    """Parse a single event card element."""
    event = {
        "series": SERIES_NAME,
        "series_url": SERIES_URL,
        "location": DEFAULT_LOCATION,
    }

    # Title and URL from title-link
    title_link = card.select_one(".title-link")
    if title_link:
        href = title_link.get("href", "")
        if href.startswith("/"):
            event["url"] = "https://www.csail.mit.edu" + href
        else:
            event["url"] = href

    title_elem = card.select_one(".event-title")
    if title_elem:
        event["title"] = title_elem.get_text(strip=True)

    # Speaker name
    speaker_elem = card.select_one(".field--name-field-speaker-name")
    if speaker_elem:
        event["speaker"] = speaker_elem.get_text(strip=True)

    # Speaker affiliation
    affil_elem = card.select_one(".field--name-field-speaker-affiliation")
    if affil_elem:
        event["affiliation"] = affil_elem.get_text(strip=True)

    # Date and time from add-to-calendar data
    atc_date = card.select_one(".atc_date_start")
    if atc_date:
        # Format: "2026-03-17 16:15:00"
        datetime_str = atc_date.get_text(strip=True)
        if " " in datetime_str:
            date_part, time_part = datetime_str.split(" ", 1)
            event["date"] = date_part
            # Convert "16:15:00" to "16:15"
            event["time"] = time_part[:5]
        else:
            event["date"] = datetime_str[:10]

    # Location from room-popup link (more reliable than atc_location)
    room_elem = card.select_one(".room-popup")
    if room_elem:
        room_text = room_elem.get_text(strip=True)
        if room_text:
            event["location"] = f"MIT {room_text}"

    return event


def main():
    """Main entry point."""
    print(f"Scraping {URL}...")

    try:
        events = scrape_events()
    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        return

    print(f"Found {len(events)} events")

    # Create output directory
    output_dir = Path(__file__).parent / "scraped"
    output_dir.mkdir(exist_ok=True)

    # Write output
    output_file = output_dir / "mit_toc.json"
    with open(output_file, "w") as f:
        json.dump(events, f, indent=2)

    print(f"Wrote events to {output_file}")

    # Print summary
    for event in events[:5]:
        print(f"  - {event.get('date')}: {event.get('speaker', 'TBA')} - {event.get('title', 'TBA')[:40]}")
    if len(events) > 5:
        print(f"  ... and {len(events) - 5} more")


if __name__ == "__main__":
    main()
