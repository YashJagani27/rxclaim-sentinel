#!/usr/bin/env python3
"""Restore genuine Oracle view DDL from a chunked SQL Worksheet CSV export.

Usage: python3 scripts/import_oracle_views.py ~/Downloads/your-export.csv
       python3 scripts/import_oracle_views.py ~/Downloads/your-export.csv --overwrite

Only SQL DDL is written. No database connection is made.
"""

import argparse
import csv
from collections import defaultdict
from pathlib import Path
import re

VIEW_PATHS = {
    "RAW_MEDICAID_2025": "sql/bronze/01_raw_medicaid_2025.sql",
    "CLEAN_MEDICAID_2025": "sql/silver/02_clean_medicaid_2025.sql",
    "GOLD_QUARTERLY_PHARMACY_KPIS": "sql/gold/01_quarterly_pharmacy_kpis.sql",
    "GOLD_QUARTERLY_TRENDS": "sql/gold/02_quarterly_trends.sql",
    "GOLD_QUARTERLY_RISK_FLAGS": "sql/gold/03_quarterly_risk_flags.sql",
    "GOLD_NDC_QUARTERLY": "sql/gold/04_ndc_quarterly.sql",
    "GOLD_NDC_QOQ_ANALYSIS": "sql/gold/05_ndc_qoq_analysis.sql",
    "GOLD_NDC_INVESTIGATION_QUEUE": "sql/gold/06_ndc_investigation_queue.sql",
    "GOLD_NDC_REVIEW_DASHBOARD": "sql/gold/07_ndc_review_dashboard.sql",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path, help="CSV exported from docs/export_all_views.sql")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing SQL files")
    parser.add_argument("--dry-run", action="store_true", help="Validate and show planned writes without changing files")
    args = parser.parse_args()

    if not args.csv_path.is_file():
        parser.error(f"Export file not found: {args.csv_path}")

    groups = defaultdict(dict)
    lengths = {}
    with args.csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            parser.error("CSV has no headers")
        column_names = {name.strip().upper(): name for name in reader.fieldnames}
        if len(column_names) != len(reader.fieldnames):
            parser.error("Duplicate CSV column names")
        needed = {"VIEW_NAME", "PART_NUMBER", "DDL_LENGTH", "DDL_PART"}
        if not needed.issubset(column_names):
            parser.error("Missing CSV columns: " + ", ".join(sorted(needed - set(column_names))))

        for row in reader:
            if None in row:
                parser.error("CSV row has more fields than its header")
            name = (row[column_names["VIEW_NAME"]] or "").strip().upper()
            if name not in VIEW_PATHS:
                parser.error(f"Unexpected or unknown view in CSV: {name!r}")
            try:
                number = int(row[column_names["PART_NUMBER"]])
                length = int(row[column_names["DDL_LENGTH"]])
            except (TypeError, ValueError):
                parser.error(f"Invalid part number or DDL length for {name}")
            chunk = row[column_names["DDL_PART"]]
            if number < 1 or length <= 0 or chunk is None:
                parser.error(f"Invalid chunk for {name} (part {number})")
            if number in groups[name]:
                parser.error(f"Duplicate chunk {number} for {name}")
            if name in lengths and lengths[name] != length:
                parser.error(f"Inconsistent DDL_LENGTH for {name}")
            groups[name][number] = chunk
            lengths[name] = length

    missing = set(VIEW_PATHS) - set(groups)
    if missing:
        parser.error("Export is missing views: " + ", ".join(sorted(missing)))

    restored = {}
    for name, parts in groups.items():
        expected_parts = sorted(parts)
        if any(number != index for index, number in enumerate(expected_parts, 1)):
            parser.error(f"Missing/out-of-order chunk numbers for {name}")
        ddl = "".join(parts[n] for n in expected_parts)
        if len(ddl) != lengths[name]:
            parser.error(f"Truncated/corrupted DDL for {name}: expected {lengths[name]} chars, got {len(ddl)}")
        identifier = r'(?:"[^"]+"|[A-Za-z][A-Za-z0-9_$#]*)'
        target = re.match(
            rf'^\s*CREATE\s+(?:OR\s+REPLACE\s+)?'
            rf'(?:(?:NOFORCE|FORCE|EDITIONABLE|NONEDITIONABLE)\s+)*VIEW\s+'
            rf'(?P<first>{identifier})(?:\s*\.\s*(?P<second>{identifier}))?(?=\s|\()',
            ddl, re.IGNORECASE,
        )
        if not target:
            parser.error(f"{name} does not begin with CREATE VIEW: review the CSV export")
        view_identifier = target.group("second") or target.group("first")
        # Quoted Oracle names are case-sensitive; unquoted identifiers are uppercase.
        actual_name = view_identifier[1:-1] if view_identifier.startswith('"') else view_identifier.upper()
        if actual_name != name:
            parser.error(f"DDL target {actual_name!r} does not match CSV view {name}")
        if re.search(r"(?i)\b(?:password|api_key|access_token|private_key|client_secret)\s*[:=]", ddl):
            parser.error(f"Potential secret text in {name}; review Oracle definition before writing")
        restored[name] = ddl

    cwd = Path.cwd()
    if not (cwd / ".git").exists():
        parser.error("Run from the root of your cloned Git repository")

    print(f"Verified all {len(restored)} SQL definitions and chunk lengths.")
    for name, relpath in VIEW_PATHS.items():
        out = cwd / relpath
        if out.exists() and not args.overwrite:
            print(f"SKIP existing  {relpath}")
            continue
        if args.dry_run:
            print(f"WOULD WRITE   {relpath}")
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        raw_ddl = restored[name]
        # Keep Oracle's definition untouched; add a SQL-script terminator if needed.
        content = raw_ddl + ("\n" if raw_ddl.rstrip().endswith(";") else ";\n")
        # Exclusive creation also protects files created after the existence check.
        with out.open("w" if args.overwrite else "x", encoding="utf-8") as destination:
            destination.write(content)
        print(f"WRITE          {relpath}")
    print("Review DDL and secrets before staging; validation does not establish SQL safety or database validity.")
    print("No files have been committed or pushed.")


if __name__ == "__main__":
    main()
