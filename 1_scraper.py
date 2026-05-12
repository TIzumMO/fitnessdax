import os
import re
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

# -----------------------------
# Config
# -----------------------------

B2RUN_CITY_SLUGS = [
    "aachen",
    "berlin",
    "bremen",
    "dillingen",
    "dortmund",
    "duesseldorf",
    "frankfurt",
    "freiburg",
    "gelsenkirchen",
    "hamburg",
    "hannover",
    "kaiserslautern",
    "karlsruhe",
    "koblenz",
    "koeln",
    "muenchen",
    "nuernberg",
    "stuttgart",
]

YEARS = [2025, 2024, 2023]

MANUAL_EVENTS = [
    {
        "city": "aachen",
        "year": 2025,
        "competition_id": "4286",
        "distance_km": 5,
        "source_url": "https://b2run-iframe.maxfunsports.com/event/competition?id=4286&lang=de",
        "event_url": "manual",
    },
    {
        "city": "aachen",
        "year": 2024,
        "competition_id": "4013",
        "distance_km": 5,
        "source_url": "https://b2run-iframe.maxfunsports.com/event/competition?id=4013&lang=de",
        "event_url": "manual",
    },
    {
        "city": "berlin",
        "year": 2024,
        "competition_id": "4220",
        "distance_km": 5.7,
        "source_url": "https://b2run-iframe.maxfunsports.com/event/competition?id=4220&lang=de",
        "event_url": "manual",
    },
    {
        "city": "berlin",
        "year": 2025,
        "competition_id": "4391",
        "distance_km": 5.7,
        "source_url": "https://b2run-iframe.maxfunsports.com/event/competition?id=4391&lang=de",
        "event_url": "manual",
    },
    {
        "city": "berlin",
        "year": 2023,
        "competition_id": "4073",
        "distance_km": 5.7,
        "source_url": "https://b2run-iframe.maxfunsports.com/event/competition?id=4073&lang=de",
        "event_url": "manual",
    },
    {
        "city": "bremen",
        "year": 2024,
        "competition_id": "4055",
        "distance_km": 6,
        "source_url": "https://b2run-iframe.maxfunsports.com/event/competition?id=4055&lang=de",
        "event_url": "manual",
    },
    {
        "city": "dormund",
        "year": 2024,
        "competition_id": "4102",
        "distance_km": 5.9,
        "source_url": "https://b2run-iframe.maxfunsports.com/event/competition?id=4102&lang=de",
        "event_url": "manual",
    },
    {
        "city": "duesseldorf",
        "year": 2024,
        "competition_id": "4201",
        "distance_km": 6,
        "source_url": "https://b2run-iframe.maxfunsports.com/event/competition?id=4201&lang=de",
        "event_url": "manual",
    },
    {
        "city": "duesseldorf",
        "year": 2024,
        "competition_id": "4201",
        "distance_km": 6,
        "source_url": "https://b2run-iframe.maxfunsports.com/event/competition?id=4201&lang=de",
        "event_url": "manual",
    },
    {
        "city": "freiburg",
        "year": 2024,
        "competition_id": "4175",
        "distance_km": 5,
        "source_url": "https://b2run-iframe.maxfunsports.com/event/competition?id=4175&lang=de",
        "event_url": "manual",
    },
    {
        "city": "freiburg",
        "year": 2024,
        "competition_id": "4207",
        "distance_km": 6.5,
        "source_url": "https://b2run-iframe.maxfunsports.com/event/competition?id=4207&lang=de",
        "event_url": "manual",
    },
    {
        "city": "kaiserslautern",
        "year": 2024,
        "competition_id": "4125",
        "distance_km": 5,
        "source_url": "https://b2run-iframe.maxfunsports.com/event/competition?id=4125&lang=de",
        "event_url": "manual",
    },
    {
        "city": "koblenz",
        "year": 2024,
        "competition_id": "4132",
        "distance_km": 5,
        "source_url": "https://b2run-iframe.maxfunsports.com/event/competition?id=4132&lang=de",
        "event_url": "manual",
    },
    {
        "city": "stuttgart",
        "year": 2024,
        "competition_id": "4156",
        "distance_km": 5,
        "source_url": "https://b2run-iframe.maxfunsports.com/event/competition?id=4156&lang=de",
        "event_url": "manual",
    },
    {
        "city": "stuttgart",
        "year": 2024,
        "competition_id": "4156",
        "distance_km": 5,
        "source_url": "https://b2run-iframe.maxfunsports.com/event/competition?id=4156&lang=de",
        "event_url": "manual",
    },
    {
        "city": "karlsruhe",
        "year": 2025,
        "competition_id": "4292",
        "distance_km": 5.5,
        "source_url": "https://b2run-iframe.maxfunsports.com/event/competition?id=4292&lang=de",
        "event_url": "manual",
    },
    {
        "city": "karlsruhe",
        "year": 2024,
        "competition_id": "4187",
        "distance_km": 5.5,
        "source_url": "https://b2run-iframe.maxfunsports.com/event/competition?id=4187&lang=de",
        "event_url": "manual",
    },
]

