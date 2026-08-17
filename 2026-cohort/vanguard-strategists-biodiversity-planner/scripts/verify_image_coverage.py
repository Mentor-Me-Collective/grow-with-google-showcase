import csv
import sys
import random
import requests

IMAGE_URL_COLUMN = "image_url"
SPOT_CHECK_COUNT = 10


def main(csv_path: str):
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if IMAGE_URL_COLUMN not in reader.fieldnames:
            print(f"ERROR: no '{IMAGE_URL_COLUMN}' column found in {csv_path}")
            print(f"Columns present: {reader.fieldnames}")
            sys.exit(1)
        rows = list(reader)

    total = len(rows)
    filled_rows = [r for r in rows if r.get(IMAGE_URL_COLUMN, "").strip()]
    filled = len(filled_rows)
    missing = total - filled

    print(f"File: {csv_path}")
    print(f"Total rows: {total}")
    print(f"Rows with image_url: {filled} ({filled/total*100:.1f}%)")
    print(f"Rows missing image_url: {missing}")

    # Spot-check a random sample of the "filled" rows to confirm the URLs
    # actually resolve to something (not broken links)
    sample_size = min(SPOT_CHECK_COUNT, filled)
    sample = random.sample(filled_rows, sample_size)

    print(f"\nSpot-checking {sample_size} random URLs...")
    ok_count = 0
    for row in sample:
        url = row[IMAGE_URL_COLUMN]
        name = row.get("scientific_name") or row.get("plant_id", "unknown")
        try:
            resp = requests.head(url, timeout=8, allow_redirects=True)
            status = "OK" if resp.status_code == 200 else f"HTTP {resp.status_code}"
            if resp.status_code == 200:
                ok_count += 1
        except requests.RequestException as e:
            status = f"FAILED ({e})"
        print(f"  {name}: {status}")

    print(f"\n{ok_count}/{sample_size} spot-checked URLs returned OK")

    # List a few missing rows so you can see what's not covered
    missing_rows = [r for r in rows if not r.get(IMAGE_URL_COLUMN, "").strip()]
    if missing_rows:
        print(f"\nFirst 10 rows missing an image:")
        for r in missing_rows[:10]:
            name = r.get("scientific_name") or r.get("plant_id", "unknown")
            print(f"  {name}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python verify_image_coverage.py path/to/file.csv")
        sys.exit(1)
    main(sys.argv[1])