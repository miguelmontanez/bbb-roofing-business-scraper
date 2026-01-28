import csv
import json

input_csv = "assets/us_cities.csv"
output_json = "assets/manual_display_texts.json"

display_texts = set()

with open(input_csv, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        city = row["city_ascii"].strip()
        state_id = row["state_id"].strip()

        if city and state_id:
            display_texts.add(f"{city}, {state_id}")

# Convert set to list (no sorting)
display_texts_list = list(display_texts)

# Save to JSON
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(display_texts_list, f, indent=2)

print(f"Saved {len(display_texts_list)} displayTexts to {output_json}")
