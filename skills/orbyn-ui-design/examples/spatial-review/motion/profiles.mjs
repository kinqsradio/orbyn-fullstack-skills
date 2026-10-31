import {validateBindings,validateOverrides} from './bindings.mjs';
import {validateComposition} from './composition.mjs';

// New profile data lives in fingerprinted targets; never trust unhashed extensions.
export function validateMotionContext(c, manifest) {
  const motion = manifest.targets.find(t => t.kind === 'profile')?.motion;
  if (!motion) throw Error('Missing sealed motion profile');
  const fields = ['profile', 'modelRevision', 'partId', 'camera', 'animation', 'layers', 'viewport', 'parameters'];
  const part = manifest.targets.find(t => t.id === 'part/' + c?.partId);
  if (!c || Object.keys(c).sort().join() !== fields.sort().join() ||
      c.profile !== 'motion-v1' || manifest.prototype.id !== 'motion-composition-v1' ||
      c.modelRevision !== manifest.assets['motion-project.json'] || !part) throw Error('Stale motion profile/anchor');
  if (!c.camera || Object.keys(c.camera).sort().join() !== 'x,y,zoom' ||
      ![c.camera.x,c.camera.y,c.camera.zoom].every(Number.isFinite) ||
      Math.abs(c.camera.x)>10000 || Math.abs(c.camera.y)>10000 || c.camera.zoom<.1 || c.camera.zoom>10) throw Error('Invalid motion camera');
  const a = c.animation;
  if (!a || Object.keys(a).sort().join() !== 'frame,rate,scene,time' ||
      !Number.isSafeInteger(a.frame) || a.frame<0 || a.frame>=motion.durationFrames ||
      !motion.scenes.includes(a.scene) || ![.25,.5,1,2].includes(a.rate) ||
      !Number.isFinite(a.time) || Math.abs(a.time-a.frame*motion.fps.denominator/motion.fps.numerator)>1e-8) throw Error('Invalid motion frame');
  const scene = motion.anchors.find(s => s.id === a.scene);
  if (!scene || a.frame<scene.start || a.frame>=scene.end || !scene.parts.includes(c.partId) ||
      a.frame<part.motionRange.start || a.frame>=part.motionRange.end) throw Error('Unmapped motion anchor');
  validateOverrides(motion.bindings??[],c.parameters);
  if (!c.layers || Object.keys(c.layers).sort().join() !== 'guides,reducedMotion' || typeof c.layers.guides !== 'boolean' || typeof c.layers.reducedMotion !== 'boolean') throw Error('Invalid motion layers');
  if (!c.viewport || Object.keys(c.viewport).sort().join() !== 'height,width' ||
      ![c.viewport.width,c.viewport.height].every(v=>Number.isInteger(v)&&v>=160&&v<=8192)) throw Error('Invalid viewport');
  return c;
}

export function motionManifest(project, assets, prototype) {
  validateComposition(project);
  const by = new Map(project.clips.map(c=>[c.id,c])), spans = new Map();
  function span(c) {
    if (spans.has(c.id)) return spans.get(c.id);
    const parent = c.parent ? span(by.get(c.parent)) : {a:1,b:0,start:0,end:project.durationFrames,root:c.id};
    const start = Math.max(parent.start,(c.start-parent.b)/parent.a);
    const end = Math.min(parent.end,(c.start+c.duration-parent.b)/parent.a);
    const result = {start,end,a:parent.a*(c.rate??1),b:(parent.b-c.start)*(c.rate??1)+(c.offset??0),root:parent.root};
    spans.set(c.id,result); return result;
  }
  const targets = project.clips.map(c => {
    const range=span(c);
    return {id:'part/'+c.id,kind:'part',motionRange:{start:Math.ceil(range.start),end:Math.ceil(range.end)}};
  });
  const anchors = project.clips.filter(c=>!c.parent).map(c=>({id:c.id,start:span(c).start,end:span(c).end,parts:project.clips.filter(p=>span(p).root===c.id).map(p=>p.id)}));
  targets.push({id:'profile/motion-v1',kind:'profile',motion:{bindings:validateBindings(project),durationFrames:project.durationFrames,fps:project.fps,scenes:anchors.map(c=>c.id),anchors}});
  return {prototype:{...prototype,id:'motion-composition-v1'},assets,targets};
}
