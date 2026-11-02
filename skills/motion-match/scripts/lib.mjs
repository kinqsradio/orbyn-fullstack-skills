// Shared helpers for the motion-match scripts. Node 22 standard library only.
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readdirSync, readFileSync, realpathSync, renameSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { basename, dirname, isAbsolute, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const RIGHTS = ['own', 'licensed', 'third-party'];
export const FIDELITY = ['motion', 'pixel'];
export const EXIT = { ok: 0, failed: 1, usage: 2, blocked: 3 };

export class UsageError extends Error {}
// A rights or access limit stopped the run. Exit 3 so a caller cannot mistake it for a bad flag.
export class BlockedError extends Error {}

export function isMain(url) {
  return !!process.argv[1] && realpathSync(process.argv[1]) === fileURLToPath(url);
}

export function runCli(main) {
  Promise.resolve().then(main).then(
    (code) => { process.exitCode = code ?? EXIT.ok; },
    (error) => {
      console.error(error instanceof Error ? error.message : String(error));
      process.exitCode = error instanceof UsageError ? EXIT.usage : error instanceof BlockedError ? EXIT.blocked : EXIT.failed;
    },
  );
}

/**
 * Strict parser: unknown or repeated flags and invalid numbers stop the run.
 * Schema values are 'string', 'flag', or { type: 'number', min, max, integer }.
 */
export function parseArgs(argv, schema, { positionals = 0 } = {}) {
  const out = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const item = argv[i];
    if (!item.startsWith('--')) {
      if (out._.length >= positionals) throw new UsageError(`Unexpected argument: ${item}`);
      out._.push(item);
      continue;
    }
    const eq = item.indexOf('=');
    const name = eq > 0 ? item.slice(2, eq) : item.slice(2);
    const kind = name === 'help' ? 'flag' : schema[name];
    if (!kind) throw new UsageError(`Unknown option: --${name}`);
    if (name in out) throw new UsageError(`Repeated option: --${name}`);
    if (kind === 'flag') {
      if (eq > 0) throw new UsageError(`--${name} takes no value`);
      out[name] = true;
      continue;
    }
    const raw = eq > 0 ? item.slice(eq + 1) : argv[++i];
    if (raw === undefined || (eq < 0 && raw.startsWith('--'))) throw new UsageError(`--${name} needs a value`);
    out[name] = kind === 'string' ? raw : parseNumber(name, raw, kind);
  }
  return out;
}

function parseNumber(name, raw, { min = -Infinity, max = Infinity, integer = false }) {
  const value = Number(raw);
  if (raw.trim() === '' || !Number.isFinite(value) || value < min || value > max || (integer && !Number.isInteger(value))) {
    const range = `${min === -Infinity ? '' : ` >= ${min}`}${max === Infinity ? '' : ` <= ${max}`}`;
    throw new UsageError(`--${name} must be a ${integer ? 'whole ' : ''}number${range}, got "${raw}"`);
  }
  return value;
}

export function requireOptions(args, names) {
  const missing = names.filter((name) => args[name] === undefined);
  if (missing.length) throw new UsageError(`Missing ${missing.map((name) => `--${name}`).join(', ')} (see --help)`);
}

export function oneOf(name, value, allowed) {
  if (!allowed.includes(value)) throw new UsageError(`--${name} must be one of ${allowed.join(', ')}, got "${value}"`);
  return value;
}

export function parseSize(value, fallback) {
  if (value === undefined) return fallback;
  const match = String(value).match(/^(\d{1,5})x(\d{1,5})$/);
  if (!match || !Number(match[1]) || !Number(match[2])) throw new UsageError(`Bad size "${value}", expected WxH`);
  return { width: Number(match[1]), height: Number(match[2]) };
}

export function parseRect(value) {
  if (value === undefined) return undefined;
  const parts = String(value).split(',').map(Number);
  if (parts.length !== 4 || parts.some((part) => !Number.isFinite(part)) || parts[0] < 0 || parts[1] < 0 || parts[2] <= 0 || parts[3] <= 0) {
    throw new UsageError(`Bad rectangle "${value}", expected x,y,w,h`);
  }
  return { x: parts[0], y: parts[1], width: parts[2], height: parts[3] };
}

