import {constantTransitions,psm,survivor,competingIncidence,intervalFromCurves,tunnelProbabilities,runCohort} from "./model-core.mjs";
const $=id=>document.getElementById(id),f=(v,n=4)=>Number(v).toFixed(n),pct=(v,n=2)=>(100*v).toFixed(n)+"%";
const table=(heads,rows)=>'<div class="table-scroll"><table><thead><tr>'+heads.map(h=>'<th>'+h+'</th>').join("")+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(v=>'<td>'+v+'</td>').join("")+'</tr>').join("")+'</tbody></table></div>';
const stat=(label,v,sub="")=>'<div class="stat"><small>'+label+'</small><strong>'+v+'</strong><small>'+sub+'</small></div>';
let chapter=0,lastRun=null;
const sections=[...document.querySelectorAll(".section")];
function showChapter(index){
  chapter=Math.max(0,Math.min(sections.length-1,index));
  sections.forEach((s,i)=>s.classList.toggle("active",i===chapter));
  document.querySelectorAll(".navbtn").forEach((b,i)=>{b.classList.toggle("active",i===chapter);b.setAttribute("aria-current",i===chapter?"step":"false");});
  $("prev").disabled=chapter===0;$("next").disabled=chapter===sections.length-1;
  $("chapter-position").textContent=(chapter+1)+" / "+sections.length;
  const frag=location.hash.slice(1);
  if(frag!=="c"+chapter)history.replaceState(null,"","#c"+chapter);
  window.scrollTo({top:0,behavior:"instant"});
  if(window.MathJax?.typesetPromise)window.MathJax.typesetPromise([sections[chapter]]).catch(()=>{});
}
function drawLines(node,data,series,{xMax=null}={}){
  const W=900,H=310,p={left:58,right:16,top:25,bottom:39},plotW=W-p.left-p.right,plotH=H-p.top-p.bottom;
  const max=xMax??Math.max(...data.map(d=>d.t),1);
  const X=t=>p.left+t/max*plotW,Y=v=>p.top+(1-v)*plotH;
  const colors=["#177d78","#bb7b32","#b55258","#4169a0","#765c9c"];
  let body="";
  for(let q=0;q<=4;q++){
    let v=q/4,yy=Y(v);body+='<line x1="'+p.left+'" y1="'+yy+'" x2="'+(W-p.right)+'" y2="'+yy+'" stroke="#dce7eb" stroke-dasharray="3 3"/><text x="'+(p.left-12)+'" y="'+(yy+4)+'" text-anchor="end" fill="#516a78" font-size="11">'+Math.round(100*v)+'%</text>';
  }
  for(let q=0;q<=4;q++){let t=max*q/4,x=X(t);body+='<text x="'+x+'" y="'+(H-13)+'" text-anchor="middle" fill="#516a78" font-size="11">'+f(t,1)+'</text>';}
  for(let i=0;i<series.length;i++){const s=series[i],points=data.map(d=>X(d.t)+","+Y(Math.max(0,Math.min(1,d[s.key])))).join(" ");body+='<polyline points="'+points+'" fill="none" stroke="'+(s.color||colors[i%colors.length])+'" stroke-width="2.7" stroke-linejoin="round"/>';}
  const legends='<div class="legend">'+series.map((s,i)=>'<span><i style="background:'+(s.color||colors[i%colors.length])+'"></i>'+s.label+'</span>').join("")+"</div>";
  node.innerHTML='<svg viewBox="0 0 '+W+" "+H+'" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'+body+'<text x="'+(W/2)+'" y="'+(H-1)+'" text-anchor="middle" font-size="12" fill="#516a78">Months</text></svg>'+legends;
}
function hazard(){
  const hp=Number($("hp").value),hd=Number($("hd").value),T=Number($("ht").value),dt=Number($("dt").value);
  $("hpv").textContent=f(hp,3)+"/month";$("hdv").textContent=f(hd,3)+"/month";
  $("htv").textContent=T;$("dtv").textContent=f(dt,2);
  const x=competingIncidence(hp,hd,T),tr=constantTransitions(hp,hd,dt);
  $("hazard-stats").innerHTML=[
    stat("PFS at month "+T,pct(x.pf),"Alive and progression-free"),
    stat("Net TTP survival",pct(x.netTTP),"Not actual PF occupancy"),
    stat("Pre-PD death CIF",pct(x.preDeath),"Correct competing event probability"),
    stat("Progression CIF",pct(x.progressed),"Progression as first exit from PF"),
    stat("Wrong TTP minus PFS",pct(x.naiveDeathGap),"Not death incidence"),
    stat("Total PF exit hazard",f(hp+hd,3),"Per month")].join("");
  const data=Array.from({length:101},(_,i)=>{let t=T*i/100,z=competingIncidence(hp,hd,t);return {t,pfs:z.pf,ttp:z.netTTP,preD:z.preDeath,prog:z.progressed};});
  drawLines($("hazard-chart"),data,[{key:"pfs",label:"PFS"},{key:"ttp",label:"Net TTP"},{key:"preD",label:"Pre-PD death CIF"},{key:"prog",label:"Progression CIF"}]);
  $("hazard-steps").innerHTML="<strong>Cycle-specific first-exit probabilities over "+f(dt,2)+" month(s):</strong>"+
   table(["Stay PF","Progress to PD","Die before PD","Sum"],[[pct(tr.stay),pct(tr.prog),pct(tr.death),pct(tr.stay+tr.prog+tr.death)]])+
   '<p>Step 1: total hazard = '+f(hp,3)+' + '+f(hd,3)+' = '+f(hp+hd,3)+
   '. Step 2: any-exit probability = 1 − exp(−total hazard × cycle length) = '+f(1-tr.stay,6)+
   '. Step 3: split exits in the ratio of cause-specific hazards.</p>';
}
["hp","hd","ht","dt"].forEach(id=>$(id).addEventListener("input",hazard));hazard();
function compare(){
  const dt=Number($("compare-delta").value),p=Number($("compare-prog").value),d=Number($("compare-death").value);
  $("compare-delta-value").textContent=f(dt,1)+" months";$("compare-prog-value").textContent=f(p,2);
  $("compare-death-value").textContent=f(d,2);
  const exact=constantTransitions(p,d,dt),netProg=1-Math.exp(-p*dt),netDeath=Math.exp(-p*dt)-Math.exp(-(p+d)*dt);
  $("method-compare").innerHTML=table(["Method","PF → PF","PF → PD","PF → death","Row sum"],[
    ["Exact competing first exits",pct(exact.stay,3),pct(exact.prog,3),pct(exact.death,3),pct(exact.stay+exact.prog+exact.death,3)],
    ["Net-TTP discrete allocation",pct(exact.stay,3),pct(netProg,3),pct(netDeath,3),pct(exact.stay+netProg+netDeath,3)],
    ["Difference (net minus exact)","0",pct(netProg-exact.prog,3),pct(netDeath-exact.death,3),"0"]]);
}
["compare-delta","compare-prog","compare-death"].forEach(id=>$(id).addEventListener("input",compare));compare();
function paths(){
 const pre=Number($("path-pre").value),post=25-pre,progressed=25+post;
 $("path-pre-val").textContent=pre;
 $("paths-output").innerHTML=[
   stat("Ever progressed",progressed,"25 remain PD, "+post+" subsequently died"),
   stat("Died before progression",pre,"Direct PF → death"),
   stat("Died after progression",post,"Through PD → death"),
   stat("PF at month 12",50,"PFS remains 50%"),
   stat("PD alive",25,"OS minus PFS"),
   stat("Dead",25,"OS remains 75%")].join("");
}
$("path-pre").addEventListener("input",paths);paths();
function pps(){
  const v=[1,...["pps1","pps2","pps3"].map(id=>Number($(id).value)/100)];
  try{
    const q=tunnelProbabilities(v);
    $("pps-results").innerHTML=table(["Interval","PPS entering","PPS ending","Conditional mortality","Surviving proportion"],
      q.map((p,i)=>["Month "+(i+1),pct(v[i]),pct(v[i+1]),p===null?"Undefined":pct(p),p===null?"Undefined":pct(1-p)]));
  }catch(e){$("pps-results").innerHTML='<div class="callout danger" role="alert">'+e.message+'</div>';}
}
["pps1","pps2","pps3"].forEach(id=>$(id).addEventListener("input",pps));pps();
function cfg(){
 const n=Number($("sim-n").value),months=Number($("sim-months").value),hp=Number($("sim-hp").value),hd=Number($("sim-hd").value),
 cut=Number($("sim-threshold").value),mode=$("sim-mode").value,
 e=["e1","e2","e3"].map(id=>Number($(id).value)),l=["l1","l2","l3"].map(id=>Number($(id).value));
 if(!Number.isInteger(n)||n<10||n>100000)throw Error("Initial cohort must be an integer between 10 and 100000.");
 if(!Number.isInteger(months)||months<3||months>120)throw Error("The model horizon must be 3–120 whole months.");
 if(!Number.isInteger(cut)||cut<1||cut>120)throw Error("Early progression threshold must be 1–120 months.");
 if([hp,hd].some(v=>!Number.isFinite(v)||v<0||v>1))throw Error("PF hazards must be between 0 and 1 per month.");
 if([...e,...l].some(v=>!Number.isFinite(v)||v<0||v>.95))throw Error("PPS probabilities must be between 0 and 0.95.");
 const early=mode==="constant"?[e[0],e[0],e[0]]:e;
 const late=mode==="history"?l:early;
 return {N:n,months,hProg:hp,hPfDeath:hd,earlyCut:mode==="history"?cut:months,
  earlyPPS:[1,...early.reduce((a,q)=>{a.push((a.length?a[a.length-1]:1)*(1-q));return a;},[])],
  latePPS:[1,...late.reduce((a,q)=>{a.push((a.length?a[a.length-1]:1)*(1-q));return a;},[])]};
}
function renderSim(){
 if(!lastRun)return;
 const rows=lastRun.history,N=rows[0].total,last=rows.at(-1);
 $("sim-summary").innerHTML=[
   stat("Final PFS",pct(last.pf/N),"Alive and progression-free"),
   stat("Final PD",pct(last.pd/N),"Alive after progression"),
   stat("Final OS",pct(last.os/N),"All living patients"),
   stat("Final deaths",pct(last.dead/N),"Before + after progression"),
   stat("Ever progressed",pct(last.cumProg/N),"Includes those who died in PD"),
   stat("Conservation max error",Math.max(...rows.map(r=>Math.abs(r.total-N))).toExponential(2),"Expected count")
 ].join("");
 const slider=$("sim-inspect");slider.max=last.month;slider.value=Math.min(Number(slider.value),last.month);
 const points=rows.map(r=>({t:r.month,pf:r.pf/N,pd:r.pd/N,dead:r.dead/N}));
 drawLines($("sim-chart"),points,[{key:"pf",label:"PF"},{key:"pd",label:"PD alive"},{key:"dead",label:"Death"}]);
 const tbody=$("trace-table").querySelector("tbody");
 tbody.innerHTML=rows.map(r=>'<tr>'+[
 r.month,f(r.pf,2),f(r.early,2),f(r.late,2),f(r.deadPF,2),f(r.deadPD,2),f(r.os,2),f(r.pf,2),f(r.total,2)]
 .map(v=>'<td class="number">'+v+'</td>').join("")+'</tr>').join("");
 inspect();
 const good=rows.every(r=>Math.abs(r.total-N)<1e-7*N&&r.pf>=-1e-8&&r.pd>=-1e-8);
 const monotonic=rows.every((r,i)=>i===0||(r.dead>=rows[i-1].dead-1e-8&&r.pf<=rows[i-1].pf+1e-8));
 $("teststatus").textContent=(good&&monotonic?"✓":"✕")+
   " Cohort conservation, non-negative states and monotonic PF/death checks: "+(good&&monotonic?"PASSED":"FAILED");
}
function inspect(){
 if(!lastRun)return;
 const month=Number($("sim-inspect").value),r=lastRun.history[month],N=lastRun.history[0].total;
 $("sim-inspect-value").textContent=month;
 const parts=[{label:"PF",val:r.pf,color:"#177d78"},{label:"Early PD",val:r.early,color:"#c38c38"},
 {label:"Late PD",val:r.late,color:"#6984b5"},{label:"Death",val:r.dead,color:"#a85a60"}];
 $("sim-stacked").innerHTML='<div class="bar">'+parts.map(p=>'<span title="'+p.label+": "+f(p.val,2)+'" style="width:'+(100*p.val/N)+'%;background:'+p.color+'">'+((p.val/N>.055)?pct(p.val/N,0):"")+'</span>').join("")+'</div>'+
 '<div class="legend">'+parts.map(p=>'<span><i style="background:'+p.color+'"></i>'+p.label+'</span>').join("")+'</div>';
 $("sim-inspection").innerHTML=table(["Current state/pathway","Expected patients","Fraction of initial cohort"],[
 ["PF",f(r.pf,3),pct(r.pf/N)],["Early PD",f(r.early,3),pct(r.early/N)],["Late PD",f(r.late,3),pct(r.late/N)],
 ["Dead before progression",f(r.deadPF,3),pct(r.deadPF/N)],["Dead after progression",f(r.deadPD,3),pct(r.deadPD/N)],
 ["Total",f(r.total,3),pct(r.total/N)] ])+
 table(["Flow in selected month","Patients"],[["Newly progressed",f(r.newProg,3)],
 ["New PF deaths",f(r.fromPfDeath,3)],["New deaths from PD",f(r.postDeath,3)],
 ["Early tunnel counts at cycle end",r.earlyTunnels.map(x=>f(x,2)).join(" / ")],
 ["Late tunnel counts at cycle end",r.lateTunnels.map(x=>f(x,2)).join(" / ")]]);
}
function run(){
 try{lastRun=runCohort(cfg());$("sim-error").textContent="";renderSim();}
 catch(e){$("sim-error").textContent=e.message;lastRun=null;["sim-summary","sim-stacked","sim-chart","sim-inspection"].forEach(id=>$(id).innerHTML="");$("trace-table").querySelector("tbody").innerHTML="";}
}
const defaults={"sim-n":"1000","sim-months":"24","sim-hp":".08","sim-hd":".04","sim-threshold":"6","sim-mode":"history",
"e1":".30","e2":".20","e3":".15","l1":".10","l2":".05","l3":".05"};
$("sim-run").addEventListener("click",run);
$("sim-reset").addEventListener("click",()=>{Object.entries(defaults).forEach(([k,v])=>$(k).value=v);$("sim-inspect").value=12;run();});
$("sim-inspect").addEventListener("input",inspect);
$("sim-export").addEventListener("click",()=>{
 if(!lastRun)return;
 const keys=["month","pf","early","late","pd","deadPF","deadPD","dead","os","cumProg","newProg","fromPfDeath","postDeath","total"];
 const csv=[keys.join(","),...lastRun.history.map(r=>keys.map(k=>r[k]).join(","))].join("\n");
 const url=URL.createObjectURL(new Blob([csv],{type:"text/csv;charset=utf-8"}));
 const a=document.createElement("a");a.href=url;a.download="oncology-survival-cohort-trace.csv";a.click();URL.revokeObjectURL(url);
});
run();
document.querySelectorAll(".quiz").forEach(quiz=>{
 const btn=quiz.querySelector(".check-exercise"),field=quiz.querySelector("input"),result=quiz.querySelector(".feedback");
 btn.addEventListener("click",()=>{
   const val=Number(field.value),answer=Number(quiz.dataset.answer),tol=Number(quiz.dataset.tolerance);
   if(!field.value||!Number.isFinite(val)){result.textContent="Enter a number first.";return;}
   const good=Math.abs(val-answer)<=tol;
   result.style.color=good?"#18764e":"#9d4344";
   result.textContent=good?"Correct. Open the worked solution to check every step.":"Not quite. Check whether you are entering a hazard, probability, or expected count, then open the worked solution.";
 });
});
sections.forEach((section,i)=>{
 const b=document.createElement("button");b.type="button";b.className="navbtn";b.innerHTML='<span class="navnum">'+String(i).padStart(2,"0")+'</span><span>'+section.dataset.title+'</span>';
 b.addEventListener("click",()=>showChapter(i));$("chapternav").append(b);
});
$("prev").addEventListener("click",()=>showChapter(chapter-1));
$("next").addEventListener("click",()=>showChapter(chapter+1));
window.addEventListener("hashchange",()=>{const n=Number(location.hash.slice(2));if(location.hash.match(/^#c\d+$/)&&n!==chapter)showChapter(n);});
let target=location.hash.match(/^#c(\d+)$/);showChapter(target?Number(target[1]):0);
