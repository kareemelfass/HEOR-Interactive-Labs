#!/usr/bin/env python3
"""Check all archive/ISPOR-index discrepancies against individual official pages.

Official pages, not the archive, determine verification status. This is
read-only, uses two workers, respects HTTP errors/rate limits, and retains
every unsuccessful/mismatched check as an open item. No abstract prose is
published.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import time
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.request import Request,urlopen

DATA=Path(__file__).resolve().parents[1]/"data"
SOURCE=DATA/"official-reconciliation.json"
OUT=DATA/"official-page-checks.json"
BASE="https://www.ispor.org/heor-resources/presentations-database/"

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__();self.text=[];self.invisible=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","noscript"):self.invisible+=1
    def handle_endtag(self,tag):
        if tag in ("script","style","noscript") and self.invisible:self.invisible-=1
    def handle_data(self,data):
        if not self.invisible:self.text.append(html.unescape(data))

def norm(value):
    value=unicodedata.normalize("NFKD",html.unescape(value or "")).casefold()
    value="".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(re.findall(r"[a-z0-9]+",value))

def check(task):
    result={
      "archive_code":task.get("archive_code"),"archive_title":task.get("archive_title"),
      "archive_url":task.get("archive_url"),"reconciliation_status":task["status"],
      "official_index_url":task.get("official_url"),"page_status":"unverified",
      "http_status":None,"title_match":False,"code_match":False,"page_reachable":False,
      "page_url":None,"page_text_sha256":None,
    }
    url=task.get("archive_url") or ""
    if not url.startswith(BASE):
        result["page_status"]="invalid_or_missing_url"
        return result
    for attempt in range(2):
        try:
            req=Request(url,headers={"User-Agent":"Mozilla/5.0 (Academic ISPOR metadata source audit)","Accept":"text/html"})
            with urlopen(req,timeout=25) as response:
                status=response.status
                final=response.geturl()
                raw=response.read(1_800_000).decode("utf-8","replace")
            parser=TextParser();parser.feed(raw)
            text=" ".join(parser.text)
            normtext=norm(text)
            title=norm(task.get("archive_title"))
            code=norm(task.get("archive_code"))
            result.update({"http_status":status,"page_reachable":status==200,
                           "page_url":final,"page_text_sha256":hashlib.sha256(text.encode()).hexdigest(),
                           "title_match":bool(title and title in normtext),
                           "code_match":bool(code and re.search(r"(?<![a-z0-9])"+re.escape(code)+r"(?![a-z0-9])",normtext))})
            result["page_status"]=("official_page_title_code_verified"
                if result["title_match"] and result["code_match"]
                else "official_page_reachable_content_mismatch")
            return result
        except HTTPError as e:
            result["http_status"]=e.code
            if e.code in (429,500,502,503,504) and attempt==0:
                time.sleep(3)
                continue
            result["page_status"]="http_"+str(e.code)
            return result
        except (URLError,TimeoutError,ConnectionError) as e:
            result["page_status"]="network_error"
            result["error"]=type(e).__name__+": "+str(e)[:120]
            if attempt==0:
                time.sleep(2)
                continue
            return result
        except Exception as e:
            result["page_status"]="parse_or_unknown_error"
            result["error"]=type(e).__name__+": "+str(e)[:120]
            return result
    return result

def main():
    doc=json.loads(SOURCE.read_text(encoding="utf-8"))
    tasks=[r for r in doc["archive_to_official"] if r["status"]!="url_match"]
    tasks.sort(key=lambda r:(r["status"],r.get("archive_code") or "",r.get("archive_url") or ""))
    print("OFFICIAL_PAGE_AUDIT_TARGET",len(tasks),flush=True)
    results=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures={pool.submit(check,r):r for r in tasks}
        for fut in as_completed(futures):
            results.append(fut.result())
            if len(results)%35==0:
                print("OFFICIAL_PAGE_AUDIT_PROGRESS",len(results),"/",len(tasks),
                      dict(Counter(r["page_status"] for r in results)),flush=True)
    results.sort(key=lambda r:(r["reconciliation_status"],r.get("archive_code") or "",r.get("archive_url") or ""))
    counters=Counter(r["page_status"] for r in results)
    crossed=Counter((r["reconciliation_status"],r["page_status"]) for r in results)
    payload={
       "metadata":{"checked_at_utc":datetime.now(timezone.utc).isoformat(),
                   "source":"Individual ISPOR presentation page HTTP and visible text",
                   "audited_records":len(tasks),"workers":2,
                   "method":"HTTP 200 + full normalized title + presentation code match in official page",
                   "scope":"All independent archive records that did not exactly match an official index URL",
                   "not_a_full_conference_census":True,
                   "not_independent_validation_of_study_results":True},
       "counts":dict(counters),
       "status_cross_tab":[{"archive_status":a,"page_status":b,"count":count}
                           for (a,b),count in sorted(crossed.items())],
       "results":results
    }
    OUT.write_text(json.dumps(payload,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print("OFFICIAL_PAGE_AUDIT_FINAL",json.dumps({
        "tested":len(results),"counts":dict(counters),"cross_tab":payload["status_cross_tab"]
    },ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
