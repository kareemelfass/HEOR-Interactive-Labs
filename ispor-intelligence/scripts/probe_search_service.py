#!/usr/bin/env python3
"""Read-only probe of ISPOR's own publicly configured search service."""
import json
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError
endpoint="https://isporsearch303.aws.mtxgp.net/rest/v2/api/search"
common={"query":"*","col":"2","pagesize":"2","facet":"true","facet.field":"events"}
tests=[
 common,
 {**common,"query":""},
 {**common,"query":"ISPOR"},
 {**common,"query":"*","filter":'events:("2026-11, ISPOR Europe 2026, Vienna, Austria")'},
 {**common,"query":"*","filter":'events:("ISPOR Europe 2026")'},
]
for i,params in enumerate(tests):
 try:
  url=endpoint+"?"+urlencode(params)
  with urlopen(Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json","Origin":"https://www.ispor.org"}),timeout=25) as r:
   raw=r.read(700000).decode("utf-8","replace")
   parsed=json.loads(raw)
   print("SEARCHBLOX_TRIAL",json.dumps({"case":i,"status":r.status,
    "keys":list(parsed.keys()),"hits":parsed.get("hits"),"result_type":type(parsed.get("result")).__name__,
    "sample":parsed.get("result",[])[:2],"facet":str(parsed.get("facets"))[:1500]},ensure_ascii=False)[:5400])
 except Exception as e:
  print("SEARCHBLOX_ERROR",i,type(e).__name__,str(e)[:220])
