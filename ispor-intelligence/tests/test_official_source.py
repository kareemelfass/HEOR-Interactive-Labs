"""Source-of-truth regression tests. No external website requests are made."""
import collections
import json
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=ROOT/"data"

class OfficialSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index=json.loads((DATA/"official-index-records.json").read_text(encoding="utf-8"))
        cls.graph=json.loads((DATA/"official-index-graph.json").read_text(encoding="utf-8"))
        cls.summary=json.loads((DATA/"official-index-summary.json").read_text(encoding="utf-8"))
        cls.reconciliation=json.loads((DATA/"official-reconciliation.json").read_text(encoding="utf-8"))
        cls.js=(ROOT/"app.js").read_text(encoding="utf-8")
        cls.html=(ROOT/"index.html").read_text(encoding="utf-8")
        cls.gap_js=(ROOT/"knowledge-gaps.js").read_text(encoding="utf-8")

    def test_backend_provenance_and_census_caveats(self):
        md=self.index["metadata"]
        self.assertIn("ISPOR website configured",md["source"])
        self.assertTrue(md["independent_archive_not_used_for_official_records"])
        self.assertFalse(md["point_in_time_census_verified"])
        self.assertTrue(md["source_count_discrepancy_unresolved"])
        self.assertEqual(md["records"],len(self.index["records"]))

    def test_official_item_subtypes_and_source_urls(self):
        rows=self.index["records"]
        self.assertGreater(len(rows),2500)
        self.assertEqual(len(rows),len({r["uid"] for r in rows}))
        self.assertEqual(len(rows),len({r["url"] for r in rows}))
        self.assertEqual(sum(r["index_content_kind"]=="Confex Presentation" for r in rows),
                         self.summary["official_index_content_kinds"]["Confex Presentation"])
        self.assertEqual(sum(r["index_content_kind"]=="Confex Session" for r in rows),
                         self.summary["official_index_content_kinds"]["Confex Session"])
        self.assertTrue(all("www.ispor.org/" in (r.get("url") or "") for r in rows))
        self.assertTrue(all(r["record_source"]=="ISPOR website configured SearchBlox index" for r in rows))

    def test_graph_edges_map_to_direct_fields(self):
        rows={r["uid"]:r for r in self.index["records"]}
        nodes={n["id"]:n for n in self.graph["nodes"]}
        self.assertEqual(len(nodes),len(self.graph["nodes"]))
        fields={"OFFICIAL_INDEX_TOPIC":"topic_groups",
                "OFFICIAL_INDEX_CATEGORY":"category_paths",
                "OFFICIAL_INDEX_DISEASE":"disease_areas",
                "OFFICIAL_INDEX_SESSION":"parent_session"}
        for e in self.graph["edges"]:
            self.assertIn(e["source"],nodes)
            self.assertIn(e["target"],nodes)
            self.assertFalse(e["provenance"]["inferred"])
            uid=e["provenance"]["record_uid"]
            self.assertEqual(e["source"],"presentation:"+uid)
            source=rows[uid]
            field=fields[e["relation"]]
            self.assertEqual(e["provenance"]["source_field"],field)
            values=source[field]
            if isinstance(values,list):
                self.assertIn(nodes[e["target"]]["label"],values)
            else:
                self.assertEqual(nodes[e["target"]]["label"],values)

    def test_reconciliation_is_lossless(self):
        rec=self.reconciliation
        self.assertEqual(rec["archive_records"],len(rec["archive_to_official"]))
        counts=collections.Counter(x["status"] for x in rec["archive_to_official"])
        self.assertEqual(dict(counts),self.summary["comparison"]["archive_reconciliation_status"])
        self.assertEqual(len(rec["official_only"]),
                         self.summary["comparison"]["official_index_not_matched_to_archive"])

    def test_main_dashboard_is_official_first_and_archive_not_fallback(self):
        self.assertIn('fetch("./data/official-index-records.json"',self.js)
        self.assertIn('fetch("./data/official-index-graph.json"',self.js)
        self.assertIn('async function loadOfficialIndex()',self.js)
        start=self.js.index("async function init(){")
        end=self.js.index("\n bind();",start)
        init=self.js[start:end]
        self.assertIn("await loadOfficialIndex()",init)
        self.assertNotIn("await loadArchive()",init)
        self.assertNotIn("await loadLocalIndex()",init)
        self.assertNotIn("await loadSeed()",init)
        self.assertIn('getJson("./data/official-index-records.json")',self.gap_js)
        self.assertNotIn('getJson("./data/records-index.json")',self.gap_js)

    def test_main_dashboard_exposes_reconciliation_and_uncertainty(self):
        self.assertIn('id="officialReconciliation"',self.html)
        self.assertIn('id="metricRecords"',self.html)
        self.assertIn("not a verified final-conference census",self.html)
        self.assertIn("official-reconciliation.json",self.html)

if __name__=="__main__":
    unittest.main()
