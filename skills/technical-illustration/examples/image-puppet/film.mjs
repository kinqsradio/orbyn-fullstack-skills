// A window.streamFrame page: one flat picture cut into a plate and a character by an
// authored mask, with the character bent on a mesh. The camera never moves, so all the
// life in the shot comes from the character. render() draws from `time` alone, so the
// exporter's --samples gives real motion blur.
import {characterAlpha, cutOut, loadPicture, plateFrom, validateMask} from './mask.mjs';
import {createMesh, deform, drawnState, validateRegions} from './puppet.mjs';
import {paintLayer, paintPicture} from './portrait.mjs';
import {layers, mask, regions} from './regions.mjs';

// A real job names the user's file here, keeps it in this folder, and lists it with
// check-code-only.py --allow. Left empty, the page paints its own test picture.
const PICTURE = null;

const canvas = document.getElementById('film');
const VERTEX = `#version 300 es
in vec2 a; out vec2 uv;
void main() { uv = a; gl_Position = vec4(a.x * 2. - 1., 1. - a.y * 2., 0, 1); }`;
const MOVED = `#version 300 es
in vec2 a; in vec2 home; out vec2 uv;
void main() { uv = home; gl_Position = vec4(a.x * 2. - 1., 1. - a.y * 2., 0, 1); }`;
const FRAGMENT = `#version 300 es
precision highp float; in vec2 uv; out vec4 color; uniform sampler2D art;
void main() { color = texture(art, uv); }`;
const SCALE = 2;
let stack, gl, width, height, pixels, flat, bent, backdrop, character, plateTarget, output, mesh, quad, moved;

function program(vertex) {
  const build = (type, text) => { const s = gl.createShader(type); gl.shaderSource(s, text); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw Error(gl.getShaderInfoLog(s)); return s; };
  const p = gl.createProgram(); gl.attachShader(p, build(gl.VERTEX_SHADER, vertex)); gl.attachShader(p, build(gl.FRAGMENT_SHADER, FRAGMENT)); gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw Error(gl.getProgramInfoLog(p));
  return p;
}
function texture(source) {
  const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false); gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, true);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, source); gl.generateMipmap(gl.TEXTURE_2D);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  for (const k of [gl.TEXTURE_WRAP_S, gl.TEXTURE_WRAP_T]) gl.texParameteri(gl.TEXTURE_2D, k, gl.CLAMP_TO_EDGE);
  return t;
}
function target(w, h) {
  const t = gl.createTexture(), b = gl.createFramebuffer(); gl.bindTexture(gl.TEXTURE_2D, t); gl.texStorage2D(gl.TEXTURE_2D, 1, gl.RGBA8, w, h);
  gl.bindFramebuffer(gl.FRAMEBUFFER, b); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0);
  return {b, w, h};
}
const paint = (draw, w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d', {willReadFrequently: true}), w, h); return c; };

function drawFlat(art) {
  gl.useProgram(flat); gl.bindVertexArray(quad); gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, art);
  gl.drawArrays(gl.TRIANGLES, 0, 6);
}
function drawMesh(points, art) {
  gl.useProgram(bent); gl.bindVertexArray(moved.vao); gl.bindBuffer(gl.ARRAY_BUFFER, moved.points); gl.bufferSubData(gl.ARRAY_BUFFER, 0, points);
  gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, art); gl.drawElements(gl.TRIANGLES, mesh.indices.length, gl.UNSIGNED_INT, 0);
}
function finish() {
  gl.bindFramebuffer(gl.READ_FRAMEBUFFER, plateTarget.b); gl.bindFramebuffer(gl.DRAW_FRAMEBUFFER, output.b);
  gl.blitFramebuffer(0, 0, plateTarget.w, plateTarget.h, 0, 0, width, height, gl.COLOR_BUFFER_BIT, gl.LINEAR);
}
function begin() {
  gl.bindFramebuffer(gl.FRAMEBUFFER, plateTarget.b); gl.viewport(0, 0, plateTarget.w, plateTarget.h); gl.disable(gl.BLEND); gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT);
}

