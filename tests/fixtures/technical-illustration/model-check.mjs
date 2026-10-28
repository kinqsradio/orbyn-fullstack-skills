import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { readFile, writeFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';
const repository=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const dir=resolve(process.env.ILLUSTRATION_PROOF_DIR ?? '');
assert.ok(process.env.ILLUSTRATION_PROOF_DIR && process.env.CHROME_PATH);
const page=join(dir,'figure.html');
const driver=join(repository,'skills/technical-illustration/references/upstream/anatomy/scripts/drive.mjs');
const oracle=v=>`(()=>{const expectedY=210-(10-${v})*Math.cos(Math.PI/6)*8*Math.sqrt(1.6);const marker=document.querySelector('[data-cap-top]');if(Math.abs(Number(marker.getAttribute('cy'))-expectedY)>1e-6)throw new Error('projected marker/model mismatch');const expected=${JSON.stringify(v+' units — '+(v>=4?'closed':'open'))};if(document.querySelector('[data-readout]').textContent!==expected)throw new Error('readout/model mismatch');if(document.querySelector('svg').getAttribute('aria-label')!==${JSON.stringify(v+' schematic travel units, '+(v>=4?'closed':'open'))})throw new Error('accessible state mismatch');return{travel:${v},markerY:Number(marker.getAttribute('cy')),expectedY,readout:expected}})()`;
const actions=[];
for(const v of [0,2,4,6])actions.push(['eval',`window.setState(${v});true`],['eval',oracle(v)]);
actions.push(['eval','window.setState(0);true'],['key','ArrowDown','.iso-plate'],['eval',oracle(1)],['shot',join(dir,'model-active.png'),'.iso-plate']);
const run=async(name,list)=>{
 const argv=[driver,page,JSON.stringify(list)];
 const r=await promisify(execFile)(process.execPath,argv,{timeout:35000}).then(x=>({code:0,...x}),e=>({code:e.code,stdout:e.stdout,stderr:e.stderr}));
 await writeFile(join(dir,name+'.json'),JSON.stringify({argv,...r},null,2));return r;
};
const valid=await run('model-positive',actions);assert.equal(valid.code,0,valid.stderr);
for(const [name,damage,pattern]of[['wrong-readout',`document.querySelector('[data-readout]').textContent='99 units — open'`,/readout\/model mismatch/],['wrong-marker',`document.querySelector('[data-cap-top]').setAttribute('cy','0')`,/projected marker\/model mismatch/]]){
 const r=await run(name,[['eval','window.setState(0);true'],['eval',damage],['eval',oracle(0)]]);assert.equal(r.code,1);assert.match(r.stderr,pattern);
}
console.log(JSON.stringify({status:'passed finite actual model/readout/projected marker/native key and two planted-mismatch controls',scope:'Five sampled states, instantaneous user stepping; not full shape collision/continuous takeover/reversal evidence'}));
