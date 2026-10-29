export const title = 'Lease-fenced job: durable state and two delivery slots';
export const state = v => ({
  Job: `${v.phase}, epoch ${v.generation}${v.resultGeneration ? `, result ${v.resultGeneration}` : ''}${v.publishCount ? ', published' : ''}${v.lateCancel ? ', cancel too late' : ''}`,
  Worker1: v.tokens[1] ? `holds epoch ${v.tokens[1]}` : 'free',
  Worker2: v.tokens[2] ? `holds epoch ${v.tokens[2]}` : 'free',
});
// Do not use custom brackets: the compiler retains other-region guards.
export const step = (action, from, to) => {
  if (action === 'Claim') return `worker ${to.owner} claims`;
  if (action === 'Complete') {
    const worker = [1, 2].find(w => from.tokens[w] !== to.tokens[w]);
    return to.resultGeneration !== from.resultGeneration ? `worker ${worker} commits` : `worker ${worker} delivery rejected`;
  }
  return ({ Claim1: 'worker 1 claims', Claim2: 'worker 2 claims', Expire: 'lease expires',
    Cancel: 'cancel before commit', LateCancel: 'cancel arrives too late', Publish: 'publish once', Terminal: 'terminal stutter' })[action] ?? action;
};
