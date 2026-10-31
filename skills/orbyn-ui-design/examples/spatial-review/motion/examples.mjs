// Three unrelated authored compositions. Components are trusted repo source, not JSON imports.
export const examples=[
 {version:2,title:'From signal to release',fps:{numerator:30,denominator:1},durationFrames:600,sourceRevision:'delivery-v1',bindings:[{id:'orb-radius',clip:'signal',property:'props.radius',label:'Orbit radius',type:'number',min:10,max:60,step:1,default:28},{id:'title-size',clip:'heading',property:'props.fontSize',label:'Title size',type:'number',min:28,max:56,step:1,default:44},{id:'orbit-speed',clip:'signal',property:'rate',label:'Orbit time rate',type:'number',min:.5,max:2,step:.25,default:1},{id:'orb-color',clip:'signal',property:'props.color',label:'Orbit color',type:'color',default:'#f8b454'}],clips:[
  {id:'heading',component:'title-card',start:0,duration:600,props:{text:'FROM SIGNAL TO RELEASE',detail:'One timeline. Every layer. Reviewable decisions.'},transform:{x:64,y:74}},
  {id:'signal',component:'orbit-map',start:30,duration:480,props:{text:'Intake → reproduce → verify'},transform:{x:64,y:230},tracks:[{kind:'spring',property:'transform.x',from:-300,to:64,mass:1,stiffness:90,damping:20}]},
  {id:'evidence',component:'metric-card',start:90,duration:450,props:{text:'EVIDENCE',value:0},transform:{x:620,y:230},tracks:[{kind:'keyframes',property:'props.value',keys:[{time:0,value:0},{time:12,value:100}],easing:'smooth'}]}
 ]},
 {version:2,title:'A small solar system',fps:{numerator:30000,denominator:1001},durationFrames:600,sourceRevision:'orbit-v1',clips:[
  {id:'sun',component:'title-card',start:0,duration:600,props:{text:'ORBITS, FROM CODE',detail:'Parent-local time · deterministic geometry'},transform:{x:64,y:64}},
  {id:'system',component:'orbit-map',start:0,duration:600,props:{text:'A sampled orbital diagram'},transform:{x:220,y:240}},
  {id:'moon',component:'metric-card',parent:'system',start:30,duration:500,rate:.5,props:{text:'LOCAL CLOCK',value:0},transform:{x:380,y:20},tracks:[{kind:'keyframes',property:'props.value',keys:[{time:0,value:0},{time:8,value:8}]}]}
 ]},
 {version:2,title:'A measured greenhouse',fps:{numerator:30,denominator:1},durationFrames:600,sourceRevision:'garden-v1',clips:[
  {id:'garden',component:'title-card',start:0,duration:600,props:{text:'GROWTH, MADE VISIBLE',detail:'An original abstract greenhouse study'},transform:{x:64,y:64}},
  {id:'growth',component:'growth-chart',start:0,duration:600,props:{text:'Sampled growth'},transform:{x:64,y:240},tracks:[{kind:'keyframes',property:'props.value',keys:[{time:0,value:.1},{time:18,value:1}],easing:'smooth'}]},
  {id:'label',component:'metric-card',start:180,duration:420,props:{text:'LIGHT CYCLE',value:12},transform:{x:620,y:240},tracks:[{kind:'path',property:'position',duration:10,points:[[620,240],[650,260],[620,240]]}]}
 ]}
];
const svgNS='http://www.w3.org/2000/svg';
export function registerExamples(registry){
 const base={dependencies:[],sample:s=>s,mount(host){const el=host.ownerDocument.createElement('section');el.className='motion-part';el.style.position='absolute';host.append(el);return el;},async ready(el,signal){await el.ownerDocument.fonts?.ready;if(signal.aborted)throw Error('Aborted');},dispose:el=>el.remove()};
 const pose=(el,s)=>{el.dataset.part=s.id;el.style.transform=`matrix(${s.worldMatrix.join(',')})`;el.style.opacity=s.opacity;el.style.zIndex=s.zIndex;};
 registry.register('title-card',{...base,update(el,s){pose(el,s);el.style.width='940px';el.replaceChildren();const h=el.ownerDocument.createElement('h1'),p=el.ownerDocument.createElement('p');h.textContent=s.props.text;h.style.fontSize=String(s.props.fontSize??44)+'px';h.style.maxWidth='940px';p.textContent=s.props.detail;el.append(h,p);}});
 registry.register('metric-card',{...base,update(el,s){pose(el,s);el.classList.add('metric');el.textContent=`${s.props.text}\n${Number(s.props.value??0).toFixed(1)}`;}});
 registry.register('orbit-map',{...base,update(el,s){pose(el,s);el.replaceChildren();const svg=el.ownerDocument.createElementNS(svgNS,'svg');svg.setAttribute('viewBox','0 0 460 240');svg.setAttribute('role','img');svg.setAttribute('aria-label',s.props.text);const node=(tag,attrs)=>{const n=el.ownerDocument.createElementNS(svgNS,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,String(v));svg.append(n);};node('ellipse',{cx:230,cy:120,rx:200,ry:80,fill:'none',stroke:'#74849d'});node('circle',{cx:230,cy:120,r:s.props.radius??28,fill:s.props.color??'#f8b454'});const angle=s.localTime*.8;node('circle',{cx:230+200*Math.cos(angle),cy:120+80*Math.sin(angle),r:14,fill:'#a3bfff'});el.append(svg);}});
 registry.register('growth-chart',{...base,update(el,s){pose(el,s);el.replaceChildren();const svg=el.ownerDocument.createElementNS(svgNS,'svg');svg.setAttribute('viewBox','0 0 460 240');svg.setAttribute('role','img');svg.setAttribute('aria-label',s.props.text);for(let i=0;i<7;i++){const r=el.ownerDocument.createElementNS(svgNS,'rect');r.setAttribute('x',String(i*60));const h=(35+i*23)*(s.props.value??.1);r.setAttribute('y',String(240-h));r.setAttribute('width','40');r.setAttribute('height',String(h));r.setAttribute('rx','8');r.setAttribute('fill',i%2?'#a3bfff':'#8fe0b1');svg.append(r);}el.append(svg);}});
 return registry;
}
