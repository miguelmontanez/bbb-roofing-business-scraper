import requests
import json
import time

from config import (
    LOWER_48_STATES
)

BASE_URL = "https://www.bbb.org/api/suggest/location"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
    "Referer": "https://www.bbb.org/"
}

MAX_MATCHES = 5000
OUTPUT_FILE = "assets/display_texts.json"

all_display_texts = set()

for state_id in LOWER_48_STATES:
    # The input parameter can be ", state" to trigger the autocomplete for that state
    params = {
        "country": "USA",
        "input": f", {state_id.lower()}",
        "maxMatches": MAX_MATCHES
    }
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        for item in data:
            display_text = item.get("displayText")
            if display_text and display_text.endswith(f", {state_id}"):
                all_display_texts.add(display_text)
        
        print(f"[{state_id}] Collected {len(all_display_texts)} unique cities so far...")
        
        # Be polite, avoid rate-limiting
        time.sleep(0.5)
        
    except Exception as e:
        print(f"Error fetching state {state_id}: {e}")

# Convert set to list for JSON serialization
all_display_texts_list = list(all_display_texts)

# Save to JSON file
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(all_display_texts_list, f, indent=2)

print(f"\nDone! Total unique cities collected: {len(all_display_texts_list)}")
print(f"Saved to {OUTPUT_FILE}")
