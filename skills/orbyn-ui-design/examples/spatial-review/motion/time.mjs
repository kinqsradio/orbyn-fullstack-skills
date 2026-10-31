// Original exact rational clock. Integer frame/sample addresses are canonical.
const integer = (n, low = 0) => { if (!Number.isSafeInteger(n) || n < low) throw Error('Expected bounded integer'); return n; };
const gcd = (a,b) => b ? gcd(b,a%b) : a;
export function rate(value) {
  const r = typeof value === 'number' ? {numerator:value,denominator:1} : value;
  if (!r || Object.keys(r).sort().join() !== 'denominator,numerator') throw Error('Invalid rational rate');
  integer(r.numerator,1); integer(r.denominator,1);
  if (r.numerator/r.denominator < 1 || r.numerator/r.denominator > 240 || r.numerator > 1000000 || r.denominator > 1000000) throw Error('Rate budget');
  const d=gcd(r.numerator,r.denominator); return {numerator:r.numerator/d,denominator:r.denominator/d};
}
export function frameTime(frame,fps) { integer(frame); const r=rate(fps); return frame*r.denominator/r.numerator; }
export function timeFrame(seconds,fps,round='floor') {
  if (!Number.isFinite(seconds)||seconds<0||!['floor','ceil','round'].includes(round)) throw Error('Invalid time/round');
  const r=rate(fps), result=Math[round](seconds*r.numerator/r.denominator); return integer(result);
}
export function audioSample(frame,fps,sampleRate,round='round') {
  integer(frame); integer(sampleRate,1); if (!['floor','ceil','round'].includes(round)) throw Error('Invalid rounding');
  const r=rate(fps), a=BigInt(frame)*BigInt(r.denominator)*BigInt(sampleRate), b=BigInt(r.numerator);
  const q=a/b, rem=a%b, v=q+(round==='ceil'&&rem>0n||round==='round'&&2n*rem>=b?1n:0n);
  if(v>BigInt(Number.MAX_SAFE_INTEGER)) throw Error('Sample address overflow'); return Number(v);
}
export function frameFraction(frame,fps) { integer(frame); const r=rate(fps), a=BigInt(frame)*BigInt(r.denominator), b=BigInt(r.numerator); return {numerator:a.toString(),denominator:b.toString()}; }