/** "1:23.5" | "83.5" | "83.5s" | "1500ms" -> seconds */
export function parseTime(value) {
  if (value === undefined) return undefined;
  const text = String(value).trim();
  const seconds = text.endsWith('ms') ? Number(text.slice(0, -2)) / 1000
    : text.includes(':') ? text.split(':').reduce((sum, part) => sum * 60 + Number(part), 0)
    : Number(text.replace(/s$/, ''));
  if (!Number.isFinite(seconds) || seconds < 0) throw new UsageError(`Bad time "${value}"`);
  return seconds;
}

function isInside(root, target) {
  const path = relative(root, target);
  return path === '' || (!path.startsWith(`..${sep}`) && path !== '..' && !isAbsolute(path));
}

/** Resolve through the deepest existing folder, so a symlink cannot walk out of the root. */
function canonical(target) {
  const missing = [];
  let current = target;
  while (!existsSync(current)) {
    missing.unshift(basename(current));
    if (dirname(current) === current) break;
    current = dirname(current);
  }
  return join(realpathSync(current), ...missing);
}

/** Output and supplied script paths must stay under --root, which defaults to the working directory. */
export function pathInside(value, root = '.', label = 'Path') {
  const base = realpathSync(resolve(root));
  const target = canonical(resolve(base, String(value)));
  if (!isInside(base, target)) throw new UsageError(`${label} "${value}" leaves ${base}; pass --root to choose another folder`);
  return target;
}

export function child(folder, name) {
  const target = resolve(folder, name);
  if (!isInside(folder, target) || target === folder) throw new UsageError(`"${name}" leaves ${folder}`);
  return target;
}

/** Create the output folder. Replacing earlier output needs --replace and our own marker file. */
export function prepareOutput(target, { marker, replace = false, keep = [] } = {}) {
  if (existsSync(target)) {
    if (!statSync(target).isDirectory()) throw new UsageError(`Output is not a folder: ${target}`);
    const entries = readdirSync(target).filter((name) => !keep.includes(name));
    if (entries.length) {
      if (!replace) throw new UsageError(`Output is not empty: ${target}. Use a new folder for each round, or pass --replace`);
      if (!marker || !existsSync(join(target, marker))) throw new UsageError(`Refusing to replace ${target}: ${marker ?? 'marker file'} is missing, so this may not be our output`);
      for (const name of entries) rmSync(join(target, name), { recursive: true, force: true });
    }
  }
  mkdirSync(target, { recursive: true });
  return target;
}

export function atomicWrite(path, data) {
  const temp = `${path}.${process.pid}.tmp`;
  writeFileSync(temp, data);
  renameSync(temp, path);
}

export const writeJson = (path, value) => atomicWrite(path, `${JSON.stringify(value, null, 2)}\n`);
export const readJson = (path) => JSON.parse(readFileSync(path, 'utf8'));
export const pad = (value, width = 4) => String(value).padStart(width, '0');

export function listFrames(folder) {
  if (!existsSync(folder) || !statSync(folder).isDirectory()) throw new UsageError(`No frames folder: ${folder}`);
  return readdirSync(folder).filter((name) => /\.png$/i.test(name)).sort().map((name) => join(folder, name));
}

const realFolder = (folder) => (existsSync(folder) ? realpathSync(folder) : resolve(folder));

/**
 * frames.mjs writes frames.json beside the frames; capture.mjs writes it one level up, in a
 * folder named frames with capture.json beside it. Anything else, such as a copy dropped into
 * a capture's output or a link to someone else's frames, must not inherit that record.
 */
export function frameMeta(folder) {
  const real = realFolder(folder);
  const beside = join(real, 'frames.json');
  if (existsSync(beside)) return readJson(beside);
  const parent = dirname(real);
  const captured = basename(real) === 'frames' && existsSync(join(parent, 'capture.json')) && existsSync(join(parent, 'frames.json'));
  return captured ? readJson(join(parent, 'frames.json')) : null;
}

