
import csv
from pathlib import Path

# --------------------------------------------------
# RxClaim Sentinel - NADAC Historical CSV Filtering
# Source: Medicaid.gov NADAC 2025
# --------------------------------------------------

HOME = Path.home()
PROJECT_ROOT = Path(__file__).resolve().parent.parent

NADAC_FILE = (
    HOME / "Downloads" /
    "nadac-national-average-drug-acquisition-cost-12-31-2025.csv"
)

MEDICAID_DIR = HOME / "Downloads" / "rxclaim-state-files"

STATES = ["MA", "TN", "CA"]

OUTPUT_DIR = (
    PROJECT_ROOT / "data" / "processed" / "nadac_filtered"
)

ROWS_PER_FILE = 50000


def load_medicaid_ndcs():
    """Collect unique NDCs from all three Medicaid datasets."""

    unique_ndcs = set()

    for state in STATES:
        file_path = (
            MEDICAID_DIR / f"medicaid_2025_{state}.csv"
        )

        if not file_path.exists():
            raise FileNotFoundError(file_path)

        count = 0

        with file_path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as file:

            reader = csv.DictReader(file)

            if "NDC" not in (reader.fieldnames or []):
                raise ValueError(f"NDC column missing: {file_path}")

            for row in reader:
                ndc = row["NDC"].strip()

                if len(ndc) == 11 and ndc.isdigit():
                    unique_ndcs.add(ndc)

                count += 1

        print(f"{state}: {count:,} Medicaid records scanned")

    print(f"\nUnique Medicaid NDCs: {len(unique_ndcs):,}")

    return unique_ndcs


def filter_nadac(medicaid_ndcs):
    """Filter historical NADAC records for Medicaid NDCs."""

    if not NADAC_FILE.exists():
        raise FileNotFoundError(NADAC_FILE)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Remove only output parts created by previous runs.
    for old_file in OUTPUT_DIR.glob("nadac_matched_*.csv"):
        old_file.unlink()

    total_scanned = 0
    matched_rows = 0
    matched_ndcs = set()
    output_files = []

    output_file = None
    writer = None

    try:
        with NADAC_FILE.open(
            "r", encoding="utf-8-sig", newline=""
        ) as source:

            reader = csv.DictReader(source)

            required = {
                "NDC",
                "NADAC Per Unit",
                "Effective Date",
                "Pricing Unit",
                "As of Date",
            }

            missing = required - set(reader.fieldnames or [])

            if missing:
                raise ValueError(
                    f"Missing required columns: {missing}"
                )

            for row in reader:
                total_scanned += 1

                ndc = row["NDC"].strip()

                if ndc not in medicaid_ndcs:
                    continue

                # Open a new output CSV when the previous
                # file reaches the configured row limit.
                if matched_rows % ROWS_PER_FILE == 0:

                    if output_file is not None:
                        output_file.close()

                    part_number = len(output_files) + 1

                    path = OUTPUT_DIR / (
                        f"nadac_matched_{part_number:03d}.csv"
                    )

                    output_file = path.open(
                        "w", encoding="utf-8", newline=""
                    )

                    writer = csv.DictWriter(
                        output_file,
                        fieldnames=reader.fieldnames
                    )

                    writer.writeheader()
                    output_files.append(path)

                # Preserve all 12 original source fields.
                writer.writerow(row)

                matched_rows += 1
                matched_ndcs.add(ndc)

    finally:
        if output_file is not None:
            output_file.close()

    print("\n" + "=" * 45)
    print("NADAC FILTERING COMPLETED")
    print("=" * 45)

    print(f"NADAC rows scanned: {total_scanned:,}")
    print(f"NADAC rows matched: {matched_rows:,}")
    print(f"Unique NDCs matched: {len(matched_ndcs):,}")

    coverage = (
        100 * len(matched_ndcs) / len(medicaid_ndcs)
        if medicaid_ndcs else 0
    )

    print(f"NDC identifier coverage: {coverage:.2f}%")
    print(f"Output files created: {len(output_files)}")

    for path in output_files:
        size = path.stat().st_size / (1024 * 1024)

        print(f"{path.name}: {size:.2f} MiB")

    print(f"\nFiles saved to: {OUTPUT_DIR}")


def main():
    print("========================================")
    print("RxClaim Sentinel - NADAC CSV Processing")
    print("========================================\n")

    medicaid_ndcs = load_medicaid_ndcs()

    if not medicaid_ndcs:
        raise ValueError("No valid Medicaid NDCs found.")

    filter_nadac(medicaid_ndcs)


if __name__ == "__main__":
    main()
