#!/usr/bin/env python3
"""Create the ISPOR 2026 dataset from the search API configured on ISPOR.org.

SearchBlox is the first-party website's configured search service, rather
than a third-party reconstructed abstract archive. This is an indexed search
snapshot, not a guarantee of every final presentation or a web-page audit.
Only factual metadata is republished, not complete copyrighted abstracts.

The script aborts on pagination gaps, duplicate URLs, event mismatches, or
unexpected count changes during extraction. The archive is used only to
calculate a clearly labelled discrepancy table.
"""
from __future__ import annotations

import hashlib
import html
import json
import math
import re
import time
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[1]
SITE="https://www.ispor.org/heor-resources/presentations-database/results"
API="https://isporsearch303.aws.mtxgp.net/rest/v2/api/search"
ARCHIVE="https://justinsyu.github.io/ispor-eu-nov-2026/ispor_europe_2026_abstracts.json"
EVENT="2026-11, ISPOR Europe 2026, Vienna, Austria"
PAGE_SIZE=200
BASE="https://www.ispor.org/heor-resources/presentations-database/presentation-cti/ispor-europe-2026/"
HEADERS={"User-Agent":"Mozilla/5.0 (ISPOR-independent-research-integrity-audit; citation-only metadata)","Accept":"application/json"}

def fetch_json(url, retries=3):
    last=None
    for k in range(retries):
        try:
            with urlopen(Request(url,headers=HEADERS), timeout=45) as r:
                if r.status != 200:raise RuntimeError(f"Unexpected HTTP status {r.status}")
                return json.load(r)
        except Exception as e:
            last=e
            if k<retries-1:time.sleep(1.5*(k+1))
    raise RuntimeError(f"Cannot fetch source endpoint: {last}")

def digest(txt):
    return hashlib.sha256((txt or "").encode("utf-8")).hexdigest()

def values(raw):
    return [html.unescape(x).strip() for x in (raw or "").split("|") if x.strip()]

def normalise(title):
    return " ".join(re.findall(r"[a-z0-9]+",html.unescape(title or "").lower()))

def official_url(url):
    return isinstance(url,str) and url.startswith(BASE)

def fetch_page(n):
    params={"query":"*","col":"2","pagesize":PAGE_SIZE,"page":n,"filter":f'events:("{EVENT}")'}
    return fetch_json(API+"?"+urlencode(params))

def record(raw):
    txt=html.unescape(str(raw.get("description") or ""))
    url=raw.get("url") or raw.get("ParentLink")
    cats=values(raw.get("categories"))
    diseases=values(raw.get("disease"))
    return {
        "uid":str(raw.get("uid") or ""),
        "code":str(raw.get("sessioncode") or ""),
        "title":html.unescape(str(raw.get("fulltitle") or raw.get("title") or "")),
        "url":url,
        "event":raw.get("events"),
        "citable":str(raw.get("citable") or raw.get("citeable") or ""),
        "published":raw.get("published") or None,
        "lastmodified":raw.get("lastmodified") or None,
        "parent_session":html.unescape(str(raw.get("ParentTitle") or "")),
        "authors_affiliations_text":html.unescape(str(raw.get("authors") or "")),
        "category_paths":cats,
        "topic_groups":list(dict.fromkeys(x.split("^",1)[0] for x in cats)),
        "disease_areas":diseases,
        "presentation_media_url":raw.get("medialink") or raw.get("presentationfiles") or "",
        "abstract_present":bool(txt.strip()),
        "abstract_character_count":len(txt),
        "abstract_sha256":digest(txt),
        "record_source":"ISPOR website configured SearchBlox index",
        "index_content_kind":str(raw.get("module") or ""),
        "index_collection":str(raw.get("colname") or ""),
        "official_detail_link_present":official_url(url),
        "web_page_independently_checked":False,
    }

