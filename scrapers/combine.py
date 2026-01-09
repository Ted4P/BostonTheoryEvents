#!/usr/bin/env python3
"""
Combine events from all sources (scrapers + manual) into events.json
"""

import json
import glob
import os
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    print("Warning: PyYAML not installed. Manual events won't be loaded.")
    print("Install with: pip install pyyaml")


def load_scraped_events(scrapers_dir: Path) -> list:
    """Load all JSON files from scraped/ subdirectory."""
    events = []
    scraped_dir = scrapers_dir / "scraped"

    if not scraped_dir.exists():
        return events

    for json_file in scraped_dir.glob("*.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)
                if isinstance(data, list):
                    events.extend(data)
                else:
                    print(f"Warning: {json_file} is not a list, skipping")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load {json_file}: {e}")

    return events


def load_manual_events(manual_dir: Path) -> list:
    """Load events from manual/events.yaml."""
    if not HAS_YAML:
        return []

    events = []
    yaml_file = manual_dir / "events.yaml"

    if not yaml_file.exists():
        return events

    try:
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
            if data and "events" in data and isinstance(data["events"], list):
                events.extend(data["events"])
    except (yaml.YAMLError, IOError) as e:
        print(f"Warning: Failed to load {yaml_file}: {e}")

    return events


def validate_event(event: dict) -> bool:
    """Check if event has required fields."""
    required = ["title", "date"]
    return all(event.get(field) for field in required)


def deduplicate_events(events: list) -> list:
    """Remove duplicate events based on title + date."""
    seen = set()
    unique = []

    for event in events:
        key = (event.get("title", ""), event.get("date", ""))
        if key not in seen:
            seen.add(key)
            unique.append(event)

    return unique


def main():
    # Determine paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    manual_dir = project_root / "manual"
    output_file = project_root / "events.json"

    # Collect events
    all_events = []

    # Load scraped events
    scraped = load_scraped_events(script_dir)
    print(f"Loaded {len(scraped)} scraped events")
    all_events.extend(scraped)

    # Load manual events
    manual = load_manual_events(manual_dir)
    print(f"Loaded {len(manual)} manual events")
    all_events.extend(manual)

    # Filter and deduplicate
    valid_events = [e for e in all_events if validate_event(e)]
    if len(valid_events) < len(all_events):
        print(f"Warning: Filtered out {len(all_events) - len(valid_events)} invalid events")

    unique_events = deduplicate_events(valid_events)
    if len(unique_events) < len(valid_events):
        print(f"Removed {len(valid_events) - len(unique_events)} duplicate events")

    # Sort by date
    unique_events.sort(key=lambda e: e.get("date", ""))

    # Write output
    with open(output_file, "w") as f:
        json.dump(unique_events, f, indent=2)

    print(f"Wrote {len(unique_events)} events to {output_file}")


if __name__ == "__main__":
    main()
