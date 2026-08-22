import csv
import sys

ID_COLUMN = "plant_id"
IMAGE_URL_COLUMN = "image_url"
IMAGE_SOURCE_COLUMN = "image_source"
SOURCE_VALUE = "iNaturalist"


def main(master_path: str, app_path: str, output_path: str):
    # Build a lookup: plant_id -> image_url, from the file you already generated
    image_lookup = {}
    with open(master_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            plant_id = row.get(ID_COLUMN, "")
            url = row.get(IMAGE_URL_COLUMN, "")
            if plant_id and url:
                image_lookup[plant_id] = url

    print(f"Loaded {len(image_lookup)} image URLs from {master_path}")

    # Now go through plants_app.csv and fill in image_url / image_source where we have a match
    with open(app_path, newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        rows = list(reader)

    filled = 0
    for row in rows:
        plant_id = row.get(ID_COLUMN, "")
        if plant_id in image_lookup:
            row[IMAGE_URL_COLUMN] = image_lookup[plant_id]
            row[IMAGE_SOURCE_COLUMN] = SOURCE_VALUE
            filled += 1

    with open(output_path, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Filled {filled} of {len(rows)} rows in {app_path}")
    print(f"Wrote result to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python merge_images_into_app.py master_with_images.csv plants_app.csv output.csv")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])