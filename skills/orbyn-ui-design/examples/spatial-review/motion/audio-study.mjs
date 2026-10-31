// Analysis is inert, source-bound project data. Runtime loads no model or audio.
import {audioBarsComponent} from './audio.mjs';
export function registerCustomComponents(registry){
 return registry.register('audio-energy',audioBarsComponent()).register('original-artwork',{
  dependencies:[{kind:'local-raster',path:'media/gallery.png'}],
  sample(clip){return{time:clip.localTime,reducedMotion:clip.reducedMotion};},
  mount(host){const image=host.ownerDocument.createElement('img');image.src=new URL('../media/gallery.png',import.meta.url).href;image.alt='Original code-generated abstract scenery; moving artwork, not character animation';Object.assign(image.style,{position:'absolute',inset:'0',width:'100%',height:'100%',objectFit:'cover',opacity:'.3'});host.append(image);return image;},
  update(image,state){image.style.transform=`scale(${state.reducedMotion?1.05:1.05+state.time*.008})`;},
  async ready(image,signal){await image.decode();if(signal.aborted)throw Error('Artwork readiness cancelled');},
  dispose(image){image.remove();}
 });
}
