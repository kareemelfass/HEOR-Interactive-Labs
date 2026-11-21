#!/usr/bin/env python3
import json
from urllib.parse import urlencode
from urllib.request import Request,urlopen
root="https://isporsearch303.aws.mtxgp.net/rest/v2/api/search"
event="2026-11, ISPOR Europe 2026, Vienna, Austria"
tests=[
 {"query":"*","col":"2","pagesize":"2","facet":"true","facet.field":"events","f.events.size":"1000"},
 {"query":"*","col":"2","pagesize":"5","filter":f'events:("{event}")'},
 {"query":"*","col":"2","pagesize":"5","filter":f'events:"{event}"'},
 {"query":"*","col":"2","pagesize":"5","filter":f'(events:"{event}")'},
 {"query":"*","col":"2","pagesize":"5","filter":f'events:("{event}") AND citable:("True")'},
 {"query":"*","col":"2","pagesize":"100","filter":f'events:("{event}")'},
 {"query":"*","col":"2","pagesize":"5","filter":f'events:("{event}")',"page":"2"},
 {"query":"*","col":"2","pagesize":"5","filter":f'events:("{event}")',"start":"5"},
 {"query":"AI DELPHI","col":"2","pagesize":"5"},
 {"query":"REPLACING ASPARAGINASE","col":"2","pagesize":"5"}
]
for i,q in enumerate(tests):
 try:
  with urlopen(Request(root+"?"+urlencode(q),headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"}),timeout=25) as r:d=json.load(r)
  hits=d.get("result",[])
  print("OFFICIAL_SEARCH_TEST",json.dumps({"case":i,"hits":d.get("hits"),"currentPage":d.get("currentPage"),"lastPage":d.get("lastPage"),"pageSize":d.get("pageSize"),
       "n":len(hits),"fields":list(hits[0])[:40] if hits else [],
       "first":[{"code":x.get("sessioncode"),"title":x.get("fulltitle"),"event":x.get("events"),"citable":x.get("citable"),"url":x.get("url")} for x in hits[:3]],
       "facets":str(d.get("facets"))[:1000] if i==0 else None},ensure_ascii=False)[:2800])
 except Exception as e:print("OFFICIAL_SEARCH_ERROR",i,type(e).__name__,str(e)[:160])