# Important:
# B2Run distances vary roughly between 5 and 6 km.
# Add exact distances here as we verify them.
DISTANCE_BY_CITY = {
    "aachen": 5,
    "berlin": 5.7,
    "bremen": 6,
    "dillingen": 5.3,
    "dortmund": 5.9,
    "duesseldorf": 6,
    "frankfurt": 5.6,
    "freiburg": 5,
    "gelsenkirchen": 5,
    "hamburg": 5,
    "hannover": 6.5,
    "kaiserslautern": 5,
    "karlsruhe": 5.3,
    "koblenz": 5,
    "koeln": 5,
    "muenchen": 5.7,
    "nuernberg": 6.1,
    "stuttgart": 5
}

DEFAULT_DISTANCE_KM = 5.4

REQUEST_DELAY_SECONDS = 0.5
MAX_PAGES_PER_EVENT = 1200

os.makedirs("html", exist_ok=True)
os.makedirs("data", exist_ok=True)

HEADERS = {
    "User-Agent": "FitnessDAX research scraper; personal project; respectful request rate"
}

# -----------------------------
# Helpers
# -----------------------------

def get_html(url):
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text

def extract_id_from_url(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if "id" in query:
        return query["id"][0]
    return None

def time_to_seconds(t):
    """
    Supports:
    00:18:56.4
    00:18:56
    """
    if not isinstance(t, str):
        return None

    t = t.strip()

    match = re.match(r"^(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?$", t)
    if not match:
        return None

    h, m, s, decimal = match.groups()
    seconds = int(h) * 3600 + int(m) * 60 + int(s)

    if decimal:
        seconds += float("0." + decimal)

    return seconds

def clean_text(text):
    return " ".join(str(text).split())

# -----------------------------
# Step 1: Discover all events
# -----------------------------

def discover_events():
    discovered = []

    for slug in B2RUN_CITY_SLUGS:
        main_url = f"https://www.b2run.de/run/de/de/{slug}/ergebnisse/index.html"

        try:
            html = get_html(main_url)
        except Exception as e:
            print(f"Could not open {slug}: {e}")
            continue

        soup = BeautifulSoup(html, "html.parser")

        year_pages = []

        # 1) Add main page for current year
        year_pages.append((2025, main_url))

        # 2) Find historical year pages
        for a in soup.find_all("a", href=True):
            label = clean_text(a.get_text(" ", strip=True))

            for year in YEARS:
                if f"Ergebnisse {year}" in label:
                    year_url = urljoin(main_url, a["href"])
                    year_pages.append((year, year_url))

        # Deduplicate
        year_pages = list(dict.fromkeys(year_pages))

        for year, year_page_url in year_pages:
            if year not in YEARS:
                continue

            try:
                year_html = get_html(year_page_url)
            except Exception as e:
                print(f"Could not open {slug} {year}: {e}")
                continue

            year_soup = BeautifulSoup(year_html, "html.parser")

            event_url = None

            for a in year_soup.find_all("a", href=True):
                href = a["href"]

                if "b2run-iframe.maxfunsports.com/event/view" in href:
                    event_url = urljoin(year_page_url, href)
                    break

            if not event_url:
                print(f"No MaxFunSports event link found for {slug} {year}")
                continue

            try:
                event_html = get_html(event_url)
            except Exception as e:
                print(f"Could not open event page for {slug} {year}: {e}")
                continue

            event_soup = BeautifulSoup(event_html, "html.parser")

            competition_url = None

            for a in event_soup.find_all("a", href=True):
                link_text = clean_text(a.get_text(" ", strip=True)).lower()
                href = a["href"]

                if link_text == "einzelwertung" and "/event/competition" in href:
                    competition_url = urljoin(event_url, href)
                    competition_url = competition_url.split("&ResultSearch")[0]
                    break

            if not competition_url:
                print(f"No Einzelwertung link found for {slug} {year}")
                continue

            competition_id = extract_id_from_url(competition_url)

            # Validate that the competition page really belongs to the target year
            try:
                competition_html = get_html(competition_url)
                competition_soup = BeautifulSoup(competition_html, "html.parser")
                competition_text = clean_text(competition_soup.get_text(" ", strip=True))

                if str(year) not in competition_text:
                    print(
                        f"Skipping {slug} {year}: competition_id={competition_id} "
                        f"does not seem to belong to {year}"
                    )
                    continue

            except Exception as e:
                print(f"Could not validate competition page for {slug} {year}: {e}")
                continue

            distance_km = DISTANCE_BY_CITY.get(slug, DEFAULT_DISTANCE_KM)

            discovered.append(
                {
                    "city": slug,
                    "year": year,
                    "competition_id": competition_id,
                    "distance_km": distance_km,
                    "source_url": competition_url,
                    "event_url": event_url,
                }
            )

            print(
                f"Discovered {slug} {year}: "
                f"competition_id={competition_id}, distance={distance_km} km"
            )

            time.sleep(REQUEST_DELAY_SECONDS)

    return discovered

# -----------------------------
# Step 2: Parse competition pages
# -----------------------------

def parse_table_rows(html, event, page):
    soup = BeautifulSoup(html, "html.parser")
    rows = []

    table_rows = soup.find_all("tr")

    for tr in table_rows:
        cells = [clean_text(td.get_text(" ", strip=True)) for td in tr.find_all(["td", "th"])]

        # Expected:
        # Pos | Stnr | Vorname | Nachname | Team | Kategorie | Bruttozeit | Nettozeit
        if len(cells) < 8:
            continue

        if cells[0].lower().startswith("pos"):
            continue

        pos = cells[0].replace(".", "").strip()

        if not pos.isdigit():
            continue

        row = {
            "city": event["city"],
            "year": event["year"],
            "competition_id": event["competition_id"],
            "page": page,
            "source_url": event["source_url"],
            "event_url": event["event_url"],
            "distance_km": event["distance_km"],

            "pos": pos,
            "stnr": cells[1],
            "first_name": cells[2],
            "last_name": cells[3],
            "company": cells[4],
            "category": cells[5],
            "gross_time": cells[6],
            "time": cells[7],
        }

        row["time_seconds"] = time_to_seconds(row["time"])

        if row["time_seconds"] is not None and event["distance_km"]:
            row["pace_min_per_km"] = row["time_seconds"] / 60 / event["distance_km"]
        else:
            row["pace_min_per_km"] = None

        rows.append(row)

    return rows

def scrape_event(event):
    all_rows = []
    seen_first_runner = set()

    for page in range(1, MAX_PAGES_PER_EVENT + 1):
        separator = "&" if "?" in event["source_url"] else "?"
        url = f"{event['source_url']}{separator}page={page}&per-page=50"

        try:
            html = get_html(url)
        except Exception as e:
            print(f"Error scraping {event['city']} page {page}: {e}")
            break

        html_file = f"html/{event['city']}_{event['year']}_competition_{event['competition_id']}_page_{page}.html"

        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)

        rows = parse_table_rows(html, event, page)

        if not rows:
            print(f"No rows found for {event['city']} page {page}. Stopping event.")
            break
 
        # detect repeated pages
        first_runner_key = (
            rows[0]["first_name"],
            rows[0]["last_name"],
            rows[0]["time"]
        )

        if first_runner_key in seen_first_runner:
            print(f"Detected repeated page for {event['city']} page {page}. Stopping event.")
            break

        seen_first_runner.add(first_runner_key)

        if not rows:
            print(f"No rows found for {event['city']} page {page}. Stopping event.")
            break

        all_rows.extend(rows)

        print(f"Scraped {event['city']} page {page}: {len(rows)} runners")

        time.sleep(REQUEST_DELAY_SECONDS)

    return all_rows

# -----------------------------
# Run full pipeline step 1
# -----------------------------

events = discover_events()

# Add manual events that discovery missed
existing_keys = {
    (str(e["city"]), int(e["year"]), str(e["competition_id"]))
    for e in events
}

for manual_event in MANUAL_EVENTS:
    key = (
        str(manual_event["city"]),
        int(manual_event["year"]),
        str(manual_event["competition_id"])
    )

    if key not in existing_keys:
        events.append(manual_event)

        print(
            f"Added manual event "
            f"{manual_event['city']} "
            f"{manual_event['year']} "
            f"(competition_id={manual_event['competition_id']})"
        )

events_df = pd.DataFrame(events)
events_df.to_csv("data/discovered_events_all_years.csv", index=False)

print("")
print(f"Discovered {len(events)} events.")
print("Saved discovered events to data/discovered_events_all_years.csv")
print("")

all_results = []

for event in events:
    all_results.extend(scrape_event(event))

df = pd.DataFrame(all_results)
df.to_csv("data/b2run_results_structured.csv", index=False)

print("")
print(f"Done. Saved {len(df)} runner rows to data/b2run_results_structured.csv")