// The proof film as a window.streamFrame page: raymarched scene, bloom chain, post.
// render() draws from `time`, so the exporter's --samples gives real motion blur. Only the film grain reads the
// output frame, so the grain stays the same across one frame's samples. Nothing carries over from the last frame.
// A page that sets window.FILM_PLATE before loading this module renders without the word, for legibility-check.py.
import { VERTEX, SCENE, BRIGHT, BLUR, POST } from './shaders.mjs';
import { WORD, frameState } from './world.mjs';

const canvas = document.getElementById('film');
const SUPERSAMPLE = 2, STRIPS = 10; // Strips keep any one draw short enough for the GPU watchdog.
const FONT = '-apple-system, "Helvetica Neue", Arial, sans-serif';
let gl, width, height, spec, reduced, art, layer, pixels, scene, near, wide, swap, output, programs, plate = false;

function compile(source) {
  const build = (type, text) => { const s = gl.createShader(type); gl.shaderSource(s, text); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw Error(gl.getShaderInfoLog(s)); return s; };
  const program = gl.createProgram(); gl.attachShader(program, build(gl.VERTEX_SHADER, VERTEX)); gl.attachShader(program, build(gl.FRAGMENT_SHADER, source)); gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw Error(gl.getProgramInfoLog(program));
  const uniforms = new Map();
  return { program, at: name => { if (!uniforms.has(name)) uniforms.set(name, gl.getUniformLocation(program, name)); return uniforms.get(name); } };
}
function target(w, h, format = gl.RGBA16F, type = gl.HALF_FLOAT) {
  const texture = gl.createTexture(), buffer = gl.createFramebuffer(); gl.bindTexture(gl.TEXTURE_2D, texture);
  gl.texImage2D(gl.TEXTURE_2D, 0, format, w, h, 0, gl.RGBA, type, null);
  for (const [k, v] of [[gl.TEXTURE_MIN_FILTER, gl.LINEAR], [gl.TEXTURE_MAG_FILTER, gl.LINEAR], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D, k, v);
  gl.bindFramebuffer(gl.FRAMEBUFFER, buffer); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0);
  if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) throw Error('Render target unavailable');
  return { texture, buffer, w, h };
}
const bind = (unit, texture, location) => { gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, texture); gl.uniform1i(location, unit); };
function pass(program, destination, set) {
  gl.bindFramebuffer(gl.FRAMEBUFFER, destination.buffer); gl.viewport(0, 0, destination.w, destination.h); gl.useProgram(program.program); set(program); gl.drawArrays(gl.TRIANGLES, 0, 3);
}
// The single upload path for Y-down art: the word and the orientation card both arrive here.
function upload(source) {
  gl.bindTexture(gl.TEXTURE_2D, art); gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false); gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, source);
}
function drawWord() {
  const c = layer.getContext('2d'), size = height * .31;
  c.clearRect(0, 0, width, height); c.fillStyle = '#fff'; c.textAlign = 'center'; c.textBaseline = 'alphabetic';
  c.font = `800 ${size}px ${FONT}`; c.letterSpacing = `${size * .02}px`; c.fillText(WORD.text, width / 2, height * .8);
}
function drawScene(state, calibrate) {
  gl.bindFramebuffer(gl.FRAMEBUFFER, scene.buffer); gl.viewport(0, 0, scene.w, scene.h); const p = programs.scene; gl.useProgram(p.program);
  gl.uniform1f(p.at('uCalibrate'), calibrate ? 1 : 0); bind(0, art, p.at('uArt'));
  if (state) {
    gl.uniform3fv(p.at('uEye'), state.eye); gl.uniformMatrix3fv(p.at('uBasis'), false, state.basis); gl.uniform1f(p.at('uFocal'), state.focal); gl.uniform1f(p.at('uAspect'), width / height);
    gl.uniform3fv(p.at('uJ'), state.joints); gl.uniform3fv(p.at('uScarf'), state.scarf); gl.uniform2f(p.at('uPixel'), 1 / width, 1 / height);
    gl.uniform4fv(p.at('uCube'), state.cubes.flatMap(c => [...c.center, c.size])); gl.uniformMatrix3fv(p.at('uCubeR'), false, state.cubes.flatMap(c => c.rotation));
    gl.uniform1f(p.at('uWordOn'), state.wordOn); gl.uniform1f(p.at('uSplit'), state.split > .06 ? state.split : 0); gl.uniform1f(p.at('uBoil'), state.boil); gl.uniform1f(p.at('uBeaconTurn'), state.turn);
  }
  gl.enable(gl.SCISSOR_TEST);
  for (let i = 0; i < STRIPS; i++) { const y = Math.floor(scene.h * i / STRIPS), top = Math.floor(scene.h * (i + 1) / STRIPS); gl.scissor(0, y, scene.w, top - y); gl.drawArrays(gl.TRIANGLES, 0, 3); gl.flush(); }
  gl.disable(gl.SCISSOR_TEST);
}
function finish(hit, seed, exposure, index, calibrate) {
  const blur = (from, to, step) => pass(programs.blur, to, p => { bind(0, from.texture, p.at('uImage')); gl.uniform2fv(p.at('uStep'), step); });
  const image = p => bind(0, scene.texture, p.at('uImage'));
  pass(programs.bright, near, image);
  blur(near, swap.near, [1 / near.w, 0]); blur(swap.near, near, [0, 1 / near.h]);
  blur(near, wide, [0, 0]); blur(wide, swap.wide, [1.6 / wide.w, 0]); blur(swap.wide, wide, [0, 1.6 / wide.h]);
  pass(programs.post, output, p => {
    image(p); bind(1, near.texture, p.at('uNear')); bind(2, wide.texture, p.at('uWide'));
    gl.uniform1f(p.at('uHit'), hit); gl.uniform1f(p.at('uSeed'), seed); gl.uniform1f(p.at('uExposure'), exposure); gl.uniform1f(p.at('uFrame'), index); gl.uniform1f(p.at('uCalibrate'), calibrate ? 1 : 0);
  });
}

