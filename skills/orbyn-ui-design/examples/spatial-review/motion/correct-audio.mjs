// Apply an explicitly authored correction file. No model estimate is silently
// accepted, and every output is new. Store inputs/edits/results in the consumer.
import {readFile,writeFile,mkdir,realpath,lstat} from 'node:fs/promises';
import {resolve,dirname,join} from 'node:path';
import {createHash} from 'node:crypto';
import {parseJSONStrict} from '../../review-workspace/model.mjs';
import {correctWords,wordsToCues,withBeatCorrections} from './audio.mjs';
const args={};
for(let i=2;i<process.argv.length;i+=2){const k=process.argv[i],v=process.argv[i+1];if(!['--transcript','--analysis','--edits','--output'].includes(k)||!v||k in args)throw Error('Unknown/duplicate/missing option');args[k]=v;}
if(!args['--edits']||!args['--output']||Boolean(args['--transcript'])===Boolean(args['--analysis']))throw Error('Select --transcript or --analysis, plus --edits and fresh --output');
async function read(path){const p=resolve(path),s=await lstat(p);if(s.isSymbolicLink()||!s.isFile()||s.size>8*1024*1024)throw Error('Bounded regular JSON input required');const bytes=await readFile(p);return{data:parseJSONStrict(bytes.toString()),sha256:createHash('sha256').update(bytes).digest('hex')};}
const input=await read(args['--transcript']??args['--analysis']),edits=await read(args['--edits']);
const out=resolve(args['--output']);if(await realpath(dirname(out))!==dirname(out))throw Error('Existing real output parent required');
const hash=value=>createHash('sha256').update(value).digest('hex');
let result,outputs;
if(args['--transcript']){result=correctWords(input.data,edits.data);outputs={'transcript.json':result,'caption-review.json':wordsToCues(result)};}
else{if(Object.keys(edits.data).sort().join()!=='audioSha256,beats')throw Error('Explicit source hash and beats required');result=withBeatCorrections(input.data,edits.data.audioSha256,edits.data.beats);outputs={'audio-analysis.json':result};}
await mkdir(out);
const saved={};for(const[name,value]of Object.entries(outputs)){const bytes=JSON.stringify(value,null,2)+'\n';await writeFile(join(out,name),bytes,{flag:'wx'});saved[name]=hash(bytes);}
await writeFile(join(out,'receipt.json'),JSON.stringify({status:'completed',inputSha256:input.sha256,editsSha256:edits.sha256,audioSha256:result.audioSha256??result.audio.sha256,outputs:saved,meaning:'Explicit caller-authored corrections; this tool does not establish human review, transcription accuracy or media rights.'},null,2)+'\n',{flag:'wx'});
console.log(out);
