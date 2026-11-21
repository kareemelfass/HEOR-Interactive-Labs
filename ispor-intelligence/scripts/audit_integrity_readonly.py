#!/usr/bin/env python3
"""Read-only ISPOR source-integrity audit. Does not alter the graph."""
import json
from pathlib import Path
from collections import Counter
from urllib.request import Request, urlopen

root=Path(__file__).resolve().parents[1]
source="https://justinsyu.github.io/ispor-eu-nov-2026/ispor_europe_2026_abstracts.json"
raw=json.load(urlopen(Request(source,headers={"User-Agent":"ISPOR-Audit/1.0"}),timeout=70))
from importlib.machinery import SourceFileLoader
builder=SourceFileLoader("builder",str(root/"scripts"/"build_kg.py")).load_module()
original=builder.extract_rows(raw)
data=root/"data"
index=json.loads((data/"records-index.json").read_text())
graph=json.loads((data/"knowledge-graph.json").read_text())
summary=json.loads((data/"summary.json").read_text())
gaps=json.loads((data/"knowledge-gaps.json").read_text())
claims=json.loads((data/"reviewed-claims.json").read_text())
records=index["records"]
present=Counter()
for r in original:
 for k,v in r.items():
  if v is not None and v!="" and v!=[]:present[k]+=1
index_fields=set(records[0])
omitted={k:v for k,v in present.items() if k not in index_fields}
src_urls={r.get("source_url") or r.get("url") for r in original}
idx_urls={r["url"] for r in records}
device=[r for r in records if "Medical devices" in r["tags"] and "Medical Technologies" in r.get("source_categories",[]) and not any(x in r["title"].lower() for x in ("device","medtech","medical technolog","digital therapeutic","implant","diagnostic","robotic"))]
nodetypes=Counter(n["type"] for n in graph["nodes"])
edgetypes=Counter(e.get("relation") or e.get("type") for e in graph["edges"])
codes={r["id"] for r in records}
claimcodes={c["presentation_code"] for c in claims["claims"]}
out={
 "source":"Independent pre-conference archive, NOT a final November census",
 "source_rows":len(original),
 "indexed_rows":len(records),
 "published_index_fields":sorted(index_fields),
 "omitted_fields_with_nonempty_source_rows":dict(sorted(omitted.items())),
 "source_urls_absent_from_index":len((src_urls-idx_urls)-{None}),
 "index_urls_absent_from_source":len((idx_urls-src_urls)-{None}),
 "index_rows_with_preserved_abstract":sum(bool(r.get("abstract") or r.get("sections") or r.get("summary")) for r in records),
 "build_claims_abstract_present":index["metadata"].get("abstract_text_present"),
 "ambiguous_device_classifications_using_archive_category":len(device),
 "device_examples":[{"id":r["id"],"title":r["title"]} for r in device[:12]],
 "gap_themes_without_manual_claims":[g["theme"] for g in gaps["themes"] if not g.get("claimIds")],
 "analyst_proposed_gap_count":sum(len(g["items"]) for g in gaps["themes"]),
 "manual_claim_count":len(claims["claims"]),
 "manual_claim_codes_not_in_index":sorted(claimcodes-codes),
 "graph_node_types":dict(nodetypes),
 "graph_relationship_types":dict(edgetypes),
 "index_and_summary_same_count":len(records)==summary["metadata"]["unique_usable_records"]
}
print("AUDIT_REPORT_START")
print(json.dumps(out,indent=2,ensure_ascii=False))
print("AUDIT_REPORT_END")
