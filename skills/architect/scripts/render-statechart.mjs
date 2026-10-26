#!/usr/bin/env node
// Orbyn adapter. The explicitly supplied trusted Pele module owns rendering.
import { readFile, stat, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const usage = 'Usage: node render-statechart.mjs --input flow.mmd --output flow.svg --pele /trusted/installed/pele/dist/pele.js';

async function main(args) {
  if (args.length === 1 && args[0] === '--help') {
    console.log(`${usage}\nNo installation or network access. Output must be new. Rendering does not verify behavior.`);
    return;
  }
  const options = {};
  for (let i = 0; i < args.length; i += 2) {
    const key = args[i];
    if (!['--input', '--output', '--pele'].includes(key) || !args[i + 1] || options[key]) {
      throw new Error(usage);
    }
    options[key] = args[i + 1];
  }
  if (Object.keys(options).length !== 3) throw new Error(usage);
  const input = resolve(options['--input']);
  const output = resolve(options['--output']);
  const modulePath = resolve(options['--pele']);
  if (!output.endsWith('.svg') || output === input || output === modulePath) {
    throw new Error('Choose a new .svg output distinct from input and renderer.');
  }
  const info = await stat(input);
  if (!info.isFile() || info.size > 262144) throw new Error('Input must be a regular file up to 256 KiB.');
  const source = await readFile(input, 'utf8');
  const { render } = await import(pathToFileURL(modulePath).href);
  if (typeof render !== 'function') throw new Error('Renderer must export render(source).');
  const result = render(source);
  if (typeof result?.svg !== 'string' || !/<svg(?:\s|>)/.test(result.svg) || Buffer.byteLength(result.svg) > 8388608) {
    throw new Error('Renderer did not return an SVG within the 8 MiB limit.');
  }
  // Exclusive creation preserves earlier captures and refuses symlink destinations.
  await writeFile(output, result.svg, { flag: 'wx' });
  console.log(JSON.stringify({ input, output, renderer: modulePath, result: 'rendered; behavior unverified' }));
}

main(process.argv.slice(2)).catch(error => {
  console.error(error.message);
  process.exitCode = 1;
});
