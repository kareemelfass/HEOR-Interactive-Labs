"use strict";
/* Editorial questions, explicitly separate from source-verified classifications. */
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
  let claims = [];
  let sourceLabel = "Editorial research agenda; not a systematic review";
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
  function itemCard(item, index) {
    const card = node("section","kg-gap-question");
    const eyebrow = node("div","kg-gap-kicker","Unverified research hypothesis " + (index + 1));
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
    const title = node("h4","","Illustrative author-reported statements (context only)");
    section.append(title,node("p","kg-gap-qualifier","No supporting, contradicting or contextual relationship to the proposed hypotheses has been independently established. These examples must not be used as proof that a research gap exists."));
    if (matched.length) {
      matched.forEach(claim => {
        const block = node("div","kg-gap-claim");
        block.append(node("p","",claim.claim));
        if(claim.qualifier) block.append(node("p","kg-gap-qualifier",claim.qualifier));
        attachLink(block, claim.source_url, "Read original author-reported statement, " + claim.presentation_code);
        section.append(block);
      });
    } else {
      section.append(node("p","kg-gap-qualifier","No illustrative ISPOR statement is attached. This is an editorial hypothesis, not an identified literature gap."));
    }
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
      const n = node("span","kg-gap-theme-count",entry.items.length + " hypotheses to test");
      heading.append(headingText,n);
      const body = node("div","kg-gap-body");
      body.append(node("p","kg-gap-statement","Editorial research hypotheses; these are neither an official ISPOR topic taxonomy nor empirically demonstrated gaps. Contextual statements below are not validation of the hypotheses."));
      body.append(evidence(entry));
      const grid = node("div","kg-gap-grid");
      entry.items.forEach((item,i)=>grid.append(itemCard(item,i)));
      body.append(grid);
      details.append(heading,body);
      root.append(details);
    });
    if(!matches.length)root.append(node("p","kg-gap-no-results","No theme matches your search."));
    count.textContent = matches.length + " of " + entries.length + " editorial topics · " + matches.reduce((n,x)=>n+x.items.length,0) + " proposed hypotheses";
  }
  function exportCsv() {
    const cols=["Editorial theme","Unverified research hypothesis","Suggested investigation","Decision relevance","Evidence status"];
    const csvRow=arr=>arr.map(v=>'"'+String(v||"").replace(/"/g,'""')+'"').join(",");
    const lines=[csvRow(cols)];
    entries.forEach(entry=>entry.items.forEach(item=>{
      lines.push(csvRow([entry.theme,item.gap,item.direction,item.decision,"Editorial proposal, not established by an evidence gap assessment"]));
    }));
    const url=URL.createObjectURL(new Blob(["\ufeff"+lines.join("\r\n")],{type:"text/csv;charset=utf-8"}));
    const a=node("a");a.href=url;a.download="ispor_2026_proposed_research_questions.csv";
    document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  async function init() {
    try {
      const loaded = await getJson("./data/knowledge-gaps.json");
      entries = Array.isArray(loaded.themes) ? loaded.themes : [];
      if(entries.length!==16)throw new Error("Expected 16 existing themes, got " + entries.length);
      const reviewed = await getJson("./data/reviewed-claims.json").catch(() => ({claims: []}));
      claims = Array.isArray(reviewed.claims) ? reviewed.claims : [];
      sourceLabel = "Independent editorial proposals; 16 legacy themes; no conference-wide gap assessment";
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