// Source-declared editable fields. Saved values cannot introduce paths or code.
const safeId=v=>typeof v==='string'&&/^[a-z][a-z0-9-]{0,79}$/.test(v);
export function validateBindings(project) {
  const bindings=project.bindings??[], ids=new Set(),writers=new Set();
  if(!Array.isArray(bindings)||bindings.length>32)throw Error('Binding budget');
  for(const b of bindings){
    const fields=['id','clip','property','label','type','default',...(b.type==='number'?['min','max','step']:b.type==='enum'?['options']:[])];
    if(!b||Object.keys(b).sort().join()!==fields.sort().join()||!safeId(b.id)||ids.has(b.id)||
        typeof b.label!=='string'||!b.label.trim()||b.label.length>80||!project.clips.some(c=>c.id===b.clip)||
        !/^(props\.[a-z][a-zA-Z0-9]*|transform\.(x|y|rotate|scaleX|scaleY)|rate)$/.test(b.property)||
        ['constructor','prototype','__proto__'].includes(b.property.split('.').at(-1)))throw Error('Invalid binding');
    const writer=b.clip+'/'+b.property;
    if(writers.has(writer))throw Error('Duplicate binding writer');
    writers.add(writer);ids.add(b.id);
    if(!['number','color','enum'].includes(b.type))throw Error('Unsupported binding type');
    if(b.type==='number'&&(![b.min,b.max,b.step].every(v=>Number.isFinite(v)&&Math.abs(v)<=1e7)||b.min>=b.max||b.step<=0||b.max-b.min>1e7))throw Error('Invalid numeric binding');
    if(b.type==='enum'&&(!Array.isArray(b.options)||b.options.length<1||b.options.length>20||new Set(b.options).size!==b.options.length||b.options.some(v=>typeof v!=='string'||!v.trim()||v.length>80)))throw Error('Invalid enum binding');
    if(!b.property.startsWith('props.')&&b.type!=='number')throw Error('Transform/time binding must be numeric');
    if(b.property==='rate'&&(b.min<.001||b.max>1000||project.clips.some(c=>c.parent===b.clip)))throw Error('Rate binding requires a leaf and bounded range');
    const clip=project.clips.find(c=>c.id===b.clip);
    const properties=(clip.tracks??[]).map(t=>t.property);
    if(properties.includes(b.property)||b.property.startsWith('transform.')&&['transform.x','transform.y'].includes(b.property)&&properties.includes('position'))throw Error('Binding competes with track writer');
    validateValue(b,b.default);
  }
  return bindings;
}
export function validateValue(binding,value) {
  if(binding.type==='number'){
    if(typeof value!=='number'||!Number.isFinite(value)||value<binding.min||value>binding.max||
        Math.abs((value-binding.min)/binding.step-Math.round((value-binding.min)/binding.step))>1e-6)throw Error('Numeric binding range/step');
  }else if(binding.type==='color'){
    if(typeof value!=='string'||!/^#[0-9a-f]{6}$/i.test(value))throw Error('Invalid color binding');
  }else if(binding.type==='enum'){
    if(!binding.options.includes(value))throw Error('Invalid enum binding');
  }else throw Error('Unknown binding type');
  return value;
}
export function bindingValues(project) {return Object.fromEntries(validateBindings(project).map(b=>[b.id,b.default]));}
export function validateOverrides(bindings,values) {
  if(!values||typeof values!=='object'||Array.isArray(values)||Object.keys(values).sort().join()!==bindings.map(b=>b.id).sort().join())throw Error('Unknown/missing parameter binding');
  for(const b of bindings)validateValue(b,values[b.id]);
  return values;
}
export function boundClip(clip,bindings,values) {
  const result={...clip,props:{...(clip.props??{})},transform:{...(clip.transform??{})}};
  for(const b of bindings.filter(b=>b.clip===clip.id)){
    if(b.property==='rate')result.rate=values[b.id];
    else{const[owner,key]=b.property.split('.');result[owner][key]=values[b.id];}
  }
  return result;
}