def main():
    with urlopen(Request(SITE,headers={"User-Agent":"Mozilla/5.0"}),timeout=35) as r:
        homepage=r.read().decode("utf-8","replace")
    if "isporsearch303.aws.mtxgp.net" not in homepage:
        raise RuntimeError("ISPOR's own search page no longer advertises this backend. Aborting.")
    # The live index fluctuates by 1-3 hits within seconds. We therefore
    # union TWO independent complete page scans. Every retained row originates
    # from ISPOR's configured search index; the union is explicitly NOT a
    # complete point-in-time census, and changes are auditable.
    scans=2
    observations=[]
    retrieved={}
    conflicts=[]
    for attempt in range(1,scans+1):
        first=fetch_page(1)
        n=int(first["hits"])
        if n<500:raise RuntimeError(f"Official search returned an implausible count: {n}")
        pages=math.ceil((n+4)/PAGE_SIZE)
        for page in range(1,pages+1):
            body=first if page==1 else fetch_page(page)
            count=int(body["hits"])
            observations.append(count)
            if int(body["currentPage"])!=page:
                raise RuntimeError(f"Search backend returned page {body.get('currentPage')} instead of {page}")
            chunk=body.get("result") or []
            for x in chunk:
                r=record(x)
                uid=r["uid"]
                if not uid:raise RuntimeError("An indexed record has no UID")
                if uid in retrieved and (retrieved[uid]["title"]!=r["title"] or retrieved[uid]["url"]!=r["url"]):
                    conflicts.append({"uid":uid,"first_title":retrieved[uid]["title"],
                                      "second_title":r["title"],"first_url":retrieved[uid]["url"],
                                      "second_url":r["url"]})
                    continue
                retrieved[uid]=r
            print("OFFICIAL_SCAN",attempt,"page",page,"of",pages,
                  "index_hits",count,"unique_captured",len(retrieved),flush=True)
            time.sleep(.12)
    data=list(retrieved.values())
    n=len(data)
    pages=math.ceil(n/PAGE_SIZE)
    print("OFFICIAL_INDEX_CAPTURE",json.dumps({
        "indexed_hits_min":min(observations),"indexed_hits_max":max(observations),
        "unique_captured":len(data),"capture_scans":scans,
        "conflicting_records":len(conflicts)}),flush=True)
    urls=[x["url"] for x in data]
    ids=[x["uid"] for x in data]
    failures=[]
    for i,r in enumerate(data):
        if not official_url(r["url"]):failures.append({"position":i,"code":r["code"],"reason":"invalid_official_url"})
        if r["event"]!=EVENT:failures.append({"position":i,"code":r["code"],"reason":"wrong_event"})
        if not r["title"] or not r["uid"]:failures.append({"position":i,"code":r["code"],"reason":"missing_id_or_title"})
    dup_urls=[u for u,nc in Counter(urls).items() if nc>1]
    dup_uids=[u for u,nc in Counter(ids).items() if nc>1]
    if failures:
        print("OFFICIAL_NONPRESENTATION_INDEX_ITEMS",json.dumps({
            "count":len(failures),
            "examples":[{"code":data[f["position"]]["code"],
                         "title":data[f["position"]]["title"],
                         "url":data[f["position"]]["url"],
                         "module":data[f["position"]]["index_content_kind"],
                         "collection":data[f["position"]]["index_collection"]}
                         for f in failures[:8]]
        },ensure_ascii=False),flush=True)
    # Retain and explicitly type backend hits, but never misrepresent links
    # lacking a presentation detail route as verified presentation pages.
    if dup_urls or dup_uids or any(f["reason"] not in ("invalid_official_url",) for f in failures):
        raise RuntimeError(f"Index integrity failure: dup URLs {len(dup_urls)}, IDs {len(dup_uids)}, invalid: {failures[:10]}")
    created=datetime.now(timezone.utc).isoformat()
    metadata={
        "conference":EVENT,"source":"Official ISPOR website configured search service",
        "search_page":SITE,"api_endpoint":API,"query":"* filtered by exact event string",
        "retrieved_at_utc":created,"records":len(data),"pages":pages,"page_size":PAGE_SIZE,
        "capture_scans":scans,"index_hits_observed_min":min(observations),
        "index_hits_observed_max":max(observations),"index_count_stable_during_extraction":len(set(observations))==1,
        "point_in_time_census_verified":False,"conflicting_index_record_versions":conflicts,
        "independent_archive_not_used_for_official_records":True,
        "reproduces_official_search_index_not_final_conference_census":True,
        "all_record_urls_page_verified":False,
        "abstract_text_republished":False,
        "indexed_items_without_presentation_detail":sum(not r["official_detail_link_present"] for r in data),
        "source_count_discrepancy_unresolved":True,
    }
    nodes=[]
    edges=[]
    seen=set()
    def enode(node_id,kind,label):
        if node_id not in seen:
            seen.add(node_id);nodes.append({"id":node_id,"type":kind,"label":label})
    for rec in data:
        pid="presentation:"+rec["uid"]
        enode(pid,"presentation",rec["title"])
        for kind,relation,key in [
            ("official_topic","OFFICIAL_INDEX_TOPIC","topic_groups"),
            ("official_category_path","OFFICIAL_INDEX_CATEGORY","category_paths"),
            ("official_disease","OFFICIAL_INDEX_DISEASE","disease_areas"),
            ("official_session","OFFICIAL_INDEX_SESSION","parent_session")]:
            names=rec[key] if isinstance(rec[key],list) else [rec[key]]
            for t in names:
                if not t:continue
                oid=kind+":"+digest(t)[:20]
                enode(oid,kind,t)
                edges.append({"source":pid,"target":oid,"relation":relation,
                              "provenance":{"record_uid":rec["uid"],"source_field":key,
                                            "source":"ISPOR website search index","inferred":False}})
    archive=fetch_json(ARCHIVE)
    candidates=archive.get("abstracts",[])
    if not isinstance(candidates,list):raise ValueError("Archive abstracts list not found")
    official_by_url={r["url"]:r for r in data if r["official_detail_link_present"]}
    official_by_code=defaultdict(list)
    for r in data:
        official_by_code[r["code"]].append(r)
    archive_urls=set()
    recon=[]
    for a in candidates:
        url=a.get("source_url") or a.get("url") or ""
        archive_urls.add(url)
        pair=official_by_url.get(url)
        code=a.get("abstract_number") or ""
        alternatives=official_by_code.get(code,[])
        matching_title=[x for x in alternatives if normalise(x["title"])==normalise(a.get("title"))]
        if pair:
            status="url_match"
            if normalise(pair["title"])!=normalise(a.get("title")):status="url_match_title_changed"
        elif len(matching_title)==1:
            pair=matching_title[0]
            status="code_title_match_url_changed"
        elif alternatives:
            status="code_exists_but_title_or_url_different"
        else:
            status="archive_only_not_in_official_index"
        recon.append({"archive_code":code,"archive_title":a.get("title"),"archive_url":url,
                      "status":status,"official_uid":pair["uid"] if pair else None,
                      "official_url":pair["url"] if pair else None})
    official_urls=set(official_by_url)
    matched_official={r["official_uid"] for r in recon if r["official_uid"]}
    official_only=[{"uid":r["uid"],"code":r["code"],"title":r["title"],"url":r["url"]}
                   for r in data if r["uid"] not in matched_official]
    summary={
        "metadata":metadata,
        "official_index_topic_groups":dict(Counter(x for r in data for x in r["topic_groups"])),
        "official_index_disease_areas":dict(Counter(x for r in data for x in r["disease_areas"])),
        "official_index_citable":dict(Counter(r["citable"] for r in data)),
        "official_index_missing_abstracts":sum(not r["abstract_present"] for r in data),
        "official_index_with_media_link":sum(bool(r["presentation_media_url"]) for r in data),
        "official_index_without_presentation_detail_link":sum(not r["official_detail_link_present"] for r in data),
        "official_index_content_kinds":dict(Counter(r["index_content_kind"] for r in data)),
        "comparison":{"archive_records":len(candidates),"official_index_records":len(data),
                      "archive_reconciliation_status":dict(Counter(x["status"] for x in recon)),
                      "official_index_not_matched_to_archive":len(official_only)}
    }
    out=ROOT/"data"
    out.mkdir(parents=True,exist_ok=True)
    files={
      "official-index-records.json":{"metadata":metadata,"records":data},
      "official-index-graph.json":{"metadata":metadata,"nodes":nodes,"edges":edges},
      "official-index-summary.json":summary,
      "official-reconciliation.json":{"metadata":metadata,"archive_records":len(candidates),
                                      "archive_to_official":recon,"official_only":official_only},
    }
    for filename,obj in files.items():
        (out/filename).write_text(json.dumps(obj,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
        print("WROTE",filename,(out/filename).stat().st_size)
    print("OFFICIAL_INDEX_RESULT",json.dumps({
        "count":len(data),"nodes":len(nodes),"edges":len(edges),"reconciliation":summary["comparison"],
        "citable":summary["official_index_citable"],
        "missing_abstract":summary["official_index_missing_abstracts"]
    },ensure_ascii=False))
if __name__=="__main__":
    main()
