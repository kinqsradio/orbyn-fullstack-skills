import {bindingValues,validateBindings,validateOverrides} from './bindings.mjs';
import {createLayoutOwner} from './layout.mjs';
import {createRegistry,createPlayer} from './components.mjs';
import {examples,registerExamples} from './examples.mjs';
import {createInspector,createLiveSpring,createPresence,createDrag} from './inspector.mjs';
import {frameTime} from './time.mjs';
import {fresh,validate,validateContext,canonical} from '../review-model.mjs';
const $=id=>document.getElementById(id),stage=$('stage'),status=$('status'),registry=registerExamples(createRegistry());
// Consumer authors can register any trusted component here before creating the player.
let manifest=null,serverState=null,project=examples[0],player,frame=0,playing=false,last=0,accumulator=0,raf=0,exitTimer=null,saveDoc=null,selectedPart=null,saving=false;
const layout=createLayoutOwner();
const spring=createLiveSpring(),presence=createPresence(),drag=createDrag(),media=matchMedia('(prefers-reduced-motion: reduce)');
let inspector;
function makeInspector(){return createInspector({x:0,parameters:bindingValues(project)},{validate(v){if(!v||Object.keys(v).sort().join()!=='parameters,x'||!Number.isFinite(v.x)||v.x< -200||v.x>200)throw Error('Invalid camera');validateOverrides(validateBindings(project),v.parameters);},onChange(v){playing=false;$('play').textContent='Play';$('camera').value=v.x;$('drag').setAttribute('aria-valuenow',String(v.x));spring.target(v.x);if($('reduced').checked)spring.snap(v.x);for(const b of project.bindings??[]){const input=document.getElementById('binding-'+b.id);if(input)input.value=String(v.parameters[b.id]);}if(player)void seek(frame);},async save(v){
 if(!manifest||!serverState)throw Error('Prepare a source-bound package to save');
 if(saving)throw Error('A save is already running');
 if(saveDoc?.state==='submitted')throw Error('Submitted review is immutable; start a new review round');
 const snapshot=structuredClone(saveDoc??fresh(manifest,context(v)));snapshot.settings=context(v);validate(snapshot,manifest);
 saving=true;renderFeedback();
 try{
  await verifyLiveSource();
  const response=await fetch('/api/review',{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':serverState.token,'X-Review-Revision':String(serverState.revision)},body:JSON.stringify({review:snapshot})});
  const result=await response.json();if(!response.ok)throw Error(result.error??'Save rejected');
  if(result.readback!==true||canonical(result.review)!==canonical(snapshot))throw Error('Saved review readback differs');
  serverState=result;saveDoc=result.review;return result;
 }finally{saving=false;renderFeedback();}
}});}
async function verifyLiveSource(){
 const response=await fetch('../manifest.json',{cache:'no-store'});
 if(!response.ok||canonical(await response.json())!==canonical(manifest))throw Error('Source changed; preserve this review and start a new source round');
}
function renderFeedback(){
 const closed=!manifest||!saveDoc||saveDoc.state!=='draft';
 for(const name of ['feedback-text','feedback-post','feedback-submit'])$(name).disabled=closed||saving;
 $('save').disabled=closed||saving;
 $('feedback-text').value=saveDoc?.pending?.text??'';
 $('feedback-context').textContent=saveDoc?.pending?`Captured ${saveDoc.pending.targetId} at ${saveDoc.pending.context.animation.time.toFixed(3)}s; later view changes keep this anchor.`:saveDoc?`${saveDoc.state}: ${saveDoc.comments.length} feedback items. Pick a component or choose Review part.`:'A source-bound package is required to retain feedback.';
 $('feedback-list').replaceChildren();
 for(const comment of saveDoc?.comments??[]){
  const item=document.createElement('li'),text=document.createElement('p'),restore=document.createElement('button');
  text.textContent=`${comment.targetId} at ${comment.context.animation.time.toFixed(3)}s: ${comment.text} (${comment.disposition})`;
  restore.textContent='Restore paused context';restore.disabled=saving;
  restore.onclick=async()=>{try{if(saveDoc.pending?.text.trim())throw Error('Post or clear pending feedback first');await applyReviewSettings(comment.context);status.textContent='Restored exact part, camera, parameters and frame.';}catch(error){status.textContent=error.message;}};
  item.append(text,restore);$('feedback-list').append(item);
 }
}

function renderBindings(){
 const container=$('bindings');container.replaceChildren();$('part').replaceChildren(new Option('Active scene',''));for(const clip of project.clips)$('part').append(new Option(clip.id,clip.id));
 for(const b of validateBindings(project)){
  const label=document.createElement('label');label.textContent=b.label+' ';
  const input=document.createElement(b.type==='enum'?'select':'input');input.id='binding-'+b.id;
  if(b.type==='number'){input.type='range';input.min=b.min;input.max=b.max;input.step=b.step;}
  else if(b.type==='color')input.type='color';
  else for(const option of b.options)input.append(new Option(option,option));
  input.value=String(inspector.value.parameters[b.id]);
  const value=()=>b.type==='number'?Number(input.value):input.value;
  input.onpointerdown=()=>{playing=false;try{inspector.begin();}catch{}};
  input.oninput=()=>{const next={...inspector.value,parameters:{...inspector.value.parameters,[b.id]:value()}};try{inspector.preview(next);}catch{inspector.commit(next);}};
  input.onchange=()=>inspector.commit({...inspector.value,parameters:{...inspector.value.parameters,[b.id]:value()}});
  input.onpointercancel=()=>inspector.cancel();label.append(input);container.append(label);
 }
}
function context(v){
 const part=selectedPart?project.clips.find(c=>c.id===selectedPart):project.clips.find(c=>!c.parent&&frame>=c.start&&frame<c.start+c.duration);
 if(!part)throw Error('Select an active source-bound component');
 let root=part;while(root.parent)root=project.clips.find(c=>c.id===root.parent);
 return{profile:'motion-v1',modelRevision:manifest.assets['motion-project.json'],partId:part.id,camera:{x:v.x,y:0,zoom:1},animation:{frame,time:frameTime(frame,project.fps),scene:root.id,rate:1},layers:{guides:true,reducedMotion:$('reduced').checked},viewport:{width:1080,height:608},parameters:structuredClone(v.parameters)};
}

async function applyReviewSettings(settings){
 await verifyLiveSource();validateContext(settings,manifest);selectedPart=settings.partId;$('part').value=selectedPart;
 $('reduced').checked=settings.layers.reducedMotion;
 inspector.commit({x:settings.camera.x,parameters:structuredClone(settings.parameters)});
 spring.snap(settings.camera.x);resize();await seek(settings.animation.frame,true);
}
async function seek(n,strict=false){frame=n;$('time').value=String(n);$('clock').textContent=`Frame ${n} · ${frameTime(n,project.fps).toFixed(3)}s`;try{return await player.seek(n,{reducedMotion:$('reduced').checked,parameters:inspector.value.parameters});}catch(e){if(!/Stale|cancelled/.test(e.message))status.textContent=e.message;if(strict)throw e;}}
function resize(){const scale=stage.parentElement.clientWidth/1080;stage.style.transform=`scale(${scale}) translateX(${spring.sample().x}px)`;}
function switchProject(next){player?.dispose().catch(e=>status.textContent=e.message);inspector?.dispose();project=next;selectedPart=null;inspector=makeInspector();renderBindings();frame=0;playing=false;$('play').textContent='Play';$('time').max=String(project.durationFrames-1);player=createPlayer(stage,project,registry);void seek(0);}
examples.forEach((s,i)=>{const o=document.createElement('option');o.value=String(i);o.textContent=s.title;$('example').append(o);});
$('example').onchange=()=>{if(manifest){status.textContent='Prepared review is source-bound; open a separate package to review another composition.';$('example').value='0';return;}switchProject(examples[Number($('example').value)]);};
function selectPart(id){
 if(saveDoc?.pending?.text.trim())throw Error('Post or clear pending feedback before changing its part');
 selectedPart=id;$('part').value=id??'';status.textContent=id?'Selected source part: '+id:'Automatic active scene selected';
}
$('part').onchange=()=>{try{selectPart($('part').value||null);}catch(error){$('part').value=selectedPart??'';status.textContent=error.message;}};
stage.onclick=e=>{const node=e.composedPath().find(n=>n?.dataset?.part&&project.clips.some(c=>c.id===n.dataset.part));if(node){try{selectPart(node.dataset.part);}catch(error){status.textContent=error.message;}}};
$('feedback-text').oninput=()=>{
 try{
  if(saving||saveDoc?.state!=='draft')throw Error('Review is not editable');
  const candidate=structuredClone(saveDoc);
  if(!$('feedback-text').value){candidate.pending=null;validate(candidate,manifest);saveDoc=candidate;renderFeedback();return;}
  if(!candidate.pending){const captured=context(inspector.value);candidate.pending={targetId:'part/'+captured.partId,context:structuredClone(captured),text:''};}
  candidate.pending.text=$('feedback-text').value;validate(candidate,manifest);saveDoc=candidate;
  $('feedback-context').textContent=`Captured ${saveDoc.pending.targetId} at ${saveDoc.pending.context.animation.time.toFixed(3)}s; later view changes keep this anchor.`;
 }catch(error){status.textContent=error.message;}
};
$('feedback-post').onclick=()=>{
 try{
  if(saving||saveDoc?.state!=='draft')throw Error('Review is not editable');
  const candidate=structuredClone(saveDoc);
  if(!candidate.pending&&$('feedback-text').value.trim()){const captured=context(inspector.value);candidate.pending={targetId:'part/'+captured.partId,context:structuredClone(captured),text:$('feedback-text').value};}
  if(!candidate.pending?.text.trim())throw Error('Choose an active part and write feedback');
  candidate.comments.push({...structuredClone(candidate.pending),id:crypto.randomUUID(),disposition:'unresolved',decision:''});candidate.pending=null;validate(candidate,manifest);saveDoc=candidate;
  renderFeedback();status.textContent='Feedback retained locally; Save review makes it durable.';
 }catch(error){status.textContent=error.message;}
};
$('feedback-submit').onclick=async()=>{
 if(saving){status.textContent='A save is already running.';return;}
 let submitting=false;
 try{
  if(saveDoc?.pending?.text.trim())throw Error('Post or clear pending feedback first');
  await inspector.save();submitting=true;saving=true;renderFeedback();
  const submitted=structuredClone(saveDoc);submitted.state='submitted';submitted.pending=null;validate(submitted,manifest);
  const response=await fetch('/api/review',{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':serverState.token,'X-Review-Revision':String(serverState.revision)},body:JSON.stringify({review:submitted})});
  const result=await response.json();if(!response.ok)throw Error(result.error??'Submission failed');
  if(result.readback!==true||canonical(result.review)!==canonical(submitted))throw Error('Submission readback differs');
  saveDoc=result.review;serverState=result;status.textContent='Submitted review retained; decisions use the existing reconciliation flow.';
 }catch(error){status.textContent=error.message;}
 finally{if(submitting)saving=false;renderFeedback();}
};
$('reorder').onclick=()=>{const list=$('layout-list');layout.update([...list.children],()=>list.prepend(list.lastElementChild),{reducedMotion:$('reduced').checked});};
$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play';if(playing&&frame===project.durationFrames-1)void seek(0);};
$('time').oninput=()=>{playing=false;$('play').textContent='Play';void seek(Number($('time').value));};
$('reduced').checked=media.matches;const preference=e=>{$('reduced').checked=e.matches;spring.snap(inspector.value.x);void seek(frame);};media.addEventListener('change',preference);$('reduced').onchange=()=>{spring.snap(inspector.value.x);void seek(frame);};
$('camera').onpointerdown=()=>{playing=false;inspector.begin();};$('camera').oninput=()=>{const next={...inspector.value,x:Number($('camera').value)};try{inspector.preview(next);}catch{inspector.commit(next);}};$('camera').onchange=()=>inspector.commit({...inspector.value,x:Number($('camera').value)});
$('drag').onpointerdown=e=>{if(drag.begin(e.pointerId,e.clientX)){playing=false;inspector.begin();$('drag').setPointerCapture(e.pointerId);$('drag').dataset.start=String(inspector.value.x);}};
$('drag').onpointermove=e=>{const delta=drag.move(e.pointerId,e.clientX);if(delta!==null)inspector.preview({...inspector.value,x:Math.max(-200,Math.min(200,Number($('drag').dataset.start)+delta))});};
$('drag').onpointerup=e=>{if(drag.end(e.pointerId))inspector.commit();};$('drag').onpointercancel=()=>{drag.cancel();inspector.cancel();};$('drag').onlostpointercapture=()=>{if(drag.active){drag.cancel();inspector.cancel();}};
$('drag').onkeydown=e=>{if(['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();inspector.commit({...inspector.value,x:Math.max(-200,Math.min(200,inspector.value.x+(e.key==='ArrowLeft'?-10:10)))});}};
$('toggle').onclick=()=>{if(presence.state==='open'){const token=presence.close();$('toggle').setAttribute('aria-expanded','false');exitTimer=setTimeout(()=>{if(presence.completeExit(token)){if($('panel').contains(document.activeElement))$('toggle').focus();$('panel').hidden=true;}},$('reduced').checked?0:180);}else{clearTimeout(exitTimer);presence.open();$('panel').hidden=false;$('toggle').setAttribute('aria-expanded','true');}};presence.open();
for(const action of ['undo','redo','reset'])$(action).onclick=()=>inspector[action]();
$('save').onclick=async()=>{try{await inspector.save();status.textContent='Saved to existing review.json bridge.';}catch(e){status.textContent=e.message;}};
$('reopen').onclick=async()=>{try{const response=await fetch('/api/review');const result=await response.json();if(!response.ok)throw Error('Bridge unavailable');if(result.review){validate(result.review,manifest);saveDoc=result.review;await applyReviewSettings(saveDoc.settings);}serverState=result;renderFeedback();status.textContent='Source-bound review reopened.';}catch(e){status.textContent=e.message;}};
try{const response=await fetch('../manifest.json');if(response.ok){const candidate=await response.json();if(candidate.prototype.id==='motion-composition-v1'){manifest=candidate;project=await(await fetch('../motion-project.json')).json();serverState=await(await fetch('/api/review')).json();$('example').replaceChildren(new Option(project.title??'Prepared composition','0'));}}}catch{/* A standalone static source preview has no durable writer. */}
switchProject(project);await seek(0,true);if(manifest){saveDoc=serverState.review?validate(structuredClone(serverState.review),manifest):fresh(manifest,context(inspector.value));if(serverState.review)await applyReviewSettings(saveDoc.settings);}for(const control of document.querySelectorAll('button,input,select'))control.disabled=false;renderFeedback();status.textContent=manifest?'Ready. Source-bound review and parameters are available.':'Ready. Source preview; durable saves require a prepared package.';const observer=new ResizeObserver(resize);observer.observe(stage.parentElement);resize();
function tick(now){const dt=Math.min(.1,last?(now-last)/1000:0);last=now;spring.step(dt);resize();if(playing){accumulator+=dt*project.fps.numerator/project.fps.denominator;if(accumulator>=1){const advance=Math.floor(accumulator);accumulator-=advance;void seek(Math.min(project.durationFrames-1,frame+advance));if(frame===project.durationFrames-1){playing=false;$('play').textContent='Play';}}}raf=requestAnimationFrame(tick);}raf=requestAnimationFrame(tick);
window.motionDemo={seek:n=>seek(n,true),applyReviewSettings,snapshot:()=>({frame,playing,reducedMotion:$('reduced').checked,camera:inspector.value,source:project.sourceRevision,selectedPart}),player:()=>player};
window.addEventListener('pagehide',()=>{cancelAnimationFrame(raf);clearTimeout(exitTimer);observer.disconnect();media.removeEventListener('change',preference);drag.cancel();layout.dispose();inspector.dispose();void player.dispose();},{once:true});
