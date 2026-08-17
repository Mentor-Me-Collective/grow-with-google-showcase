import csv
import sys
import time
import requests

INATURALIST_URL = "https://api.inaturalist.org/v1/taxa"
REQUEST_DELAY_SECONDS = 1.1  # stay safely under iNaturalist's rate limit
TEST_MODE = False   
TEST_ROWS = 10

SCIENTIFIC_NAME_COLUMN = "scientific_name"  # properly capitalized, e.g. "Abies balsamea"
ID_COLUMN = "plant_id"
NEW_COLUMN = "image_url"


def get_image_url(scientific_name: str) -> str:
    """Query iNaturalist for a species and return its default photo URL, or '' if none found."""
    try:
        response = requests.get(
            INATURALIST_URL,
            params={"q": scientific_name, "rank": "species", "per_page": 1},
            timeout=10,
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        if not results:
            return ""
        photo = results[0].get("default_photo")
        if not photo:
            return ""
        # square_url is a thumbnail; swap to medium_url for a bigger image
        return photo.get("medium_url", "") or photo.get("square_url", "")
    except requests.RequestException as e:
        print(f"  [warning] request failed for '{scientific_name}': {e}")
        return ""


def main(input_path: str, output_path: str):
    with open(input_path, newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        if SCIENTIFIC_NAME_COLUMN not in reader.fieldnames:
            print(f"ERROR: column '{SCIENTIFIC_NAME_COLUMN}' not found. "
                  f"Available columns: {reader.fieldnames}")
            sys.exit(1)
        fieldnames = reader.fieldnames + [NEW_COLUMN]
        rows = list(reader)

    if TEST_MODE:
        rows = rows[:TEST_ROWS]

    total = len(rows)
    with open(output_path, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for i, row in enumerate(rows, start=1):
            plant_id = row.get(ID_COLUMN, "")
            species = row.get(SCIENTIFIC_NAME_COLUMN, "").strip()
            print(f"[{i}/{total}] {plant_id}: {species}")

            image_url = get_image_url(species) if species else ""
            row[NEW_COLUMN] = image_url

            writer.writerow(row)
            outfile.flush()  # write progress to disk as we go, in case it's interrupted

            time.sleep(REQUEST_DELAY_SECONDS)

    print(f"\nDone. Wrote {total} rows to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python add_plant_images.py input.csv output.csv")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])