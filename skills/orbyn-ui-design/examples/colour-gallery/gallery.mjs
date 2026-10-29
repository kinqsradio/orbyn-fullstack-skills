// Original reference gallery; the source screenshots and their layout are not included.
export const thresholds = { normal: 4.5, large: 3, nontext: 3, 'focus-adjacency': 3 };
export function parseHex(value) {
  if (typeof value !== 'string' || !/^#[0-9a-f]{6}$/i.test(value)) throw new Error('Use an exact #RRGGBB value. Unknown labels, gradients and other CSS forms remain unverified.');
  return [1, 3, 5].map(i => parseInt(value.slice(i, i+2), 16) / 255);
}
const lum = rgb => rgb.map(c => c <= .04045 ? c/12.92 : ((c+.055)/1.055)**2.4).reduce((total,c,i) => total+c*[.2126,.7152,.0722][i],0);
export function ratio(foreground, background, alpha=1) {
  if (!Number.isFinite(alpha) || alpha<0 || alpha>1) throw new Error('Alpha must be finite in 0..1.');
  const f=parseHex(foreground), b=parseHex(background), l1=lum(f.map((c,i)=>c*alpha+b[i]*(1-alpha))), l2=lum(b);
  return (Math.max(l1,l2)+.05)/(Math.min(l1,l2)+.05);
}
export function qualifies(value, kind) {
  if (!Object.hasOwn(thresholds,kind) || !Number.isFinite(value) || value<1 || value>21.00000000001) throw new Error('Invalid criterion or ratio.');
  return value>=thresholds[kind];
}
export const checks = [
 ['Body / page','text','page','normal'], ['Body / surface','text','surface','normal'],
 ['Secondary / page','muted','page','normal'], ['Secondary / surface','muted','surface','normal'],
 ['Action label / fill','onAccent','accent','normal'], ['Action label / hover','onAccent','hoverAccent','normal'],
 ['Input boundary / surface','border','surface','nontext'], ['Focus ring / page','focus','page','focus-adjacency'],
 ['Focus ring / surface','focus','surface','focus-adjacency'], ['Success text / surface','success','surface','normal'],
 ['Error text / surface','error','surface','normal'], ['Selected marker / surface','accent','surface','nontext'],
];
const text = (tag, value, cls) => { const node=document.createElement(tag);node.textContent=value;if(cls)node.className=cls;return node; };
function start() {
 const catalog=JSON.parse(document.querySelector('#catalog').textContent);
 const selector=document.querySelector('#palettes');let selected=catalog.palettes[0];
 const isSeed=(palette,value)=>palette.swatches.includes(value);
 function theme(palette,mode) {
  const role=palette.role_proposals[mode],section=document.createElement('section');section.className='theme';section.dataset.mode=mode;
  for(const [name,value]of Object.entries(role))section.style.setProperty('--'+name,value);
  section.innerHTML=`<header><p class="mode"></p><h3>Ready for review.</h3><p class="secondary">One proposal, two surfaces. This changes only the local illustration.</p></header>
   <form class="panel" novalidate><div class="panel-heading"><h4>Release review</h4><span class="selected-marker">✓ Selected</span></div>
   <label>Project title<input name="title" value="Release review" required placeholder="Enter a project title"></label>
   <p class="help secondary">Use a name your teammates can recognize.</p><div class="actions"><button class="primary" type="submit">Save preview</button><button class="secondary-button" type="button" disabled>Export unavailable</button></div>
   <p class="feedback" aria-live="polite">✓ Ready — no changes saved.</p><p class="error-example">⚠ Error example — permissions need review.</p></form>
   <details class="roles"><summary>Semantic roles & origins</summary><dl></dl></details>
   <details class="audit"><summary>Computed role-pair checks</summary><div class="table-scroll"><table><caption>Solid sRGB numeric checks; not full accessibility compliance</caption><thead><tr><th>Pair / criterion</th><th>Ratio</th><th>Target</th><th>Result</th></tr></thead><tbody></tbody></table></div></details>`;
  section.querySelector('.mode').textContent=mode==='light'?'Light proposal':'Dark proposal';
  const form=section.querySelector('form'),input=form.elements.title,feedback=section.querySelector('.feedback');
  input.id=`title-${mode}`;feedback.id=`feedback-${mode}`;input.setAttribute('aria-describedby',feedback.id);
  form.addEventListener('submit',event=>{event.preventDefault();const valid=Boolean(input.value.trim());input.setAttribute('aria-invalid',String(!valid));feedback.classList.toggle('has-error',!valid);feedback.textContent=valid?'✓ Save simulated — preview only.':'⚠ Error — enter a project title before saving.';if(!valid)input.focus();});
  const dl=section.querySelector('dl');
  for(const [name,value]of Object.entries(role)){
   dl.append(text('dt',name));dl.append(text('dd',`${value} · ${isSeed(palette,value)?'reference swatch':catalog.added_colours[value]??'UNDECLARED — review required'}`));
  }
  for(const [label,fg,bg,kind]of checks){
   const value=ratio(role[fg],role[bg]),met=qualifies(value,kind),tr=document.createElement('tr');
   tr.dataset.fg=fg;tr.dataset.bg=bg;tr.dataset.kind=kind;tr.dataset.ratio=String(value);
   tr.append(text('td',`${label} · ${kind}`),text('td',value.toFixed(2)+':1'),text('td',thresholds[kind]+':1'),text('td',met?'Target met':'Below target'));
   section.querySelector('tbody').append(tr);
  }
  return section;
 }
 function choose(palette, announce=true) {
  selected=palette;
  for(const b of selector.querySelectorAll('button'))b.setAttribute('aria-pressed',String(b.dataset.palette===palette.id));
  document.querySelector('#selected-name').textContent=palette.editorial_name;
  document.querySelector('#themes').replaceChildren(theme(palette,'light'),theme(palette,'dark'));
  document.querySelector('#selection-note').textContent=announce?`${palette.editorial_name} selected. Role assignments are illustrative; no project tokens were changed.`:'';
 }
 for(const palette of catalog.palettes){
  const button=document.createElement('button');button.type='button';button.className='palette';button.dataset.palette=palette.id;button.setAttribute('aria-pressed','false');
  const strip=document.createElement('span');strip.className='strip';strip.setAttribute('aria-hidden','true');
  for(const value of palette.swatches){const swatch=document.createElement('span');if(value)swatch.style.background=value;else swatch.className='unknown';strip.append(swatch);}
  button.append(strip,text('strong',palette.editorial_name),text('small',`${palette.swatches.filter(Boolean).length} confirmed${palette.swatches.includes(null)?' · 1 unknown':''}`));button.addEventListener('click',()=>choose(palette));selector.append(button);
  const row=document.createElement('tr');row.append(text('th',palette.editorial_name),text('td',palette.swatches.map((value,i)=>value??`Position ${i+1}: unknown label`).join(' · ')));document.querySelector('#raw-values tbody').append(row);
 }
 choose(selected,false);
 function inspectPair(){
  const fg=document.querySelector('#pair-fg').value.trim(),bg=document.querySelector('#pair-bg').value.trim();const rawAlpha=document.querySelector('#pair-alpha').value;const result=document.querySelector('#pair-result'),sample=document.querySelector('#pair-sample');
  try{
   if(!rawAlpha.trim())throw new Error('Enter a known alpha; an empty value is not zero.');
   const alpha=Number(rawAlpha),value=ratio(fg,bg,alpha);result.replaceChildren(text('strong',`${value.toFixed(2)}:1`));
   for(const [kind,target]of Object.entries(thresholds))result.append(text('p',`${kind}: ${qualifies(value,kind)?'numeric target met':'below target'} (${target}:1)`));
   result.append(text('small','Thresholds use the unrounded ratio. This sample is 16px: its applicable text target remains 4.5:1. Large-text, UI and focus targets require the relevant context.'));
   const channels=parseHex(fg).map(c=>Math.round(c*255));sample.style.color=`rgba(${channels.join(',')},${alpha})`;sample.style.background=bg;sample.textContent='Preview text — this pair may fail.';
   result.dataset.ratio=String(value);result.dataset.verified='solid-pair';
  }catch(error){result.replaceChildren(text('strong','Unverified — '+error.message));sample.removeAttribute('style');sample.textContent='No colour inferred.';delete result.dataset.ratio;result.dataset.verified='unverified';}
 }
 for(const id of ['pair-fg','pair-bg','pair-alpha'])document.querySelector('#'+id).addEventListener('input',inspectPair);
 inspectPair();
}
if(typeof document!=='undefined')start();
