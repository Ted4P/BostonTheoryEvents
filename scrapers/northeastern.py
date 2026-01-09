#!/usr/bin/env python3
"""
Scraper for Northeastern CS Theory Seminar.
Source: https://theory.khoury.northeastern.edu/seminar.html
"""

import json
import re
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://theory.khoury.northeastern.edu/seminar.html"
SERIES_NAME = "Northeastern Theory Seminar"
SERIES_URL = "https://theory.khoury.northeastern.edu/seminar.html"


def fetch_page(url: str) -> str:
    """Fetch the HTML content of the page."""
    headers = {
        "User-Agent": "BostonTheoryEvents/1.0 (academic seminar aggregator)"
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def parse_date(date_str: str, year: int) -> str:
    """Parse date string like 'Apr 30' with year to YYYY-MM-DD."""
    date_str = date_str.strip()

    # Handle various month formats
    month_map = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
    }

    match = re.match(r"(\w+)\s+(\d{1,2})", date_str)
    if match:
        month_str, day = match.groups()
        month = month_map.get(month_str[:3])
        if month:
            return f"{year}-{month:02d}-{int(day):02d}"

    return ""


def parse_time(time_str: str) -> str:
    """Parse time string like '12:00 pm' to HH:MM."""
    time_str = time_str.strip().lower()

    match = re.match(r"(\d{1,2}):(\d{2})\s*(am|pm)?", time_str)
    if match:
        hour, minute, ampm = match.groups()
        hour = int(hour)
        if ampm == "pm" and hour != 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute}"

    return ""


def get_semester_year(semester_text: str) -> tuple:
    """Extract semester and year from text like 'Spring 2025'."""
    match = re.search(r"(Spring|Fall)\s*,?\s*(\d{4})", semester_text, re.I)
    if match:
        semester, year = match.groups()
        return semester.capitalize(), int(year)
    return None, None


def scrape_events() -> list:
    """Scrape all events from the Northeastern page."""
    html = fetch_page(URL)
    soup = BeautifulSoup(html, "html.parser")

    events = []
    current_year = datetime.now().year

    # Find all semester sections
    for h2 in soup.find_all("h2"):
        semester, year = get_semester_year(h2.get_text())
        if not year:
            continue

        # Only scrape recent semesters (current year and next)
        if year < current_year - 1:
            continue

        # Find the corresponding content div
        div_id = h2.get_text().replace(" ", "").replace(",", "")
        content_div = soup.find("div", id=re.compile(div_id, re.I))

        if not content_div:
            # Try finding next sibling div
            content_div = h2.find_next_sibling("div")

        if content_div:
            table = content_div.find("table", class_="schedule")
            if table:
                events.extend(parse_semester_table(table, year, semester))

    return events


def parse_semester_table(table, year: int, semester: str) -> list:
    """Parse events from a semester's schedule table."""
    events = []

    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        event = parse_event_row(cells, year)
        if event and event.get("title") and event.get("date"):
            events.append(event)

    return events


def parse_event_row(cells, year: int) -> dict:
    """Parse a single event row."""
    event = {
        "series": SERIES_NAME,
        "series_url": SERIES_URL,
    }

    # First cell: date, time, location (each in <strong> tags)
    meta_cell = cells[0]
    strong_tags = meta_cell.find_all("strong")

    if len(strong_tags) >= 1:
        event["date"] = parse_date(strong_tags[0].get_text(), year)
    if len(strong_tags) >= 2:
        event["time"] = parse_time(strong_tags[1].get_text())
    if len(strong_tags) >= 3:
        location = strong_tags[2].get_text(strip=True)
        if location:
            event["location"] = f"Northeastern {location}"

    # Second cell: speaker, title
    content_cell = cells[1]

    # Speaker is usually first <strong> tag
    speaker_tag = content_cell.find("strong")
    if speaker_tag:
        # Check if it's not a title or abstract link
        text = speaker_tag.get_text(strip=True)
        if not text.startswith("Abstract") and not speaker_tag.find("talktitle"):
            event["speaker"] = text

    # Title is in <talktitle> tag
    title_tag = content_cell.find("talktitle")
    if title_tag:
        event["title"] = title_tag.get_text(strip=True)
    else:
        # Sometimes title is just in a strong tag after speaker
        for strong in content_cell.find_all("strong"):
            text = strong.get_text(strip=True)
            if text and text != event.get("speaker") and not text.startswith("Abstract"):
                if not event.get("title"):
                    event["title"] = text
                    break

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
    output_file = output_dir / "northeastern.json"
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
