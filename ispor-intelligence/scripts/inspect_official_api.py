#!/usr/bin/env python3
import re
import json
from urllib.request import Request,urlopen
from urllib.parse import urljoin, urlencode
page="https://www.ispor.org/heor-resources/presentations-database/results"
with urlopen(Request(page,headers={"User-Agent":"Mozilla/5.0"}),timeout=30) as r:
  html=r.read().decode("utf-8","replace")
for pattern in ("window.mgSearchbloxConfig","window.presentationSearchSbData","mg-search-results","mgPdfDisplayDates","window.mg"):
  matches=list(re.finditer(re.escape(pattern),html,re.I))
  print("OFFICIAL_CONFIG",pattern,"instances",len(matches))
  for m in matches[:2]: print(html[max(0,m.start()-130):min(len(html),m.start()+3200)].replace("\n"," ")[:3300])
url=urljoin(page,"/ResourcePackages/ISPOR/modules/searchblox/dist/main.js?v=2024-02-14T17:06")
with urlopen(Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=30) as r:
  js=r.read(2_000_000).decode("utf-8","replace")
for pattern in ("executeSearchSbUrl","actualSearchQuery","searchBloxServer","eventCollection","facet.field","pagesize=","getSearchResults"):
  matches=list(re.finditer(re.escape(pattern),js,re.I))
  print("JS_CONTEXT",pattern,"instances",len(matches))
  for m in matches[:3]:print(js[max(0,m.start()-700):min(len(js),m.start()+1400)][:2200])
