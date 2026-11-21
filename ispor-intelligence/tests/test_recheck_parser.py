#!/usr/bin/env python3
"""Behavioural tests for ISPOR page identification, not live-site validation."""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.error import HTTPError
import verify_discrepant_pages as pagecheck

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_discrepant_pages import PrimaryPage, heading_matches, code_in, spaced_404_observation, select_controls


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
                                                  t + timedelta(minutes=59), previous_controls_passed=True))
        self.assertEqual(spaced_404_observation("repeated_http_404_unconfirmed", old,
                                                t + timedelta(hours=2), previous_controls_passed=True), t.isoformat())
        self.assertIsNone(spaced_404_observation("heading_and_code_verified", old,
                                                  t + timedelta(hours=2), previous_controls_passed=True))


    def test_furniture_does_not_supply_code_for_body_fallback(self):
        page = self.parse(
            "<html><head><title>Diabetes Control | ISPOR</title></head>"
            "<body><header><span>P41</span></header>"
            "<nav>Presentation P41</nav><aside>Related P41</aside>"
            "<article>Presentation P42</article>"
            "<footer>P41</footer></body></html>"
        )
        self.assertTrue(heading_matches(page, "Diabetes Control"))
        self.assertFalse(page.has_main)
        self.assertFalse(code_in(" ".join(page.body_chunks), "P41"))
        self.assertTrue(code_in(" ".join(page.body_chunks), "P42"))

    def test_failed_http_control_marks_run_invalid(self):
        from verify_discrepant_pages import HOST_PREFIX
        rows = [{"status": "url_match", "archive_url": HOST_PREFIX + str(i)} for i in range(10)]
        class FakeResponse:
            status = 200
            headers = {"Content-Type": "text/html"}
            def __init__(self, url):
                self.url = url
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def geturl(self):
                return self.url

        def fake_open(req, timeout):
            if req.full_url.endswith("/9"):
                raise HTTPError(req.full_url, 404, "Not Found", {}, None)
            return FakeResponse(req.full_url)

        with TemporaryDirectory() as tmp:
            with patch.object(pagecheck, "CONTROL_OUT", Path(tmp) / "controls.json"), \
                 patch.object(pagecheck.time, "sleep", return_value=None):
                result = pagecheck.check_transport_controls(
                    {"archive_to_official": rows},
                    {"metadata": {"retrieved_at_utc": "2026-11-21T13:00:00+00:00"}},
                    opener=fake_open,
                )
                self.assertFalse(result["metadata"]["controls_passed"])
                self.assertTrue((Path(tmp) / "controls.json").exists())

    def test_control_selection_is_deterministic_and_without_duplicates(self):
        from verify_discrepant_pages import HOST_PREFIX
        rows = [{"status": "url_match", "archive_url": HOST_PREFIX + str(i)}
                for i in range(15)]
        rows.append({"status": "archive_only_not_in_official_index",
                     "archive_url": HOST_PREFIX + "excluded"})
        original = select_controls({"archive_to_official": rows})
        reversed_input = select_controls({"archive_to_official": list(reversed(rows))})
        self.assertEqual(original, reversed_input)
        self.assertEqual(len({r["archive_url"] for r in original}), 10)
        self.assertTrue(all("excluded" not in r["archive_url"] for r in original))

    def test_cross_run_404_refused_if_prior_controls_not_healthy(self):
        t = datetime(2026, 11, 21, 12, tzinfo=timezone.utc)
        old = {"classification": "repeated_http_404_unconfirmed",
               "observations": [{"checked_at_utc": t.isoformat(), "http_status": 404}]}
        self.assertIsNone(spaced_404_observation("repeated_http_404_unconfirmed", old,
                                                 t + timedelta(hours=2),
                                                 previous_controls_passed=False))


if __name__ == "__main__":
    unittest.main()
