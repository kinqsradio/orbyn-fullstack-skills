#!/usr/bin/env node
// Trusted local build, not a JSON-provided import path or downloaded authoring app.
import { mkdir, readFile, writeFile, stat, readdir } from 'node:fs/promises';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
const here = dirname(fileURLToPath(import.meta.url));
const digest = data => createHash('sha256').update(data).digest('hex');
const usage = 'node graphics/build-profile.mjs --profile /ABS/prepared-local-dependencies --out /ABS/new-local-profile';
if (process.argv.length !== 6 || process.argv[2] !== '--profile' || process.argv[4] !== '--out') { console.error(usage); process.exitCode = 2; }
else {
  const dependencies = resolve(process.argv[3]), out = resolve(process.argv[5]);
  try {
    if (!(await stat(dirname(out))).isDirectory()) throw Error('Existing output parent required');
    const { build } = await import(pathToFileURL(join(dependencies, 'node_modules/esbuild/lib/main.js')).href);
    const profile = JSON.parse(await readFile(join(here, 'package.json'))), lock = await readFile(join(here, 'package-lock.json'));
    if (digest(await readFile(join(dependencies, 'package-lock.json'))) !== digest(lock)) throw Error('Installed profile lock differs from reviewed source lock');
    for (const [name, version] of Object.entries({ ...profile.dependencies, ...profile.devDependencies })) if (JSON.parse(await readFile(join(dependencies, 'node_modules', name, 'package.json'))).version !== version) throw Error('Installed dependency version mismatch: ' + name);
    const receipts = { version: 1, status: 'building', lockSha256: digest(lock), builderSha256: digest(await readFile(fileURLToPath(import.meta.url))), node: process.version, dependencies: profile.dependencies, files: {}, limits: ['No Draco/Meshopt/KTX2 decoder assets included', 'No external textures, fonts, denoiser weights or hosted services', 'Jolt single-thread embedded-WASM profile; no SharedArrayBuffer isolation requirement', 'A built module is not GPU/native quality qualification'] };
    await mkdir(out); // exclusive, preserving earlier qualified profiles
    const inputs = {
      'vendor-raster.mjs': "import * as THREE from 'three'; import * as postprocessing from 'postprocessing'; import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'; import {OrbitControls} from 'three/addons/controls/OrbitControls.js'; import {WebGLPathTracer} from 'three-gpu-pathtracer'; export {THREE,postprocessing,GLTFLoader,OrbitControls,WebGLPathTracer};",
      'vendor-webgpu.mjs': "import * as THREE from 'three/webgpu'; import {WebGPUPathTracer} from 'three-gpu-pathtracer/webgpu'; export {THREE,WebGPUPathTracer};",
      'vendor-jolt.mjs': "export {default as initJolt} from 'jolt-physics/wasm-compat';"
    };
    for (const [name, source] of Object.entries(inputs)) {
      const result = await build({ stdin: { contents: source, resolveDir: dependencies, sourcefile: name + '.entry.js' }, outfile: join(out, name), bundle: true, format: 'esm', platform: 'browser', target: 'es2022', minify: true, legalComments: 'external', metafile: true, external: ['node:*', 'fs', 'path', 'url', 'module'], write: true, logLevel: 'silent' });
      receipts[name] = { entrySha256: digest(source), inputs: Object.keys(result.metafile.inputs).length };
    }
    let notices = '# Optional code-driven graphics profile licenses\n\nNo original upstream authorship is claimed. Modules are unmodified dependency builds; Orbyn owns the adapters and build orchestration. Package tarball integrity is in package-lock.json.\n';
    for (const name of Object.keys(profile.dependencies)) {
      const directory = join(dependencies, 'node_modules', name), packageData = JSON.parse(await readFile(join(directory, 'package.json')));
      const license = (await readdir(directory)).find(n => /^license(?:\.(?:md|txt))?$/i.test(n));
      if (!license) throw Error('Dependency license missing: ' + name);
      notices += `\n## ${name}@${packageData.version} (${packageData.license})\n\n` + await readFile(join(directory, license), 'utf8') + '\n';
    }
    await writeFile(join(out, 'NOTICES.md'), notices, { flag: 'wx' });
    let bytes = 0;
    for (const name of await readdir(out)) { const data = await readFile(join(out, name)); bytes += data.length; receipts.files[name] = { sha256: digest(data), bytes: data.length }; }
    if (bytes > 32 * 1024 * 1024) throw Error('Graphics bundle profile exceeds 32 MiB');
    receipts.status = 'built; runtime qualification separate'; receipts.totalBytes = bytes;
    await writeFile(join(out, 'profile.json'), JSON.stringify(receipts, null, 2) + '\n', { flag: 'wx' });
    console.log(JSON.stringify({ output: out, files: Object.keys(receipts.files).length, bytes, status: receipts.status }));
  } catch (error) { console.error(error.message); process.exitCode = 2; }
}
