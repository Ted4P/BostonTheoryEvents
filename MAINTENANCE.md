# Scraper Maintenance Guide

This document provides instructions for an AI agent or developer tasked with maintaining the Boston Theory Events scrapers.

## Permissions and Restrictions

### ALLOWED Actions
- Modify scraper files in `scrapers/` directory:
  - `mit_toc.py`
  - `northeastern.py`
  - `harvard.py`
  - `bu.py`
  - `crypto_day.py`
  - `combine.py`
- Add new scraper files for additional seminar sources
- Update `scrapers/requirements.txt` if new dependencies are needed
- Add events to `manual/events.yaml` for events that can't be scraped
- Update this maintenance document

### FORBIDDEN Actions
- DO NOT modify website display files:
  - `index.html`
  - `style.css`
  - `script.js`
- DO NOT change the event data schema (fields in events.json)
- DO NOT modify GitHub Actions workflow without explicit approval
- DO NOT remove existing scrapers without approval

## Validation Procedure

Run this checklist periodically (weekly recommended) to verify scrapers are working:

### 1. Run All Scrapers
```bash
cd /path/to/BostonTheory
python scrapers/mit_toc.py
python scrapers/northeastern.py
python scrapers/harvard.py
python scrapers/bu.py
python scrapers/crypto_day.py
python scrapers/combine.py
```

### 2. Check for Errors
Each scraper should:
- Print "Found N events" where N > 0
- Not throw any exceptions
- Create/update a JSON file in `scrapers/scraped/`

### 3. Validate Event Quality
For each scraper output, verify:
- [ ] Dates are reasonable (within last year to next year)
- [ ] Titles are not empty or generic placeholders
- [ ] Speaker names look like real names (not HTML artifacts)
- [ ] Locations make sense (university names, room numbers)

### 4. Cross-Reference with Source
Manually visit each source URL and compare:
- MIT: https://www.csail.mit.edu/taxonomy/term/443
- Northeastern: https://theory.khoury.northeastern.edu/seminar.html
- Harvard: https://toc.seas.harvard.edu/toc-seminar (check linked Google Doc)
- BU: https://www.bu.edu/cs/research-groups/theory/algorithms-and-theory-seminar/
- Crypto Day: https://bostoncryptoday.wordpress.com/

## Common Issues and Fixes

### Scraper Returns 0 Events
**Likely cause:** Website structure changed
**Fix approach:**
1. Fetch the source page manually: `curl -s [URL] | head -200`
2. Identify new HTML structure/class names
3. Update CSS selectors in the scraper
4. Test with `python scrapers/[name].py`

### Wrong Dates/Years
**Likely cause:** Date parsing logic doesn't match new format
**Fix approach:**
1. Print raw date strings from the page
2. Adjust regex patterns in `parse_date()` functions
3. For Crypto Day specifically, year estimation is approximate

### Missing Fields (speaker, location, etc.)
**Likely cause:** HTML selectors outdated
**Fix approach:**
1. Inspect page HTML for the field's current location
2. Update the appropriate `select_one()` or `find()` call

### HTTP Errors (403, 404, etc.)
**Likely cause:** URL changed or access blocked
**Fix approach:**
1. Verify URL is still valid in browser
2. Check if User-Agent header needs updating
3. For calendar feeds (BU), verify calendar is still public

## Event Data Schema

Each event in `events.json` should have:
```json
{
  "title": "Talk Title",           // REQUIRED
  "date": "YYYY-MM-DD",            // REQUIRED
  "time": "HH:MM",                 // Optional, 24-hour format
  "speaker": "Speaker Name",       // Optional
  "affiliation": "University",     // Optional
  "location": "Room/Building",     // Optional
  "series": "Seminar Series Name", // Optional
  "series_url": "https://...",     // Optional, link to series homepage
  "url": "https://..."             // Optional, link to specific event
}
```

## Adding a New Scraper

1. Create `scrapers/[source_name].py` following existing patterns
2. Define constants: `URL`, `SERIES_NAME`, `SERIES_URL`
3. Implement `scrape_events()` returning list of event dicts
4. Output to `scrapers/scraped/[source_name].json`
5. Test: `python scrapers/[source_name].py`
6. Update `combine.py` if needed (it auto-discovers JSON files)

## Manual Event Entry

For events that can't be scraped (one-off workshops, etc.):

Edit `manual/events.yaml`:
```yaml
events:
  - title: "Workshop on XYZ"
    speaker: "Multiple speakers"
    date: "2025-03-15"
    time: "09:00"
    location: "MIT Building 32"
    series: "Special Event"
    url: "https://..."
```

Then run: `python scrapers/combine.py`

## Scraper-Specific Notes

### MIT TOC (`mit_toc.py`)
- Source: CSAIL events page with `.event-card` elements
- Date/time from `.atc_date_start` (add-to-calendar data)
- Usually well-structured, rarely changes

### Northeastern (`northeastern.py`)
- Source: Static HTML with `<table class="schedule">`
- Events organized by semester (`<h2>Spring, 2025</h2>`)
- Custom `<talktitle>` tags for titles

### Harvard (`harvard.py`)
- Source: Google Doc export (plain text)
- Pattern: Date line, then Speaker/Title/Time/Location lines
- Doc may be updated for new semesters - check if URL changes

### BU (`bu.py`)
- Source: Google Calendar iCal feed
- Calendar ID: `hmaqnavg6bjvd84ib0qjk07hcg@group.calendar.google.com`
- Speaker/title parsing from SUMMARY field is imperfect

### Crypto Day (`crypto_day.py`)
- Source: WordPress RSS feed (`/feed/`)
- Year derived from RSS `<pubDate>` field (reliable)
- Events ~4 times per year

## Contact

If scrapers fail persistently and you cannot fix them, flag the issue for human review.
