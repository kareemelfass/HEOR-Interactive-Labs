import assert from "node:assert/strict";
import {constantTransitions,competingIncidence,intervalFromCurves,psm,tunnelProbabilities,runCohort} from "./model-core.mjs";
const close=(a,b,eps=1e-10)=>assert.ok(Math.abs(a-b)<=eps,"Expected "+a+" approximately "+b);
let tests=0;
const test=(name,fn)=>{fn();tests++;console.log("PASS "+name);};
test("Exact competing first-exit row and expected counts",()=>{
 const x=constantTransitions(.08,.04,1);
 close(x.stay+x.prog+x.death,1);close(x.stay,Math.exp(-.12));
 close(x.prog,2*(1-Math.exp(-.12))/3);close(x.death,(1-Math.exp(-.12))/3);
});
test("First-exit CIF partitions cohort at month 12",()=>{
 const x=competingIncidence(.08,.04,12);close(x.pf+x.progressed+x.preDeath,1);
 close(x.preDeath,(1-Math.exp(-1.44))/3);
 assert.ok(Math.abs(x.preDeath-x.naiveDeathGap)>.10);
});
test("Hazard subtraction from six-month fitted curves",()=>{
 const x=intervalFromCurves(1,.5,1,.7,6);
 close(x.H_death,-Math.log(.5)+Math.log(.7));
 close(x.h_death,(-Math.log(.5)+Math.log(.7))/6);
 close(x.stay+x.prog+x.death,1);
});
test("Reject negative implied PF death hazards",()=>assert.throws(()=>intervalFromCurves(1,.8,1,.6,1),/Negative/));
test("Reject an increasing fitted survival interval",()=>assert.throws(()=>intervalFromCurves(.5,.6,1,.9,1),/increase/));
test("PPS conditional mortality from survival ratios",()=>{
 const q=tunnelProbabilities([1,.9,.72,.648]);
 close(q[0],.1);close(q[1],.2);close(q[2],.1);
});
test("Reject increasing PPS",()=>assert.throws(()=>tunnelProbabilities([1,.7,.9]),/increase/));
test("PSM occupancy identity",()=>assert.deepEqual(psm(.5,.75),{pf:.5,pd:.25,death:.25}));
test("Reject incompatible PSM curves",()=>assert.throws(()=>psm(.75,.5),/requires/));
test("Zero PF hazards preserve everybody in PF",()=>{
 const x=runCohort({N:100,months:12,hProg:0,hPfDeath:0});
 close(x.history.at(-1).pf,100);close(x.history.at(-1).dead,0);
});
test("No progression means no PD, no post-PD deaths",()=>{
 const x=runCohort({N:100,months:12,hProg:0,hPfDeath:.04});
 for(const row of x.history){close(row.pd,0);close(row.deadPD,0);}
 close(x.history.at(-1).pf,100*Math.exp(-.48));
});
test("History-specific PPS differentiates equal-duration cohorts",()=>{
 const x=runCohort({N:1000,months:12,hProg:.08,hPfDeath:.04,
   earlyCut:6,earlyPPS:[1,.70,.56,.476],latePPS:[1,.90,.855,.81225]});
 close(x.ep[0],.30);close(x.lp[0],.10);
 assert.ok(x.history.at(-1).early>0&&x.history.at(-1).late>0);
});
test("Cohort mass, absorbing death and monotone PF",()=>{
 const x=runCohort({N:1000,months:48});
 x.history.forEach((row,i)=>{
  close(row.total,1000,1e-7);
  assert.ok([row.pf,row.pd,row.dead,row.deadPF,row.deadPD].every(y=>y>=-1e-9));
  if(i){assert.ok(row.dead>=x.history[i-1].dead-1e-9);assert.ok(row.pf<=x.history[i-1].pf+1e-9);}
 });
});
test("End-of-cycle progression has zero post-PD deaths in cycle one",()=>{
 const x=runCohort({N:1000,months:2});close(x.history[1].deadPD,0);
 assert.ok(x.history[1].newProg>0);assert.ok(x.history[2].postDeath>0);
});
console.log(tests+" regression tests passed.");
