// Parse static module requests with Node's real JS parser. No source is evaluated.
// This checks packaged static dependencies; trusted authored source is NOT sandboxed.
import {SourceTextModule} from 'node:vm';
import {readFile,lstat,realpath} from 'node:fs/promises';
import {resolve,dirname,relative,join} from 'node:path';
const [rootArg,entryArg]=process.argv.slice(2),root=await realpath(rootArg),entry=resolve(entryArg),visited=new Set();
async function visit(filename){
  const name=relative(root,filename);
  if(name.startsWith('..')||name.includes('node_modules')||!name.endsWith('.mjs'))throw Error('Foreign module closure');
  if(visited.has(name))return;
  if(visited.size>=100)throw Error('Module closure budget');
  for(let current=root,parts=name.split('/'),i=0;i<parts.length;i++){current=join(current,parts[i]);if((await lstat(current)).isSymbolicLink())throw Error('Module closure symlink');}
  const source=await readFile(filename,'utf8');if(Buffer.byteLength(source)>1048576)throw Error('Module source budget');
  const parsed=new SourceTextModule(source,{identifier:filename});visited.add(name);
  for(const request of parsed.dependencySpecifiers){
    if(!request.startsWith('./')&&!request.startsWith('../'))throw Error('Offline local module request required: '+request);
    await visit(resolve(dirname(filename),request));
  }
}
await visit(entry);
console.log(JSON.stringify({staticModules:[...visited].sort(),limit:'Static requests parsed, no evaluation. Trusted source review and actual offline runtime checks remain required; computed fetch/import behavior is not proved by static closure.'}));