window.streamFrame = {
  rowOrder: 'bottom-first',
  async boot(config) {
    ({width, height} = config); canvas.width = 2; canvas.height = 2;
    gl = canvas.getContext('webgl2', {antialias: false, alpha: false}); if (!gl) throw Error('WebGL2 unavailable');
    pixels = new Uint8Array(width * height * 4); validateRegions(regions); validateMask(mask);
    flat = program(VERTEX); bent = program(MOVED); mesh = createMesh(160, 90);
    plateTarget = target(width * SCALE, height * SCALE); output = target(width, height);
    const image = PICTURE && await loadPicture(PICTURE), alpha = characterAlpha(width * SCALE, height * SCALE, mask);
    const picture = state => paint((c, w, h) => paintPicture(c, w, h, state, image), width * SCALE, height * SCALE);
    backdrop = texture(plateFrom(picture({}), alpha));
    // Registered drawings of the same character, bent by the same mesh. A flat image has one
    // layer until its hair is cut out; the drawn demo has its three.
    const layer = (part, state) => texture(image
      ? cutOut(picture(state), alpha)
      : paint((c, w, h) => paintLayer(c, w, h, part, state), width * SCALE, height * SCALE));
    character = {};
    for (const eyesClosed of [false, true]) for (const mouthOpen of [false, true]) {
      character[[eyesClosed, mouthOpen]] = layer('body', {eyesClosed, mouthOpen});
    }
    stack = image ? [{regions, art: state => character[state]}] : layers.map(({part, regions: own}) => {
      const still = part === 'body' ? null : layer(part, {});
      return {regions: own, art: state => still ?? character[state]};
    });
    quad = gl.createVertexArray(); gl.bindVertexArray(quad);
    const corners = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, corners); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1]), gl.STATIC_DRAW);
    gl.enableVertexAttribArray(gl.getAttribLocation(flat, 'a')); gl.vertexAttribPointer(gl.getAttribLocation(flat, 'a'), 2, gl.FLOAT, false, 0, 0);
    const vao = gl.createVertexArray(); gl.bindVertexArray(vao);
    const points = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, points); gl.bufferData(gl.ARRAY_BUFFER, mesh.points, gl.DYNAMIC_DRAW);
    gl.enableVertexAttribArray(gl.getAttribLocation(bent, 'a')); gl.vertexAttribPointer(gl.getAttribLocation(bent, 'a'), 2, gl.FLOAT, false, 0, 0);
    const home = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, home); gl.bufferData(gl.ARRAY_BUFFER, mesh.points, gl.STATIC_DRAW);
    gl.enableVertexAttribArray(gl.getAttribLocation(bent, 'home')); gl.vertexAttribPointer(gl.getAttribLocation(bent, 'home'), 2, gl.FLOAT, false, 0, 0);
    const elements = gl.createBuffer(); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, elements); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, mesh.indices, gl.STATIC_DRAW);
    moved = {vao, points};
  },
  calibrate({width: w, height: h, pixels: chart}) {
    const card = document.createElement('canvas'); card.width = w; card.height = h;
    card.getContext('2d').putImageData(new ImageData(new Uint8ClampedArray(chart), w, h), 0, 0);
    begin(); drawFlat(texture(card)); finish();
  },
  render({time}) {
    begin(); drawFlat(backdrop);
    gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    const {eyesClosed, mouthOpen} = drawnState(regions, time);
    for (const {regions: own, art} of stack) drawMesh(deform(mesh, own, time), art([eyesClosed, mouthOpen]));
    finish();
  },
  read() { gl.bindFramebuffer(gl.FRAMEBUFFER, output.b); gl.readPixels(0, 0, width, height, gl.RGBA, gl.UNSIGNED_BYTE, pixels); return pixels; },
};
