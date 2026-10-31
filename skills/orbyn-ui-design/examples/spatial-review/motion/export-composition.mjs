// Local deterministic capture of the same trusted component registry used by preview.
// Tools are caller-selected existing binaries; this command installs nothing.
import {readFile,writeFile,mkdir,lstat,realpath,statfs} from 'node:fs/promises';
import {join,resolve,dirname} from 'node:path';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {rate,frameTime,audioSample} from './time.mjs';
import {validateComposition} from './composition.mjs';
import {validateScene} from './three.mjs';
const options={};
for(let i=2;i<process.argv.length;i+=2){const name=process.argv[i];if(!['--package','--output','--playwright','--chrome','--python','--ffmpeg','--ffprobe','--width','--height','--timeout','--frames','--fps','--mode','--from-frame'].includes(name)||name in options||!process.argv[i+1])throw Error('Unknown/duplicate/missing option');options[name]=process.argv[i+1];}
if(!options['--package']||!options['--output']||!options['--playwright'])throw Error('Use --package SOURCE --output FRESH_OUTPUT --playwright EXISTING_IMPORT [--chrome EXISTING_BINARY]');
const pkg=await realpath(options['--package']),out=resolve(options['--output']);
if(await realpath(dirname(out))!==dirname(out))throw Error('Existing real output parent required');
const width=Number(options['--width']??1080),height=Number(options['--height']??608),timeout=Number(options['--timeout']??600);
if(![width,height].every(v=>Number.isSafeInteger(v)&&v>=240&&v<=3840&&v%2===0)||width*height>8294400||!Number.isFinite(timeout)||timeout<10||timeout>1800)throw Error('Render budget');
const hash=v=>createHash('sha256').update(v).digest('hex'),manifest=JSON.parse(await readFile(join(pkg,'manifest.json'),'utf8'));
const graphics=manifest.prototype.id==='graphics-review-v1';
let spec;
const selectedMode=options['--mode']??'raster';
const fromFrame=Number(options['--from-frame']??0);if(!Number.isSafeInteger(fromFrame)||fromFrame<0)throw Error('Invalid source frame start');
let sourceDurationFrames;
if(graphics){
 if(!options['--frames']||!options['--fps']||!['raster','effects','pathtrace','webgpu'].includes(selectedMode))throw Error('Graphics export requires --frames INTEGER --fps INTEGER_OR_RATIO [--mode raster|effects|pathtrace|webgpu]');
 const parts=options['--fps'].split('/');if(parts.length>2||parts.some(p=>!/^\d+$/.test(p)))throw Error('Invalid explicit graphics FPS');
 const fps=rate({numerator:Number(parts[0]),denominator:Number(parts[1]??1)}),frames=Number(options['--frames']);
 const scene=validateScene(JSON.parse(await readFile(join(pkg,'motion/graphics-scene.json'),'utf8'))),profile=manifest.targets.find(t=>t.id==='profile/graphics-v1')?.graphics;
 if(!Number.isSafeInteger(frames)||frames<1||frames>1000||!profile||frameTime(fromFrame+frames-1,fps)>profile.maxTicks/profile.tickRate)throw Error('Graphics frame/time budget');
 spec={fps,durationFrames:frames,sourceRevision:scene.sourceRevision};sourceDurationFrames=Math.floor(profile.maxTicks/profile.tickRate*fps.numerator/fps.denominator)+1;
}else{
 if(manifest.prototype.id!=='motion-composition-v1'||['--fps','--mode'].some(k=>options[k]!==undefined))throw Error('Explicit motion profile required; graphics controls cannot retime a DOM project');
 spec=validateComposition(JSON.parse(await readFile(join(pkg,'motion-project.json'),'utf8')));sourceDurationFrames=spec.durationFrames;
 const count=Number(options['--frames']??sourceDurationFrames-fromFrame);if(!Number.isSafeInteger(count)||count<1||count>3600||fromFrame+count>sourceDurationFrames)throw Error('DOM source frame window/budget');spec={...spec,durationFrames:count};
}

let reviewInput=null,reviewBytes=null;
try{
 const reviewStat=await lstat(join(pkg,'review.json'));if(!reviewStat.isFile()||reviewStat.isSymbolicLink()||reviewStat.size>524288)throw Error('Regular bounded review input required');
 reviewBytes=await readFile(join(pkg,'review.json'));reviewInput=JSON.parse(reviewBytes);
 if(!reviewInput||Object.keys(reviewInput).sort().join()!=='review,revision'||!Number.isSafeInteger(reviewInput.revision)||reviewInput.revision<1||JSON.stringify(Object.entries(reviewInput.review?.prototype??{}).sort())!==JSON.stringify(Object.entries(manifest.prototype).sort()))throw Error('Stale/invalid review input');
}catch(error){if(error.code!=='ENOENT')throw error;}

