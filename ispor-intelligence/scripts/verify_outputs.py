#!/usr/bin/env python3
"""Validate published ISPOR metadata and ensure the dashboard has required assets."""
import json
import pathlib
import re

ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
index=json.loads((DATA/"records-index.json").read_text())
graph=json.loads((DATA/"knowledge-graph.json").read_text())
summary=json.loads((DATA/"summary.json").read_text())
rows=index["records"]
nodes=graph["nodes"]
edges=graph["edges"]
assert len(rows)>=3000, f"Insufficient indexed records: {len(rows)}"
assert len(rows)==summary["metadata"]["unique_usable_records"]
assert len(rows)==graph["metadata"]["unique_usable_records"]
assert all(r.get("title") and r.get("id") and r.get("year")==2026 for r in rows)
assert all(re.match(r"^https://(?:www\.)?ispor\.org/",r.get("url") or "") for r in rows), "Missing official ISPOR links"
node_ids=[n["id"] for n in nodes]
assert len(node_ids)==len(set(node_ids)), "Duplicate KG node ID"
node_set=set(node_ids)
assert all(e.get("source") in node_set and e.get("target") in node_set for e in edges), "Dangling KG relationship"
assert any(n.get("type")=="reported_claim" for n in nodes)
assert any(e.get("relation")=="REPORTS" for e in edges)
assert any(e.get("relation")=="MENTIONS" for e in edges)
assert (ROOT/"index.html").is_file() and (ROOT/"app.js").is_file() and (ROOT/"styles.css").is_file()
for s in ('id="metricRecords"','id="graphCanvas"','id="resultList"'):
    assert s in (ROOT/"index.html").read_text(), f"Missing {s} in dashboard"
print("CHECKS PASSED",{
    "records":len(rows),"nodes":len(nodes),"edges":len(edges),
    "reviewed_claims":sum(n.get("type")=="reported_claim" for n in nodes),
    "official_links":sum(bool(r.get("url")) for r in rows)
})
