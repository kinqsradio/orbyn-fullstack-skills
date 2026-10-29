import assert from 'node:assert/strict';
import { test } from 'node:test';
import fs from 'node:fs';
import { ratio, qualifies, checks, parseHex } from '../skills/orbyn-ui-design/examples/colour-gallery/gallery.mjs';
const data=JSON.parse(fs.readFileSync(new URL('../skills/orbyn-ui-design/assets/reference-palettes.json',import.meta.url),'utf8'));
test('independent exact ratio anchors and unrounded threshold classification',()=>{
 assert.equal(ratio('#000000','#FFFFFF'),21);assert.equal(ratio('#123456','#123456'),1);
 const value=ratio('#81737A','#FFFFFF');assert(Math.abs(value-4.499922485663913)<1e-12);assert.equal(value.toFixed(2),'4.50');assert.equal(qualifies(value,'normal'),false);
 assert.equal(qualifies(3,'large'),true);assert.equal(qualifies(2.999,'focus-adjacency'),false);
});
test('unknown hex, gradient, malformed alpha and criterion remain errors',()=>{
 for(const value of [null,'#123','unknown','linear-gradient(#000000,#FFFFFF)'])assert.throws(()=>parseHex(value));
 for(const alpha of [NaN,Infinity,-1,2])assert.throws(()=>ratio('#000000','#FFFFFF',alpha));
 assert.throws(()=>qualifies(4.5,'__proto__'));
});
test('known alpha is composited over stated background',()=>{
 assert.equal(ratio('#000000','#FFFFFF',0),1);assert.equal(ratio('#000000','#FFFFFF',1),21);
 assert.equal(qualifies(ratio('#000000','#FFFFFF',.5),'normal'),false);
});
test('all 168 illustrative pair checks meet their explicitly named target',()=>{
 let count=0;
 for(const palette of data.palettes)for(const roles of Object.values(palette.role_proposals))for(const [,fg,bg,kind]of checks){assert(qualifies(ratio(roles[fg],roles[bg]),kind),`${palette.id} ${fg}/${bg}`);count++;}
 assert.equal(count,168);
});
test('source positions and role origins remain distinct',()=>{
 assert.equal(data.palettes.flatMap(p=>p.swatches).filter(Boolean).length,41);assert.equal(data.palettes[2].swatches[2],null);
 for(const p of data.palettes)for(const roles of Object.values(p.role_proposals))for(const value of Object.values(roles))assert(p.swatches.includes(value)||Object.hasOwn(data.added_colours,value));
});
