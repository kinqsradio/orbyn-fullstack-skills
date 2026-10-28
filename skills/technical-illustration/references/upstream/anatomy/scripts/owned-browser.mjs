import { spawn } from 'node:child_process';
import { rmSync } from 'node:fs';

// Only a child handle/profile created by this invocation may be passed here.
export async function stopOwnedChrome(child, profile, { graceMs = 2000, limitMs = 5000 } = {}) {
  if (child.exitCode === null && child.signalCode === null) {
    await new Promise((resolve) => {
      const timer = setTimeout(() => child.kill('SIGKILL'), graceMs);
      const limit = setTimeout(() => { clearTimeout(timer); resolve(); }, limitMs);
      child.once('exit', () => { clearTimeout(timer); clearTimeout(limit); resolve(); });
      child.kill('SIGTERM');
    });
  }
  if (child.exitCode === null && child.signalCode === null) throw new Error('Owned Chrome still alive; profile retained');
  if (profile) rmSync(profile, { recursive: true, force: true });
  owned.delete(child);
  if (!owned.size) {
    for (const [signal, handler] of handlers) process.removeListener(signal, handler);
    handlers.clear();
  }
}

const owned = new Map();
let handlingSignal = false;
const handlers = new Map();

export function ownBrowser(child, profile, options = {}) {
  owned.set(child, { profile, options });
  if (!handlers.size) {
    for (const signal of ['SIGINT', 'SIGTERM']) {
      const handler = async () => {
        if (handlingSignal) return;
        handlingSignal = true;
        const records = [...owned];
        const results = await Promise.allSettled(records.map(([handle, record]) => stopOwnedChrome(handle, record.profile, record.options)));
        for (const [, record] of records) if (record.options.retainedDirectory) console.error('Retained owned output directory:', record.options.retainedDirectory);
        for (const result of results) if (result.status === 'rejected') console.error('Owned browser cleanup incomplete; profile retained:', result.reason);
        process.exit(signal === 'SIGINT' ? 130 : 143);
      };
      handlers.set(signal, handler);
      process.once(signal, handler);
    }
  }
}

// Async printed/captured subprocesses must remain interruptible while waiting.
export async function runOwned(binary, args, { timeout = 120000, stdio = ['ignore', 'pipe', 'pipe'], nested = false, retainedDirectory = null } = {}) {
  const child = spawn(binary, args, { stdio });
  const cleanup = nested ? { graceMs: 6000, limitMs: 9000 } : {};
  ownBrowser(child, null, { ...cleanup, retainedDirectory }); // Caller owns retained staging/log directories.
  let stdout = '', stderr = '', timer;
  child.stdout?.on('data', chunk => { stdout = (stdout + chunk).slice(-(1 << 26)); });
  child.stderr?.on('data', chunk => { stderr = (stderr + chunk).slice(-(1 << 20)); });
  const done = new Promise((resolve, reject) => {
    child.once('error', reject);
    child.once('close', (status, signal) => resolve({ status, signal }));
  });
  try {
    const terminal = await Promise.race([done, new Promise((_, reject) => { timer = setTimeout(() => reject(new Error(`Owned process deadline ${timeout} ms exceeded`)), timeout); })]);
    return { ...terminal, stdout, stderr };
  } finally {
    clearTimeout(timer);
    await stopOwnedChrome(child, null, cleanup);
  }
}
