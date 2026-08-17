import csv
import sys

IMAGE_URL_COLUMN = "image_url"


def main(input_path: str, output_path: str):
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if IMAGE_URL_COLUMN not in reader.fieldnames:
            print(f"ERROR: no '{IMAGE_URL_COLUMN}' column found in {input_path}")
            sys.exit(1)
        rows = list(reader)

    # Pick a few useful identifying columns to include, if they exist
    id_columns = [c for c in ["plant_id", "scientific_name", "common_name"] if c in reader.fieldnames]

    missing_rows = [r for r in rows if not r.get(IMAGE_URL_COLUMN, "").strip()]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=id_columns)
        writer.writeheader()
        for row in missing_rows:
            writer.writerow({col: row.get(col, "") for col in id_columns})

    print(f"Found {len(missing_rows)} of {len(rows)} rows with no image_url")
    print(f"Wrote list to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python export_missing_images.py input.csv output.csv")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])