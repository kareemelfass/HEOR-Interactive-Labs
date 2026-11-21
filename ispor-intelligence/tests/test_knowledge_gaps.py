"""Audit tests for explicitly editorial research proposals, not literature gaps."""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class ProposedQuestionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gaps = json.loads((ROOT / "data" / "knowledge-gaps.json").read_text(encoding="utf-8"))
        cls.claims = json.loads((ROOT / "data" / "reviewed-claims.json").read_text(encoding="utf-8"))
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.js = (ROOT / "knowledge-gaps.js").read_text(encoding="utf-8")

    def test_editorial_themes_not_mislabelled_as_index_topics(self):
        themes = self.gaps["themes"]
        names = [x["theme"] for x in themes]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(names), 16)
        self.assertIn("historical editorial", self.gaps["metadata"]["scope"])
        self.assertTrue(all(t["theme_basis"] == "legacy_editorial_not_official_index_topic_group" for t in themes))
        self.assertTrue(all(t["evidence_status"] == "hypotheses_not_literature_verified" for t in themes))
        self.assertNotIn("Knowledge gaps and future directions", self.html)

    def test_every_theme_contains_two_hypotheses(self):
        for theme in self.gaps["themes"]:
            with self.subTest(theme=theme["theme"]):
                self.assertTrue(theme["intro"])
                self.assertEqual(len(theme["items"]), 2)
                for item in theme["items"]:
                    self.assertGreater(len(item["gap"]), 30)
                    self.assertGreater(len(item["direction"]), 50)
                    self.assertGreater(len(item["decision"]), 20)
        self.assertIn("Unverified research hypothesis", self.js)

    def test_claims_are_context_not_proof(self):
        ids = {claim["id"] for claim in self.claims["claims"]}
        for theme in self.gaps["themes"]:
            self.assertTrue(set(theme.get("claimIds", [])) <= ids)
            self.assertEqual(theme["claim_relation"], "context_only_not_support_established")
        self.assertIn("context only", self.html.lower())
        self.assertIn("not validation of the hypotheses", self.js.lower())

    def test_no_dead_related_presentation_claim(self):
        self.assertNotIn("function linkedPresentations(", self.js)
        self.assertNotIn("function related(", self.js)
        self.assertNotIn("Related ISPOR presentations", self.html)
        self.assertNotIn("Related presentations are examples", self.html)

    def test_tab_is_renderable(self):
        self.assertEqual(self.html.count('data-tab="gaps"'), 1)
        self.assertEqual(self.html.count('id="panel-gaps"'), 1)
        self.assertIn('id="kgGapsCount"', self.html)
        self.assertIn('id="kgGapsContent"', self.html)
        self.assertIn('src="./knowledge-gaps.js"', self.html)
        self.assertIn('getJson("./data/reviewed-claims.json")', self.js)
        ids = re.findall(r'\bid="([^"]+)"', self.html)
        self.assertEqual(len(ids), len(set(ids)))

if __name__ == "__main__":
    unittest.main()
