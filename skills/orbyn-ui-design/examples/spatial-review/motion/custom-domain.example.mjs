// This is reviewed trusted source, supplied explicitly through --component-source.
// The JSON cannot name or import it. Its only dependency is packaged local source.
import {frameTime} from './time.mjs';
export function registerCustomComponents(registry) {
  registry.register('tidal-observatory',{
    dependencies:[{path:'motion/time.mjs',kind:'packaged-source'}],
    sample(clip){return{...clip,wave:clip.reducedMotion?0:Math.sin(clip.localTime*2)*10,clock:frameTime(Math.floor(Math.max(0,clip.localFrame)),{numerator:30000,denominator:1001})};},
    mount(host){const el=host.ownerDocument.createElement('section');el.className='motion-part';el.style.width='940px';el.style.position='absolute';host.append(el);return el;},
    update(el,state){
      el.replaceChildren();el.dataset.part=state.id;el.style.transform=`matrix(${state.worldMatrix.join(',')})`;
      const doc=el.ownerDocument,title=doc.createElement('h1'),copy=doc.createElement('p');
      title.textContent=state.props.label;copy.textContent='An original source-defined coastal instrument. Inert parameters. One rational clock.';
      const svg=doc.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 900 280');svg.style.width='900px';svg.style.height='280px';svg.setAttribute('role','img');svg.setAttribute('aria-label',`Illustrative tide ${state.props.height}; not measured weather`);
      for(let i=0;i<10;i++){
        const bar=doc.createElementNS(svg.namespaceURI,'rect'),height=state.props.height+state.wave*Math.sin(i*.6);
        for(const[k,v]of Object.entries({x:i*88,y:260-height,width:64,height,rx:12,fill:state.props.color}))bar.setAttribute(k,String(v));svg.append(bar);
      }
      const readout=doc.createElement('p');readout.textContent=`FRAME ${Math.floor(state.localFrame)} / TIME ${state.clock.toFixed(3)}s · illustrative tide ${state.props.height}`;el.append(title,copy,svg,readout);
    },
    async ready(el,signal){await el.ownerDocument.fonts.ready;if(signal.aborted)throw Error('Aborted');},
    dispose:el=>el.remove()
  });
  return registry;
}
