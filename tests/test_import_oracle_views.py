"""Exercise the real CLI with synthetic exports in temporary repositories."""

import csv
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/import_oracle_views.py"
spec = importlib.util.spec_from_file_location("import_oracle_views", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ImportOracleViewsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / ".git").mkdir()
        self.headers = ["VIEW_NAME", "PART_NUMBER", "DDL_LENGTH", "DDL_PART"]
        self.rows = []
        self.definitions = {}
        for name in module.VIEW_PATHS:
            ddl = (f'CREATE OR REPLACE FORCE EDITIONABLE VIEW "ADMIN"."{name}" '
                   'AS SELECT \'synthetic\' AS LABEL FROM DUAL')
            self.definitions[name] = ddl
            self.rows.extend([[name, index, len(ddl), part]
                              for index, part in enumerate([ddl[:50], ddl[50:]], 1)])

    def run_import(self, *args):
        export = self.root / "export.csv"
        with export.open("w", newline="", encoding="utf-8-sig") as output:
            writer = csv.writer(output)
            writer.writerow(self.headers)
            writer.writerows(self.rows)
        return subprocess.run([sys.executable, "-B", str(SCRIPT), str(export), *args],
                              cwd=self.root, capture_output=True, text=True)

    def replace_ddl(self, name, ddl):
        self.rows = [row for row in self.rows if row[0] != name]
        self.rows.append([name, 1, len(ddl), ddl])

    def assert_rejected(self, expected_message):
        result = self.run_import()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(expected_message, result.stderr)
        self.assertFalse((self.root / "sql").exists(), "Invalid export caused partial writes")

    def test_complete_export_preserves_ddl(self):
        self.rows.reverse()  # Export row order need not equal chunk order.
        result = self.run_import()
        self.assertEqual(result.returncode, 0, result.stderr)
        for name, relative_path in module.VIEW_PATHS.items():
            self.assertEqual((self.root / relative_path).read_text(), self.definitions[name] + ";\n")

    def test_dry_run_never_creates_sql_directory(self):
        result = self.run_import("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("WOULD WRITE"), 9)
        self.assertFalse((self.root / "sql").exists())

    def test_existing_file_is_preserved(self):
        existing = self.root / module.VIEW_PATHS["RAW_MEDICAID_2025"]
        existing.parent.mkdir(parents=True)
        existing.write_text("existing SQL")
        self.assertEqual(self.run_import().returncode, 0)
        self.assertEqual(existing.read_text(), "existing SQL")

    def test_explicit_overwrite_replaces_existing_file(self):
        existing = self.root / module.VIEW_PATHS["RAW_MEDICAID_2025"]
        existing.parent.mkdir(parents=True)
        existing.write_text("existing SQL")
        self.assertEqual(self.run_import("--overwrite").returncode, 0)
        self.assertEqual(existing.read_text(), self.definitions["RAW_MEDICAID_2025"] + ";\n")

    def test_missing_view(self):
        self.rows = self.rows[:-2]
        self.assert_rejected("Export is missing views")

    def test_duplicate_chunk(self):
        self.rows.append(self.rows[0])
        self.assert_rejected("Duplicate chunk")

    def test_missing_first_chunk(self):
        self.rows.pop(0)
        self.assert_rejected("chunk numbers")

    def test_truncated_export(self):
        self.rows[-1][3] = self.rows[-1][3][:-1]
        self.assert_rejected("Truncated/corrupted DDL")

    def test_inconsistent_lengths(self):
        self.rows[0][2] += 1
        self.assert_rejected("Inconsistent DDL_LENGTH")

    def test_wrong_view_target(self):
        self.replace_ddl("CLEAN_MEDICAID_2025", "CREATE VIEW OTHER_VIEW AS SELECT 1 FROM DUAL")
        self.assert_rejected("does not match CSV view")

    def test_other_create_statement(self):
        self.replace_ddl("CLEAN_MEDICAID_2025", "CREATE TABLE CLEAN_MEDICAID_2025 (X NUMBER)")
        self.assert_rejected("does not begin with CREATE VIEW")

    def test_case_sensitive_quoted_identifier(self):
        self.replace_ddl("CLEAN_MEDICAID_2025", 'CREATE VIEW "clean_medicaid_2025" AS SELECT 1 FROM DUAL')
        self.assert_rejected("does not match CSV view")

    def test_secret_marker(self):
        self.replace_ddl("CLEAN_MEDICAID_2025", self.definitions["CLEAN_MEDICAID_2025"] + " -- password=synthetic")
        self.assert_rejected("Potential secret text")

    def test_duplicate_headers(self):
        self.headers.append("view_name")
        for row in self.rows:
            row.append(row[0])
        self.assert_rejected("Duplicate CSV column names")

    def test_extra_csv_fields(self):
        self.rows[0].append("unexpected")
        self.assert_rejected("more fields than its header")

    def test_missing_headers(self):
        self.headers[3] = "WRONG_COLUMN"
        self.assert_rejected("Missing CSV columns")


if __name__ == "__main__":
    unittest.main()
