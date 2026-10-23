
import csv
import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# ----------------------------------------------
# RxClaim Sentinel - NADAC API Ingestion
# Source: Medicaid.gov, NADAC 2025
# ----------------------------------------------

BASE_URL = (
    "https://data.medicaid.gov/api/1/datastore/query/"
    "f38d0706-1239-442c-a3cc-40ef1b686ac0/0"
)

PAGE_SIZE = 100
MAX_PAGES = 2
MAX_RETRIES = 3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "nadac"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

CSV_FILE = PROCESSED_DIR / "nadac_api_test.csv"

CSV_COLUMNS = [
    "ndc",
    "ndc_description",
    "nadac_per_unit",
    "pricing_unit",
    "effective_date",
    "as_of_date",
]


def fetch_page(offset):
    """Fetch a page, retrying temporary errors."""

    params = {
        "limit": PAGE_SIZE,
        "offset": offset,
        "results": "true",
        "format": "json",
    }

    url = BASE_URL + "?" + urlencode(params)
    request = Request(
        url, headers={"Accept": "application/json"}
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urlopen(request, timeout=30) as response:
                return json.load(response)

        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504):
                raise
            last_error = error

        except (URLError, TimeoutError) as error:
            last_error = error

        if attempt < MAX_RETRIES:
            wait = 2 ** (attempt - 1)
            print(f"Request failed. Retrying in {wait}s...")
            time.sleep(wait)

    raise RuntimeError(
        f"Failed after {MAX_RETRIES} attempts"
    ) from last_error


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    all_records = []

    print("RxClaim Sentinel - NADAC Pagination Test")
    print("--------------------------------------")

    for page in range(MAX_PAGES):
        offset = page * PAGE_SIZE

        response = fetch_page(offset)
        records = response.get("results", [])

        if not isinstance(records, list):
            raise ValueError("Unexpected API response format")

        # Preserve the complete original API response.
        raw_file = RAW_DIR / f"page_{page:03d}.json"

        with raw_file.open("w", encoding="utf-8") as file:
            json.dump(response, file, indent=2)

        all_records.extend(records)

        print(
            f"Page {page + 1}: "
            f"{len(records)} records received"
        )

        if len(records) < PAGE_SIZE:
            print("Reached the final available page.")
            break

    # Create a CSV for Oracle ingestion testing.
    with CSV_FILE.open(
        "w", newline="", encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file, fieldnames=CSV_COLUMNS
        )
        writer.writeheader()

        for record in all_records:
            writer.writerow({
                column: record.get(column, "")
                for column in CSV_COLUMNS
            })

    print("\nIngestion test complete!")
    print("Total records:", len(all_records))
    print("CSV saved to:", CSV_FILE)
    print("Raw JSON saved to:", RAW_DIR)


if __name__ == "__main__":
    main()
