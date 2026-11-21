"use strict";
(function () {
 const ARCHIVE = "https://justinsyu.github.io/ispor-eu-nov-2026/ispor_europe_2026_abstracts.json";
 const PREFIX = "https://www.ispor.org/heor-resources/presentations-database/";
 const TOPICS = [
  {name:"JCA",re:/\bJCA\b|joint clinical assessment|EU HTA regulation|\bHTAR\b/i},
  {name:"AI",re:/\bartificial intelligence\b|\bAI[- ](?:assisted|enabled|based|driven|agent)\b|\blarge language models?\b|\bLLMs?\b|generative AI|machine learning/i},
  {name:"Economic evaluation",re:/cost[- ]effective|cost[- ]utility|budget impact|economic evaluation|\bQALY\b|\bICER\b/i},
  {name:"RWE",re:/real[- ]world (?:evidence|data)|\bRWE\b|\bRWD\b|electronic (?:health|medical) record|claims database/i},
  {name:"Causal inference",re:/target trial emulation|causal inference|propensity score|external control arm|marginal structural model/i},
  {name:"Indirect comparisons",re:/indirect treatment comparison|\bMAIC\b|\bSTC\b|network meta.analysis|\bNMA\b/i},
  {name:"ML-NMR",re:/\bML[- ]?NMR\b|multilevel network meta.regression/i},
  {name:"Survival modelling",re:/survival extrapolat|survival model|Kaplan.Meier|flexible parametric|M.spline|mortality extrapolat/i},
  {name:"Bayesian methods",re:/\bBayesian\b|\bposterior\b|\bprior distribution\b/i},
  {name:"MFN pricing",re:/most.fav(?:or|our)ed.nation|\bMFN\b|TrumpRx/i},
  {name:"Market access",re:/market access|launch sequenc|reimbursement|price referencing|pricing polic|affordability/i},
  {name:"Evidence synthesis",re:/systematic literature review|\bSLR\b|evidence synthesis|meta.analysis/i},
  {name:"PICO",re:/\bPICO\b|population.intervention.comparator.outcome/i},
  {name:"Estimands",re:/\bestimands?\b|intercurrent event/i},
  {name:"Patient-reported outcomes",re:/patient.reported outcome|\bPROMs?\b|\bEQ.5D\b|health.utility/i},
  {name:"Medical devices",re:/medical devices?|medical technolog(?:y|ies)|\bmedtech\b|implantable devices?|\bin vitro diagnostic|\bIVD\b|digital therapeutics|robotic surgery/i}
 ];
 const DISEASES = [
  {name:"Oncology",re:/\boncolog|\bcancer\b|\btumou?r\b|\bcarcinoma\b|\bleukemia\b|\bmyeloma\b/i},
  {name:"Rare disease",re:/rare diseases?|orphan medicines?|ultra.rare/i},
  {name:"Metabolic / obesity",re:/\bobesity\b|\bdiabetes\b|\bmetabolic\b|\bGLP.1\b/i},
  {name:"Cardiovascular",re:/cardiovascular|\bheart failure\b|\bstroke\b|\batrial fibrillation\b/i},
  {name:"Neurology",re:/neurolog|\balzheimer|\bparkinson|\bmultiple sclerosis\b/i},
  {name:"Respiratory",re:/\basthma\b|\bCOPD\b|respiratory/i},
  {name:"Infectious disease",re:/\binfection\b|\bHIV\b|\bviral\b|\bantibiotic\b/i}
 ];
 const el = id => document.getElementById(id);
 const state = {records:[],source:"",snapshot:"",isFull:false,rawCount:0,filtered:[],shown:20,graphFocus:"",filter:"",isOfficial:false,query:"",searchMode:"all",error:""};
 let reviewedClaims=[];
 const h = (tag,cls,text) => { const n=document.createElement(tag); if(cls)n.className=cls;if(text!==undefined)n.textContent=String(text);return n; };
 const safeUrl = v => typeof v==="string" && /^https:\/\/(www\.)?ispor\.org\//i.test(v) ? v : "";
 const sourceLink = r => safeUrl(r.url);
 const format = n => Number(n||0).toLocaleString("en-GB");
 const byCount = (a,b) => b.count-a.count || a.name.localeCompare(b.name);
 const str = v => {
  if(v===null || v===undefined)return "";
  if(typeof v==="string" || typeof v==="number")return String(v);
  if(Array.isArray(v))return v.map(str).filter(Boolean).join(" ");
  if(typeof v==="object")return Object.values(v).map(str).filter(Boolean).join(" ");
  return "";
 };
 function field(o,aliases){
  if(!o || typeof o!=="object")return undefined;
  const map={}; Object.keys(o).forEach(k=>map[k.toLowerCase().replace(/[^a-z0-9]/g,"")]=k);
  for(const a of aliases){const k=map[a.toLowerCase().replace(/[^a-z0-9]/g,"")];if(k!==undefined && o[k]!==null)return o[k]}
  return undefined;
 }
 function extractRows(raw){
  if(Array.isArray(raw))return raw;
  const candidates=[];
  function walk(o,depth){
   if(!o || depth>3)return;
   if(Array.isArray(o)){
    if(o.length && typeof o[0]==="object" && o[0]!==null)candidates.push(o);
    return;
   }
   if(typeof o==="object")Object.keys(o).forEach(k=>walk(o[k],depth+1));
  }
  walk(raw,0);
  candidates.sort((a,b)=>{
   function score(x){const y=x[0]||{};return x.length+(field(y,["title","presentation_title","abstract_title"]) ? 100000:0)}
   return score(b)-score(a);
  });
  return candidates[0]||[];
 }
 function guessUrl(row){
  const potential=[
   field(row,["source_url","ispor_url","presentation_url","original_url","url","source_link","link","href"]),
   field(field(row,["source","metadata","links"]),["url","source_url","href","official_url"])
  ];
  for(const p of potential)if(safeUrl(p))return p;
  const all=str(field(row,["source","citation","source_metadata","source_reference"]));
  const m=all.match(/https:\/\/(?:www\.)?ispor\.org\/[^\s"'<>]+/i);
  return m?safeUrl(m[0]):"";
 }
 function asLabels(v){
  const values=Array.isArray(v)?v:v===null||v===undefined?[]:[v];
  return [...new Set(values.map(x=>typeof x==="object"&&x!==null?(field(x,["name","label","category","topic","disease"])||""):x).map(str).map(x=>x.trim()).filter(Boolean))];
 }
 function normalize(row,i){
  const title=str(field(row,["title","presentation_title","abstract_title","name","paper_title"])).trim();
  if(!title || (title.length<8 && !guessUrl(row)))return null;
  const parts=["abstract_text","abstract","structured_abstract","abstract_body","summary","sections","objectives","objective","methods","results","conclusions","background","full_text","body"].map(k=>field(row,[k])).filter(x=>x!==undefined);
  const abstract=str(parts).replace(/\s+/g," ").slice(0,12000);
  const code=str(field(row,["abstract_number","presentation_code","presentation_id","abstract_id","code","number","id"])).trim().slice(0,80);
  const url=guessUrl(row);
  const sourceCategories=asLabels(field(row,["source_categories","categories","topic_groups","topic","category"]));
  const sourceDiseases=asLabels(field(row,["source_diseases","diseases","disease_areas","disease"]));
  const topicsRaw=sourceCategories.join(" ");
  const diseaseRaw=sourceDiseases.join(" ");
  const haystack=[title,abstract,topicsRaw].join(" ");
  const inputTags=field(row,["tags"]);
  const inputDiseases=field(row,["diseases"]);
  const tagNames=Array.isArray(inputTags)?inputTags:[];
  const diseaseNames=Array.isArray(inputDiseases)?inputDiseases:[];
  const tags=[...new Set([...TOPICS.filter(x=>x.re.test(haystack)).map(x=>x.name),...tagNames.filter(x=>TOPICS.some(t=>t.name===x))])];
  const diseases=[...new Set([...DISEASES.filter(x=>x.re.test([title,abstract,diseaseRaw].join(" "))).map(x=>x.name),...diseaseNames.filter(x=>DISEASES.some(t=>t.name===x))])];
  return {id:code || "r"+i,title,abstract,code,url,tags,diseases,sourceCategories,sourceDiseases,topicsRaw,diseaseRaw,sourceType:"Archive record",year:2026};
 }
 function fromSeed(items){
  return items.map((r,i)=>({id:r.id||"seed"+i,title:r.title,abstract:"",code:r.id||"",url:safeUrl(r.url),tags:r.tags||[],diseases:DISEASES.filter(x=>x.re.test(r.title)).map(x=>x.name),sourceCategories:[],sourceDiseases:[],topicsRaw:"",diseaseRaw:"",sourceType:"Verified official presentation",year:2026}));
 }
 function clean(rows){
  const seen=new Set(),out=[];
  rows.forEach((r,i)=>{
   const record=r && r.sourceType?r:normalize(r,i);
   if(!record)return;
   const key=(record.url || (record.title.toLowerCase().replace(/\s+/g," "))).trim();
   if(!key || seen.has(key))return;
   seen.add(key);out.push(record);
  });
  return out;
 }
 function setData(records,source,full,rawCount,error){
  state.records=clean(records); state.rawCount=rawCount||records.length;state.source=source;state.isFull=full;state.isOfficial=(source==="Official ISPOR search index");state.error=error||"";
  state.shown=20;
  updateThemeSelect();updateGraphSelect();applyFilters();
  el("sourceName").textContent=source;
  el("sourceDetail").textContent=state.isOfficial?"Search-index snapshot, not a final census; individual page validation is not complete":(error||"Unverified input");
  el("liveDot").className="live-dot "+(full?"ok":"warn");
  el("metricQualifier").textContent=state.isOfficial?"Official search-index records; denominator not reconciled":"Unverified dataset";
  renderQuality();
 }
 function updateThemeSelect(){
  const current=state.filter;
  const sel=el("themeFilter");sel.replaceChildren(h("option","", "All themes"));sel.options[0].value="";
  const values=[...new Set(state.records.flatMap(r=>r.tags))].sort();
  values.forEach(t=>{const op=h("option","",t);op.value=t;sel.append(op)});
  sel.value=values.includes(current)?current:"";
  state.filter=sel.value;
 }
 function updateGraphSelect(){
  const sel=el("graphFocus");sel.replaceChildren();
  const values=[...new Set(state.records.flatMap(r=>r.tags))].sort();
  values.forEach(t=>{const op=h("option","",t);op.value=t;sel.append(op)});
  if(!values.includes(state.graphFocus))state.graphFocus=values[0]||"";
  sel.value=state.graphFocus;
 }
 function matchSearch(r){
  if(!state.query)return true;
  const value=(state.searchMode==="title"?r.title:[r.title,r.abstract,r.code,r.topicsRaw,r.diseaseRaw,r.authorText||""].join(" ")).toLowerCase();
  return state.query.trim().toLowerCase().split(/\s+/).every(t=>value.includes(t));
 }
 function applyFilters(){
  state.filtered=state.records.filter(r=>matchSearch(r) && (!state.filter || r.tags.includes(state.filter)));
  el("metricRecords").textContent=format(state.records.length);
  el("metricThemes").textContent=format(new Set(state.records.flatMap(r=>r.tags)).size);
  el("metricEdges").textContent=format(state.records.reduce((sum,r)=>sum+r.tags.length,0));
  el("metricLinks").textContent=format(state.records.filter(r=>sourceLink(r)).length);
  el("filteredCount").textContent=format(state.filtered.length)+" matching";
  renderBars();renderInsights();renderGraph();renderResults();renderMatrix();renderQuality();
 }
 function counts(fieldName){return [...new Set(state.filtered.flatMap(r=>r[fieldName]))].map(name=>({name,count:state.filtered.filter(r=>r[fieldName].includes(name)).length})).sort(byCount)}
 function drawBars(target,items,interactive){
  const parent=el(target);parent.replaceChildren();
  if(!items.length){parent.append(h("p","muted","No matching topic signals."));return}
  const max=items[0].count;
  items.slice(0,10).forEach(item=>{
   const b=h("button","bar-button");b.type="button";if(!interactive)b.disabled=true;
   const head=h("div","bar-head"), label=h("span","",item.name), cnt=h("strong","",format(item.count)+" · "+(state.filtered.length?Math.round(item.count/state.filtered.length*100):0)+"%");
   head.append(label,cnt);
   const track=h("div","bar-track"),fill=h("div","bar-fill");fill.style.width=(item.count/max*100)+"%";track.append(fill);b.append(head,track);
   if(interactive)b.addEventListener("click",()=>{state.filter=item.name;el("themeFilter").value=item.name;state.shown=20;applyFilters()});
   parent.append(b);
  });
 }
 function renderBars(){drawBars("themeBars",counts("tags"),true);drawBars("diseaseBars",counts("diseases"),false);drawBars("sourceTopicBars",counts("sourceCategories"),false);drawBars("sourceDiseaseBars",counts("sourceDiseases"),false)}
 function renderInsights(){
  const top=counts("tags")[0]; const pct=top&&state.filtered.length?Math.round(100*top.count/state.filtered.length):0;
  el("insightTitle").textContent=top?top.name+" appears in "+format(top.count)+" matching records":"No records match these filters";
  el("insightText").textContent=top?"This is "+pct+"% of the currently filtered records. It measures an official search-index category, not discussion intensity, methodological quality or year-on-year growth.":"Try clearing your filters or importing a different corpus.";
  const links=el("insightSources");links.replaceChildren();
  if(top)state.filtered.filter(r=>r.tags.includes(top.name)&&sourceLink(r)).slice(0,3).forEach(r=>{const a=h("a","",r.title.slice(0,55)+(r.title.length>55?"…":""));a.href=r.url;a.target="_blank";a.rel="noopener noreferrer";links.append(a)});
 }
 function makeSvg(tag,attr,text){
  const n=document.createElementNS("http://www.w3.org/2000/svg",tag);Object.entries(attr||{}).forEach(([k,v])=>n.setAttribute(k,String(v)));if(text!==undefined)n.textContent=String(text);return n;
 }
 function renderGraph(){
  const focus=state.graphFocus, svg=el("graphCanvas");svg.replaceChildren();
  const matches=state.filtered.filter(r=>r.tags.includes(focus));
  const sample=matches.slice(0,11);
  const neighborCounts=new Map();
  matches.forEach(r=>r.tags.filter(t=>t!==focus).forEach(t=>neighborCounts.set(t,(neighborCounts.get(t)||0)+1)));
  const other=[...neighborCounts].sort((a,b)=>b[1]-a[1]).slice(0,5);
  const center={x:430,y:245}, graphNodes=[];
  graphNodes.push({id:"topic:"+focus,label:focus,kind:"focus",x:center.x,y:center.y});
  sample.forEach((r,i)=>{const a=Math.PI*2*(i/sample.length)-Math.PI/2;graphNodes.push({id:"rec:"+i,label:r.code&&r.code!=="r"+i?r.code:r.title.slice(0,22),kind:"record",x:center.x+182*Math.cos(a),y:center.y+172*Math.sin(a),record:r})});
  other.forEach(([name,count],i)=>{const a=Math.PI*2*(i/other.length)-Math.PI/2+0.25;graphNodes.push({id:"topic:"+name,label:name,kind:"topic",count,x:center.x+343*Math.cos(a),y:center.y+211*Math.sin(a)})});
  const bg=makeSvg("text",{x:18,y:24,fill:"#637b91","font-size":12},format(matches.length)+" linked presentations; showing "+format(sample.length)+" examples");
  svg.append(bg);
  graphNodes.filter(n=>n.kind==="record").forEach(n=>svg.append(makeSvg("line",{x1:center.x,y1:center.y,x2:n.x,y2:n.y,class:"graph-edge"})));
  graphNodes.filter(n=>n.kind==="topic").forEach(n=>svg.append(makeSvg("line",{x1:center.x,y1:center.y,x2:n.x,y2:n.y,class:"graph-edge","stroke-dasharray":"5 5"})));
  graphNodes.forEach(n=>{
   const g=makeSvg("g",{class:"graph-node",role:"button",tabindex:"0","aria-label":n.kind==="record"?n.record.title:n.label});
   const radius=n.kind==="focus"?43:n.kind==="record"?16:27;
   const fill=n.kind==="record"?"#747fc1":n.kind==="focus"?"#086d79":"#32a6aa";
   g.append(makeSvg("circle",{cx:n.x,cy:n.y,r:radius,fill}));
   if(n.kind==="focus")g.append(makeSvg("text",{x:n.x,y:n.y+4,"text-anchor":"middle",fill:"#fff","font-size":14},n.label.length>12?n.label.slice(0,11)+"…":n.label));
   else{
    const label= n.kind==="record"?(n.record.code&&n.record.code.length<=8?n.record.code:"Abstract") : n.label;
    g.append(makeSvg("text",{x:n.x,y:n.y+radius+16,"text-anchor":"middle"},label.length>18?label.slice(0,17)+"…":label));
   }
   const click=()=>n.kind==="record"?showRecordDetail(n.record):n.kind==="topic"?switchGraphFocus(n.label):showThemeDetail(focus,matches);
   g.addEventListener("click",click);g.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();click()}});
   svg.append(g);
  });
  showThemeDetail(focus,matches);
 }
 function switchGraphFocus(t){state.graphFocus=t;el("graphFocus").value=t;renderGraph()}
 function showThemeDetail(t,matching){
  el("detailTitle").textContent=t;
  el("detailText").textContent=format(matching.length)+" currently filtered presentations mention this theme. Links represent source-index topic classifications, not confirmed method use or findings.";
  el("detailLinks").replaceChildren();
  related(matching);
  renderReviewedClaims(matching,t);
 }
 function showRecordDetail(r){
  el("detailTitle").textContent=r.title;
  el("detailText").textContent=(r.code?r.code+" · ":"")+"Indexed categories: "+(r.tags.join(", ")||"none")+". Check the official source for methods and findings.";
  const out=el("detailLinks");out.replaceChildren();
  if(sourceLink(r)){const a=h("a","","Open original ISPOR presentation ↗");a.href=r.url;a.target="_blank";a.rel="noopener noreferrer";out.append(a)}
  related([r]);
  renderReviewedClaims([r]);
 }
 function renderReviewedClaims(records,topic){
  const target=el("claimsList");target.replaceChildren();
  const urls=new Set(records.map(r=>r.url).filter(Boolean));
  const codes=new Set(records.map(r=>r.code.toUpperCase()).filter(Boolean));
  const matches=reviewedClaims.filter(c=>
   (urls.has(c.source_url) || codes.has(c.presentation_code.toUpperCase())) &&
   (!topic || c.topic===topic || records.some(r=>r.tags.includes(topic)))
  );
  matches.slice(0,8).forEach(c=>{
   const card=h("div","claim-card");
   card.append(h("div","claim-kind",c.type.replace(/_/g," ")),h("p","",c.claim),h("small","",c.qualifier));
   const a=h("a","","Original ISPOR abstract ↗");
   a.href=c.source_url;a.target="_blank";a.rel="noopener noreferrer";card.append(a);
   target.append(card);
  });
  if(!matches.length)target.append(h("p","muted","No manually reviewed finding is linked to these displayed records. A keyword connection alone does not establish a result."));
 }
 function related(items){
  const out=el("graphRecordList");out.replaceChildren();
  items.slice(0,13).forEach(r=>{
   const node=sourceLink(r)?h("a","related-link",r.title):h("div","related-link",r.title);
   if(sourceLink(r)){node.href=r.url;node.target="_blank";node.rel="noopener noreferrer"}
   out.append(node);
  });
  if(!items.length)out.append(h("p","muted","No linked presentations for the current filters."));
 }
 function renderResults(){
  const target=el("resultList");target.replaceChildren();
  state.filtered.slice(0,state.shown).forEach(r=>{
   const article=h("article","result"),head=h("div","result-head");
   if(r.code)head.append(h("span","pill",r.code));
   head.append(h("span","pill secondary","2026"));
   const title=h("h3");const a=sourceLink(r)?h("a","",r.title):h("span","",r.title);
   if(sourceLink(r)){a.href=r.url;a.rel="noopener noreferrer";a.target="_blank"}
   title.append(a);
   const caption=h("p","",r.sourceType+(sourceLink(r)?" · Search-index URL, not yet individually page-checked":" · Official link not available in source"));
   const tags=h("div","tags");r.tags.forEach(t=>tags.append(h("span","",t)));
   article.append(head,title,caption,tags);target.append(article);
  });
  if(!state.filtered.length)target.append(h("p","muted","No records matched your filters."));
  el("loadMore").hidden=state.shown>=state.filtered.length;
 }
 function renderMatrix(){
  const top=counts("tags").slice(0,7);
  const parent=el("matrix");parent.replaceChildren();
  if(top.length<2){parent.append(h("p","muted","Insufficient linked themes."));return}
  const table=h("table","matrix");const header=h("tr");header.append(h("th","","Theme"));
  top.forEach((t,i)=>{const c=h("th","",String(i+1));c.title=t.name;header.append(c)});
  table.append(header);
  const pairs=[];
  top.forEach((a,i)=>{
   const tr=h("tr"),th=h("th","vertical",(i+1)+". "+a.name);tr.append(th);
   top.forEach((b,j)=>{
    const n=state.filtered.filter(r=>r.tags.includes(a.name)&&r.tags.includes(b.name)).length;
    const c=h("td","",n);c.title=a.name+" and "+b.name+": "+n+" records";
    c.style.background="rgba(0,142,146,"+(n/(top[0].count||1)*0.65+0.04).toFixed(3)+")";c.style.color=n/(top[0].count||1)>.45?"#fff":"#254358";tr.append(c);
    if(j>i)pairs.push({a:a.name,b:b.name,n});
   });table.append(tr);
  });
  parent.append(table);
  const box=el("pairs");box.replaceChildren();
  pairs.sort((a,b)=>b.n-a.n).slice(0,10).forEach(p=>box.append(h("div","pair",p.a+" + "+p.b+" · "+format(p.n))));
 }
 function renderQuality(){
  const valid=state.records.filter(r=>sourceLink(r)).length;
  const abstract=state.records.filter(r=>r.abstract.length>40).length;
  const tagged=state.records.filter(r=>r.tags.length>0).length;
  const items=[
   [format(state.rawCount),"Input rows"],
   [format(state.records.length),"Usable unique records"],
   [format(valid),"ISPOR-domain URLs"],
   [format(abstract),"Local abstract text (not republished)"],
   [format(tagged),"Records with official topic group"],
   [format(state.records.filter(r=>r.sourceCategories.length>0).length),"Official index category coverage"],
   [state.isOfficial?"ISPOR search index":"Unverified","Data coverage"]
  ];
  el("quality").replaceChildren(...items.map(([v,label])=>{const box=h("div","quality-box");box.append(h("strong","",v),h("span","",label));return box}));
 }
 function makeGraph(records){
  const themes=[...new Set(records.flatMap(r=>r.tags))].sort();
  const categories=[...new Set(records.flatMap(r=>r.sourceCategories))].sort();
  const diseases=[...new Set(records.flatMap(r=>r.sourceDiseases))].sort();
  const nodes=themes.map(t=>({id:"topic:"+t,type:"theme",label:t,provenance:"Keyword-detected text mention"}));
  categories.forEach(t=>nodes.push({id:"ispor_topic:"+t,type:"archive_topic_group",label:t}));
  diseases.forEach(t=>nodes.push({id:"disease_area:"+t,type:"archive_disease_area",label:t}));
  const edges=[],recordByUrl=new Map();
  records.forEach((r,i)=>{
   const id="presentation:"+(r.code||"index"+i).replace(/[^a-z0-9_-]/gi,"_")+"_"+i;
   nodes.push({id,type:"presentation",label:r.title,url:sourceLink(r)||null,abstract_code:r.code||null});
   if(sourceLink(r))recordByUrl.set(r.url,id);
   r.tags.forEach(t=>edges.push({source:id,target:"topic:"+t,relation:"MENTIONS",provenance:"Rule-based keyword classification, not an author-reported finding"}));
   r.sourceCategories.forEach(t=>edges.push({source:id,target:"ispor_topic:"+t,relation:"ARCHIVE_CLASSIFIES_AS"}));
   r.sourceDiseases.forEach(t=>edges.push({source:id,target:"disease_area:"+t,relation:"ARCHIVE_DISEASE_AREA"}));
  });
  reviewedClaims.forEach(c=>{
   const pid=recordByUrl.get(c.source_url);
   if(!pid)return;
   const cid="claim:"+c.id;
   nodes.push({id:cid,type:"reported_claim",label:c.claim,qualifier:c.qualifier,source_url:c.source_url});
   edges.push({source:pid,target:cid,relation:"REPORTS",provenance:"Manually checked author-reported claim"});
   if(themes.includes(c.topic))edges.push({source:cid,target:"topic:"+c.topic,relation:"ABOUT"});
  });
  return {metadata:{conference:"ISPOR Europe 2026",records:records.length,source:state.source,full_archive:state.isFull,created_utc:new Date().toISOString(),interpretation:"Keyword and archive-classification edges are not scientific findings. Claims are author-reported."},nodes,edges};
 }
 function download(filename,text,type){
  const blob=new Blob([text],{type:type||"application/json"}),url=URL.createObjectURL(blob),a=h("a");a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);
 }
 function exportCsv(){
  const cols=["id","title","url","tags","diseases","year"];
  const quote=v=>'"'+String(v===undefined?"":Array.isArray(v)?v.join("; "):v).replace(/"/g,'""')+'"';
  const csv=[cols.join(","),...state.filtered.map(r=>cols.map(c=>quote(r[c])).join(","))].join("\r\n");
  download("ispor_europe_2026_filtered.csv",csv,"text/csv;charset=utf-8");
 }
 function renderOfficialReconciliation(summary){
  const target=el("officialReconciliation");
  if(!target)return;
  const comparison=summary.comparison||{};
  const status=comparison.archive_reconciliation_status||{};
  const meta=summary.metadata||{};
  const values=[
    ["Official-index items captured",meta.records],
    ["Indexed research presentations",(summary.official_index_content_kinds||{})["Confex Presentation"]||0],
    ["Indexed conference sessions",(summary.official_index_content_kinds||{})["Confex Session"]||0],
    ["Archive records",comparison.archive_records],
    ["Exact URL matches",status.url_match||0],
    ["Changed URL, matching code and title",status.code_title_match_url_changed||0],
    ["Same code, differing title or URL",status.code_exists_but_title_or_url_different||0],
    ["Archive only, not in captured official index",status.archive_only_not_in_official_index||0],
    ["Official-index items without archive match",comparison.official_index_not_matched_to_archive||0]
  ];
  target.replaceChildren(...values.map(([label,count])=>{
    const box=h("div","quality-box");
    box.append(h("strong","",format(count)),h("span","",label));
    return box;
  }));
 }
  function renderOfficialPageAudit(audit){
  const target=el("officialPageAudit");
  if(!target)return;
  const counts=audit.counts||{};
  const separatelyConfirmed=(audit.results||[]).filter(r=>r.reconciliation_status==="archive_only_not_in_official_index" && r.page_status==="official_page_title_code_verified").length;
  const labels={
    official_page_title_code_verified:"Official page verified (title and code)",
    official_page_reachable_content_mismatch:"Official page reachable, title/code unresolved",
    http_404:"Official page returned HTTP 404",
    http_403:"Official page returned HTTP 403",
    network_error:"Network error, not verified",
    invalid_or_missing_url:"No valid ISPOR page URL",
    parse_or_unknown_error:"Other verification errors"
  };
  target.replaceChildren(...[["additional verified official pages absent from index",separatelyConfirmed],...Object.entries(counts).sort((a,b)=>b[1]-a[1])].map(([k,v])=>{
    const box=h("div","quality-box");
    box.append(h("strong","",format(v)),h("span","",labels[k]||k));
    return box;
  }));
 }
  function fromOfficial(items) {
  return items.map((r,i)=>({
    id:r.uid || "official"+i,
    code:r.code || "",
    title:r.title,
    abstract:"",
    authorText:r.authors_affiliations_text || "",
    url:safeUrl(r.url),
    tags:r.topic_groups || [],
    diseases:r.disease_areas || [],
    sourceCategories:r.category_paths || [],
    sourceDiseases:r.disease_areas || [],
    topicsRaw:(r.category_paths||[]).join(" "),
    diseaseRaw:(r.disease_areas||[]).join(" "),
    sourceType:r.index_content_kind==="Confex Session"?"Official indexed conference session":"Official indexed research presentation",
    year:2026
  }));
 }
 async function loadOfficialIndex(){
  const response=await fetch("./data/official-index-records.json",{cache:"no-store"});
  if(!response.ok)throw Error("Official-index file unavailable, HTTP "+response.status);
  const data=await response.json();
  if(!Array.isArray(data.records)||data.records.length<1000)throw Error("Official-index corpus incomplete");
  const official=fromOfficial(data.records);
  setData(official,"Official ISPOR search index",true,data.records.length,"");
  const sessions=data.records.filter(r=>r.index_content_kind==="Confex Session").length;
  el("sourceDetail").textContent="Official indexed items: "+format(data.records.length)+" ("+format(data.records.length-sessions)+" presentations, "+format(sessions)+" sessions). Index count changed during collection; final census unresolved.";
  try{const response=await fetch("./data/official-index-summary.json",{cache:"no-store"});if(response.ok)renderOfficialReconciliation(await response.json())}catch(_e){}
  try{const response=await fetch("./data/official-page-checks.json",{cache:"no-store"});if(response.ok)renderOfficialPageAudit(await response.json())}catch(_e){}
  return data;
 }
  async function loadSeed(){
  const response=await fetch("./data/verified-records.json",{cache:"no-store"});
  if(!response.ok)throw Error("Curated seed unavailable");
  const body=await response.json();
  setData(fromSeed(body.records||[]),"Verified official ISPOR seed",false,(body.records||[]).length,"");
 }
 async function loadLocalIndex(){
  const response=await fetch("./data/records-index.json",{cache:"no-store"});
  if(!response.ok)throw Error("No prebuilt full metadata index");
  const body=await response.json();
  const rows=extractRows(body);
  if(rows.length<1000)throw Error("Incomplete local metadata index");
  setData(rows,"Prebuilt 2026 metadata KG index",true,rows.length,"");
 }
 async function loadArchive(){
  el("sourceName").textContent="Retrieving 2026 archive...";
  try{
   const response=await fetch(ARCHIVE,{mode:"cors",cache:"no-store"});
   if(!response.ok)throw Error("HTTP "+response.status);
   const body=await response.json();
   const rows=extractRows(body);
   if(rows.length<1000)throw Error("Archive shape could not be interpreted reliably ("+rows.length+" candidate rows)");
   const records=clean(rows);
   if(records.length<1000)throw Error("Only "+records.length+" titles were usable; not accepting partial corpus");
   setData(records,"Independent 2026 abstract archive",true,rows.length,"");
  }catch(e){
   const reason=e&&e.message?e.message:String(e);
   if(state.records.length===0){el("sourceName").textContent="Unable to load research records";el("sourceDetail").textContent=reason}
   else{el("sourceName").textContent=state.source;el("sourceDetail").textContent="Live archive fetch unavailable: "+reason+". Displaying "+(state.isFull?"the prebuilt metadata index":"the verified seed")+".";state.error=reason;renderQuality()}
  }
 }
 async function importFile(file){
  if(!file)return;
  try{
   const body=JSON.parse(await file.text());
   const rows=extractRows(body);
   if(!rows.length)throw Error("No candidate record array in this JSON file");
   const records=clean(rows);
   if(!records.length)throw Error("No identifiable presentations with titles");
   setData(records,"User-imported JSON: "+file.name,records.length>1000,rows.length,"");
  }catch(e){alert("Import failed: "+e.message)}
 }
 function bind(){
  document.querySelectorAll(".tab").forEach(b=>b.addEventListener("click",()=>{
   document.querySelectorAll(".tab").forEach(x=>{x.classList.remove("active");x.setAttribute("aria-selected","false")});
   document.querySelectorAll(".view").forEach(x=>x.classList.remove("active"));
   b.classList.add("active");b.setAttribute("aria-selected","true");el("panel-"+b.dataset.tab).classList.add("active");
  }));
  el("search").addEventListener("input",e=>{state.query=e.target.value;state.shown=20;applyFilters()});
  el("themeFilter").addEventListener("change",e=>{state.filter=e.target.value;state.shown=20;applyFilters()});
  el("textMode").addEventListener("change",e=>{state.searchMode=e.target.value;applyFilters()});
  el("clearFilters").addEventListener("click",()=>{state.query="";state.filter="";state.searchMode="all";el("search").value="";el("themeFilter").value="";el("textMode").value="all";state.shown=20;applyFilters()});
  el("graphFocus").addEventListener("change",e=>{state.graphFocus=e.target.value;renderGraph()});
  el("resetGraph").addEventListener("click",()=>switchGraphFocus([...new Set(state.records.flatMap(r=>r.tags))].sort()[0]||""));
  el("loadMore").addEventListener("click",()=>{state.shown+=20;renderResults()});
  el("refreshData").addEventListener("click",loadOfficialIndex);
  el("importJson").addEventListener("change",e=>{if(e.target.files&&e.target.files[0])importFile(e.target.files[0])});
  el("exportCsv").addEventListener("click",exportCsv);
  el("exportKg").addEventListener("click",async()=>{
    if(!state.isOfficial)return alert("Official source graph unavailable");
    try{
      const response=await fetch("./data/official-index-graph.json");
      if(!response.ok)throw Error("Official graph unavailable");
      const body=await response.text();
      download("ispor_europe_2026_official_index_graph.json",body);
    }catch(e){alert("Export failed: "+e.message)}
  });
 }
 async function init(){
  try{
    const response=await fetch("./data/reviewed-claims.json");
    if(response.ok){const raw=await response.json();reviewedClaims=(raw.claims||[]).filter(c=>safeUrl(c.source_url))}
  }catch(_e){}
  try{await loadOfficialIndex()}
  catch(e){
    setData([],"Official index unavailable",false,0,String(e));
    el("sourceName").textContent="Official dataset unavailable";
    el("sourceDetail").textContent="Unable to verify source: "+String(e)+". Archive data is not substituted.";
  }
 }
 bind();
 init();
})();