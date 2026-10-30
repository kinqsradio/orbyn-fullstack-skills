// Original generated raster study and wordmark; no downloaded assets.
import { mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { deflateSync } from 'node:zlib';
const out = process.argv[2]; if (!out) throw Error('Fresh media directory required'); await mkdir(out);
const crc = bytes => { let c=0xffffffff; for(const b of bytes){ c^=b; for(let i=0;i<8;i++)c=(c>>>1)^(0xedb88320 & -(c&1)); } return (c^0xffffffff)>>>0; };
function chunk(type, data){ const name=Buffer.from(type), size=Buffer.alloc(4), sum=Buffer.alloc(4);size.writeUInt32BE(data.length);sum.writeUInt32BE(crc(Buffer.concat([name,data])));return Buffer.concat([size,name,data,sum]); }
for(const name of ['gallery','logo']) {
  const w=256,h=256, rows=Buffer.alloc((w*4+1)*h);
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){const i=y*(w*4+1)+1+x*4, inside=name==='gallery'?Math.hypot(x-128,y-128)<80:Math.abs(x-128)+Math.abs(y-128)<86;rows[i]=inside?185:21;rows[i+1]=inside?89:40;rows[i+2]=inside?55:35;rows[i+3]=255;}
  const header=Buffer.alloc(13);header.writeUInt32BE(w);header.writeUInt32BE(h,4);header[8]=8;header[9]=6;
  await writeFile(join(out,name+'.png'),Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',header),chunk('IDAT',deflateSync(rows)),chunk('IEND',Buffer.alloc(0))]),{flag:'wx'});
}
