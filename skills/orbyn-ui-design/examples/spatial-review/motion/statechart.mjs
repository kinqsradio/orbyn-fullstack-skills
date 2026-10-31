// Animate supplied chart occurrences; this is neither a model checker nor a trace inference engine.
const finite=(v,min,max)=>typeof v==='number'&&Number.isFinite(v)&&v>=min&&v<=max;
const identifier=v=>typeof v==='string'&&/^[a-zA-Z][a-zA-Z0-9_.-]{0,79}$/.test(v);
const text=(v,max)=>typeof v==='string'&&v.trim().length>0&&v.length<=max;
export function validateTrace(chart) {
  if (!chart || !finite(chart.width,100,10000) || !finite(chart.height,100,10000) || !text(chart.title,200) ||
      !Array.isArray(chart.nodes) || !Array.isArray(chart.edges) || !Array.isArray(chart.trace) ||
      chart.nodes.length<1 || chart.nodes.length>100 || chart.edges.length>250 || chart.trace.length<1 || chart.trace.length>250) throw Error('Chart/trace budget');
  if(chart.evidence!==undefined&&!text(chart.evidence,20000))throw Error('Invalid evidence text');
  const nodes=new Map(chart.nodes.map(n=>[n.id,n])),edges=new Map(chart.edges.map(e=>[e.id,e]));
  if(nodes.size!==chart.nodes.length||edges.size!==chart.edges.length)throw Error('Duplicate chart identity');
  for(const n of chart.nodes){
    if(!identifier(n.id)||!finite(n.x,0,chart.width)||!finite(n.y,0,chart.height)||
        !finite(n.width,1,chart.width)||!finite(n.height,1,chart.height)||n.x+n.width>chart.width||n.y+n.height>chart.height||!text(n.title,160))throw Error('Node identity/geometry');
  }
  for(const e of chart.edges){
    if(!identifier(e.id)||!nodes.has(e.from)||!nodes.has(e.to)||!text(e.label,500)||
        e.guard!==undefined&&!text(e.guard,1000)||!Array.isArray(e.points)||e.points.length<2||e.points.length>100||
        e.points.some(p=>!Array.isArray(p)||p.length!==2||!finite(p[0],0,chart.width)||!finite(p[1],0,chart.height))||
        e.labelX!==undefined&&!finite(e.labelX,0,chart.width)||e.labelY!==undefined&&!finite(e.labelY,0,chart.height))throw Error('Edge record/geometry');
  }
  chart.trace.forEach((o,i)=>{
    if(o.step!==i||!nodes.has(o.node)||i===0&&o.edge!==undefined)throw Error('Occurrence identity');
    if(i>0){const e=edges.get(o.edge);if(!e||e.from!==chart.trace[i-1].node||e.to!==o.node)throw Error('Trace edge must connect exact consecutive occurrences');}
  });
  return chart;
}

export function sampleTrace(chart,time,{stepSeconds=1,reducedMotion=false}={}) {
  validateTrace(chart);
  if(typeof reducedMotion!=='boolean'||!Number.isFinite(time)||time<0||!finite(stepSeconds,.001,3600))throw Error('Invalid trace time');
  const index=Math.min(chart.trace.length-1,reducedMotion?chart.trace.length-1:Math.floor(time/stepSeconds));
  return {index,occurrence:{...chart.trace[index]},visited:chart.trace.slice(0,index+1).map(o=>({...o})),evidence:chart.evidence??'Supplied chart; no checker result inferred'};
}
export function statechartComponent(){const ns='http://www.w3.org/2000/svg';return{
  dependencies:[],
  sample(clip){const chart=validateTrace(clip.props.chart);return{...clip,trace:sampleTrace(chart,Math.max(0,clip.localTime),{stepSeconds:clip.props.stepSeconds??1,reducedMotion:clip.reducedMotion})};},
  mount(host){const el=host.ownerDocument.createElement('figure');host.append(el);return el;},
  update(el,state){const chart=state.props.chart,doc=el.ownerDocument;el.replaceChildren();el.dataset.part=state.id;el.style.transform=`matrix(${state.worldMatrix.join(',')})`;el.style.opacity=state.opacity;
    const svg=doc.createElementNS(ns,'svg');svg.setAttribute('viewBox',`0 0 ${chart.width} ${chart.height}`);svg.setAttribute('role','img');svg.setAttribute('aria-label',`${chart.title}; occurrence ${state.trace.index}: ${state.trace.occurrence.node}`);
    const append=(tag,attrs,text)=>{const n=doc.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,String(v));if(text!==undefined)n.textContent=text;svg.append(n);return n;};
    for(const e of chart.edges){append('polyline',{points:e.points.map(p=>p.join(',')).join(' '),fill:'none',stroke:e.id===state.trace.occurrence.edge?'#e4a05a':'#71829b','stroke-width':e.id===state.trace.occurrence.edge?7:3});append('text',{x:e.labelX??e.points[0][0],y:e.labelY??e.points[0][1],fill:'#eef3ff','font-size':18},`${e.label}${e.guard?' ['+e.guard+']':''}`);}
    for(const n of chart.nodes){append('rect',{x:n.x,y:n.y,width:n.width,height:n.height,rx:12,fill:n.id===state.trace.occurrence.node?'#395d78':'#24344d',stroke:'#a7b9ce'});append('text',{x:n.x+12,y:n.y+28,fill:'#fff','font-size':18},n.title);}
    const caption=doc.createElement('figcaption');caption.textContent=`Occurrence ${state.trace.index}: ${state.trace.occurrence.node}. ${state.trace.evidence}`;
    const details=doc.createElement('details'),summary=doc.createElement('summary'),records=doc.createElement('pre');summary.textContent='Full nodes, guards, edges and numbered occurrences';records.textContent=JSON.stringify(chart,null,2);details.append(summary,records);el.append(svg,caption,details);
  },
  async ready(_el,signal){if(signal.aborted)throw Error('Aborted');},dispose:el=>el.remove()
};}
