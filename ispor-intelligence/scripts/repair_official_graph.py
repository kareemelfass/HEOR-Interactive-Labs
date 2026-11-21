#!/usr/bin/env python3
"""Deterministic repair of a published ISPOR index graph's node types.

The original graph classified every indexed item as a presentation, even
when the official source field identified it as a session. This repair uses
the exact saved index_content_kind, without contacting a live source or
introducing new graph edges or unsourced claims.

The command is idempotent. --check-only validates an already-repaired file.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "data" / "official-index-records.json"
GRAPH = ROOT / "data" / "official-index-graph.json"

def repair(index: dict, graph: dict) -> dict:
    records = index["records"]
    kinds = {r["uid"]: ("session" if r["index_content_kind"] == "Confex Session"
                         else "presentation" if r["index_content_kind"] == "Confex Presentation"
                         else None) for r in records}
    if None in kinds.values():
        raise ValueError("Unexpected source index item type; do not guess presentation status")
    assert len(kinds) == len(records), "Duplicate source UID"
    nodes = graph["nodes"]
    old_to_new = {}
    presentation_count = 0
    session_count = 0
    for node in nodes:
        if node["id"].startswith(("presentation:", "session:")):
            old_id = node["id"]
            uid = old_id.split(":", 1)[1]
            if uid not in kinds:
                raise ValueError("Graph node absent from official records: " + uid)
            kind = kinds[uid]
            node["type"] = kind
            node["id"] = kind + ":" + uid
            old_to_new[old_id] = node["id"]
            if kind == "session":
                session_count += 1
            else:
                presentation_count += 1
    for edge in graph["edges"]:
        edge["source"] = old_to_new.get(edge["source"], edge["source"])
        edge["target"] = old_to_new.get(edge["target"], edge["target"])
    ids = {n["id"] for n in nodes}
    assert len(ids) == len(nodes), "Duplicated repaired IDs"
    assert all(e["source"] in ids and e["target"] in ids for e in graph["edges"])
    assert presentation_count == Counter(r["index_content_kind"] for r in records)["Confex Presentation"]
    assert session_count == Counter(r["index_content_kind"] for r in records)["Confex Session"]
    assert presentation_count + session_count == len(records)
    graph["metadata"]["presentation_nodes"] = presentation_count
    graph["metadata"]["session_nodes"] = session_count
    graph["metadata"]["graph_subject_types_from_index_content_kind"] = True
    return graph

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--check-only", action="store_true")
    args = p.parse_args()
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    repaired = repair(index, graph)
    changed = repaired != graph  # graph mutated in place, so inspect source file for changes below
    source = GRAPH.read_text(encoding="utf-8")
    output = json.dumps(repaired, ensure_ascii=False, separators=(",", ":"))
    if args.check_only:
        assert json.loads(source) == repaired, "Graph is not repaired"
    elif json.loads(source) != repaired:
        GRAPH.write_text(output, encoding="utf-8")
    print("OFFICIAL_GRAPH_TYPES_OK", {"presentations": repaired["metadata"]["presentation_nodes"],
                                     "sessions": repaired["metadata"]["session_nodes"],
                                     "edges": len(repaired["edges"]),
                                     "changed": source != output and not args.check_only})

if __name__ == "__main__":
    main()
