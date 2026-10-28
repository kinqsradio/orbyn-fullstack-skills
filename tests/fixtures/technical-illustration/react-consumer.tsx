import * as React from 'react';
import { useReadout, useStillness } from './support/kit/react/live';

declare global { interface Window { hydrated?: boolean; oldSay?: (value: string) => void } }
export function Figure({ id, initial }: { id: string; initial: number }) {
  const [value, setValue] = React.useState(initial);
  const { anchor, say } = useReadout<HTMLDivElement>();
  const calm = useStillness();
  React.useLayoutEffect(() => { say(value + ' tokens'); }, [value, say]);
  React.useEffect(() => { if (id === 'a') window.oldSay = say; }, [id, say]);
  return <section id={id} className="iso-plate"><h2>Bucket {id.toUpperCase()}</h2>
    <span data-readout>{initial} tokens</span><div ref={anchor}>
      <button onClick={() => setValue(v => v + 1)}>Add token</button>
      <svg viewBox="0 0 200 90" role="img" aria-label={value + ' tokens'}><rect x="12" y="12" width={value * 5} height="50" fill="#416caa" /></svg>
      <p>{calm ? 'Reduced motion: controls remain available' : 'Interactive model'}</p>
    </div></section>;
}
export interface ReadyGate { ready: boolean; pending: Promise<void> }
function Deferred({ gate }: { gate?: ReadyGate }) { if (gate && !gate.ready) throw gate.pending; return <p id="streamed">Streamed explanation arrived.</p>; }
export function App({ showA = true, gate }: { showA?: boolean; gate?: ReadyGate }) {
  React.useEffect(() => { window.hydrated = true; }, []);
  return <><h1>Two independent model readouts</h1>{showA ? <Figure id="a" initial={10} /> : null}<Figure id="b" initial={20} />
    <React.Suspense fallback={<p>Preparing explanation…</p>}><Deferred gate={gate} /></React.Suspense></>;
}
