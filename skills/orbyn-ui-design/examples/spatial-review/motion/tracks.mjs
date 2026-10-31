// Pure sampled tracks; no ticking, callbacks, eval, DOM reads or random globals.
export const easings=Object.freeze({linear:t=>t,smooth:t=>t*t*(3-2*t),in:t=>t*t,out:t=>1-(1-t)**2});
const num=(n)=>{if(typeof n!=='number'||!Number.isFinite(n)||Math.abs(n)>1e9)throw Error('Invalid track number');return n;};
export function validateTrack(track) {
  if(!track||!['keyframes','spring','path'].includes(track.kind)||!/^([a-z][a-zA-Z0-9]*)(\.[a-z][a-zA-Z0-9]*)?$/.test(track.property)||['__proto__','prototype','constructor'].some(k=>track.property.split('.').includes(k)))throw Error('Invalid track/property');
  if(Object.keys(track).some(k=>!['kind','property','keys','easing','from','to','mass','stiffness','damping','velocity','start','points','duration','priority','blend'].includes(k)))throw Error('Unknown track field');
  if(track.blend!==undefined&&!['replace','add'].includes(track.blend))throw Error('Unsupported blend');
  if(track.priority!==undefined&&!Number.isSafeInteger(track.priority))throw Error('Invalid priority');
  if(track.easing!==undefined&&!Object.hasOwn(easings,track.easing))throw Error('Unknown easing');
  if(track.kind==='keyframes') {if(!Array.isArray(track.keys)||track.keys.length<2||track.keys.length>1000)throw Error('Keyframe budget');let last=-Infinity;for(const k of track.keys){if(!k||Object.keys(k).sort().join()!=='time,value'||num(k.time)<0||k.time<=last)throw Error('Key order');num(k.value);last=k.time;}}
  if(track.kind==='spring'){num(track.from);num(track.to);for(const k of ['mass','stiffness','damping'])if(num(track[k])<.0001||track[k]>1e6)throw Error('Positive spring parameters');num(track.velocity??0);if(num(track.start??0)<0)throw Error('Spring start');}
  if(track.kind==='path'){if(!Array.isArray(track.points)||track.points.length<2||track.points.length>1000||num(track.duration)<=0)throw Error('Path budget');for(const p of track.points){if(!Array.isArray(p)||p.length!==2)throw Error('Path point');p.forEach(num);}}
  return track;
}
export function spring(track,time) {
  const x0=track.from-track.to,v=track.velocity??0,w=Math.sqrt(track.stiffness/track.mass),z=track.damping/(2*Math.sqrt(track.stiffness*track.mass));
  const t=Math.max(0,time-(track.start??0));
  if(z<1){const wd=w*Math.sqrt(1-z*z);return track.to+Math.exp(-z*w*t)*(x0*Math.cos(wd*t)+(v+z*w*x0)/wd*Math.sin(wd*t));}
  if(Math.abs(z-1)<1e-9)return track.to+Math.exp(-w*t)*(x0+(v+w*x0)*t);
  const root=Math.sqrt(z*z-1),r1=-w*(z-root),r2=-w*(z+root),a=(v-r2*x0)/(r1-r2);return track.to+a*Math.exp(r1*t)+(x0-a)*Math.exp(r2*t);
}
export function sampleTrack(track,time,{reducedMotion=false}={}) {
  validateTrack(track);num(time);const ease=easings[track.easing??'linear'];
  if(track.kind==='spring')return reducedMotion?track.to:(time<(track.start??0)?track.from:spring(track,time));
  if(track.kind==='keyframes'){const keys=track.keys;if(reducedMotion||time>=keys.at(-1).time)return keys.at(-1).value;if(time<=keys[0].time)return keys[0].value;const i=keys.findIndex(k=>k.time>time),a=keys[i-1],b=keys[i];return a.value+(b.value-a.value)*ease((time-a.time)/(b.time-a.time));}
  const p=track.points, lengths=p.slice(1).map((b,i)=>Math.hypot(b[0]-p[i][0],b[1]-p[i][1])), total=lengths.reduce((a,b)=>a+b,0);let d=(reducedMotion?1:ease(Math.max(0,Math.min(1,time/track.duration))))*total;
  for(let i=0;i<lengths.length;i++){if(d<=lengths[i]||i===lengths.length-1){const t=lengths[i]?d/lengths[i]:0;return [p[i][0]+(p[i+1][0]-p[i][0])*t,p[i][1]+(p[i+1][1]-p[i][1])*t];}d-=lengths[i];}return [...p.at(-1)];
}
export function stagger(count,interval,{start=0,from='first'}={}) {if(!Number.isSafeInteger(count)||count<1||count>10000||num(interval)<0||num(start)<0||!['first','last','center'].includes(from))throw Error('Invalid stagger');return Array.from({length:count},(_,i)=>start+(from==='last'?count-1-i:from==='center'?Math.abs(i-(count-1)/2):i)*interval);}
export function resolveLabels(value,labels={}) {if(typeof value==='number')return num(value);if(typeof value!=='string')throw Error('Invalid label');const m=/^([a-z][a-z0-9-]*)(?:([+-])(\d+(?:\.\d+)?))?$/.exec(value);if(!m||!Object.hasOwn(labels,m[1]))throw Error('Unknown label');return num(labels[m[1]])+(m[2]==='-'?-1:1)*Number(m[3]??0);}
export function sampleTracks(tracks,time,options={}) {
  const by=new Map();for(const track of tracks){validateTrack(track);const list=by.get(track.property)??[];list.push(track);by.set(track.property,list);}
  const values={};for(const [property,list]of by){const replacements=list.filter(t=>(t.blend??'replace')==='replace').sort((a,b)=>(b.priority??0)-(a.priority??0));if(replacements.length>1&&(replacements[0].priority??0)===(replacements[1].priority??0))throw Error('Competing property writers');let value=replacements.length?sampleTrack(replacements[0],time,options):0;for(const t of list.filter(t=>t.blend==='add')){const add=sampleTrack(t,time,options);if(typeof value!=='number'||typeof add!=='number')throw Error('Additive tracks require scalar');value+=add;}values[property]=value;}return values;
}
