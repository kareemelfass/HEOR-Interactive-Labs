"""Offline regression tests for metadata extraction and safe publication."""
import importlib.util
import pathlib
import unittest

MODULE = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "build_kg.py"
spec = importlib.util.spec_from_file_location("build_kg", MODULE)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PipelineTests(unittest.TestCase):
    def sample(self):
        return {
            "records": [
                {
                    "title": "A TEST OF EU JOINT CLINICAL ASSESSMENT AND ML-NMR",
                    "abstract_number": "P101",
                    "source_url": "https://www.ispor.org/heor-resources/presentations-database/test",
                    "abstract": {
                        "objectives": "Review JCA evidence and conditional survival modelling.",
                        "methods": "Applied ML-NMR to comparative evidence.",
                    },
                },
                {
                    "title": "TARGET TRIAL EMULATION IN REAL-WORLD EVIDENCE",
                    "abstract_number": "R33",
                    "source_url": "https://example.com/not-an-official-source",
                    "abstract": "Causal inference and propensity score methods.",
                },
            ]
        }

    def test_extract_normalize_and_classify(self):
        records, rows = builder.build(self.sample(), allow_small=True)
        self.assertEqual((len(records), rows), (2, 2))
        self.assertEqual(records[0]["id"], "P101")
        self.assertIn("JCA", records[0]["tags"])
        self.assertIn("ML-NMR", records[0]["tags"])
        self.assertIn("Causal inference", records[1]["tags"])

    def test_does_not_invent_official_urls(self):
        records, _ = builder.build(self.sample(), allow_small=True)
        self.assertIsNone(records[1]["url"])

    def test_metadata_graph_has_only_mention_edges(self):
        records, n = builder.build(self.sample(), allow_small=True)
        graph, index, summary = builder.outputs(records, n, "test.json")
        self.assertEqual(len(index["records"]), 2)
        self.assertTrue(graph["edges"])
        self.assertTrue(all(e["relation"] == "MENTIONS" for e in graph["edges"]))
        self.assertEqual(summary["metadata"]["linked_ispor_records"], 1)
        self.assertFalse(any("abstract_text" in node for node in graph["nodes"]))

    def test_duplicate_deduplication(self):
        sample = self.sample()
        sample["records"].append(dict(sample["records"][0]))
        records, rows = builder.build(sample, allow_small=True)
        self.assertEqual(rows, 3)
        self.assertEqual(len(records), 2)

    def test_refuses_partial_archive_by_default(self):
        with self.assertRaises(ValueError):
            builder.build(self.sample())


if __name__ == "__main__":
    unittest.main()
