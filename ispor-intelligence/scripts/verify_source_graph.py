#!/usr/bin/env python3
"""Independent source-graph audit, against the original archive, not only graph internals."""
from __future__ import annotations
import collections
import json
from pathlib import Path
from importlib.machinery import SourceFileLoader

ROOT=Path(__file__).resolve().parents[1]
builder=SourceFileLoader("build_source_graph",str(ROOT/"scripts"/"build_source_graph.py")).load_module()
raw=builder.load_source(builder.SOURCE)
index=json.loads((ROOT/"data"/"source-records.json").read_text(encoding="utf-8"))
graph=json.loads((ROOT/"data"/"source-knowledge-graph.json").read_text(encoding="utf-8"))
coverage=json.loads((ROOT/"data"/"source-coverage.json").read_text(encoding="utf-8"))
rows=index["records"]
assert len(raw)==len(rows)==3097, "Record mismatch"
assert graph["metadata"]["source_sha256"]==builder.sha(raw)
assert not graph["metadata"]["full_abstract_text_redistributed"]
assert graph["metadata"]["source_only_graph"]
assert not any(n["type"] in ("research_gap","inferred_method","sponsor","person") for n in graph["nodes"])
for i,(source,record) in enumerate(zip(raw,rows)):
    assert record["source_row"]==i, ("Row reorder",i)
    assert record["id"]==source["uid"], ("UID mismatch",i)
    for field in builder.FIELDS:
        assert record[field]==source.get(field), ("Changed source metadata",i,field)
    assert record["abstract_summary_sha256"]==builder.sha(source.get("summary"))
    assert record["abstract_sections_sha256"]==builder.sha(source.get("sections"))
nodes={n["id"]:n for n in graph["nodes"]}
assert len(nodes)==len(graph["nodes"]), "Duplicate node IDs"
expected=collections.Counter()
for edge in graph["edges"]:
    assert edge["source"] in nodes and edge["target"] in nodes
    provenance=edge["provenance"]
    assert provenance["source"]=="archive" and provenance["assertion"]=="literal value, not inferred"
    source=raw[provenance["source_row"]]
    field=provenance["field"]
    assert field in builder.FIELDS
    srcnode=nodes[edge["source"]]
    dstnode=nodes[edge["target"]]
    assert srcnode["type"]=="presentation"
    assert srcnode["record_id"]==source["uid"]
    value=source.get(field)
    if isinstance(value,list):
        assert dstnode["label"] in value, ("Edge not supported by source field",field,dstnode["label"])
    else:
        assert dstnode["label"]==value, ("Edge not supported by source field",field,dstnode["label"])
    expected[edge["relation"]]+=1
assert len([n for n in graph["nodes"] if n["type"]=="presentation"])==3097
assert dict(expected)==coverage["relationship_types"]
print("SOURCE_GRAPH_AUDIT_OK",json.dumps({
    "rows":len(rows),"nodes":len(nodes),"edges":len(graph["edges"]),
    "author_name_links":expected["ARCHIVE_LISTS_AUTHOR_NAME"],
    "organisation_name_links":expected["ARCHIVE_LISTS_INSTITUTION_NAME"],
    "source_sha256":graph["metadata"]["source_sha256"]
}))
