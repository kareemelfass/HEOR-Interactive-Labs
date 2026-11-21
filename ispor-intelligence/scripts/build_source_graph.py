#!/usr/bin/env python3
"""Build a source-only ISPOR Europe 2026 KG with explicit provenance.

No keyword inference, method-use inference, author disambiguation, or gap inference.
The output is complete relative to the pinned independent source snapshot,
not certified as the final official ISPOR conference universe.

Full copyright-protected abstract prose is not republished. Its section lengths
and SHA-256 digests are retained for identity checking, with official source links.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import urllib.request
from pathlib import Path

SOURCE = "https://justinsyu.github.io/ispor-eu-nov-2026/ispor_europe_2026_abstracts.json"
EXPECTED = 3097
ORIGIN = "independent pre-conference snapshot, collected 2026-08-24"
ROOT = Path(__file__).resolve().parents[1]
FIELDS = (
    "uid", "abstract_number", "session_code", "title", "authors",
    "source_authors_affiliations", "normalized_authors", "affiliations",
    "normalized_institutions", "section_labels", "session_type", "track",
    "categories", "category_path", "diseases", "disease_path",
    "area_of_study", "display_date", "session_date", "published",
    "meeting", "journal", "source_pdf_url", "url", "source_url",
    "pdfs", "pdf_count", "is_structured", "word_count"
)
TEXT_FIELDS = ("summary", "sections")
REQUIRED = ("uid", "abstract_number", "title", "source_url", "categories")
URL = re.compile(r"^https://www\.ispor\.org/heor-resources/presentations-database/", re.I)


def sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()


def nonempty(value):
    return value is not None and value != "" and value != [] and value != {}


def load_source(location: str):
    if location.startswith(("http://", "https://")):
        req = urllib.request.Request(location, headers={"User-Agent": "ISPOR-source-integrity-build/2.0"})
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.load(r)
    return json.loads(Path(location).read_text(encoding="utf-8"))


def normalised_text_items(row, field):
    """Preserve archive-normalised strings exactly without merging identities."""
    values = row.get(field)
    if not isinstance(values, list):
        return []
    return [v for v in values if isinstance(v, str) and v.strip()]


def build(data, source_url: str, expected: int = EXPECTED):
    if not isinstance(data, list):
        raise ValueError("The pinned archive must be a JSON array, not an inferred nested structure")
    if len(data) != expected:
        raise ValueError(f"Source snapshot changed: expected {expected}, observed {len(data)}. "
                         "Stop rather than silently representing the changed source as a validated snapshot.")
    if not all(isinstance(row, dict) for row in data):
        raise ValueError("Source contains a non-object record")
    fieldnames = sorted(set().union(*(r.keys() for r in data)))
    unknown_fields = sorted(set(fieldnames) - set(FIELDS) - set(TEXT_FIELDS))
    if unknown_fields:
        raise ValueError("New source fields require explicit mapping before publication: " +
                         ", ".join(unknown_fields))
    records = []
    errors = []
    unique_uid, unique_url = set(), set()
    for position, row in enumerate(data):
        missing = [field for field in REQUIRED if not nonempty(row.get(field))]
        if missing:
            errors.append({"row": position, "issue": "required_fields_missing", "fields": missing})
            continue
        identifier = row["uid"]
        url = row["source_url"]
        if not isinstance(identifier, str) or not isinstance(url, str) or not URL.match(url):
            errors.append({"row": position, "issue": "uid_or_official_url_invalid"})
            continue
        if identifier in unique_uid or url in unique_url:
            errors.append({"row": position, "issue": "duplicate_uid_or_url", "uid": identifier})
            continue
        unique_uid.add(identifier)
        unique_url.add(url)
        record = {field: row.get(field) for field in FIELDS}
        # Keep an exact archive object reference by UID. Authors/institutions are
        # preserved as source text; no inferred person identity or affiliations.
        record.update({
            "id": identifier,
            "source_row": position,
            "year": 2026,
            "source_provenance": "independent_archive",
            "source_snapshot": ORIGIN,
            "abstract_summary_sha256": sha(row.get("summary")),
            "abstract_sections_sha256": sha(row.get("sections")),
            "abstract_summary_character_count": len(row.get("summary") or "")
                if isinstance(row.get("summary"), str) else None,
            "abstract_section_names": list(row.get("sections", {}).keys())
                if isinstance(row.get("sections"), dict) else [],
            "full_abstract_reproduced": False,
        })
        records.append(record)
    if errors or len(records) != expected:
        raise ValueError(f"Cannot certify source record identity: {len(errors)} errors, "
                         f"{len(records)}/{expected} retained; examples: {errors[:5]}")
    graph_nodes = []
    graph_edges = []
    seen_entities = set()
    def entity(node_id, type_name, label, **extra):
        if node_id not in seen_entities:
            seen_entities.add(node_id)
            graph_nodes.append({"id": node_id, "type": type_name, "label": label, **extra})
    def connect(src, dst, relation, field, source_row):
        graph_edges.append({"source": src, "target": dst, "relation": relation,
                            "provenance": {"source": "archive", "source_row": source_row, "field": field,
                                           "assertion": "literal value, not inferred"}})
    for record in records:
        uid = record["uid"]
        pid = "presentation:" + uid
        entity(pid, "presentation", record["title"], record_id=uid,
               abstract_number=record["abstract_number"], url=record["source_url"])
        fields = (
            ("categories", "archive_topic", "ARCHIVE_CATEGORISES_AS"),
            ("category_path", "archive_topic_path", "ARCHIVE_TOPIC_PATH"),
            ("diseases", "archive_disease_area", "ARCHIVE_DISEASE"),
            ("disease_path", "archive_disease_path", "ARCHIVE_DISEASE_PATH"),
        )
        for field, typ, relation in fields:
            values = record.get(field) or []
            if not isinstance(values, list):
                raise ValueError(f"Unexpected {field} type for record {uid}")
            for name in sorted(set(v for v in values if isinstance(v, str) and v.strip())):
                eid = typ + ":" + sha(name)[:20]
                entity(eid, typ, name)
                connect(pid, eid, relation, field, record["source_row"])
        for field, typ, relation in (
            ("track", "archive_track", "ARCHIVE_TRACK"),
            ("session_type", "archive_session", "ARCHIVE_SESSION"),
            ("session_date", "archive_session_date", "ARCHIVE_DATE"),
        ):
            name = record.get(field)
            if isinstance(name, str) and name.strip():
                eid = typ + ":" + sha(name)[:20]
                entity(eid, typ, name)
                connect(pid, eid, relation, field, record["source_row"])
        # Deliberately *scoped per presentation*. Identically named people are
        # NOT merged. The archive's name-normalisation is not identity evidence.
        for field, typ, relation in (
            ("normalized_authors", "author_name_mention", "ARCHIVE_LISTS_AUTHOR_NAME"),
            ("normalized_institutions", "institution_name_mention", "ARCHIVE_LISTS_INSTITUTION_NAME"),
            ("affiliations", "affiliation_text", "ARCHIVE_LISTS_AFFILIATION_TEXT"),
        ):
            for j, name in enumerate(normalised_text_items(record, field)):
                eid = typ + ":" + uid + ":" + str(j)
                entity(eid, typ, name, parent_record_uid=uid, source_order=j,
                       not_unique_person_or_organisation=True)
                connect(pid, eid, relation, field, record["source_row"])
        # Do not create person -> organisation, sponsor, effect, gap or
        # methodology edges, since the source does not establish them.
    counts = collections.Counter()
    available = collections.Counter()
    for row in data:
        for field in FIELDS + TEXT_FIELDS:
            counts[field] += 1
            if nonempty(row.get(field)):
                available[field] += 1
    missing = {k: counts[k] - available[k] for k in FIELDS + TEXT_FIELDS}
    sourcehash = sha(data)
    foundation = {
        "dataset": "ISPOR Europe 2026 presentation archive",
        "source_url": source_url,
        "source_type": "independent_archive_not_official_final_census",
        "snapshot": ORIGIN,
        "source_sha256": sourcehash,
        "input_records": len(data),
        "retained_records": len(records),
        "identity_and_url_completeness": True,
        "primary_source_record_urls_present": len(records),
        "assumptions_used_for_graph_edges": False,
        "source_only_graph": True,
        "provenance_scope": "Each graph edge is directly determined from an exact source metadata field.",
        "full_abstract_text_redistributed": False,
        "abstracts_available_at_original_sources": True,
        "unverified": ["completeness_against_final_November_2026_official_ISPOR_census",
                       "HTTP_content_and_pdf_availability_for_every_2026_source_url",
                       "accuracy_of_independent_archive_transcription",
                       "accuracy_of_archive_normalised_author_and_institution_strings"],
    }
    graph = {"metadata": foundation, "nodes": graph_nodes, "edges": graph_edges}
    indexed = {"metadata": foundation, "records": records}
    check = {
        "metadata": foundation,
        "source_schema_fields": fieldnames,
        "preserved_fields": list(FIELDS),
        "intentionally_not_redistributed_abstract_fields": list(TEXT_FIELDS),
        "source_nonempty_counts": dict(available),
        "source_missing_counts": missing,
        "relationship_types": dict(collections.Counter(e["relation"] for e in graph_edges)),
        "node_types": dict(collections.Counter(n["type"] for n in graph_nodes)),
        "records_with_one_or_more_pdf": sum(bool(r.get("pdf_count")) for r in records),
        "records_with_normalised_author_names": sum(bool(r.get("normalized_authors")) for r in records),
        "records_with_normalised_institution_names": sum(bool(r.get("normalized_institutions")) for r in records),
        "validation_issues": errors,
    }
    summary = {
        "metadata": foundation,
        "source_categories": dict(collections.Counter(
            x for r in records for x in set(r["categories"] or []))).copy(),
        "source_diseases": dict(collections.Counter(
            x for r in records for x in set(r["diseases"] or []))).copy(),
        "source_tracks": dict(collections.Counter(
            r.get("track") for r in records if r.get("track"))),
    }
    return indexed, graph, check, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=SOURCE)
    parser.add_argument("--output-dir", default=str(ROOT / "data"))
    parser.add_argument("--expected-records", type=int, default=EXPECTED)
    args = parser.parse_args()
    raw = load_source(args.source)
    index, graph, coverage, summary = build(raw, args.source, args.expected_records)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, value in [
        ("source-records.json", index),
        ("source-knowledge-graph.json", graph),
        ("source-coverage.json", coverage),
        ("source-summary.json", summary),
    ]:
        (out / name).write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(name, "records:", len(value.get("records", [])), "nodes:", len(value.get("nodes", [])),
              "edges:", len(value.get("edges", [])))
    print("SOURCE_FIDELITY", json.dumps({
        "record_count": len(index["records"]),
        "node_count": len(graph["nodes"]),
        "edge_count": len(graph["edges"]),
        "source_sha256": index["metadata"]["source_sha256"],
        "missing_fields": {k:v for k,v in coverage["source_missing_counts"].items() if v},
        "edge_types": coverage["relationship_types"],
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
