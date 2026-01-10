#!/usr/bin/env python3
"""
Scraper for MIT CSAIL Algorithms & Complexity seminars.
Source: https://www.csail.mit.edu/taxonomy/term/445
Uses same structure as TOC scraper (CSAIL events page).
"""

import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://www.csail.mit.edu/taxonomy/term/445"
SERIES_NAME = "MIT Algorithms & Complexity"
SERIES_URL = "https://www.csail.mit.edu/taxonomy/term/445"
DEFAULT_LOCATION = "MIT 32-G575"


def fetch_page(url: str) -> str:
    """Fetch the HTML content of the page."""
    headers = {
        "User-Agent": "BostonTheoryEvents/1.0 (academic seminar aggregator)"
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def scrape_events() -> list:
    """Scrape all events from the MIT A&C page."""
    html = fetch_page(URL)
    soup = BeautifulSoup(html, "html.parser")

    events = []

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
        datetime_str = atc_date.get_text(strip=True)
        if " " in datetime_str:
            date_part, time_part = datetime_str.split(" ", 1)
            event["date"] = date_part
            event["time"] = time_part[:5]
        else:
            event["date"] = datetime_str[:10]

    # Location (may override default)
    loc_elem = card.select_one(".atc_location")
    if loc_elem:
        loc_text = loc_elem.get_text(strip=True)
        if loc_text and loc_text != "TBD":
            event["location"] = loc_text

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

    output_dir = Path(__file__).parent / "scraped"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "mit_ac.json"
    with open(output_file, "w") as f:
        json.dump(events, f, indent=2)

    print(f"Wrote events to {output_file}")

    for event in events[:5]:
        print(f"  - {event.get('date')}: {event.get('speaker', 'TBA')} - {event.get('title', 'TBA')[:40]}")
    if len(events) > 5:
        print(f"  ... and {len(events) - 5} more")


if __name__ == "__main__":
    main()
