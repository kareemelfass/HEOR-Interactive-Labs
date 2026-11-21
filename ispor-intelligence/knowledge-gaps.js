"use strict";
/* Add-on only. The existing dashboard and its data processing are untouched. */
(() => {
  const root = document.getElementById("kgGapsContent");
  if (!root) return;
  const search = document.getElementById("kgGapsSearch");
  const count = document.getElementById("kgGapsCount");
  const expandButton = document.getElementById("kgGapsExpand");
  const collapseButton = document.getElementById("kgGapsCollapse");
  const exportButton = document.getElementById("kgGapsExport");
  const domainPattern = /^https:\/\/(?:www\.)?ispor\.org\//i;
  let entries = [];
  let records = [];
  let claims = [];
  let sourceLabel = "No archive index available";
  const node = (tag, cls, value) => {
    const item = document.createElement(tag);
    if (cls) item.className = cls;
    if (value !== undefined && value !== null) item.textContent = String(value);
    return item;
  };
  function sourceUrl(value) {
    return typeof value === "string" && domainPattern.test(value) ? value : "";
  }
  function attachLink(target, url, title) {
    const a = node("a", "", title);
    a.href = url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    target.append(a);
    return a;
  }
  async function getJson(path) {
    const response = await fetch(path, {cache: "no-store"});
    if (!response.ok) throw new Error("HTTP " + response.status + " for " + path);
    return response.json();
  }
  const clean = text => String(text || "").trim().toLowerCase();
  function linkedPresentations(entry) {
    const related = records.filter(r => Array.isArray(r.tags) && r.tags.includes(entry.theme) && sourceUrl(r.url));
    const evidenceCodes = new Set(claims.filter(c => entry.claimIds.includes(c.id)).map(c => clean(c.presentation_code)));
    const terms = (entry.searchTerms || []).map(clean);
    return related.map(r => {
      const title = clean(r.title);
      const score = (evidenceCodes.has(clean(r.id)) ? 16 : 0)
        + terms.reduce((acc, term) => acc + (title.includes(term) ? 3 : 0), 0)
        + (title.includes(clean(entry.theme)) ? 2 : 0);
      return {r, score};
    }).sort((a,b) => b.score - a.score || String(a.r.title).localeCompare(String(b.r.title))).slice(0, 3).map(x => x.r);
  }
  function itemCard(item, index) {
    const card = node("section","kg-gap-question");
    const eyebrow = node("div","kg-gap-kicker","Research question " + (index + 1));
    const question = node("h4","",item.gap);
    const action = node("p","",item.direction);
    const direction = node("span","kg-gap-small-label","Suggested investigation");
    const impactLabel = node("span","kg-gap-small-label","Decision relevance");
    const impact = node("p","kg-gap-implication",item.decision);
    card.append(eyebrow,question,direction,action,impactLabel,impact);
    return card;
  }
  function evidence(entry) {
    const matched = claims.filter(c => entry.claimIds.includes(c.id) && sourceUrl(c.source_url));
    const section = node("section","kg-gap-evidence");
    const title = node("h4","","Specific evidence from reviewed ISPOR abstracts");
    section.append(title);
    if (matched.length) {
      matched.forEach(claim => {
        const block = node("div","kg-gap-claim");
        block.append(node("p","",claim.claim));
        if(claim.qualifier) block.append(node("p","kg-gap-qualifier",claim.qualifier));
        attachLink(block, claim.source_url, "Read author-reported result, " + claim.presentation_code);
        section.append(block);
      });
    } else {
      section.append(node("p","kg-gap-qualifier","No manually reviewed abstract finding has yet been mapped to this theme. The proposed gaps below are research questions, not verified claims of missing evidence."));
    }
    return section;
  }
  function related(entry, amount) {
    const section = node("section","kg-gap-related");
    section.append(node("h4","","Related ISPOR presentations"));
    section.append(node("p","kg-gap-qualifier","These are automatically selected related abstracts. Their presence does not prove that the proposed gaps were identified by the authors."));
    const list = node("ul","");
    const selected = linkedPresentations(entry);
    selected.forEach(r => {
      const li = node("li","");
      attachLink(li, sourceUrl(r.url), (r.id ? r.id + ": " : "") + r.title);
      list.append(li);
    });
    if(!selected.length) list.append(node("li","kg-gap-qualifier","No suitable official links are available in the currently loaded index."));
    section.append(list);
    return section;
  }
  function draw() {
    const query = clean(search.value);
    const matches = entries.filter(entry => {
      if (!query) return true;
      return clean([entry.theme,entry.intro,entry.items.map(x => [x.gap,x.direction,x.decision].join(" "))].join(" ")).includes(query);
    });
    root.replaceChildren();
    matches.forEach((entry,index) => {
      const details = node("details","kg-gap-theme");
      details.dataset.theme = entry.theme;
      if(!query && index === 0) details.open = true;
      if(query) details.open = true;
      const heading = node("summary","kg-gap-summary");
      const headingText = node("div","kg-gap-summary-copy");
      headingText.append(node("strong","",entry.theme),node("span","",entry.intro));
      const n = node("span","kg-gap-theme-count",entry.items.length + " proposed research directions");
      heading.append(headingText,n);
      const body = node("div","kg-gap-body");
      body.append(node("p","kg-gap-statement","Research agenda, not a measured conference-wide consensus: the following are analytical questions and prospective study designs. Where available, specific authors' findings are separately identified."));
      body.append(evidence(entry));
      const grid = node("div","kg-gap-grid");
      entry.items.forEach((item,i)=>grid.append(itemCard(item,i)));
      body.append(grid);
      details.append(heading,body);
      root.append(details);
    });
    if(!matches.length)root.append(node("p","kg-gap-no-results","No theme matches your search."));
    count.textContent = matches.length + " of " + entries.length + " themes · " + matches.reduce((n,x)=>n+x.items.length,0) + " proposed research directions";
  }
  function exportCsv() {
    const cols=["Theme","Research question","Suggested investigation","Decision relevance","Evidence status"];
    const csvRow=arr=>arr.map(v=>'"'+String(v||"").replace(/"/g,'""')+'"').join(",");
    const lines=[csvRow(cols)];
    entries.forEach(entry=>entry.items.forEach(item=>{
      lines.push(csvRow([entry.theme,item.gap,item.direction,item.decision,entry.claimIds.length?"Some author-reported examples available":"Analyst proposed, not verified conference gap"]));
    }));
    const url=URL.createObjectURL(new Blob(["\ufeff"+lines.join("\r\n")],{type:"text/csv;charset=utf-8"}));
    const a=node("a");a.href=url;a.download="ispor_2026_knowledge_gaps_research_agenda.csv";
    document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  async function init() {
    try {
      const loaded = await getJson("./data/knowledge-gaps.json");
      entries = Array.isArray(loaded.themes) ? loaded.themes : [];
      if(entries.length!==16)throw new Error("Expected 16 existing themes, got " + entries.length);
      const [index,reviewed] = await Promise.allSettled([
        getJson("./data/official-index-records.json"),
        getJson("./data/reviewed-claims.json")
      ]);
      if(index.status==="fulfilled" && Array.isArray(index.value.records)) {
        records=index.value.records.map(r=>({
          id:r.code,title:r.title,url:r.official_detail_link_present?r.url:"",
          tags:r.topic_groups||[]
        }));
        sourceLabel="ISPOR-configured search index (" + records.length.toLocaleString("en-GB") +
          " captured items); future directions are proposals, NOT conference-verified gaps";
      } else {
        records=[];
        sourceLabel="Official index unavailable; proposed directions do not establish conference findings";
      }
      claims=reviewed.status==="fulfilled" && Array.isArray(reviewed.value.claims) ? reviewed.value.claims : [];
      document.getElementById("kgGapsSource").textContent=sourceLabel;
      draw();
    }catch(e){
      root.replaceChildren(node("p","kg-gap-error","Could not load the additional research agenda: "+ e.message));
      count.textContent="Unavailable";
    }
  }
  search.addEventListener("input",draw);
  expandButton.addEventListener("click",()=>root.querySelectorAll("details").forEach(d=>d.open=true));
  collapseButton.addEventListener("click",()=>root.querySelectorAll("details").forEach(d=>d.open=false));
  exportButton.addEventListener("click",exportCsv);
  init();
})();