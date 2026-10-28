// Synthetic artifact builder: one model drives live geometry/readout and exported poses.
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
if (!process.env.ILLUSTRATION_PROOF_DIR) throw new Error('Explicit owned output required');
const out = resolve(process.env.ILLUSTRATION_PROOF_DIR);
await mkdir(out, { recursive: true });
const support = join(root, 'skills/technical-illustration/references/upstream/anatomy');
const kit = (await readFile(join(support, 'kit/iso-kit.mjs'), 'utf8')).replace(/^export /gm, '').replace(/<\/script/gi, '<\\/script');
const html = `<!doctype html><meta charset="utf-8"><title>Schematic switch — one model</title><style>body{font:18px system-ui;color:#213047;background:#f5f7fb;margin:0;padding:30px}.iso-plate{max-width:780px;background:white;border:1px solid #bac8db;border-radius:20px;padding:30px}.iso-stage{width:500px;max-width:100%}svg{display:block;width:100%;height:auto}button{font:inherit;padding:10px 16px;margin:8px}p{line-height:1.5}#summary{font-weight:700}.note{color:#5e6e83}</style><div class="iso-plate" tabindex="0"><h1>A switch, from one model</h1><p>Press ↓ to lower the cap; ↑ to release it.</p><div class="iso-stage"><svg class="iso-svg" viewBox="0 0 440 290" role="img" aria-label="Schematic switch"></svg></div><p id="summary" data-readout></p><button id="press">Press</button><button id="release">Release</button><p class="note">An illustrative mechanism. Travel units and contact threshold are schematic, not measured hardware.</p></div><script>${kit}
const P={origin:[220,210],scale:8};
const model=value=>{const travel=Math.max(0,Math.min(6,value));return{travel,closed:travel>=4,capZ:10-travel}};
let state=model(0);
const solid=(shape,color)=>'<path d="'+shape.fill+'" fill="'+color+'" stroke="#263a52" stroke-width="1.1"/>'+shape.shades.map((d,i)=>'<path d="'+d+'" fill="'+['#577799','#6d8aab','#91a6bf','#bac9dc'][i]+'"/>').join('')+'<path d="'+shape.top+'" fill="'+color+'" stroke="#263a52"/>';
window.setState=value=>{state=model(value);const center=iso([0,0,state.capZ],P);const content='<g data-piece="base">'+solid(slabOf({x:-10,y:-8,w:20,d:16,r:1},0,2,P),'#c6d3e4')+'</g><g data-piece="shaft">'+solid(cylinder(0,0,2,2,Math.max(1,state.capZ-3),P),'#9caec6')+'</g><g data-piece="cap">'+solid(cylinder(0,0,5,state.capZ-1,1,P),'#7296c4')+'<circle data-cap-top cx="'+center[0]+'" cy="'+center[1]+'" r="3" fill="#fff"/></g><circle data-contact cx="350" cy="240" r="12" fill="'+(state.closed?'#2c805e':'#b0803e')+'"/>';document.querySelector('svg').innerHTML=content;document.querySelector('[data-readout]').textContent=state.travel+' units — '+(state.closed?'closed':'open');document.querySelector('svg').setAttribute('aria-label',state.travel+' schematic travel units, '+(state.closed?'closed':'open'));window.currentFrame={...state,center};};
document.querySelector('#press').onclick=()=>setState(state.travel+1);document.querySelector('#release').onclick=()=>setState(state.travel-1);document.querySelector('.iso-plate').onkeydown=e=>{if(e.key==='ArrowDown'){e.preventDefault();setState(state.travel+1)}if(e.key==='ArrowUp'){e.preventDefault();setState(state.travel-1)}};setState(0);
</script>`;
await writeFile(join(out, 'figure.html'), html);
const spec = {
  page: 'figure.html', out: 'switch', settle: 0,
  views: { rest: {}, pressed: { actions: [['eval', 'window.setState(6)']], reset: [['eval', 'window.setState(0)']] } },
  name: 'Schematic switch', title: 'One model drives every view', number: 'ORB-001', tagline: 'A finite illustration fixture',
  question: 'When does the contact close?', lead: 'A single travel value positions the cap, determines the contact state and supplies the live readout. The same built page supplies both print views.', quote: 'Draw and describe the same state',
  numbers: [['0–6','units','schematic travel'],['4','units','contact threshold']], spec: [['Model','Clamped integer travel'],['Scope','Schematic explanation, not measured physics']],
  why: { title: 'Why one model?', text: 'Independent decorative readouts can contradict the visible mechanism. Here geometry, phase and text use the same sample.' },
  parts: [{ id: 'base', name: 'Base', say: 'A fixed reference.', select: '[data-piece="base"]' }, { id: 'shaft', name: 'Shaft', say: 'Follows the cap.', select: '[data-piece="shaft"]' }, { id: 'cap', name: 'Cap', say: 'Its top marker follows the projected travel.', select: '[data-piece="cap"]' }],
  main: { view: 'pressed' }, inset: { view: 'rest', label: 'Released' },
  steps: [{ view: 'rest', title: 'Released', text: 'Zero travel, open contact.', focus: ['cap'] }, { view: 'pressed', title: 'Pressed', text: 'Six units, closed contact.', focus: ['cap','shaft'] }],
  details: [{ view: 'pressed', title: 'Projected cap', text: 'The marker and part share one camera and sample.', around: ['cap'], focus: ['cap'] }],
};
await writeFile(join(out, 'sheet.mjs'), 'export default '+JSON.stringify(spec,null,2)+';\n');
console.log(JSON.stringify({ status: 'built synthetic model-driven fixture', directory: out }));
