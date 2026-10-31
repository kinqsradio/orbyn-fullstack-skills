import {validateBindings,bindingValues,validateOverrides,boundClip} from './bindings.mjs';
import {rate, frameTime} from './time.mjs';
import {sampleTracks} from './tracks.mjs';

const plain = v => v && typeof v==='object' && !Array.isArray(v) && Object.getPrototypeOf(v)===Object.prototype;
const id = v => typeof v==='string' && /^[a-z][a-z0-9-]{0,79}$/.test(v);
const finite = v => typeof v==='number' && Number.isFinite(v) && Math.abs(v)<=1e7;
const integer = (v,min=0) => Number.isSafeInteger(v) && v>=min;

export function inert(value,depth=0) {
  if(depth>16)throw Error('Parameter depth');
  if(value===null||typeof value==='boolean')return;
  if(typeof value==='number'&&Number.isFinite(value)&&Math.abs(value)<=1e9)return;
  if(typeof value==='string'&&value.length<=10000)return;
  if(Array.isArray(value)&&value.length<=1000){value.forEach(v=>inert(v,depth+1));return;}
  if(plain(value)&&Object.keys(value).length<=100){
    for(const [k,v]of Object.entries(value)){
      if(['__proto__','constructor','prototype'].includes(k))throw Error('Unsafe key');
      inert(v,depth+1);
    }
    return;
  }
  throw Error('Inert bounded data required');
}

function matrix(t) {
  const r=(t.rotate??0)*Math.PI/180,c=Math.cos(r),s=Math.sin(r),sx=t.scaleX??1,sy=t.scaleY??1;
  return[c*sx,s*sx,-s*sy,c*sy,t.x??0,t.y??0];
}
function multiply(a,b) {
  return[a[0]*b[0]+a[2]*b[1],a[1]*b[0]+a[3]*b[1],
    a[0]*b[2]+a[2]*b[3],a[1]*b[2]+a[3]*b[3],
    a[0]*b[4]+a[2]*b[5]+a[4],a[1]*b[4]+a[3]*b[5]+a[5]];
}

export function validateComposition(spec) {
  const projectKeys=['version','fps','durationFrames','sourceRevision','clips','title','bindings'];
  if(!plain(spec)||Object.keys(spec).some(k=>!projectKeys.includes(k))||spec.version!==2||
      !integer(spec.durationFrames,1)||spec.durationFrames>100000||
      typeof spec.sourceRevision!=='string'||!spec.sourceRevision.trim()||spec.sourceRevision.length>200||
      !Array.isArray(spec.clips)||spec.clips.length>500)throw Error('Invalid composition schema/budget');
  if(spec.title!==undefined&&(typeof spec.title!=='string'||!spec.title.trim()||spec.title.length>200))throw Error('Invalid composition title');
  rate(spec.fps);
  const ids=new Map();
  const clipKeys=['id','component','start','duration','offset','rate','parent','props','transform','opacity','zIndex','tracks'];
  for(const c of spec.clips){
    if(!plain(c)||Object.keys(c).some(k=>!clipKeys.includes(k))||!id(c.id)||!id(c.component)||ids.has(c.id)||
        !integer(c.start)||!integer(c.duration,1)||c.start+c.duration>100000||
        !finite(c.offset??0)||!finite(c.rate??1)||(c.rate??1)<.001||(c.rate??1)>1000||
        !integer(c.zIndex??0,-10000)||Math.abs(c.zIndex??0)>10000||
        !finite(c.opacity??1)||(c.opacity??1)<0||(c.opacity??1)>1)throw Error('Invalid clip');
    inert(c.props??{});
    if(!plain(c.props??{}))throw Error('Props object');
    const t=c.transform??{};
    if(!plain(t)||Object.entries(t).some(([k,v])=>!['x','y','rotate','scaleX','scaleY'].includes(k)||!finite(v)))throw Error('Invalid transform');
    if(!Array.isArray(c.tracks??[])||(c.tracks??[]).length>100)throw Error('Track budget');
    const writes=sampleTracks(c.tracks??[],0);
    if(Object.hasOwn(writes,'position')&&(Object.hasOwn(writes,'transform.x')||Object.hasOwn(writes,'transform.y')))throw Error('Competing position writers');
    for(const [k,v]of Object.entries(writes)){
      if(!['opacity','position','transform.x','transform.y','transform.rotate','transform.scaleX','transform.scaleY'].includes(k)&&!k.startsWith('props.'))throw Error('Unsupported property binding');
      if(k==='position'&&(!Array.isArray(v)||v.length!==2))throw Error('Position needs path');
      if(k!=='position'&&typeof v!=='number')throw Error('Scalar binding required');
    }
    ids.set(c.id,c);
  }
  for(const c of spec.clips){
    const seen=new Set([c.id]);let node=c;
    while(node.parent!==undefined){
      if(!ids.has(node.parent)||seen.has(node.parent))throw Error('Missing/cyclic parent');
      seen.add(node.parent);node=ids.get(node.parent);
    }
    if(!c.parent&&c.start+c.duration>spec.durationFrames)throw Error('Clip outside composition');
  }
  validateBindings(spec);
  return spec;
}