window.streamFrame = {
  rowOrder: 'bottom-first', // gl.readPixels below.
  boot(config) {
    ({ width, height, spec } = config); reduced = config.reducedMotion; canvas.width = 2; canvas.height = 2; plate = !!window.FILM_PLATE;
    gl = canvas.getContext('webgl2', { antialias: false, alpha: false }); if (!gl || !gl.getExtension('EXT_color_buffer_float')) throw Error('WebGL2 with float targets is required');
    gl.bindVertexArray(gl.createVertexArray()); pixels = new Uint8Array(width * height * 4);
    programs = { scene: compile(SCENE), bright: compile(BRIGHT), blur: compile(BLUR), post: compile(POST) };
    scene = target(width * SUPERSAMPLE, height * SUPERSAMPLE); output = target(width, height, gl.RGBA8, gl.UNSIGNED_BYTE);
    const size = d => [Math.ceil(width / d), Math.ceil(height / d)];
    near = target(...size(3)); wide = target(...size(9)); swap = { near: target(...size(3)), wide: target(...size(9)) };
    art = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, art);
    for (const [k, v] of [[gl.TEXTURE_MIN_FILTER, gl.LINEAR], [gl.TEXTURE_MAG_FILTER, gl.LINEAR], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D, k, v);
    layer = document.createElement('canvas'); layer.width = width; layer.height = height;
  },
  calibrate({ width: w, height: h, pixels: chart }) {
    const card = document.createElement('canvas'); card.width = w; card.height = h;
    card.getContext('2d').putImageData(new ImageData(new Uint8ClampedArray(chart), w, h), 0, 0);
    upload(card); drawScene(null, true); finish(0, 0, 1, 0, true);
    if (!plate) drawWord(); upload(layer); // Hand the path back to the word.
  },
  render({ index, time }) {
    const state = frameState(time, spec.shots, { reducedMotion: reduced, word: !plate });
    drawScene(state, false); finish(state.hit, state.latest, state.exposure, index, false);
  },
  read() { gl.bindFramebuffer(gl.FRAMEBUFFER, output.buffer); gl.readPixels(0, 0, width, height, gl.RGBA, gl.UNSIGNED_BYTE, pixels); return pixels; }
};
