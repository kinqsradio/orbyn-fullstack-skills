// Original source-authoring example: compatible paths, explicit Lottie subset,
// and a mathematical plot all use the same deterministic composition clock.
import {vectorComponent,plotPath} from './vector.mjs';
import {lottieComponent,toLottie} from './lottie.mjs';
const move=(x,y)=>({op:'M',values:[x,y]});
const curve=(...values)=>({op:'C',values});
const close=()=>({op:'Z',values:[]});
const heart={version:1,width:1080,height:608,shapes:[{id:'heart-contour',fill:'#bc4d64',stroke:'#ffe5df',strokeWidth:3,
 from:[move(260,210),curve(130,90,80,260,260,370),curve(440,260,390,90,260,210),close()],
 to:[move(260,170),curve(100,30,40,260,260,420),curve(480,260,420,30,260,170),close()]}]};
const lottie=toLottie(heart,{durationFrames:121,title:'Original code-authored heart contour'});
const wave={version:1,width:1080,height:608,shapes:[{id:'sine-plot',from:plotPath(Math.sin,{from:0,to:Math.PI*4,samples:160,x:140,y:470,scaleX:64,scaleY:-30}),fill:'none',stroke:'#9bcec5',strokeWidth:3,trim:true}]};
export const project={version:2,title:'Contours and equations — original code study',sourceRevision:'orbyn-vector-study-v1',fps:{numerator:30,denominator:1},durationFrames:121,
 clips:[{id:'authored-heart',component:'vector-figure',start:0,duration:121,props:{vector:heart,duration:4,alt:'A code-authored heart contour expands over four seconds'}},
 {id:'lottie-heart',component:'lottie-figure',start:0,duration:121,transform:{x:500},props:{data:lottie}},
 {id:'mathematical-wave',component:'vector-figure',start:0,duration:121,props:{vector:wave,duration:4,alt:'Two sine periods are progressively drawn from a trusted JavaScript function'}}]};
export function registerCustomComponents(registry){return registry.register('vector-figure',vectorComponent()).register('lottie-figure',lottieComponent());}