export function sampleComposition(spec,frame,{reducedMotion=false,sourceRevision=spec.sourceRevision,parameters=undefined}={}) {
  validateComposition(spec);
  if(typeof reducedMotion!=='boolean')throw Error('Invalid reduced-motion preference');
  if(!integer(frame)||frame>spec.durationFrames||sourceRevision!==spec.sourceRevision)throw Error('Frame/source mismatch');
  const bindings=validateBindings(spec),values=validateOverrides(bindings,parameters??bindingValues(spec));
  const clips=spec.clips.map(c=>boundClip(c,bindings,values));
  const at=Math.min(frame,spec.durationFrames-1);
  const by=new Map(clips.map(c=>[c.id,c])),cache=new Map(),fps=rate(spec.fps);
  function sample(c) {
    if(cache.has(c.id))return cache.get(c.id);
    const parent=c.parent?sample(by.get(c.parent)):null;
    if(c.parent&&!parent){cache.set(c.id,null);return null;}
    const parentFrame=parent?parent.localFrame:at;
    if(parentFrame<c.start||parentFrame>=c.start+c.duration){cache.set(c.id,null);return null;}
    const localFrame=(parentFrame-c.start)*(c.rate??1)+(c.offset??0);
    const localTime=localFrame*fps.denominator/fps.numerator;
    const transform={...(c.transform??{})},props=structuredClone(c.props??{});
    let opacity=c.opacity??1;
    for(const[k,v]of Object.entries(sampleTracks(c.tracks??[],localTime,{reducedMotion}))){
      if(k==='opacity')opacity=Math.max(0,Math.min(1,v));
      else if(k==='position'){transform.x=v[0];transform.y=v[1];}
      else if(k.startsWith('transform.'))transform[k.slice(10)]=v;
      else props[k.slice(6)]=v;
    }
    const localMatrix=matrix(transform);
    const worldMatrix=parent?multiply(parent.worldMatrix,localMatrix):localMatrix;
    if(worldMatrix.some(v=>!finite(v)))throw Error('World transform budget');
    const state={reducedMotion,id:c.id,component:c.component,localFrame,localTime,props,transform,worldMatrix,
      opacity:opacity*(parent?.opacity??1),zIndex:(c.zIndex??0)+(parent?.zIndex??0),parent:c.parent??null};
    cache.set(c.id,state);return state;
  }
  return{frame:at,time:frameTime(at,spec.fps),terminal:frame===spec.durationFrames,sourceRevision:spec.sourceRevision,
    active:clips.map(sample).filter(Boolean).sort((a,b)=>a.zIndex-b.zIndex||a.id.localeCompare(b.id))};
}
