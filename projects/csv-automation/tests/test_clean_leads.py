from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from clean_leads import (  # noqa: E402
    Lead,
    merge_leads,
    normalize_email,
    normalize_name,
    normalize_phone,
    read_leads,
    write_leads,
    write_report,
)


SAMPLE_A = ROOT / "sample_data" / "leads_a.csv"
SAMPLE_B = ROOT / "sample_data" / "leads_b.csv"


class NormalizeTests(unittest.TestCase):
    def test_phone_keeps_plus_and_digits(self) -> None:
        self.assertEqual(normalize_phone("+380 67 111 22 33"), "+380671112233")
        self.assertEqual(normalize_phone("(202) 555-0199"), "2025550199")
        self.assertEqual(normalize_phone(""), "")

    def test_email_casefold_and_reject(self) -> None:
        self.assertEqual(normalize_email("A@Example.COM"), "a@example.com")
        self.assertEqual(normalize_email("bad-email"), "")

    def test_name_titlecase(self) -> None:
        self.assertEqual(normalize_name("anna koval"), "Anna Koval")


class PipelineTests(unittest.TestCase):
    def test_read_and_dedupe_samples(self) -> None:
        a = read_leads(SAMPLE_A)
        b = read_leads(SAMPLE_B)
        merged = merge_leads([a, b])
        emails = {lead.email for lead in merged if lead.email}
        self.assertIn("anna.koval@example.com", emails)
        self.assertIn("bohdan.melnyk@example.com", emails)
        # Anna appears twice in A with same email -> one row
        anna = [lead for lead in merged if lead.email == "anna.koval@example.com"]
        self.assertEqual(len(anna), 1)
        self.assertIn("landing", anna[0].source)
        self.assertIn("ads", anna[0].source)

    def test_merge_prefers_filling_empty_fields(self) -> None:
        first = [Lead(name="Ira", email="ira@example.com", phone="", source="web", city="")]
        second = [Lead(name="Ira", email="ira@example.com", phone="+380991112233", source="ads", city="Odesa")]
        merged = merge_leads([first, second])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].phone, "+380991112233")
        self.assertEqual(merged[0].city, "Odesa")

    def test_cli_writes_outputs(self) -> None:
        from clean_leads import main

        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out.csv"
            report = Path(td) / "report.md"
            code = main([str(SAMPLE_A), str(SAMPLE_B), "-o", str(out), "-r", str(report)])
            self.assertEqual(code, 0)
            self.assertTrue(out.exists())
            self.assertTrue(report.exists())
            text = report.read_text(encoding="utf-8")
            self.assertIn("Unique leads after dedupe", text)


class IoTests(unittest.TestCase):
    def test_roundtrip_write(self) -> None:
        leads = [
            Lead("Demo User", "demo@example.com", "+380501112233", "test", "Kyiv"),
        ]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "x.csv"
            write_leads(path, leads)
            loaded = read_leads(path)
            self.assertEqual(loaded[0].email, "demo@example.com")
            report = Path(td) / "r.md"
            write_report(report, 1, loaded, 0)
            self.assertTrue(report.exists())


if __name__ == "__main__":
    unittest.main()
