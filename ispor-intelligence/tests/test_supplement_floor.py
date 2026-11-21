#!/usr/bin/env python3
"""Floor counts must not mix historical page checks into current recheck evidence."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_official_supplement import build

HOST = "https://www.ispor.org/heor-resources/presentations-database/"
def initial(code):
    return {
        "reconciliation_status": "archive_only_not_in_official_index",
        "page_status": "official_page_title_code_verified",
        "http_status": 200, "title_match": True, "code_match": True,
        "archive_code": code, "archive_title": "Title " + code,
        "page_url": HOST + code, "page_text_sha256": "hash" + code,
    }
def latest(code, status):
    return {
        "original_reconciliation_status": "archive_only_not_in_official_index",
        "classification": status, "archive_code": code,
        "archive_title": "Title " + code, "archived_url": HOST + code,
        "observations": [{
            "checked_at_utc": "2026-11-21T17:00:00+00:00",
            "http_status": 200 if status == "heading_and_code_verified" else 404,
            "code_match_in_primary_content": status == "heading_and_code_verified",
            "archived_title_match_heading_or_meta": status == "heading_and_code_verified",
            "page_html_sha256": "new-hash-" + code,
        }],
    }


class SupplementFloorTests(unittest.TestCase):
    def setUp(self):
        self.history = {"metadata": {"checked_at_utc": "2026-11-21T13:45:00+00:00"},
                        "results": [initial("P1"), initial("P2")]}
        self.index = {"records": [{"url": HOST + "index", "code": "P0"}]}

    def test_no_recheck_uses_historical_basis(self):
        result = build(self.history, None, self.index)
        self.assertEqual(result["metadata"]["verification_basis"], "historical_first_check")
        self.assertEqual(result["metadata"]["count"], 2)

    def test_current_floor_excludes_old_match_that_is_now_404(self):
        current = {"metadata": {"controls_passed": True,
                                "checked_at_utc": "2026-11-21T17:01:00+00:00"},
                   "results": [latest("P1", "repeated_http_404_unconfirmed"),
                               latest("P2", "heading_and_code_verified"),
                               latest("P3", "heading_and_code_verified")]}
        result = build(self.history, current, self.index)
        self.assertEqual(result["metadata"]["verification_basis"], "latest_controlled_recheck")
        self.assertEqual(result["metadata"]["historical_first_check_matches"], 2)
        self.assertEqual(result["metadata"]["count"], 2)
        self.assertEqual({r["presentation_code"] for r in result["records"]}, {"P2", "P3"})

    def test_uncontrolled_recheck_cannot_supply_floor(self):
        latest_bad = {"metadata": {"controls_passed": False}, "results": []}
        with self.assertRaises(ValueError):
            build(self.history, latest_bad, self.index)

    def test_existing_index_code_is_excluded_even_if_url_changed(self):
        idx = {"records": [{"url": HOST + "different-url", "code": "P2"}]}
        result = build(self.history, None, idx)
        self.assertEqual([r["presentation_code"] for r in result["records"]], ["P1"])


if __name__ == "__main__":
    unittest.main()
