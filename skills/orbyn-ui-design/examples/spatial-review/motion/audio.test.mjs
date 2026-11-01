import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,readFile,rm,realpath} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {validateAnalysis, sampleAudio, withBeatCorrections, validateTranscript, correctWords, wordsToCues, featureSampler} from './audio.mjs';
const sha='a'.repeat(64);
const analysis=()=>({version:1,audio:{sha256:sha,bytes:100,duration:2,sourceSampleRate:22050,sourceChannels:1},analysis:{sampleRate:22050,hopLength:512,units:'seconds',duration:2,status:'estimated',tempo:120,beats:[.5,1,1.5],onsets:[.5,1],energy:[{time:0,rms:0},{time:1,rms:1}],waveform:[{time:0,min:-.5,max:.5}]},manual:{beats:null,words:[]},limits:[]});
const transcript=()=>({version:1,audioSha256:sha,duration:2,language:'en',model:{origin:'test estimate'},revision:1,words:[{id:'word-0',text:'Hello',start:.1,end:.5,status:'aligned',score:.9},{id:'word-1',text:'world',start:null,end:null,status:'missing',score:null}],history:[]});
test('audio features seek without history and explicit beat corrections supersede estimates',()=>{
 const data=analysis(), original=JSON.stringify(data);
 assert.equal(sampleAudio(data,.5).rms,.5);assert.equal(sampleAudio(data,.5).beatIndex,0);
 sampleAudio(data,1.5);assert.equal(sampleAudio(data,.2).beatIndex,-1);
 const corrected=withBeatCorrections(data,sha,[.25,.75]);assert.equal(sampleAudio(corrected,.5).beatSource,'manual');assert.equal(sampleAudio(corrected,.5).beatPhase,.5);
 assert.equal(JSON.stringify(data),original);
});
const features=()=>({version:1,audioSha256:sha,sampleRate:22050,fps:{num:30,den:1},frames:2,fftSize:2048,status:'estimated',bands:[{name:'bass',lowHz:60,highHz:250,peak:.5}],bandEnergy:{bass:[.25,1]},kick:[0,1],barEdgesHz:[40,80,160],barFloorDb:60,bars:[[0,.5],[1,.25]],grid:{status:'fitted',beatCount:8,bpm:120,periodSeconds:.5,offsetSeconds:.137,phase:.274,residualMs:1},downbeat:{status:'unknown',time:null,beatsPerBar:4,barOffsetBeats:null,method:'test'},boundaries:[],boundaryRotation:{counts:[0,0,0,0],best:null,boundaries:0},limits:[]});
test('baked features seek by exact frame and keep grid phase apart from the bar line',()=>{
 const sample=featureSampler(features(),sha);
 assert.deepEqual(sample(1),{frame:1,time:1/30,bands:{bass:1},kick:1,bars:[1,.25],gridPhase:sample(1).gridPhase,downbeatStatus:'unknown',barPhase:null,audioSha256:sha});
 assert.equal(sample(0).kick,0);assert.equal(sample(1).kick,1);
 assert.ok(Math.abs(sample(0).gridPhase-(1-.274))<1e-9);
 const manual=features();manual.downbeat={status:'manual',time:.137,beatsPerBar:4,barOffsetBeats:0,method:'manual'};
 assert.ok(Math.abs(featureSampler(manual)(0).barPhase-(4-.274)/4)<1e-9);
 assert.throws(()=>sample(2),/frame/);assert.throws(()=>sample(.5),/frame/);
});
test('feature files refuse stale sources, broken shapes and an unverified bar line',()=>{
 assert.throws(()=>featureSampler(features(),'b'.repeat(64)),/Stale/);
 for(const mutate of [d=>d.kick.pop(),d=>d.bars[1].pop(),d=>d.bars[0][0]=1.5,d=>d.bandEnergy.bass[0]=NaN,d=>delete d.bandEnergy.bass,d=>d.barEdgesHz=[40,30,20],d=>d.downbeat.time=.5,d=>{d.downbeat.status='estimated';},d=>{d.grid.status='magic';}]){const d=features();mutate(d);assert.throws(()=>featureSampler(d));}
});
test('stale source, duplicate/nonfinite times and invalid waveform reject',()=>{
 assert.throws(()=>validateAnalysis(analysis(),'b'.repeat(64)),/Stale/);
 for(const mutate of [d=>d.analysis.beats=[1,1],d=>d.analysis.energy[0].rms=NaN,d=>d.analysis.waveform[0].min=1]){const d=analysis();mutate(d);assert.throws(()=>validateAnalysis(d));}
});
test('estimated and missing words remain unaccepted until explicit source-bound corrections',()=>{
 const data=transcript(), original=JSON.stringify(data);assert.deepEqual(wordsToCues(data).unresolved,['word-0','word-1']);
 const corrected=correctWords(data,{audioSha256:sha,revision:1,edits:[{id:'word-0',text:'Hello',start:.1,end:.5},{id:'word-1',text:'world',start:.6,end:1}]});
 const result=wordsToCues(corrected);assert.equal(result.reviewRequired,false);assert.deepEqual(result.cues,[{start:.1,end:1,text:'Hello world'}]);assert.equal(corrected.history[0].previous[1].status,'missing');assert.equal(JSON.stringify(data),original);
 assert.throws(()=>correctWords(corrected,{audioSha256:sha,revision:1,edits:[]}),/Stale/);
 assert.throws(()=>correctWords(data,{audioSha256:'b'.repeat(64),revision:1,edits:[]}),/source/);
});
test('missing timing, out-of-duration correction and overlapping caption groups refuse',()=>{
 const data=transcript();data.words[1].status='manual';assert.throws(()=>validateTranscript(data));
 assert.throws(()=>correctWords(transcript(),{audioSha256:sha,revision:1,edits:[{id:'word-0',text:'Hello',start:1,end:3}]}));
 const corrected=correctWords(transcript(),{audioSha256:sha,revision:1,edits:[{id:'word-0',text:'Hello',start:.1,end:1},{id:'word-1',text:'world',start:.6,end:1.2}]});assert.throws(()=>wordsToCues(corrected,{maxWords:1}),/Overlapping/);
});
test('correction CLI preserves inputs, writes auditable output and refuses reuse or duplicate fields',async()=>{
 const directory=await realpath(await mkdtemp(join(tmpdir(),'orbyn-audio-contract-')));
 try{
  const source=join(directory,'source.json'),edits=join(directory,'edits.json'),out=join(directory,'result');
  const original=JSON.stringify(transcript());await writeFile(source,original);
  await writeFile(edits,JSON.stringify({audioSha256:sha,revision:1,edits:[{id:'word-1',text:'world',start:.6,end:1}]}));
  const invoke=output=>spawnSync(process.execPath,[new URL('./correct-audio.mjs',import.meta.url).pathname,'--transcript',source,'--edits',edits,'--output',output],{encoding:'utf8'});
  const result=invoke(out);assert.equal(result.status,0,result.stderr);
  const receipt=JSON.parse(await readFile(join(out,'receipt.json')));assert.equal(receipt.status,'completed');assert.equal(receipt.audioSha256,sha);assert.match(receipt.editsSha256,/^[a-f0-9]{64}$/);
  const captions=JSON.parse(await readFile(join(out,'caption-review.json')));assert.equal(captions.reviewRequired,true);assert.deepEqual(captions.unresolved,['word-0']);
  assert.notEqual(invoke(out).status,0);assert.equal(await readFile(source,'utf8'),original);
  await writeFile(edits,'{"revision":1,"revision":2}');assert.notEqual(invoke(join(directory,'bad')).status,0);
 }finally{await rm(directory,{recursive:true,force:true});}
});
