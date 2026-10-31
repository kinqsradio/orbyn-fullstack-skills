// A bounded live-layout owner. It never writes transforms on sampled scene parts.
export function layoutDelta(before, after, {beforeScroll={x:0,y:0},afterScroll={x:0,y:0}}={}) {
  for(const box of [before,after]) {
    if(!box||!['left','top','width','height'].every(k=>Number.isFinite(box[k]))||box.width<=0||box.height<=0) throw Error('Invalid layout rectangle');
  }
  for(const scroll of [beforeScroll,afterScroll])if(!Number.isFinite(scroll.x)||!Number.isFinite(scroll.y))throw Error('Invalid scroll');
  return {x:before.left+beforeScroll.x-after.left-afterScroll.x,y:before.top+beforeScroll.y-after.top-afterScroll.y,scaleX:before.width/after.width,scaleY:before.height/after.height};
}
export function createLayoutOwner() {
  const owned=new Map();let generation=0,disposed=false;
  return {
    update(elements,mutate,{reducedMotion=false,duration=240}={}) {
      if(disposed||!Number.isFinite(duration)||duration<0||duration>2000||!Array.isArray(elements)||elements.length>100)throw Error('Invalid layout update');
      const token=++generation,scroll={x:globalThis.scrollX??0,y:globalThis.scrollY??0};
      const before=elements.map(el=>el.getBoundingClientRect());
      for(const animation of owned.values())animation.cancel();owned.clear();
      mutate();
      elements.forEach((el,index)=>{
        const delta=layoutDelta(before[index],el.getBoundingClientRect(),{beforeScroll:scroll,afterScroll:{x:globalThis.scrollX??0,y:globalThis.scrollY??0}});
        if(reducedMotion||!duration)return;
        const animation=el.animate([{transformOrigin:'0 0',transform:`translate(${delta.x}px,${delta.y}px) scale(${delta.scaleX},${delta.scaleY})`},{transformOrigin:'0 0',transform:'none'}],{duration,easing:'cubic-bezier(.2,.7,.2,1)'});
        owned.set(el,animation);
        animation.finished.then(()=>{if(token===generation&&owned.get(el)===animation)owned.delete(el);},()=>{});
      });
    },
    cancel(){generation++;for(const animation of owned.values())animation.cancel();owned.clear();},
    dispose(){disposed=true;this.cancel();}
  };
}