async function verify(){const {fingerprint,...prototype}=manifest.prototype;const canonical=v=>JSON.stringify(v&&typeof v==='object'?Array.isArray(v)?v.map(x=>JSON.parse(canonical(x))):Object.fromEntries(Object.keys(v).sort().map(k=>[k,JSON.parse(canonical(v[k]))])):v);if(hash(canonical({prototype,targets:manifest.targets,assets:manifest.assets}))!==fingerprint)throw Error('Invalid source fingerprint');if(JSON.stringify(JSON.parse(await readFile(join(pkg,'manifest.json'),'utf8')))!==JSON.stringify(manifest))throw Error('Changed manifest');for(const[name,digest]of Object.entries(manifest.assets)){if(!/^[A-Za-z0-9_-][A-Za-z0-9_.-]*(?:\/[A-Za-z0-9_.-]+)*$/.test(name)||name.split('/').some(s=>s.startsWith('.')))throw Error('Unsafe source path');for(let i=1;i<=name.split('/').length;i++)if((await lstat(join(pkg,...name.split('/').slice(0,i)))).isSymbolicLink())throw Error('Source symlink');if(hash(await readFile(join(pkg,name)))!==digest)throw Error('Stale source '+name);}}
await verify();const disk=await statfs(dirname(out));if(Number(disk.bavail*disk.bsize)<width*height*spec.durationFrames*4.1+100e6)throw Error('Insufficient conservative disk budget');
await mkdir(out);await mkdir(join(out,'frames'));if(reviewBytes)await writeFile(join(out,'review-input.json'),reviewBytes,{flag:'wx'});
const receipt={version:1,exporterSha256:hash(await readFile(new URL(import.meta.url))),status:'preparing',sourceFingerprint:manifest.prototype.fingerprint,reviewInputSha256:reviewBytes?hash(reviewBytes):null,reviewRevision:reviewInput?.revision??null,sourceRevision:spec.sourceRevision,sourceProfile:manifest.prototype.id,mode:graphics?selectedMode:'dom-svg',sourceFromFrame:fromFrame,sourceToFrameExclusive:fromFrame+spec.durationFrames,sourceDurationFrames,fps:rate(spec.fps),frames:spec.durationFrames,width,height,audioSampleEnd48000:audioSample(spec.durationFrames,spec.fps,48000),limits:[graphics?'Explicit graphics frame sequence; media audio/EDL is separate':'Silent DOM/SVG composition export; media audio/EDL is separate','Backend/device observations apply only to this fixture/profile; no universal parity or full accessibility/artistic quality qualification','System font rendering is runtime-specific']};
let browser,server,cancelled=false;const children=new Set(),started=Date.now();
const persist=()=>writeFile(join(out,'receipt.json'),JSON.stringify(receipt,null,2)+'\n');
function stop(child){if(child.exitCode!==null||child.signalCode!==null)return;child.kill('SIGTERM');setTimeout(()=>{if(child.exitCode===null&&child.signalCode===null)child.kill('SIGKILL');},1000).unref();}
const cancel=()=>{cancelled=true;for(const child of children)stop(child);browser?.close().catch(()=>{});};
const budget=()=>{if(cancelled||Date.now()-started>timeout*1000)throw Error('Export cancelled/time budget');};
process.on('SIGINT',cancel);process.on('SIGTERM',cancel);const timer=setTimeout(cancel,timeout*1000);
async function run(binary,args,label){budget();const child=spawn(binary,args,{stdio:['ignore','pipe','pipe']});children.add(child);let stdout='',stderr='';child.stdout.on('data',b=>{stdout+=b;if(stdout.length>2e6)stop(child);});child.stderr.on('data',b=>{stderr+=b;if(stderr.length>2e6)stop(child);});try{const code=await new Promise((res,rej)=>{child.once('error',rej);child.once('exit',res);});await writeFile(join(out,label+'.log'),stdout+stderr);if(code!==0)throw Error(label+' failed');budget();return stdout;}finally{children.delete(child);}}
try{
 await persist();
 server=spawn(options['--python']??'python3',[join(pkg,'serve.py'),'--package',pkg],{stdio:['ignore','pipe','pipe']});children.add(server);
 const url=await new Promise((res,rej)=>{let text='';server.stdout.on('data',b=>{text+=b;const m=/http:\/\/127\.0\.0\.1:\d+\//.exec(text);if(m)res(m[0]);});server.once('error',rej);server.once('exit',()=>rej(Error('Preview server stopped')));});
 const {chromium}=await import(options['--playwright']);browser=await chromium.launch({headless:true,...(options['--chrome']?{executablePath:options['--chrome']}:{})});
 const page=await browser.newPage({viewport:{width:Math.max(1280,width+80),height:Math.max(800,height+200)},deviceScaleFactor:1});
 const errors=[],origin=new URL(url).origin,allowed=new Set(Object.keys(manifest.assets));
 page.setDefaultTimeout(60000);page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/*',route=>{const request=route.request(),target=new URL(request.url());let name;try{name=decodeURIComponent(target.pathname.slice(1));}catch{name='';}if(target.origin===origin&&request.method()==='GET'&&(allowed.has(name)||name==='manifest.json'||name==='api/review'))return route.continue();if(name!=='favicon.ico')errors.push('Undeclared runtime request: '+target.pathname);return route.abort();});
 await page.goto(url+(graphics?'motion/graphics-demo.html?profile=graphics-profile/':'motion/demo.html'));await page.waitForFunction(isGraphics=>isGraphics?Boolean(window.orbynGraphics):Boolean(window.motionDemo),graphics);
 if(reviewInput)await page.evaluate(async({graphics,settings})=>{const api=graphics?window.orbynGraphics:window.motionDemo;if(typeof api.applyReviewSettings!=='function')throw Error('Review restore API unavailable');await api.applyReviewSettings(settings);},{graphics,settings:reviewInput.review.settings});
 await page.evaluate(async({width,height,graphics})=>{const surface=graphics?document.getElementById('stage'):document.getElementById('stage').parentElement;Object.assign(surface.style,{width:width+'px',height:height+'px',aspectRatio:'auto',position:'fixed',left:'0',top:'0',zIndex:'100',margin:'0'});if(graphics&&window.orbynGraphics.resize)await window.orbynGraphics.resize(width,height);await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));}, {width,height,graphics});
 receipt.runtime={node:process.version,browser:browser.version(),ffmpeg:(await run(options['--ffmpeg']??'ffmpeg',['-version'],'ffmpeg-version')).split('\n')[0]};receipt.status='capturing';await persist();
 for(let frame=0;frame<spec.durationFrames;frame++){budget();const observed=await page.evaluate(async({frame,graphics,fps,mode})=>{const result=graphics?await window.orbynGraphics.renderFrame(frame,fps,mode):await window.motionDemo.seek(frame);await document.fonts.ready;return graphics?{...result,canvas:[...document.querySelectorAll('canvas')].filter(c=>!c.hidden).map(c=>({width:c.width,height:c.height}))}:{settings:window.motionDemo.snapshot(),active:result.active.map(c=>({id:c.id,component:c.component,localFrame:c.localFrame,localTime:c.localTime,opacity:c.opacity}))};},{frame:frame+fromFrame,graphics,fps:rate(spec.fps).numerator/rate(spec.fps).denominator,mode:selectedMode});if(graphics){if(observed.sourceRevision!==spec.sourceRevision||observed.metrics.currentStatus!=='completed')throw Error('Graphics readiness/source mismatch');receipt.renderedBackend=observed.metrics.backend;receipt.device=observed.metrics.backend==='WebGPU'?observed.metrics.gpu:observed.metrics.gl;receipt.lastGraphicsFrame=observed;receipt.graphicsFrames??=[];receipt.graphicsFrames.push({frame,sourceFrame:frame+fromFrame,simulationTick:observed.metrics.simulationTick,backend:observed.metrics.backend,canvas:observed.canvas,progressive:observed.metrics.pathtrace??null});}else{if(frame===0)receipt.firstDOMFrame=observed;receipt.lastDOMFrame=observed;}if(errors.length)throw Error('Runtime/closure failure: '+errors.join('; '));await page.screenshot({clip:{x:0,y:0,width,height},path:join(out,'frames',`frame-${String(frame).padStart(6,'0')}.png`)});}
 await verify();const fps=rate(spec.fps),fpsString=`${fps.numerator}/${fps.denominator}`;
 await run(options['--ffmpeg']??'ffmpeg',['-v','error','-n','-framerate',fpsString,'-i',join(out,'frames/frame-%06d.png'),'-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-r',fpsString,'-frames:v',String(spec.durationFrames),join(out,'composition.mp4')],'encode');
 const probe=JSON.parse(await run(options['--ffprobe']??'ffprobe',['-v','error','-count_frames','-show_streams','-of','json',join(out,'composition.mp4')],'probe'));const video=probe.streams.find(s=>s.codec_type==='video');const actualRate=video?.avg_frame_rate?.split('/').map(Number);if(!actualRate||actualRate[0]*fps.denominator!==actualRate[1]*fps.numerator)throw Error('Encoded rational rate differs');if(!video||video.width!==width||video.height!==height||Number(video.nb_read_frames)!==spec.durationFrames||Math.abs(Number(video.duration)-frameTime(spec.durationFrames,spec.fps))>frameTime(1,spec.fps))throw Error('Encoded timing/frame contract');
 await run(options['--ffmpeg']??'ffmpeg',['-v','error','-i',join(out,'composition.mp4'),'-f','null','-'],'decode');
 await verify();budget();receipt.status='complete';receipt.elapsedSeconds=(Date.now()-started)/1000;receipt.videoSha256=hash(await readFile(join(out,'composition.mp4')));receipt.probe=probe;await persist();console.log(JSON.stringify(receipt));
}catch(error){receipt.status=cancelled?'cancelled':'failed';receipt.error=error.message;await persist();throw error;}
finally{clearTimeout(timer);process.removeListener('SIGINT',cancel);process.removeListener('SIGTERM',cancel);await browser?.close();for(const child of children)stop(child);}
