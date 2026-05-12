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

YEAR = 2025

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
# Step 1: Discover 2025 events
# -----------------------------

def discover_events():
    discovered = []

    for slug in B2RUN_CITY_SLUGS:
        city_url = f"https://www.b2run.de/run/de/de/{slug}/ergebnisse/index.html"

        try:
            html = get_html(city_url)
        except Exception as e:
            print(f"Could not open {slug}: {e}")
            continue

        soup = BeautifulSoup(html, "html.parser")

        event_view_links = []

        for a in soup.find_all("a", href=True):
            href = a["href"]
            label = clean_text(a.get_text(" ", strip=True))

            if "b2run-iframe.maxfunsports.com/event/view" in href:
                full_url = urljoin(city_url, href)
                event_view_links.append((label, full_url))

        if not event_view_links:
            print(f"No MaxFunSports event links found for {slug}")
            continue

        for label, event_url in event_view_links:
            try:
                event_html = get_html(event_url)
            except Exception as e:
                print(f"Could not open event page for {slug}: {e}")
                continue

            event_soup = BeautifulSoup(event_html, "html.parser")
            event_text = clean_text(event_soup.get_text(" ", strip=True))

            # Keep only 2025 events
            if str(YEAR) not in event_text:
                continue

            competition_url = None

            for a in event_soup.find_all("a", href=True):
                link_text = clean_text(a.get_text(" ", strip=True)).lower()
                href = a["href"]

                if "einzelwertung" == link_text and "/event/competition" in href:
                    competition_url = urljoin(event_url, href)
                    break

            if not competition_url:
                print(f"No Einzelwertung link found for {slug} / {event_url}")
                continue

            competition_id = extract_id_from_url(competition_url)

            distance_km = DISTANCE_BY_CITY.get(slug, DEFAULT_DISTANCE_KM)

            discovered.append(
                {
                    "city": slug,
                    "year": YEAR,
                    "competition_id": competition_id,
                    "distance_km": distance_km,
                    "source_url": competition_url,
                    "event_url": event_url,
                }
            )

            print(f"Discovered {slug} {YEAR}: competition_id={competition_id}, distance={distance_km} km")

            # Usually one 2025 event per city is enough
            break

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
        url = f"{event['source_url']}&page={page}&per-page=50"

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

events_df = pd.DataFrame(events)
events_df.to_csv("data/discovered_events_2025.csv", index=False)

print("")
print(f"Discovered {len(events)} events.")
print("Saved discovered events to data/discovered_events_2025.csv")
print("")

all_results = []

for event in events:
    all_results.extend(scrape_event(event))

df = pd.DataFrame(all_results)
df.to_csv("data/b2run_results_structured.csv", index=False)

print("")
print(f"Done. Saved {len(df)} runner rows to data/b2run_results_structured.csv")