#!/usr/bin/env python3
"""Test official ISPOR index reidentification strategies for historic 404s."""
import json
from urllib.parse import urlencode
from urllib.request import Request,urlopen
API="https://isporsearch303.aws.mtxgp.net/rest/v2/api/search"
EVENT="2026-11, ISPOR Europe 2026, Vienna, Austria"
queries=["CO1","CO100","CO108","EE219","ACUPUNCTURE-RELATED THERAPIES FOR DRUG ADDICTION","ACUPUNCTURE DRUG ADDICTION","ASSOCIATION BETWEEN ACUPUNCTURE TREATMENT EXPOSURE","BIUXX","CO14"]
for q in queries:
 try:
  parameters={"query":q,"col":"2","pagesize":"20","filter":f'events:("{EVENT}")'}
  url=API+"?"+urlencode(parameters)
  with urlopen(Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"}),timeout=25) as response:
   data=json.load(response)
  rows=data.get("result") or []
  print("OFFICIAL_RECOVERY_PROBE",json.dumps({"query":q,"hits":data.get("hits"),"first":[{"code":x.get("sessioncode"),"title":x.get("fulltitle"),"url":x.get("url"),"kind":x.get("module")} for x in rows[:6]]},ensure_ascii=False),flush=True)
 except Exception as exc:
  print("OFFICIAL_RECOVERY_ERROR",q,type(exc).__name__,str(exc)[:200],flush=True)
