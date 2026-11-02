// Turn a local video or gif the user supplied into numbered PNG frames. Runs system ffmpeg on that
// one file. Writes only inside --out. Web addresses are refused: this never downloads a video.
import { spawnSync } from 'node:child_process';
import { existsSync, readdirSync, statSync } from 'node:fs';
import { extname, resolve } from 'node:path';
import { EXIT, RIGHTS, UsageError, assertIgnored, child, ffmpeg, isMain, oneOf, parseArgs, parseRect, parseTime, pathInside, prepareOutput, requireOptions, resolveFfmpeg, runCli, writeJson } from './lib.mjs';

const HELP = `
frames.mjs: extract frames from a local video or gif the user supplied.

  node frames.mjs --in <file> --out <dir> --rights <own|licensed|third-party> [options]
  node frames.mjs --in <file> --probe

  --fps N          frames per second to keep, default 10
  --start T        "0:03", "3.5" or "1500ms", default 0
  --end T          same formats, default the end of the file
  --crop x,y,w,h   crop in source pixels
  --width W        downscale to this width
  --ffmpeg PATH    system ffmpeg, or FFMPEG_PATH
  --root DIR       folder --out must stay inside, default the working directory
  --replace        replace earlier frames in --out

Accepts .mp4 .mov .webm .gif .mkv .m4v. Writes NNNN.png and frames.json inside --out.
Frame i (0-based) is at start + i/fps seconds. Third-party frames need an output folder Git ignores.
`;

const VIDEO_TYPES = ['.mp4', '.mov', '.webm', '.gif', '.mkv', '.m4v'];

export function inputFile(value) {
  const text = String(value);
  if (/^[a-z][a-z0-9+.-]+:/i.test(text)) throw new UsageError('frames.mjs reads local files only and never downloads a video. Ask the user for the file or a screen recording');
  const path = resolve(text);
  if (!existsSync(path) || !statSync(path).isFile()) throw new UsageError(`Not a file: ${path}`);
  if (!VIDEO_TYPES.includes(extname(path).toLowerCase())) throw new UsageError(`Unsupported type ${extname(path) || '(none)'}; use ${VIDEO_TYPES.join(' ')}`);
  return path;
}

function probe(binary, input) {
  const result = spawnSync(binary, ['-hide_banner', '-protocol_whitelist', 'file', '-i', input], { encoding: 'utf8' });
  if (result.error?.code === 'ENOENT') throw new UsageError(`ffmpeg not found at "${binary}". Set FFMPEG_PATH or pass --ffmpeg; this skill never downloads it`);
  const text = result.stderr;
  const duration = text.match(/Duration:\s*(\d+):(\d+):([\d.]+)/);
  const size = text.match(/Video:.*?(\d{2,5})x(\d{2,5})/);
  const fps = text.match(/([\d.]+) fps/);
  return {
    input,
    durationS: duration ? Number(duration[1]) * 3600 + Number(duration[2]) * 60 + Number(duration[3]) : undefined,
    width: size ? Number(size[1]) : undefined, height: size ? Number(size[2]) : undefined, sourceFps: fps ? Number(fps[1]) : undefined,
  };
}

function main() {
  const a = parseArgs(process.argv.slice(2), {
    in: 'string', out: 'string', rights: 'string', fps: { type: 'number', min: 0.1, max: 240 }, start: 'string', end: 'string',
    crop: 'string', width: { type: 'number', min: 2, integer: true }, ffmpeg: 'string', root: 'string', replace: 'flag', probe: 'flag',
  });
  if (a.help) { console.log(HELP.trim()); return EXIT.ok; }
  requireOptions(a, a.probe ? ['in'] : ['in', 'out', 'rights']);
  const input = inputFile(a.in);
  const binary = resolveFfmpeg(a.ffmpeg);
  if (a.probe) { console.log(JSON.stringify(probe(binary, input), null, 2)); return EXIT.ok; }
  const rights = oneOf('rights', a.rights, RIGHTS);
  const out = pathInside(a.out, a.root ?? '.', 'Output');
  if (rights === 'third-party') assertIgnored(out);
  const fps = a.fps ?? 10;
  const start = parseTime(a.start) ?? 0;
  const end = parseTime(a.end);
  if (end !== undefined && end <= start) throw new UsageError('--end must be after --start');
  const crop = parseRect(a.crop);
  prepareOutput(out, { marker: 'frames.json', replace: !!a.replace });
  const filters = [`fps=${fps}`];
  if (crop) filters.push(`crop=${crop.width}:${crop.height}:${crop.x}:${crop.y}`);
  if (a.width) filters.push(`scale=${a.width}:-2`);
  const args = ['-y', '-protocol_whitelist', 'file', '-ss', String(start), '-i', input];
  if (end !== undefined) args.push('-t', String(end - start));
  args.push('-vf', filters.join(','), '-fps_mode', 'passthrough', '-pix_fmt', 'rgba', child(out, '%04d.png'));
  ffmpeg(binary, args);
  const count = readdirSync(out).filter((name) => name.endsWith('.png')).length;
  if (!count) throw new Error('ffmpeg wrote no frames: check --start, --end and --crop');
  const meta = { ...probe(binary, input), rights, fps, count, start, end, crop, outWidth: a.width, note: 'frame i (0-based) is at start + i/fps seconds of the source' };
  writeJson(child(out, 'frames.json'), meta);
  console.log(JSON.stringify(meta, null, 2));
  return EXIT.ok;
}

if (isMain(import.meta.url)) runCli(main);
