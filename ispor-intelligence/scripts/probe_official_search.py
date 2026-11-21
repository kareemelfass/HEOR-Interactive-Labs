#!/usr/bin/env python3
"""Read-only exploration of ISPOR official search page public HTML and scripts.

Does not download abstracts or change dashboard. Reports endpoint hints only.
"""
import html
import json
import re
from html.parser import HTMLParser
from urllib.request import Request,urlopen
from urllib.parse import urljoin

BASE="https://www.ispor.org/heor-resources/presentations-database/results"
class Probe(HTMLParser):
    def __init__(self):
        super().__init__();self.scripts=[];self.forms=[];self.input_tags=[];self.links=[]
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if tag=="script" and d.get("src"):self.scripts.append(d["src"])
        if tag=="form":self.forms.append(d)
        if tag=="input":self.input_tags.append(d)
        if tag=="link" and d.get("href"):self.links.append(d["href"])
req=Request(BASE,headers={"User-Agent":"Mozilla/5.0 (research verification)"})
with urlopen(req,timeout=35) as res:
    text=res.read().decode("utf-8","replace")
parser=Probe();parser.feed(text)
print("OFFICIAL_SEARCH_PAGE",json.dumps({
    "html_bytes":len(text),"script_count":len(parser.scripts),
    "scripts":parser.scripts,"forms":parser.forms,
    "input_tags":parser.input_tags[:30],
    "keywords":[{"pattern":p,"at":m.start(),"context":text[max(0,m.start()-140):m.start()+250]} for p in
      [r"3112",r"api/",r"results",r"SearchResults",r"search-result",r"ajax",r"endPoint",r"sitefinity"] for m in list(re.finditer(p,text,re.I))[:4]
},ensure_ascii=False)[:21000])
for src in parser.scripts:
    if "ispor" not in urljoin(BASE,src):continue
    if not any(x in src.lower() for x in ["presentation","search","resource","main","custom","app","bundle"]):continue
    try:
        url=urljoin(BASE,src)
        with urlopen(Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=30) as r:
            js=r.read(4_000_000).decode("utf-8","replace")
        patterns=["presentation","heor","sitefinity","/api/","searchrequest","SearchResults","cti"]
        print("SCRIPT_PROBE",json.dumps({"url":url,"bytes":len(js),
            "hits":{p:[js[max(0,m.start()-130):m.start()+240] for m in list(re.finditer(re.escape(p),js,re.I))[:3]] for p in patterns}},
            ensure_ascii=False)[:7500])
    except Exception as exc:
        print("SCRIPT_PROBE_ERROR",src,type(exc).__name__,str(exc)[:150])
