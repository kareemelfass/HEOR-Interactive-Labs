#!/usr/bin/env python3
"""Behavioural tests for ISPOR page identification, not live-site validation."""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_discrepant_pages import PrimaryPage, heading_matches, code_in, spaced_404_observation


class DiscrepantPageParserTests(unittest.TestCase):
    def parse(self, html):
        page = PrimaryPage()
        page.feed(html)
        return page

    def test_suffixed_browser_title_matches_without_h1(self):
        page = self.parse("<html><head><title>Diabetes Control and Mortality | ISPOR</title></head>"
                          "<body><p>Presentation P41</p></body></html>")
        self.assertTrue(heading_matches(page, "Diabetes Control and Mortality"))
        self.assertFalse(page.has_main)
        self.assertTrue(code_in(" ".join(page.body_chunks), "P41"))

    def test_primary_h1_is_exact_match(self):
        page = self.parse("<html><body><h1>Diabetes Control and Mortality</h1>"
                          "<main><div>Presentation P41</div></main></body></html>")
        self.assertTrue(heading_matches(page, "Diabetes Control and Mortality"))
        self.assertTrue(page.has_main)
        self.assertTrue(code_in(" ".join(page.main_chunks), "P41"))

    def test_prefix_that_is_another_title_is_not_a_match(self):
        page = self.parse("<title>Diabetes Control and Mortality in Europe</title>")
        self.assertFalse(heading_matches(page, "Diabetes Control and Mortality"))

    def test_script_code_does_not_count_as_visible_body(self):
        page = self.parse("<body><script>P41</script><h1>Diabetes Control</h1>"
                          "<p>Presentation P42</p></body>")
        self.assertFalse(code_in(" ".join(page.body_chunks), "P41"))
        self.assertFalse(code_in(" ".join(page.body_chunks), "P4"))

    def test_main_scope_excludes_unrelated_header_code(self):
        page = self.parse("<body><header>Other P41</header><main><p>P42</p></main></body>")
        self.assertTrue(page.has_main)
        self.assertFalse(code_in(" ".join(page.main_chunks), "P41"))

    def test_404_requires_one_hour_between_runs(self):
        t = datetime(2026, 11, 21, 12, tzinfo=timezone.utc)
        old = {"classification": "repeated_http_404_unconfirmed",
               "observations": [{"checked_at_utc": t.isoformat(), "http_status": 404}]}
        self.assertIsNone(spaced_404_observation("repeated_http_404_unconfirmed", old,
                                                  t + timedelta(minutes=59)))
        self.assertEqual(spaced_404_observation("repeated_http_404_unconfirmed", old,
                                                t + timedelta(hours=2)), t.isoformat())
        self.assertIsNone(spaced_404_observation("heading_and_code_verified", old,
                                                  t + timedelta(hours=2)))


if __name__ == "__main__":
    unittest.main()
