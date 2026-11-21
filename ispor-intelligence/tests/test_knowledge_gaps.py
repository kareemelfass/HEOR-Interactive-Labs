"""Regression tests for the additive ISPOR knowledge-gaps feature.

No existing dashboard source is rewritten or reclassified.
"""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class KnowledgeGapsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gaps = json.loads((ROOT / "data" / "knowledge-gaps.json").read_text(encoding="utf-8"))
        cls.claims = json.loads((ROOT / "data" / "reviewed-claims.json").read_text(encoding="utf-8"))
        cls.summary = json.loads((ROOT / "data" / "summary.json").read_text(encoding="utf-8"))
        cls.index = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.js = (ROOT / "knowledge-gaps.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "knowledge-gaps.css").read_text(encoding="utf-8")
        cls.existing_js = (ROOT / "app.js").read_text(encoding="utf-8")

    def test_all_existing_themes_covered_exactly_once(self):
        themes = [g["theme"] for g in self.gaps["themes"]]
        existing_themes = set(self.summary["themes"])
        self.assertEqual(len(themes), 16)
        self.assertEqual(set(themes), existing_themes)
        self.assertEqual(len(themes), len(set(themes)))

    def test_each_theme_contains_two_actionable_questions(self):
        for theme in self.gaps["themes"]:
            with self.subTest(theme=theme["theme"]):
                self.assertTrue(theme["intro"])
                self.assertEqual(len(theme["items"]), 2)
                for item in theme["items"]:
                    self.assertGreater(len(item["gap"]), 30)
                    self.assertGreater(len(item["direction"]), 50)
                    self.assertGreater(len(item["decision"]), 20)

    def test_reviewed_evidence_claims_exist(self):
        ids = {claim["id"] for claim in self.claims["claims"]}
        for theme in self.gaps["themes"]:
            with self.subTest(theme=theme["theme"]):
                self.assertTrue(set(theme.get("claimIds", [])) <= ids)

    def test_evidence_language_does_not_overclaim(self):
        page = self.index
        self.assertIn("analytical hypotheses", page)
        self.assertIn("not automatically established", page)
        self.assertIn("not proof of an evidence gap", page)
        self.assertIn('id="kgGapsCount"', page)
        self.assertIn('id="kgGapsContent"', page)

    def test_new_tab_is_wired_without_duplicate_ids(self):
        self.assertEqual(self.index.count('data-tab="gaps"'), 1)
        self.assertEqual(self.index.count('id="panel-gaps"'), 1)
        self.assertEqual(self.index.count('src="./app.js"'), 1)
        self.assertEqual(self.index.count('src="./knowledge-gaps.js"'), 1)
        self.assertEqual(self.index.count('href="./knowledge-gaps.css"'), 1)
        ids = re.findall(r'\bid="([^"]+)"', self.index)
        self.assertEqual(len(ids), len(set(ids)))

    def test_addon_does_not_mutate_existing_dashboard_app(self):
        self.assertNotIn("window.location =", self.js)
        self.assertNotIn(".innerHTML", self.js)
        self.assertIn('getJson("./data/records-index.json")', self.js)
        self.assertIn('getJson("./data/reviewed-claims.json")', self.js)
        self.assertIn("sourceUrl(", self.js)

    def test_existing_archive_census_unchanged(self):
        self.assertEqual(self.summary["metadata"]["input_rows"], 3097)
        self.assertEqual(self.summary["metadata"]["unique_usable_records"], 3097)


if __name__ == "__main__":
    unittest.main()
