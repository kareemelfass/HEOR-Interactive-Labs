#!/usr/bin/env python3
"""Build a disjoint supplement from the latest controlled recheck when available.

The initial one-time HTTP 200/title/code matches remain in official-page-checks.json.
When a transport-control-validated recheck is published, use *that* check for
the current additional-page floor, never silently retain old matches as live.
No abstract text is redistributed and no final programme completeness is claimed.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
HIST = DATA / "official-page-checks.json"
LATEST = DATA / "official-page-recheck-latest.json"
INDEX = DATA / "official-index-records.json"
OUT = DATA / "official-page-verified-supplement.json"
HOST_PREFIX = "https://www.ispor.org/heor-resources/presentations-database/"
LATEST_MATCH = {"heading_and_code_verified", "revised_heading_and_code_verified"}


def build(historical, latest, index):
    source_records = index["records"]
    source_codes = {str(r.get("code") or "").strip().upper() for r in source_records}
    source_urls = {r["url"] for r in source_records}
    initial = [
        r for r in historical["results"]
        if r.get("reconciliation_status") == "archive_only_not_in_official_index"
        and r.get("page_status") == "official_page_title_code_verified"
        and r.get("http_status") == 200
        and r.get("title_match") and r.get("code_match")
    ]
    if latest is not None:
        if not latest.get("metadata", {}).get("controls_passed"):
            raise ValueError("Cannot use a recheck that did not pass transport controls")
        basis = "latest_controlled_recheck"
        matched_at = latest["metadata"]["checked_at_utc"]
        candidates = []
        for r in latest["results"]:
            if r.get("original_reconciliation_status") != "archive_only_not_in_official_index":
                continue
            if r.get("classification") not in LATEST_MATCH:
                continue
            attempt = next((a for a in r.get("observations", [])
                            if a.get("http_status") == 200
                            and a.get("code_match_in_primary_content")
                            and (a.get("archived_title_match_heading_or_meta") or
                                 a.get("current_index_title_match_heading_or_meta"))), None)
            if attempt is None:
                continue
            candidates.append({
                "presentation_code": r["archive_code"],
                "title": r["archived_title"],
                "official_verified_url": r["archived_url"],
                "page_text_sha256": attempt.get("page_html_sha256"),
                "verified_at_utc": attempt.get("checked_at_utc"),
                "source_observation": basis,
                "verification_method": "HTTP 200 with title and code match in controlled recheck",
            })
    else:
        basis = "historical_first_check"
        matched_at = historical["metadata"]["checked_at_utc"]
        candidates = [{
            "presentation_code": r["archive_code"],
            "title": r["archive_title"],
            "official_verified_url": r["page_url"],
            "page_text_sha256": r.get("page_text_sha256"),
            "verified_at_utc": matched_at,
            "source_observation": basis,
            "verification_method": "Historical HTTP 200 with full title and code match",
        } for r in initial]

    supplement = []
    seen_urls = set()
    seen_codes = set()
    for candidate in candidates:
        url = candidate["official_verified_url"]
        code = str(candidate["presentation_code"] or "").strip().upper()
        if not url or not url.startswith(HOST_PREFIX):
            raise ValueError("Supplement contained a non-ISPOR detail URL")
        if url in source_urls or code in source_codes:
            continue
        if url in seen_urls or code in seen_codes:
            raise ValueError("Duplicate code or URL in supplementary pages")
        seen_urls.add(url)
        seen_codes.add(code)
        supplement.append({
            **candidate,
            "verdict": "verified_official_page_absent_from_captured_search_index",
            "source_text_not_redistributed": True,
            "claims_about_authors_methods_results": None,
        })
    return {
        "metadata": {
            "source": "Official ISPOR presentation pages, separately checked from index",
            "verification_basis": basis,
            "scope": "Pages with a directly matched title and code outside current indexed set",
            "count": len(supplement),
            "historical_first_check_matches": len(initial),
            "last_checked_at_utc": matched_at,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "not_added_to_search_index_denominator": True,
            "cannot_certify_complete_final_conference": True,
            "not_proof_of_current_availability_after_check": True,
        },
        "records": supplement,
    }


def main():
    historical = json.loads(HIST.read_text(encoding="utf-8"))
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    latest = json.loads(LATEST.read_text(encoding="utf-8")) if LATEST.exists() else None
    output = build(historical, latest, index)
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print("SUPPLEMENT_PAGE_MATCHES", output["metadata"]["verification_basis"],
          output["metadata"]["count"], "outside-index pages; denominator unchanged")


if __name__ == "__main__":
    main()
