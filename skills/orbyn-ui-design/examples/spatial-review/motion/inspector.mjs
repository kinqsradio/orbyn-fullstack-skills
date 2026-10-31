import {inert} from './composition.mjs';

// Transient edits and committed decisions share one authoritative model. The
// caller supplies its existing source-bound writer; this creates no second store.
export function createInspector(initial, {validate=inert,onChange=()=>{},save=async()=>{}}={}) {
  validate(initial);
  const baseline=structuredClone(initial);
  let value=structuredClone(initial), undo=[], redo=[], transient=null;
  let generation=0, disposed=false;
  const copy=()=>structuredClone(value);
  const emit=()=>onChange(copy());
  const available=()=>{if(disposed)throw Error('Inspector disposed');};
  function commit(next) {
    available(); validate(next);
    if(JSON.stringify(next)===JSON.stringify(value))return;
    undo.push(copy()); if(undo.length>100)undo.shift();
    redo=[]; value=structuredClone(next); transient=null; generation++; emit();
  }
  return {
    get value(){return copy();},
    get generation(){return generation;},
    begin(){available();if(transient)throw Error('Already editing');transient=copy();generation++;},
    preview(next){available();if(!transient)throw Error('Begin editing first');validate(next);value=structuredClone(next);emit();},
    commit(next=value){
      available();validate(next);
      if(transient){value=transient;transient=null;}
      commit(next);
    },
    cancel(){available();if(transient){value=transient;transient=null;generation++;emit();}},
    undo(){
      available();if(transient)throw Error('Finish transient edit');
      if(undo.length){redo.push(copy());value=undo.pop();generation++;emit();}
    },
    redo(){
      available();if(transient)throw Error('Finish transient edit');
      if(redo.length){undo.push(copy());value=redo.pop();generation++;emit();}
    },
    reset(){available();if(transient){value=transient;transient=null;}commit(baseline);},
    async save(){
      available();if(transient)throw Error('Finish edit first');
      const version=generation,snapshot=copy();
      const result=await save(snapshot,version);
      if(disposed||version!==generation)throw Error('Stale save completion');
      return result;
    },
    dispose(){disposed=true;generation++;transient=null;}
  };
}

// Live integration preserves velocity across takeover. Offline export uses the
// analytic sampled track instead, independent of the UI's wall-clock history.
export function createLiveSpring(value=0,{stiffness=180,damping=26,mass=1}={}) {
  if(![value,stiffness,damping,mass].every(Number.isFinite)||
      [stiffness,damping,mass].some(v=>v<.0001||v>1e6))throw Error('Invalid live spring');
  let x=value,v=0,target=value;
  return {
    target(next){if(!Number.isFinite(next))throw Error('Invalid target');target=next;},
    sample(){return{x,velocity:v,target};},
    step(dt){
      if(!Number.isFinite(dt)||dt<0||dt>.25)throw Error('Invalid delta');
      const steps=Math.max(1,Math.ceil(dt/.004)),h=dt/steps;
      for(let i=0;i<steps;i++){
        v+=(-stiffness*(x-target)-damping*v)/mass*h;x+=v*h;
        if(!Number.isFinite(x)||!Number.isFinite(v))throw Error('Live spring numerical overflow');
      }
      return{x,velocity:v,target};
    },
    snap(next){if(!Number.isFinite(next))throw Error('Invalid value');x=target=next;v=0;}
  };
}

export function createPresence({onExit=()=>{}}={}) {
  let state='closed',generation=0;
  return {
    open(){state='open';return++generation;},
    close(){state='exiting';return++generation;},
    completeExit(token){
      if(state!=='exiting'||token!==generation)return false;
      state='closed';onExit();return true;
    },
    get state(){return state;},get generation(){return generation;}
  };
}

export function createDrag() {
  let owner=null;
  return {
    begin(pointerId,position){
      if(owner!==null||!Number.isInteger(pointerId)||!Number.isFinite(position))return false;
      owner={id:pointerId,start:position};return true;
    },
    move(pointerId,position){return owner?.id===pointerId&&Number.isFinite(position)?position-owner.start:null;},
    end(pointerId){if(owner?.id!==pointerId)return false;owner=null;return true;},
    cancel(){owner=null;},get active(){return owner!==null;}
  };
}
