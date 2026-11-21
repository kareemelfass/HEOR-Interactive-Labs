#!/usr/bin/env python3
"""Pilot direct verification against authoritative ISPOR pages.

This samples official pages only. A successful sample DOES NOT certify the
independent pre-conference archive or final ISPOR census. The script is
read-only, makes at most 8 serial GET requests, and fails visibly on mismatch.
"""
import html
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
index=json.loads((ROOT/"data"/"records-index.json").read_text(encoding="utf-8"))
rows=index["records"]
assert len(rows)==3097, "Archive index has changed"
pick=sorted(set([0,1,2,317,765,1548,2300,3096]))
class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.words=[]
        self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style"):self.skip+=1
    def handle_endtag(self,tag):
        if tag in ("script","style") and self.skip:self.skip-=1
    def handle_data(self,data):
        if not self.skip:self.words.append(html.unescape(data))

def canon(text):
    return " ".join(re.findall(r"[a-z0-9]+",text.casefold()))

summary=[]
for i in pick:
    r=rows[i]
    url=r["url"]
    req=Request(url,headers={"User-Agent":"ISPOR-research-source-audit/1.0 (+source quality assurance)"})
    result={"row":i,"code":r["id"],"url":url,"title_matches":False,"code_matches":False}
    try:
        with urlopen(req,timeout=35) as response:
            raw=response.read(2_000_000).decode("utf-8","replace")
            result["http"]=response.status
        parser=VisibleText();parser.feed(raw)
        visible=" ".join(parser.words)
        c=canon(visible)
        title=canon(r["title"])
        result["title_matches"]=bool(title and title in c)
        result["code_matches"]=bool(re.search(r"(?<![A-Z0-9])"+re.escape(r["id"])+r"(?![A-Z0-9])",visible,flags=re.I))
        result["size"]=len(raw)
    except Exception as e:
        result["error"]=type(e).__name__+": "+str(e)[:160]
    summary.append(result)
    print("OFFICIAL_PAGE_CHECK",json.dumps(result,ensure_ascii=False),flush=True)
    time.sleep(.5)
passed=sum(x["title_matches"] and x["code_matches"] for x in summary)
print("OFFICIAL_PILOT_SUMMARY",json.dumps({
    "sampled":len(summary),"matched":passed,"failed":len(summary)-passed,
    "denominator":len(rows),
    "caveat":"Sampled URL/title/code matches do not establish completeness or full text concordance"
},ensure_ascii=False))
