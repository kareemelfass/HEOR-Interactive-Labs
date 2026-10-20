"use strict";
/* Pure client-side calculations. No cookies, network requests, analytics, or libraries. */
const $ = id => document.getElementById(id);
const num = id => Number($(id).value);
const fmt = (v,d=0) => Number.isFinite(v)?v.toLocaleString("en-US",{minimumFractionDigits:d,maximumFractionDigits:d}):"N/A";
const safe = v => Number.isFinite(v)?v:0;
const money = (v,d=0) => (v<0?"−US$":"US$")+fmt(Math.abs(v),d);
const signed = (v,d=1) => (v<0?"−":"+")+fmt(Math.abs(v),d);
const metric = (name,value) => '<div class="metric"><strong>'+value+'</strong><span>'+name+'</span></div>';
const df=(r,t)=>Math.pow(1+r,-t);
const af=(r,n)=>Math.abs(r)<1e-12?n:(1-Math.pow(1+r,-n))/r;
const npv=(cfs,r)=>cfs.reduce((s,c,t)=>s+c*df(r,t),0);
/* Required: only report an IRR if a sign change exists between -99% and +100%. */
function irr(cfs){
 let low=-.99,high=1,fl=npv(cfs,low),fh=npv(cfs,high);
 if(!Number.isFinite(fl)||!Number.isFinite(fh))return null;
 if(Math.abs(fl)<1e-8)return low;
 if(Math.abs(fh)<1e-8)return high;
 if(Math.sign(fl)===Math.sign(fh))return null;
 for(let i=0;i<160;i++){const mid=(low+high)/2,fm=npv(cfs,mid);if(Math.abs(fm)<1e-7)return mid;if(Math.sign(fm)===Math.sign(fl)){low=mid;fl=fm;}else high=mid;}
 return (low+high)/2;
}
const esc=s=>String(s).replace(/[&<>"']/g,x=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[x]));
const svgStart=(label,w=640,h=265)=>'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+w+' '+h+'" role="img" aria-label="'+esc(label)+'">';
const chartEnd='</svg>';
const coords=(x,y)=>fmt(x,2)+","+fmt(y,2);
/* This SVG chart uses text labels as well as patterns or line geometry: colour is never essential. */
function lineChart(el,curves,xmin,xmax,ymin,ymax,labels){
 let svg=svgStart(labels.title),l=55,r=14,t=16,b=42,w=640,h=265;
 const X=x=>l+(x-xmin)/(xmax-xmin)*(w-l-r);
 const Y=y=>h-b-(y-ymin)/(ymax-ymin)*(h-t-b);
 for(let j=0;j<=4;j++){const y=ymin+(ymax-ymin)*j/4,py=Y(y);
 svg+='<line x1="'+l+'" x2="'+(w-r)+'" y1="'+py+'" y2="'+py+'" class="gridline"/><text x="'+(l-7)+'" y="'+(py+4)+'" text-anchor="end">'+esc(labels.y(y))+'</text>';}
 for(let j=0;j<=5;j++){const x=xmin+(xmax-xmin)*j/5;
 svg+='<text x="'+X(x)+'" y="'+(h-17)+'" text-anchor="middle">'+esc(labels.x(x))+'</text>';}
 svg+='<line class="axis" x1="'+l+'" y1="'+(h-b)+'" x2="'+(w-r)+'" y2="'+(h-b)+'"/>';
 curves.forEach((series,i)=>{const d=series.map((p,j)=>(j?" L":"M")+coords(X(p[0]),Y(p[1]))).join("");
 svg+='<path class="'+(i?"series-b":"series-a")+'" d="'+d+'" stroke-linejoin="round"/>';});
 svg+='<text x="'+(w/2)+'" y="'+(h-2)+'" text-anchor="middle">'+esc(labels.xlabel)+'</text>'+chartEnd;
 $(el).innerHTML=svg;
}
function groupedBars(el,values,title,labels,subtitle){
 const w=640,h=values.length>3?300:220,l=120,r=26,t=22,b=18;
 const vmin=Math.min(0,...values),vmax=Math.max(0,...values);
 const spread=(vmax-vmin)||1;
 const X=v=>l+(v-vmin)/spread*(w-l-r);
 const base=X(0),rowH=(h-t-b)/values.length;
 let svg=svgStart(title,w,h);
 svg+='<line class="axis" x1="'+base+'" x2="'+base+'" y1="'+t+'" y2="'+(h-b)+'"/>';
 values.forEach((value,i)=>{
 const y=t+i*rowH+rowH*.2,bh=rowH*.5,a=X(value);
 svg+='<rect class="'+(i===2||i===3?"bar-warn":"bar-a")+'" x="'+Math.min(a,base)+'" y="'+y+'" width="'+Math.max(1,Math.abs(a-base))+'" height="'+bh+'" rx="3"/>';
 svg+='<text x="'+(l-7)+'" y="'+(y+bh*.75)+'" text-anchor="end">'+esc(labels[i])+'</text>';
 const label=subtitle?subtitle(value,i):fmt(value,1);
 svg+='<text x="'+(value>=0?Math.min(w-5,a+5):Math.max(5,a-5))+'" y="'+(y+bh*.75)+'" text-anchor="'+(value>=0?"start":"end")+'">'+esc(label)+'</text>';
 });
 $(el).innerHTML=svg+chartEnd;
}
const QUIZ=[
 ["Digital thermometer",true,"Used for diagnosis or monitoring; works physically."],
 ["Insulin (the drug itself)",false,"Main action is metabolic, so it is a medicine."],
 ["Reusable insulin pen (empty)",true,"It delivers a medicine but works mechanically."],
 ["Software that reads chest X-rays to flag disease",true,"Software is listed; purpose is diagnosis."],
 ["Disinfectant made for cleaning endoscopes",true,'"Cleaning, disinfection or sterilization of medical devices" is a listed purpose.'],
 ["HIV test kit using a blood sample",true,"In vitro examination of human specimens."]
];
function makeQuiz(){
 $("quiz-cards").innerHTML=QUIZ.map((q,i)=>'<div class="quiz-card"><p class="tag">QUESTION '+(i+1)+'</p><strong>'+esc(q[0])+'</strong><div class="btnrow"><button type="button" data-quiz="'+i+'" data-choice="1">Device</button><button type="button" data-quiz="'+i+'" data-choice="0">Not a device</button></div><p class="quiz-feedback" id="quiz-feedback-'+i+'" aria-live="polite"></p></div>').join("");
 document.querySelectorAll("[data-quiz]").forEach(b=>b.addEventListener("click",()=>{
 const i=Number(b.dataset.quiz),chosen=b.dataset.choice==="1",correct=QUIZ[i][1];
 document.querySelectorAll('[data-quiz="'+i+'"]').forEach(k=>{k.classList.toggle("active",k===b);k.setAttribute("aria-pressed",String(k===b));});
 $("quiz-feedback-"+i).textContent=(chosen===correct?"Correct. ":"Not quite. ")+(correct?"Device. ":"Not a device. ")+QUIZ[i][2];
 }));
}
function resetQuiz(){makeQuiz();}
const CLASSES={
 "EU":{labels:["I","IIa","IIb","III"],text:"MDR (EU) 2017/745: four risk classes. Class III is highest. WHO examples: thermometer (low), infusion pump (medium), implanted stimulator (high)."},
 "US":{labels:["I","II","III"],text:"FDA: Class I generally uses general controls; Class II often requires 510(k); Class III generally requires premarket approval."},
 "Canada":{labels:["I","II","III","IV"],text:"Health Canada examples: manual wheelchair (I), hearing aid (II), hip implant (III), pacemaker (IV)."},
 "EU IVD":{labels:["A","B","C","D"],text:"IVDR (EU) 2017/746 examples: specimen receptacle (A), pregnancy test (B), genetic or cancer test (C), HIV or hepatitis infectious load (D)."}
};
let classChoice="EU";
function drawClasses(){
 $("class-tabs").innerHTML=Object.keys(CLASSES).map(name=>'<button type="button" data-class="'+esc(name)+'" class="'+(classChoice===name?"active":"")+'" aria-pressed="'+(classChoice===name)+'">'+esc(name)+'</button>').join("");
 $("class-ladder").innerHTML=CLASSES[classChoice].labels.map((label,i,all)=>'<div class="risk-step"><span class="small">'+(i===0?"Low risk":i===all.length-1?"High risk":"Increasing risk")+'</span><b>'+label+'</b></div>').join("");
 $("class-example").textContent=CLASSES[classChoice].text;
 $("class-tabs").querySelectorAll("button").forEach(b=>b.addEventListener("click",()=>{classChoice=b.dataset.class;drawClasses();}));
}
function drawDiscount(){
 const r=num("discount-rate")/100,c=num("discount-cost"),n=num("discount-years"),q=num("discount-qaly");
 $("discount-rate-label").textContent=fmt(100*r,1)+"%";
 if(!(n>=1&&Number.isInteger(n)&&q>0&&c>=0)){ $("discount-out").textContent="Enter valid positive years and QALYs.";return;}
 const a=af(r,n),qy=q*a,d=c/qy,drug=(c/n*a)/qy,pct=drug>0?(d/drug-1)*100:0;
 $("discount-out").innerHTML=metric("QALYs today",fmt(qy,4))+metric("Device ICER",money(d))+metric("Drug ICER",money(drug))+metric("Device ICER higher",fmt(pct,1)+"%");
 const series1=[],series2=[];
 for(let k=0;k<=20;k++){const rate=k*.005;series1.push([rate*100,c/(q*af(rate,n))]);series2.push([rate*100,c/(n*q)]);}
 const hi=Math.max(...series1.map(z=>z[1]),...series2.map(z=>z[1]));
 lineChart("discount-chart",[series1,series2],0,10,0,Math.max(1,hi*1.1),{title:"Device versus drug ICER across discount rates",x:v=>fmt(v,0)+"%",y:v=>"$"+fmt(v/1000,1)+"k",xlabel:"Discount rate"});
}
function drawPS(){
 const dh=num("ps-dh"),dl=num("ps-dl"),ch=num("ps-ch"),cl=num("ps-cl"),rdh=num("ps-rdh")/100,rdl=num("ps-rdl")/100,rch=num("ps-rch")/100,rcl=num("ps-rcl")/100;
 const rates=[rdh,rdl,rch,rcl];
 if([dh,dl,ch,cl].some(x=>!Number.isFinite(x)||x<0)||rates.some(x=>!Number.isFinite(x)||x<0||x>1)||dh+dl<=0||ch+cl<=0||(dh+ch)<=0||(dl+cl)<=0){
 $("ps-out").textContent="Enter non-negative patient counts, rates from 0 to 100, and at least one person in each risk stratum.";return;}
 const dr=(dh*rdh+dl*rdl)/(dh+dl),cr=(ch*rch+cl*rcl)/(ch+cl),cf=(dh*rch+dl*rcl)/(dh+dl);
 const diff=(dr-cr)*100,att=(dr-cf)*100,psh=dh/(dh+ch),psl=dl/(dl+cl);
 $("ps-out").innerHTML=metric("Naive device rate",fmt(dr*100,1)+"%")+metric("Naive standard care rate",fmt(cr*100,1)+"%")+metric("Naive difference",signed(diff,1)+" pp")+metric("Counterfactual rate",fmt(cf*100,1)+"%")+metric("ATT (adjusted)",signed(att,1)+" pp")+metric("PS, high risk",fmt(psh,2))+metric("PS, low risk",fmt(psl,2));
 groupedBars("ps-chart",[diff,att],"Naive versus adjusted complication risk difference, percentage points",["Naive","ATT"],v=>signed(v,1)+" pp");
}
function drawScale(){
 const capital=num("scale-capital"),life=num("scale-life"),r=num("scale-rate")/100,m=num("scale-maint"),c=num("scale-cons"),cap=num("scale-capacity"),vol=num("scale-volume");
 $("scale-volume-label").textContent=fmt(vol)+" cases";
 if(!(life>=1&&Number.isInteger(life)&&r>=0&&r<=.5&&capital>=0&&m>=0&&c>=0&&cap>0&&vol>0)){ $("scale-out").textContent="Enter valid non-negative costs, positive capacity/volume and a positive whole-number life.";return;}
 const eac=capital/af(r,life),fixed=eac+m,machines=Math.ceil(vol/cap),fixedCase=machines*fixed/vol,total=fixedCase+c;
 $("scale-out").innerHTML=metric("Annual capital cost (EAC)",money(eac))+metric("Machines needed",fmt(machines))+metric("Fixed cost per case",money(fixedCase,2))+metric("Total cost per case",money(total,2));
 const points=[];
 for(let v=50;v<=3000;v+=5)points.push([v,Math.ceil(v/cap)*fixed/v+c]);
 const vmax=Math.max(...points.map(p=>p[1]));
 lineChart("scale-chart",[points],50,3000,0,Math.max(1,vmax*1.03),{title:"Cost per case including machine-capacity steps",x:v=>fmt(v),y:v=>"$"+fmt(v,0),xlabel:"Cases per year"});
}
function payback(cfs){
 let cumulative=cfs[0];if(cumulative>=0)return 0;
 for(let year=1;year<cfs.length;year++){const before=cumulative;cumulative+=cfs[year];if(cumulative>=0&&cfs[year]>0)return (year-1)+(-before)/cfs[year];}
 return null;
}
function drawNPV(){
 const purchase=num("npv-purchase"),pay=num("npv-payment"),variable=num("npv-variable"),maint=num("npv-maint"),r=num("npv-rate")/100;
 const cases=Array.from({length:5},(_,i)=>num("npv-y"+(i+1)));
 if(![purchase,pay,variable,maint,...cases].every(x=>Number.isFinite(x)&&x>=0)||!Number.isFinite(r)||r<0||r>1){$("npv-out").textContent="Enter non-negative values and a discount rate between 0% and 100%.";return;}
 const margin=pay-variable,cfs=[-purchase,...cases.map(n=>n*margin-maint)],N=npv(cfs,r),I=irr(cfs),P=payback(cfs);
 const pvCases=cases.reduce((s,n,i)=>s+n*df(r,i+1),0),af5=af(r,5),bePay=pvCases>0?variable+(purchase+maint*af5)/pvCases:null;
 const beVol=pvCases>0&&margin>0?(purchase+maint*af5)/(margin*pvCases)*100:null;
 $("npv-out").innerHTML=metric("NPV at "+fmt(r*100,1)+"%",money(N))+metric("IRR",I===null?"IRR not defined for these cash flows":fmt(I*100,1)+"%")+metric("Payback (undiscounted)",P===null?"Not reached":fmt(P,1)+" years")+metric("Break-even payment",bePay===null?"N/A":money(bePay))+metric("Break-even volume",beVol===null?"N/A":fmt(beVol,0)+"% of plan");
 let cumul=0,pvs=[];const rows=cfs.map((v,i)=>{const pv=v*df(r,i);cumul+=pv;pvs.push(cumul);
 return "<tr><td>"+i+"</td><td>"+(i?fmt(cases[i-1]):"Purchase")+"</td><td>"+money(v)+"</td><td>"+fmt(df(r,i),4)+"</td><td>"+money(pv)+"</td><td>"+money(cumul)+"</td></tr>";});
 $("npv-cash-rows").innerHTML=rows.join("");
 drawNPVChart(cfs.map((x,i)=>x*df(r,i)),pvs);
 const a=[-1000,500,500,500],miniI=irr(a);
 $("mini-npv").textContent="NPV = "+fmt(npv(a,.1),1)+" and IRR = "+fmt(miniI*100,1)+"%";
}
function drawNPVChart(pv,cum){
 const w=640,h=300,l=52,r=10,t=15,b=40,lo=Math.min(0,...pv,...cum),hi=Math.max(0,...pv,...cum),span=hi-lo||1;
 const X=i=>l+i*(w-l-r)/6+(w-l-r)/12, Y=v=>h-b-(v-lo)/span*(h-t-b),base=Y(0);
 let s=svgStart("Discounted yearly cash flow bars and cumulative present value line",w,h);
 for(let i=0;i<=4;i++){let y=lo+(hi-lo)*i/4;
 s+='<line class="gridline" x1="'+l+'" x2="'+(w-r)+'" y1="'+Y(y)+'" y2="'+Y(y)+'"/><text x="'+(l-5)+'" y="'+(Y(y)+4)+'" text-anchor="end">'+fmt(y/1000,0)+'k</text>';}
 pv.forEach((v,i)=>{const x=X(i),y=Y(v);s+='<rect class="'+(v<0?"bar-warn":"bar-a")+'" x="'+(x-20)+'" y="'+Math.min(base,y)+'" width="40" height="'+Math.max(1,Math.abs(base-y))+'"/><text x="'+x+'" y="'+(h-16)+'" text-anchor="middle">Y'+i+'</text>';});
 s+='<polyline class="series-b" points="'+cum.map((v,i)=>coords(X(i),Y(v))).join(" ")+'"/>';
 cum.forEach((v,i)=>{s+='<circle cx="'+X(i)+'" cy="'+Y(v)+'" r="3" fill="#d18b39"/>';});
 s+='<text x="'+(w/2)+'" y="'+(h-2)+'" text-anchor="middle">Year</text>';
 $("npv-chart").innerHTML=s+chartEnd+'<div class="legend"><span>Discounted cash flow</span><span class="alt">Cumulative NPV</span></div>';
}
function drawCapital(){
 const cost=num("capital-cost"),n=num("capital-life"),r=num("capital-rate")/100,maint=num("capital-maint"),cons=num("capital-cons"),cases=num("capital-cases");
 if(!(n>=1&&Number.isInteger(n)&&r>=0&&r<=1&&cost>=0&&maint>=0&&cons>=0&&cases>0)){ $("capital-out").textContent="Enter valid positive life and cases, and non-negative costs and rate.";return;}
 const factor=af(r,n),eac=cost/factor,depn=cost/n,oper=maint+cons*cases,discCases=cases*factor,runPV=oper*factor;
 const capitalA=cost,capitalB=eac*factor,capitalC=depn*factor,capitalD=cost+capitalC;
 let capitalE=0;
 for(let t=1;t<=n;t++)capitalE+=(depn+r*(cost-depn*(t-1)))*df(r,t);
 const capitals=[capitalA,capitalB,capitalC,capitalD,capitalE],names=["A: Year 0","B: Annuity","C: Depreciation only","D: Year 0 + depreciation","E: Depreciation + capital charge"];
 const vals=capitals.map(c=>(c+runPV)/discCases),verdict=["Correct","Correct",r===0?"Correct at 0%":"Too low (ignores capital charge)","Double counted", "Correct"];
 $("capital-out").innerHTML=metric("Annuity factor",fmt(factor,5))+metric("Annual capital cost",money(eac))+metric("Discounted cases",fmt(discCases,1))+metric("Running cost (PV)",money(runPV));
 const discRows=['<tr><td>0</td><td>1.00000</td><td>0</td><td>0</td></tr>'];
 const loanRows=[];let bal=cost;
 for(let t=1;t<=n;t++){
 const interest=bal*r,principal=eac-interest,remain=Math.max(0,bal-principal);
 discRows.push('<tr><td>'+t+'</td><td>'+fmt(df(r,t),5)+'</td><td>'+money(eac)+'</td><td>'+money(eac*df(r,t))+'</td></tr>');
 loanRows.push('<tr><td>'+t+'</td><td>'+money(bal)+'</td><td>'+money(eac)+'</td><td>'+money(interest)+'</td><td>'+money(principal)+'</td><td>'+money(remain)+'</td></tr>');
 bal=remain;
 }
 $("capital-discount-rows").innerHTML=discRows.join("");
 $("capital-loan-rows").innerHTML=loanRows.join("");
 $("capital-method-rows").innerHTML=capitals.map((c,i)=>{
 const delta=vals[i]-vals[0],pct=vals[0]?delta/vals[0]*100:0;
 return '<tr><td>'+names[i]+'</td><td>'+money(c)+'</td><td>'+money(c+runPV)+'</td><td>'+money(vals[i],2)+'</td><td>'+signed(delta,2)+' US$ ('+signed(pct,1)+'%)</td><td>'+verdict[i]+'</td></tr>';
 }).join("");
 groupedBars("capital-chart",vals,"Cost per case: capital costing methods A to E",["A: Correct","B: Correct","C: "+(r?"Too low":"Correct"),"D: Double count","E: Correct"],v=>"$"+fmt(v,2));
}
const FEATURES=["All","Low evidence","Learning curve","Incremental innovation","Diversity","Dynamic pricing","Other"];
const COUNTRIES=["All","Canada","France","Ireland","Japan","Netherlands","New Zealand","UK"];
let guidelineFeature="All",guidelineCountry="All";
function chips(id,items,active,onSelect){
 $(id).innerHTML=items.map(x=>'<button type="button" class="chip '+(active===x?"active":"")+'" aria-pressed="'+(x===active)+'" data-value="'+esc(x)+'">'+esc(x)+'</button>').join("");
 $(id).querySelectorAll("button").forEach(b=>b.addEventListener("click",()=>onSelect(b.dataset.value)));
}
function drawGuidelines(){
 chips("feature-chips",FEATURES,guidelineFeature,x=>{guidelineFeature=x;drawGuidelines();});
 chips("country-chips",COUNTRIES,guidelineCountry,x=>{guidelineCountry=x;drawGuidelines();});
 const rows=Array.from(document.querySelectorAll("#guideline-table tbody tr")).filter(r=>(guidelineFeature==="All"||r.dataset.feature===guidelineFeature)&&(guidelineCountry==="All"||r.dataset.country===guidelineCountry));
 $("guideline-count").textContent=rows.length+" matching guideline items.";
 $("guideline-cards").innerHTML=rows.length?rows.map(r=>{
 const cells=Array.from(r.cells);
 return '<article class="quote-card"><p class="tag">'+esc(cells[0].textContent)+'</p><strong>'+esc(cells[1].textContent)+'</strong><p>'+cells[2].innerHTML+'</p></article>';
 }).join(""):'<p>No matching guideline items.</p>';
}
const TRANSFER_Q=[
 ["Have all potentially relevant RWE studies been searched for and collected systematically?","Search and collect"],
 ["Is the device in the study equivalent to the local device (no major differences)?","Equivalent technology"],
 ["Does the study pass a quality assessment (for example GRADE, ROBINS-I, ISPOR transparency) at a level suitable for pooling?","Quality"],
 ["Does a transferability checklist (for example the EUnetHTA Adaptation Toolkit) show similar patients, practice and health system?","Applicability"],
 ["Does the local system have constraints in follow-up care or very different patient pathways?","Local constraints"],
 ["Do outcomes vary little across centres in the country of origin?","Low centre variability"]
];
let transfer=Array(6).fill(null);
function makeTransfer(){
 $("transfer-questions").innerHTML=TRANSFER_Q.map((q,i)=>'<div class="quiz-card" style="margin:10px 0"><div class="tag">'+(i<4?"STEP "+(i+1):"CONTEXT "+(i-3))+" · "+esc(q[1])+'</div><p>'+esc(q[0])+'</p><div class="btnrow">'+["Yes","No","Unsure"].map(a=>'<button type="button" data-transfer="'+i+'" data-answer="'+a+'" class="'+(transfer[i]===a?"active":"")+'" aria-pressed="'+(transfer[i]===a)+'">'+a+'</button>').join("")+'</div></div>').join("");
 document.querySelectorAll("[data-transfer]").forEach(b=>b.addEventListener("click",()=>{transfer[Number(b.dataset.transfer)]=b.dataset.answer;makeTransfer();}));
 let msg="";
 if(transfer[1]==="No"||transfer[2]==="No")msg="Do not transfer this study's effect estimate.";
 else if(transfer.slice(0,4).some(x=>x===null||x==="Unsure")||transfer[4]===null||transfer[4]==="Unsure"||(transfer[4]==="No"&&(transfer[5]===null||transfer[5]==="Unsure")))msg="Gather more information before deciding.";
 else if(transfer.slice(0,4).some(x=>x==="No"))msg="Do not transfer until the systematic search and local applicability concerns are resolved.";
 else if(transfer[4]==="Yes")msg="Transfer, but use highly conservative effectiveness estimates.";
 else if(transfer[5]==="Yes")msg="Transfer is more credible; use the estimate with an appropriate comparator and test it in sensitivity analysis.";
 else msg="Transfer cautiously. Centre-level outcome variability may limit local applicability; test conservative scenarios and investigate effect modifiers.";
 $("transfer-out").textContent=msg;
}
const GROUP_IDS={
 discount:["discount-rate","discount-cost","discount-years","discount-qaly"],
 ps:["ps-dh","ps-rdh","ps-dl","ps-rdl","ps-ch","ps-rch","ps-cl","ps-rcl"],
 scale:["scale-capital","scale-life","scale-rate","scale-maint","scale-cons","scale-capacity","scale-volume"],
 npv:["npv-purchase","npv-payment","npv-variable","npv-maint","npv-y1","npv-y2","npv-y3","npv-y4","npv-y5","npv-rate"],
 capital:["capital-cost","capital-life","capital-rate","capital-maint","capital-cons","capital-cases"]
};
const DRAW={discount:drawDiscount,ps:drawPS,scale:drawScale,npv:drawNPV,capital:drawCapital};
Object.keys(GROUP_IDS).forEach(key=>{
 GROUP_IDS[key].forEach(id=>{const input=$(id);input.dataset.default=input.value;input.addEventListener("input",DRAW[key]);});
 DRAW[key]();
});
document.querySelectorAll("[data-reset]").forEach(b=>b.addEventListener("click",()=>{
 const key=b.dataset.reset;
 if(GROUP_IDS[key]){GROUP_IDS[key].forEach(id=>{$(id).value=$(id).dataset.default;});DRAW[key]();}
 else if(key==="quiz")resetQuiz();
 else if(key==="class"){classChoice="EU";drawClasses();}
 else if(key==="guidelines"){guidelineFeature="All";guidelineCountry="All";drawGuidelines();}
 else if(key==="transfer"){transfer=Array(6).fill(null);makeTransfer();}
}));
makeQuiz();drawClasses();drawGuidelines();makeTransfer();
$("backtop").addEventListener("click",()=>window.scrollTo({top:0,behavior:"smooth"}));
document.querySelectorAll(".navmenu a").forEach(a=>a.addEventListener("click",()=>{$("navmenu").open=false;}));
/* Opening a specific chapter when following an anchor to it, including on load. */
function openLinkedChapter(){
 const id=window.location.hash.substring(1),node=$(id);
 if(!node)return;
 const chapter=node.classList.contains("chapter")?node:node.closest(".chapter");
 if(chapter&&chapter.tagName==="DETAILS")chapter.open=true;
}
window.addEventListener("hashchange",openLinkedChapter);openLinkedChapter();
let beforePrint=[];
window.addEventListener("beforeprint",()=>{beforePrint=Array.from(document.querySelectorAll("details.chapter")).map(x=>x.open);document.querySelectorAll("details.chapter").forEach(x=>x.open=true);});
window.addEventListener("afterprint",()=>{document.querySelectorAll("details.chapter").forEach((x,i)=>x.open=beforePrint[i]);});
