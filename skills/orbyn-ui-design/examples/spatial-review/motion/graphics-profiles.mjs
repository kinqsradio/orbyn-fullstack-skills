import {validateScene} from './three.mjs';
import {validateSimulation} from './simulation.mjs';
import {validateOverrides} from './bindings.mjs';

export function graphicsTargets(scene,simulation,lockSha256) {
  validateScene(scene);validateSimulation(simulation);
  if(scene.sourceRevision!==simulation.sourceRevision||!/^[a-f0-9]{64}$/.test(lockSha256))throw Error('Graphics source/profile mismatch');
  const allBodyIds=new Set([...simulation.bodies.map(b=>b.id),...simulation.events.filter(e=>e.op==='add').map(e=>e.body.id)]);
  const starts=new Map(simulation.bodies.map(b=>[b.id,0])),ranges=new Map();
  for(const e of simulation.events){
    if(e.op==='remove'){
      const list=ranges.get(e.id)??[];list.push({start:starts.get(e.id),end:e.tick+1});ranges.set(e.id,list);starts.delete(e.id);
    }else if(e.op==='add')starts.set(e.body.id,e.tick+1);
  }
  for(const[id,start]of starts){const list=ranges.get(id)??[];list.push({start,end:simulation.maxTicks+1});ranges.set(id,list);}
  const targets=scene.parts.map(p=>({id:'part/'+p.id,kind:'part',tickRanges:allBodyIds.has(p.id)?ranges.get(p.id)??[]:[{start:0,end:simulation.maxTicks+1}]}));
  const ball=scene.parts.find(p=>p.id==='ball');
  const bindings=[
    {id:'ball-color',type:'color',default:ball?.material?.color??'#d19b65'},
    {id:'ball-roughness',type:'number',min:0,max:1,step:.01,default:ball?.material?.roughness??.5},
    {id:'ball-metalness',type:'number',min:0,max:1,step:.01,default:ball?.material?.metalness??0},
    {id:'key-light',type:'number',min:0,max:8,step:.1,default:scene.lights.find(l=>l.type==='directional')?.intensity??3}
  ];
  targets.push({id:'profile/graphics-v1',kind:'profile',graphics:{cameraType:scene.camera.type??'perspective',scene:'graphics-study',tickRate:simulation.tickRate,maxTicks:simulation.maxTicks,lockSha256,bindings}});
  return targets;
}
export function validateGraphicsContext(c,manifest) {
  const keys=['profile','modelRevision','partId','camera','animation','parameters','viewport'];
  const profile=manifest.targets.find(t=>t.id==='profile/graphics-v1')?.graphics;
  const part=manifest.targets.find(t=>t.id==='part/'+c?.partId);
  if(!c||Object.keys(c).sort().join()!==keys.sort().join()||c.profile!=='graphics-v1'||manifest.prototype.id!=='graphics-review-v1'||!profile||!part||c.modelRevision!==manifest.assets['motion/graphics-scene.json'])throw Error('Stale graphics source/part');
  const camera=c.camera;
  const cameraFields=['type','position','target','near','far',camera?.type==='orthographic'?'span':'fov'];
  if(!camera||Object.keys(camera).sort().join()!==cameraFields.sort().join()||camera.type!==profile.cameraType||!['perspective','orthographic'].includes(camera.type))throw Error('Invalid graphics camera');
  const bounded=(v,min,max)=>typeof v==='number'&&Number.isFinite(v)&&v>=min&&v<=max;
  if(!bounded(camera.near,.001,100)||!bounded(camera.far,camera.near+.001,1e6)||!(camera.type==='perspective'?bounded(camera.fov,1,150):bounded(camera.span,.01,1e4)))throw Error('Invalid camera projection');
  for(const vector of [camera.position,camera.target])if(!Array.isArray(vector)||vector.length!==3||!vector.every(n=>typeof n==='number'&&Number.isFinite(n)&&Math.abs(n)<=1e5))throw Error('Invalid graphics camera vector');
  if(Math.hypot(...camera.position.map((v,i)=>v-camera.target[i]))<.001)throw Error('Degenerate graphics camera');
  const a=c.animation;
  if(!a||Object.keys(a).sort().join()!=='mode,scene,tick,time'||a.scene!==profile.scene||!['raster','effects','pathtrace','webgpu'].includes(a.mode)||typeof a.time!=='number'||!Number.isFinite(a.time)||a.time<0||a.time>profile.maxTicks/profile.tickRate||!Number.isSafeInteger(a.tick)||a.tick!==Math.floor(a.time*profile.tickRate+1e-8)||!part.tickRanges.some(r=>a.tick>=r.start&&a.tick<r.end))throw Error('Inactive graphics anchor/time');
  validateOverrides(profile.bindings,c.parameters);
  if(!c.viewport||Object.keys(c.viewport).sort().join()!=='height,width'||![c.viewport.width,c.viewport.height].every(v=>Number.isInteger(v)&&v>=160&&v<=8192))throw Error('Invalid graphics viewport');
  return c;
}
