"""Regression checks for official-index metadata, source claims and UI semantics."""
import collections
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

class OfficialSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = json.loads((DATA / "official-index-records.json").read_text(encoding="utf-8"))
        cls.graph = json.loads((DATA / "official-index-graph.json").read_text(encoding="utf-8"))
        cls.summary = json.loads((DATA / "official-index-summary.json").read_text(encoding="utf-8"))
        cls.reconciliation = json.loads((DATA / "official-reconciliation.json").read_text(encoding="utf-8"))
        cls.checks = json.loads((DATA / "official-page-checks.json").read_text(encoding="utf-8"))
        cls.claims = json.loads((DATA / "reviewed-claims.json").read_text(encoding="utf-8"))
        cls.js = (ROOT / "app.js").read_text(encoding="utf-8")
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.gap_js = (ROOT / "knowledge-gaps.js").read_text(encoding="utf-8")

    def test_source_index_not_final_census(self):
        meta = self.index["metadata"]
        self.assertIn("ISPOR website configured", meta["source"])
        self.assertTrue(meta["independent_archive_not_used_for_official_records"])
        self.assertFalse(meta["point_in_time_census_verified"])
        self.assertTrue(meta["source_count_discrepancy_unresolved"])
        self.assertEqual(meta["records"], len(self.index["records"]))

    def test_presentation_session_denominators(self):
        records = self.index["records"]
        counts = collections.Counter(r["index_content_kind"] for r in records)
        self.assertEqual(len(records), len({r["uid"] for r in records}))
        self.assertEqual(len(records), len({r["url"] for r in records}))
        self.assertEqual(counts["Confex Presentation"], 2778)
        self.assertEqual(counts["Confex Session"], 139)
        self.assertEqual(dict(counts), self.summary["official_index_content_kinds"])
        self.assertIn('data.records.filter(r=>r.index_content_kind==="Confex Presentation")', self.js)
        self.assertIn('setData(official,"Official ISPOR search index",true,presentations.length,"")', self.js)
        self.assertIn("sessions excluded", self.js)
        self.assertIn("Indexed research presentations", self.html)

    def test_all_graph_edges_are_literal_and_subject_types_are_correct(self):
        rows = {r["uid"]: r for r in self.index["records"]}
        nodes = {n["id"]: n for n in self.graph["nodes"]}
        self.assertEqual(len(nodes), len(self.graph["nodes"]))
        counts = collections.Counter(n["type"] for n in self.graph["nodes"])
        self.assertEqual(counts["presentation"], 2778)
        self.assertEqual(counts["session"], 139)
        field_by_relation = {
            "OFFICIAL_INDEX_TOPIC": "topic_groups",
            "OFFICIAL_INDEX_CATEGORY": "category_paths",
            "OFFICIAL_INDEX_DISEASE": "disease_areas",
            "OFFICIAL_INDEX_SESSION": "parent_session"
        }
        for edge in self.graph["edges"]:
            self.assertIn(edge["source"], nodes)
            self.assertIn(edge["target"], nodes)
            self.assertFalse(edge["provenance"]["inferred"])
            uid = edge["provenance"]["record_uid"]
            source_row = rows[uid]
            kind = "session" if source_row["index_content_kind"] == "Confex Session" else "presentation"
            self.assertEqual(edge["source"], kind + ":" + uid)
            self.assertEqual(nodes[edge["source"]]["type"], kind)
            field = field_by_relation[edge["relation"]]
            self.assertEqual(edge["provenance"]["source_field"], field)
            field_value = source_row[field]
            label = nodes[edge["target"]]["label"]
            self.assertIn(label, field_value) if isinstance(field_value, list) else self.assertEqual(label, field_value)

    def test_reconciliation_and_page_observations_are_lossless(self):
        recon = self.reconciliation
        self.assertEqual(recon["archive_records"], len(recon["archive_to_official"]))
        counts = collections.Counter(x["status"] for x in recon["archive_to_official"])
        self.assertEqual(dict(counts), self.summary["comparison"]["archive_reconciliation_status"])
        self.assertEqual(len(recon["official_only"]), self.summary["comparison"]["official_index_not_matched_to_archive"])
        check_counts = collections.Counter(x["page_status"] for x in self.checks["results"])
        self.assertEqual(dict(check_counts), self.checks["counts"])
        self.assertEqual(sum(check_counts.values()), 374)
        self.assertIn("archive", self.html.lower())
        self.assertIn("HTTP 404 at check time (unconfirmed)", self.js)
        self.assertNotIn('http_404:"Official page returned HTTP 404"', self.js)

    def test_no_legacy_input_as_official_source(self):
        self.assertIn('fetch("./data/official-index-records.json"', self.js)
        self.assertIn('fetch("./data/official-index-graph.json"', self.js)
        self.assertNotIn("function loadSeed()", self.js)
        self.assertNotIn("function loadArchive()", self.js)
        self.assertNotIn("function makeGraph(records)", self.js)
        self.assertIn('async function loadOfficialIndex()', self.js)
        start = self.js.index("async function init(){")
        end = self.js.index("\n bind();", start)
        self.assertIn("await loadOfficialIndex()", self.js[start:end])
        self.assertNotIn('getJson("./data/records-index.json")', self.gap_js)

    def test_proposals_and_claims_are_not_unsupported_results(self):
        self.assertIn("Proposed research questions", self.html)
        self.assertIn("Unverified research hypothesis", self.gap_js)
        self.assertNotIn("Related ISPOR presentations", self.gap_js)
        claims = {c["id"]: c for c in self.claims["claims"]}
        self.assertEqual(len(claims), 10)
        self.assertIn("standard screening-efficiency metric", claims["msr231-wss"]["claim"])
        self.assertIn("ambiguous", claims["hpr213-positions"]["claim"])
        self.assertNotIn("14 of 17", claims["hpr213-positions"]["claim"])
        self.assertEqual(claims["hpr213-positions"]["evidence_status"], "ambiguous_numeric_unverified")

    def test_contraindications_in_dashboard_labels(self):
        self.assertIn('id="diseaseMissing"', self.html)
        self.assertNotIn('id="sourceDiseaseBars"', self.html)
        self.assertIn('const cols=["code","id"', self.js)
        self.assertIn("official-reconciliation.json", self.html)
        self.assertIn("not a verified final-conference census", self.html)

if __name__ == "__main__":
    unittest.main()
