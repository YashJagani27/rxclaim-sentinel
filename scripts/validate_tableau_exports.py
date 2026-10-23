#!/usr/bin/env python3
"""Check CSV compatibility with the saved Tableau workbook, without changing files."""

import argparse
import csv
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTRACT = PROJECT_ROOT / "docs" / "tableau_export_contract.json"
DEFAULT_WORKBOOK = PROJECT_ROOT / "dashboard" / "RxClaim_Sentinel_Executive_dashboard.twbx"


def valid_value(value, data_type, name):
    """Blanks remain nullable until the Oracle definitions establish nullability."""
    if name == "NDC":
        return re.fullmatch(r"[0-9]{11}", value) is not None
    if not value or data_type == "string":
        return True
    if data_type == "integer":
        return re.fullmatch(r"[+-]?[0-9]+", value) is not None
    if data_type == "real":
        if not re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", value):
            return False
        try:
            return Decimal(value).is_finite()
        except InvalidOperation:
            return False
    return False


def validate_csv(path, columns):
    result = {"file": path.name, "rows": 0, "error_count": 0, "errors": []}

    def error(message):
        result["error_count"] += 1
        if len(result["errors"]) < 20:
            result["errors"].append(message)

    try:
        with path.open(encoding="utf-8-sig", newline="") as source:
            reader = csv.reader(source, strict=True)
            if next(reader, None) != [column["name"] for column in columns]:
                error("Headers differ from the contract (including order or duplicate columns).")
                return result
            for number, row in enumerate(reader, 2):
                result["rows"] += 1
                if len(row) != len(columns):
                    error(f"Record {number}: wrong number of fields.")
                    continue
                for value, column in zip(row, columns):
                    if not valid_value(value, column["type"], column["name"]):
                        error(f"Record {number}: invalid {column['type']} in {column['name']}.")
            if not result["rows"]:
                error("Export contains no data rows.")
    except (OSError, UnicodeError, csv.Error) as exc:
        # Do not include source records or connection details in the report.
        error(f"Cannot read CSV ({type(exc).__name__}).")
    return result


def validate_workbook(path, exports):
    errors = []
    try:
        with zipfile.ZipFile(path) as package:
            names = [name for name in package.namelist() if name.lower().endswith(".twb")]
            if len(names) != 1:
                return ["Package must contain exactly one workbook definition."]
            if package.getinfo(names[0]).file_size > 10 * 1024 * 1024:
                return ["Workbook definition exceeds the 10 MiB inspection limit."]
            root = ET.fromstring(package.read(names[0]))
        observed = {}
        for source in root.findall("./datasources/datasource"):
            filenames = {connection.get("filename") for connection in source.iter("connection")
                         if connection.get("class") == "textscan"}
            fields = {column.get("name"): column.get("datatype")
                      for column in source.findall("column")
                      if column.find("calculation") is None}
            for filename in filenames:
                if filename in observed:
                    errors.append(f"Duplicate workbook source for {filename}.")
                observed[filename] = fields
        if set(observed) != set(exports):
            errors.append("Workbook CSV source names differ from the contract.")
        for filename, columns in exports.items():
            for column in columns:
                if observed.get(filename, {}).get(f"[{column['name']}]") != column["type"]:
                    errors.append(f"Workbook field missing or changed: {filename}, {column['name']}.")
    except (OSError, zipfile.BadZipFile, ET.ParseError, RuntimeError, NotImplementedError) as exc:
        errors.append(f"Cannot inspect workbook ({type(exc).__name__}).")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=PROJECT_ROOT / "data/processed/tableau")
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    args = parser.parse_args()
    exports = json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))["exports"]
    workbook_errors = validate_workbook(args.workbook, exports)
    results = [validate_csv(args.data_dir / name, columns) for name, columns in exports.items()]
    passed = not workbook_errors and all(not result["error_count"] for result in results)
    print(json.dumps({"passed": passed, "workbook_errors": workbook_errors, "exports": results}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