export function captureRecord(folder) {
  const real = realFolder(folder);
  const path = join(dirname(real), 'capture.json');
  return basename(real) === 'frames' && existsSync(path) ? readJson(path) : null;
}

/** Frames without a rights record are treated as someone else's. */
export function rightsOf(folder) {
  const rights = frameMeta(folder)?.rights;
  return RIGHTS.includes(rights) ? rights : 'third-party';
}

/** The names a run really writes, so a pattern that spares one of them cannot slip through. */
const OUTPUT_NAMES = ['capture.json', 'frames.json', 'inspect.json', 'track.json', 'frames/0001.png', 'sheet-01.png', 'sheets/sheet-01.png', 'report.json', 'report.md', 'diff/0001.png', '.rescaled/0001.png', 'spec.json', 'spec.md', 'check.md'];

function gitRoot(folder) {
  for (let at = folder; ; at = dirname(at)) {
    if (existsSync(join(at, '.git'))) return at;
    if (at === dirname(at)) return null;
  }
}

/** Raw third-party material must land somewhere Git will not pick it up. Doubt stops the run. */
export function assertIgnored(target) {
  let folder = target;
  while (!existsSync(folder)) folder = dirname(folder);
  folder = realpathSync(folder);
  if (!gitRoot(folder)) return;
  const env = { ...process.env };
  for (const name of ['GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE']) delete env[name];
  const probes = OUTPUT_NAMES.map((name) => join(target, name));
  const result = spawnSync('git', ['-C', folder, 'check-ignore', '--no-index', '--stdin', '-z'], { encoding: 'utf8', input: probes.join('\0'), env });
  if (result.error || (result.status !== 0 && result.status !== 1)) {
    throw new BlockedError(`Cannot confirm ${target} is ignored by Git, so nothing was written: ${result.error?.message ?? result.stderr.trim()}`);
  }
  const ignored = new Set(result.stdout.split('\0').filter(Boolean));
  const exposed = probes.filter((probe) => !ignored.has(probe));
  if (exposed.length) {
    throw new BlockedError(`${target} is not ignored by Git for ${exposed.length} output file(s), such as ${basename(exposed[0])}. Third-party captures stay in an ignored local folder: add it to .gitignore or choose another folder`);
  }
}

export function resolveFfmpeg(flag) {
  return flag ?? process.env.FFMPEG_PATH ?? 'ffmpeg';
}

export function ffmpeg(binary, args) {
  const result = spawnSync(binary, ['-hide_banner', '-loglevel', 'error', ...args], { encoding: 'utf8', maxBuffer: 64 << 20 });
  if (result.error?.code === 'ENOENT') throw new UsageError(`ffmpeg not found at "${binary}". Set FFMPEG_PATH or pass --ffmpeg; this skill never downloads it`);
  if (result.status !== 0) throw new Error(`ffmpeg failed (${result.status}): ${result.stderr || result.error?.message}`);
  return result.stderr;
}

/** Use the browser and driver already on the machine; nothing is installed or fetched. */
export async function loadChromium({ playwright, chrome }) {
  const driver = playwright ?? process.env.PLAYWRIGHT_CORE;
  const executablePath = chrome ?? process.env.CHROME_PATH;
  if (!driver) throw new UsageError('Pass --playwright /path/to/playwright-core/index.mjs or set PLAYWRIGHT_CORE; this skill never installs it');
  if (!executablePath) throw new UsageError('Pass --chrome or set CHROME_PATH to an existing browser; this skill never downloads one');
  for (const path of [driver, executablePath]) {
    if (!existsSync(path) || !statSync(path).isFile()) throw new UsageError(`Not a file: ${path}`);
  }
  const { chromium } = await import(pathToFileURL(resolve(driver)).href);
  if (!chromium) throw new UsageError(`${driver} does not export chromium`);
  return { chromium, executablePath };
}
