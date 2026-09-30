/* Dependency-free oncology survival modelling engine. Illustrative expected cohorts only. */
export const EPS=1e-10;
export function nonnegative(x,label){if(!Number.isFinite(x)||x<0)throw Error(label+" must be non-negative and finite.");}
export function constantTransitions(hProg,hDeath,dt=1){
  nonnegative(hProg,"Progression hazard");nonnegative(hDeath,"PF death hazard");
  if(!(Number.isFinite(dt)&&dt>0))throw Error("Cycle length must be positive.");
  const total=hProg+hDeath,stay=Math.exp(-total*dt),exit=1-stay;
  return {stay,prog:total>EPS?exit*hProg/total:0,death:total>EPS?exit*hDeath/total:0,
    total,hProg,hDeath,dt};
}
export function psm(pfs,os){
  if(!Number.isFinite(pfs)||!Number.isFinite(os)||pfs<0||os>1||pfs>os||os<0)
    throw Error("PSM requires 0 ≤ PFS ≤ OS ≤ 1 at this time.");
  return {pf:pfs,pd:os-pfs,death:1-os};
}
export function survivor(h,t){nonnegative(h,"Hazard");nonnegative(t,"Time");return Math.exp(-h*t);}
export function competingIncidence(hProg,hDeath,t){
  const tr=constantTransitions(hProg,hDeath,t);
  return {pf:tr.stay,progressed:tr.prog,preDeath:tr.death,
    netTTP:survivor(hProg,t),naiveDeathGap:survivor(hProg,t)-tr.stay};
}
export function intervalFromCurves(pfsStart,pfsEnd,ttpStart,ttpEnd,dt=1){
  for(const [x,name] of [[pfsStart,"PFS start"],[pfsEnd,"PFS end"],[ttpStart,"TTP start"],[ttpEnd,"TTP end"]])
    if(!Number.isFinite(x)||x<=0||x>1)throw Error(name+" must be >0 and ≤1.");
  if(pfsEnd>pfsStart||ttpEnd>ttpStart)throw Error("Survival curves must not increase over the interval.");
  if(!Number.isFinite(dt)||dt<=0)throw Error("Interval duration must be positive.");
  const H_pfs=-Math.log(pfsEnd/pfsStart),H_ttp=-Math.log(ttpEnd/ttpStart),H_death=H_pfs-H_ttp;
  if(H_death< -1e-8)throw Error("Negative PF death interval hazard: check endpoint compatibility and independently fitted curves.");
  const tr=constantTransitions(H_ttp/dt,Math.max(0,H_death)/dt,dt);
  return {H_pfs,H_ttp,H_death:Math.max(0,H_death),h_pfs:H_pfs/dt,h_ttp:H_ttp/dt,
    h_death:Math.max(0,H_death)/dt,...tr};
}
export function tunnelProbabilities(survival){
  if(!Array.isArray(survival)||survival.length<2)throw Error("Enter PPS at baseline and at least one follow-up time.");
  if(Math.abs(survival[0]-1)>EPS)throw Error("PPS must start at 1.");
  for(let i=0;i<survival.length;i++){
    const x=survival[i];
    if(!Number.isFinite(x)||x<0||x>1)throw Error("PPS values must lie between 0 and 1.");
    if(i&&x>survival[i-1]+EPS)throw Error("PPS must not increase.");
  }
  return survival.slice(1).map((v,i)=>survival[i]>EPS ? 1-v/survival[i] : null);
}
export function runCohort({N=100,months=12,hProg=.08,hPfDeath=.04,
  earlyCut=6,earlyPPS=[1,.7,.56,.448],latePPS=[1,.9,.855,.81225]}={}){
  nonnegative(N,"Cohort size");
  if(!(Number.isInteger(months)&&months>=1&&months<=240))throw Error("Months must be an integer from 1 to 240.");
  if(!(Number.isInteger(earlyCut)&&earlyCut>=0))throw Error("Early-progression cutoff must be non-negative integer.");
  const tp=constantTransitions(hProg,hPfDeath,1),ep=tunnelProbabilities(earlyPPS),lp=tunnelProbabilities(latePPS);
  if(ep.includes(null)||lp.includes(null))throw Error("PPS reached zero before its last interval; specify a suitable tail.");
  const ev=Array.from({length:ep.length},()=>0),lv=Array.from({length:lp.length},()=>0);
  let pf=N,deadPF=0,deadPD=0,cumProg=0;const history=[];
  const save=(month,newProg=0,fromPfDeath=0,postDeath=0)=>{
    const early=ev.reduce((a,b)=>a+b,0),late=lv.reduce((a,b)=>a+b,0),pd=early+late,dead=deadPF+deadPD;
    history.push({month,pf,early,late,pd,dead,os:pf+pd,deadPF,deadPD,cumProg,newProg,fromPfDeath,postDeath,
      total:pf+pd+dead,earlyTunnels:[...ev],lateTunnels:[...lv]});
  };
  save(0);
  const progressTunnel=(counts,prob)=>{
    let deaths=0;
    for(let i=counts.length-1;i>=0;i--){
      const enter=counts[i],d=enter*prob[i],live=enter-d;
      deaths+=d;counts[i]=0;counts[Math.min(i+1,counts.length-1)]+=live;
    }
    return deaths;
  };
  for(let month=1;month<=months;month++){
    const pdD=progressTunnel(ev,ep)+progressTunnel(lv,lp);
    const newProg=pf*tp.prog,fromPfDeath=pf*tp.death;
    pf*=tp.stay;deadPD+=pdD;deadPF+=fromPfDeath;cumProg+=newProg;
    (month<=earlyCut?ev:lv)[0]+=newProg; // new progressions enter after PPS mortality in this cycle
    save(month,newProg,fromPfDeath,pdD);
  }
  return {history,transition:tp,ep,lp};
}
export function kmTable(records,endpoint){
  if(!["PFS","TTP"].includes(endpoint))throw Error("Unknown endpoint");
  const times=[...new Set(records.map(r=>r.time))].sort((a,b)=>a-b);
  let risk=records.length,S=1;const out=[];
  for(const time of times){
    const at=records.filter(r=>r.time===time);
    const event=at.filter(r=>r.type==="progression"||(endpoint==="PFS"&&r.type==="predeath")).length;
    const censored=at.length-event;
    if(risk>0)S*=1-event/risk;
    out.push({time,risk,event,censored,S});
    risk-=at.length;
  }
  return out;
}