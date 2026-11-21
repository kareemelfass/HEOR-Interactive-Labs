#!/usr/bin/env python3
"""Prepare a separately labelled supplement of title/code-verified official pages.

No new website requests and no attempt to infer missing study data.
This uses the completed direct official-page verification, NOT archive-only
record status or keyword matches as proof.
"""
import json
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
audit=json.loads((ROOT/"data"/"official-page-checks.json").read_text(encoding="utf-8"))
index=json.loads((ROOT/"data"/"official-index-records.json").read_text(encoding="utf-8"))
source_ids={r["code"] for r in index["records"] if r.get("code")}
source_urls={r["url"] for r in index["records"]}
supplement=[]
for result in audit["results"]:
    if result["reconciliation_status"]!="archive_only_not_in_official_index":
        continue
    if result["page_status"]!="official_page_title_code_verified":
        continue
    if result["http_status"]!=200 or not result["title_match"] or not result["code_match"]:
        continue
    url=result["page_url"]
    assert url and url.startswith("https://www.ispor.org/heor-resources/presentations-database/")
    # A refreshed index may now contain an older supplementary page or code.
    # Keep the supplement disjoint from the current index instead of failing.
    if url in source_urls or result["archive_code"] in source_ids:
        continue
    supplement.append({
      "presentation_code": result["archive_code"],
      "title": result["archive_title"],
      "official_verified_url":url,
      "verification_method":"Official ISPOR page returned HTTP 200; normalized full title and presentation code both matched",
      "page_text_sha256":result["page_text_sha256"],
      "verdict":"verified_official_page_absent_from_captured_search_index",
      "source_text_not_redistributed":True,
      "claims_about_authors_methods_results":None,
    })
assert len(supplement)==len({r["official_verified_url"] for r in supplement})
assert len(supplement)==len({r["presentation_code"] for r in supplement})
payload={
 "metadata":{
  "source":"Individually verified official ISPOR presentation pages, not the SearchBlox index",
  "scope":"archive-only candidates validated by HTTP 200 + full matching title + code",
  "count":len(supplement),
  "last_checked_at_utc":audit["metadata"]["checked_at_utc"],
  "generated_at_utc":datetime.now(timezone.utc).isoformat(),
  "not_added_to_search_index_denominator":True,
  "cannot_certify_complete_final_conference":True,
 },
 "records":supplement
}
out=ROOT/"data"/"official-page-verified-supplement.json"
out.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
print("SUPPLEMENT_VERIFIED",len(supplement),"records; no source-index denominator changes")
