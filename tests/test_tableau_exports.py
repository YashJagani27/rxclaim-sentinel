import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/validate_tableau_exports.py"
spec = importlib.util.spec_from_file_location("validate_tableau_exports", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ExportValidationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.columns = [{"name": "NDC", "type": "string"}, {"name": "REPORTED_RX", "type": "integer"},
                        {"name": "REPORTED_REIMBURSEMENT", "type": "real"}]

    def validate_rows(self, rows):
        path = self.root / "synthetic.csv"
        with path.open("w", newline="", encoding="utf-8-sig") as output:
            csv.writer(output).writerows(rows)
        return module.validate_csv(path, self.columns)

    def test_leading_zero_ndc_is_preserved(self):
        result = self.validate_rows([[c["name"] for c in self.columns], ["00123456789", "3", "12.34"]])
        self.assertEqual(result["error_count"], 0)
        self.assertEqual(result["rows"], 1)

    def test_header_changes_and_duplicates_fail(self):
        for headers in [["NDC", "REPORTED_REIMBURSEMENT", "REPORTED_RX"], ["NDC", "REPORTED_RX", "REPORTED_RX"]]:
            with self.subTest(headers=headers):
                self.assertGreater(self.validate_rows([headers])["error_count"], 0)

    def test_invalid_identifiers_fail(self):
        for ndc in ["123456789", "1.23457E+10", "１２３４５６７８９０１", "", " 00123456789"]:
            with self.subTest(ndc=ndc):
                result = self.validate_rows([[c["name"] for c in self.columns], [ndc, "3", "12.34"]])
                self.assertGreater(result["error_count"], 0)

    def test_nonfinite_and_invalid_numbers_fail(self):
        for value in ["NaN", "Infinity", "-Infinity", "not-a-number", "1_000", "１２.３", " 1.0"]:
            self.assertFalse(module.valid_value(value, "real", "AMOUNT"))
        self.assertFalse(module.valid_value("1.5", "integer", "COUNT"))

    def test_decimal_and_scientific_notation_are_supported(self):
        for value in ["0", "-1.25", ".5", "1.", "+1.2e-3"]:
            self.assertTrue(module.valid_value(value, "real", "AMOUNT"))

    def test_blanks_are_allowed_except_ndc(self):
        self.assertTrue(module.valid_value("", "real", "AMOUNT"))
        self.assertTrue(module.valid_value("", "integer", "COUNT"))

    def test_wrong_row_width_and_header_only_fail(self):
        headers = [c["name"] for c in self.columns]
        self.assertGreater(self.validate_rows([headers, ["00123456789"]])["error_count"], 0)
        self.assertGreater(self.validate_rows([headers])["error_count"], 0)

    def test_missing_file_is_reported(self):
        self.assertEqual(module.validate_csv(self.root / "missing.csv", self.columns)["rows"], 0)
        self.assertGreater(module.validate_csv(self.root / "missing.csv", self.columns)["error_count"], 0)

    def test_error_details_are_bounded(self):
        result = self.validate_rows([[c["name"] for c in self.columns]] + [["invalid", "bad", "bad"]] * 100)
        self.assertEqual(result["error_count"], 300)
        self.assertEqual(len(result["errors"]), 20)
        self.assertNotIn('"invalid"', json.dumps(result))

    def test_final_workbook_matches_contract(self):
        exports = json.loads(module.DEFAULT_CONTRACT.read_text())["exports"]
        self.assertEqual(module.validate_workbook(module.DEFAULT_WORKBOOK, exports), [])

    def test_workbook_schema_changes_fail(self):
        path = self.root / "synthetic.twbx"
        with zipfile.ZipFile(path, "w") as package:
            package.writestr("synthetic.twb", '<workbook><datasources><datasource><connection class="textscan" filename="synthetic.csv"/><column name="[NDC]" datatype="integer"/></datasource></datasources></workbook>')
        errors = module.validate_workbook(path, {"synthetic.csv": self.columns})
        self.assertTrue(any("field missing or changed" in error for error in errors))

    def test_invalid_package_is_reported(self):
        path = self.root / "invalid.twbx"
        path.write_text("not a zip")
        self.assertTrue(module.validate_workbook(path, {}))

    def test_cli_reports_missing_local_exports_with_failure_exit(self):
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--data-dir", str(self.root)],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        self.assertFalse(report["passed"])
        self.assertEqual(len(report["exports"]), 3)


if __name__ == "__main__":
    unittest.main()
