// Synthetic two-pass WebGL2 film for the streaming exporter. Art is Y-down: row 0 is the top.
const ART_V = '1. - uv.y'; // The only pass that corrects art rows. A broken variant samples uv.y here.
const canvas = document.getElementById('film');
let gl, width, height, art, passes, target, pixels, frames;
const VERTEX = `#version 300 es
out vec2 uv; void main() { vec2 p = vec2(float((gl_VertexID & 1) * 4 - 1), float((gl_VertexID & 2) * 2 - 1)); uv = p * .5 + .5; gl_Position = vec4(p, 0., 1.); }`;
const shader = (type, source) => { const s = gl.createShader(type); gl.shaderSource(s, source); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw Error(gl.getShaderInfoLog(s)); return s; };
const program = body => { const p = gl.createProgram(); gl.attachShader(p, shader(gl.VERTEX_SHADER, VERTEX)); gl.attachShader(p, shader(gl.FRAGMENT_SHADER, `#version 300 es
precision highp float; in vec2 uv; out vec4 color; uniform sampler2D image; void main() { ${body} }`)); gl.linkProgram(p); return p; };
const texture = (w, h) => { const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, w, h, 0, gl.RGBA, gl.UNSIGNED_BYTE, null); for (const [k, v] of [[gl.TEXTURE_MIN_FILTER, gl.NEAREST], [gl.TEXTURE_MAG_FILTER, gl.NEAREST], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D, k, v); return t; };
const offscreen = () => { const t = texture(width, height), fb = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, fb); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0); return { t, fb }; };
const draw = (source, program, destination) => { gl.bindFramebuffer(gl.FRAMEBUFFER, destination); gl.useProgram(program); gl.bindTexture(gl.TEXTURE_2D, source); gl.drawArrays(gl.TRIANGLES, 0, 3); };
const present = (w, h, data) => {
  gl.bindTexture(gl.TEXTURE_2D, art); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, w, h, 0, gl.RGBA, gl.UNSIGNED_BYTE, data);
  draw(art, passes[0], target[0].fb); draw(target[0].t, passes[1], target[1].fb);
};
window.streamFrame = {
  rowOrder: 'bottom-first',
  boot(config) {
    ({ width, height, frames } = config); canvas.width = width; canvas.height = height;
    gl = canvas.getContext('webgl2', { antialias: false }); gl.viewport(0, 0, width, height); gl.bindVertexArray(gl.createVertexArray());
    pixels = new Uint8Array(width * height * 4); art = texture(1, 1);
    passes = [program(`color = texture(image, vec2(uv.x, ${ART_V}));`), program('color = texture(image, uv);')]; target = [offscreen(), offscreen()];
  },
  calibrate({ width: w, height: h, pixels: chart }) { present(w, h, chart); },
  // Top half red and bottom half blue, with a white column that crosses the frame over the film.
  render({ index }) {
    const w = 64, h = 64, data = new Uint8Array(w * h * 4), column = Math.floor(index / Math.max(1, frames - 1) * (w - 1));
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) data.set(x === column ? [255, 255, 255, 255] : y < h / 2 ? [255, 0, 0, 255] : [0, 0, 255, 255], (y * w + x) * 4);
    present(w, h, data);
  },
  read() { gl.readPixels(0, 0, width, height, gl.RGBA, gl.UNSIGNED_BYTE, pixels); return pixels; }
};
