// GLSL for the film. Framebuffers stay in GL order, bottom row first. Y-down art enters only in the
// scene pass, through artUv(), and that same path carries the orientation card and the word layer.
import { BEACON, CUBES, JOINTS, SCARF_POINTS, SUN } from './world.mjs';

const glsl = v => v.map(n => n.toFixed(5)).join(',');
export const VERTEX = `#version 300 es
out vec2 uv; void main() { vec2 p = vec2(float((gl_VertexID & 1) * 4 - 1), float((gl_VertexID & 2) * 2 - 1)); uv = p * .5 + .5; gl_Position = vec4(p, 0., 1.); }`;
const HEAD = `#version 300 es
precision highp float; precision highp int; in vec2 uv; out vec4 color;
`;

export const SCENE = HEAD + `
uniform vec3 uEye; uniform mat3 uBasis; uniform float uFocal, uAspect, uWordOn, uSplit, uBoil, uCalibrate; uniform vec2 uPixel;
uniform vec3 uJ[${JOINTS.length}]; uniform vec3 uScarf[${SCARF_POINTS}]; uniform vec4 uCube[${CUBES}]; uniform mat3 uCubeR[${CUBES}]; uniform float uBeaconTurn; uniform sampler2D uArt;
${JOINTS.map((name, i) => `#define ${name.toUpperCase()} uJ[${i}]`).join('\n')}
const vec3 SUN = vec3(${glsl(SUN)}), BEACON = vec3(${glsl(BEACON.position)}); const float BEACON_R = ${BEACON.radius.toFixed(2)};
vec2 artUv(vec2 q) { return vec2(q.x, 1. - q.y); } // The only Y correction in the film.

float lattice(ivec2 c) {
  uint h = (uint(c.x) * 0x3504f333u) ^ (uint(c.y) * 0xf1bbcdcbu);
  h *= 741103597u; h ^= h >> 15; h *= 0x2c1b3c6du;
  return float(h >> 8) / 16777215.;
}
float noise(vec2 p) {
  vec2 i = floor(p), f = p - i, u = f * f * f * (f * (f * 6. - 15.) + 10.); ivec2 c = ivec2(i);
  return mix(mix(lattice(c), lattice(c + ivec2(1, 0)), u.x), mix(lattice(c + ivec2(0, 1)), lattice(c + ivec2(1, 1)), u.x), u.y);
}
float ridged(vec2 p, int octaves) {
  float sum = 0., amp = .5;
  for (int k = 0; k < octaves; k++) {
    float n = 1. - abs(2. * noise(p) - 1.); sum += amp * n * n; amp *= .5;
    p = vec2((.8 * p.x + .6 * p.y) * 2.03 + 17.1, (-.6 * p.x + .8 * p.y) * 2.03 + 9.2);
  }
  return sum;
}
float rocks(vec2 p, float size, int salt) {
  float k0 = 1.7 / size, sf = float(salt); vec2 w = p + vec2(noise(vec2(p.x * k0 + sf, p.y * k0)) - .5, noise(vec2(p.y * k0, p.x * k0 + sf)) - .5) * size * .6;
  ivec2 c = ivec2(floor(w / size)); float r = lattice(c + ivec2(salt, 0)), turn = lattice(c + ivec2(0, salt)) * 6.283;
  if (r < .62) return 0.;
  vec2 d = w - (vec2(c) + .5) * size; float k = (r - .62) / .38, cs = cos(turn), sn = sin(turn), a = cs * d.x + sn * d.y, b = cs * d.y - sn * d.x, u = abs(a), v = abs(b);
  float radius = size * (.16 + .34 * k * k), edge = 1. - max(max(u * 1.25, v), (u + v) * .72) / radius;
  return edge > 0. ? min(sqrt(edge * (2. - edge)), .65 + .5 * a / radius) * radius * .62 : 0.;
}
float trailX(float z) { return 2.4 * sin(z / 13.) + 1.1 * sin(z / 5.7 + 1.2); }
// lod 0 matches world.mjs height(). Higher lods drop detail too small to see at range.
float height(vec2 p, int lod) {
  float d = abs(p.x - trailX(p.y)), m = smoothstep(5., 70., d), wall = smoothstep(170., 480., p.y), clear = smoothstep(2.5, 11., d);
  float raw = ridged(p * .0105, lod > 1 ? 4 : 5) * (6. + 78. * m + 58. * wall), steps = (raw + 7. * noise(p * .021)) / 3.4, whole = floor(steps);
  float big = mix(raw, (whole + smoothstep(.1, .5, steps - whole)) * 3.4, m * .55);
  if (lod > 2) return big - 5.5;
  float mid = (ridged(p * .07 + vec2(3.1, 0.), 3) - .42) * (.35 + 5.5 * m);
  if (lod > 1) return big - 5.5 + mid;
  float fine = (noise(p * .62) - .5) * .42 + (noise(p * 1.9 + vec2(5., 0.)) - .5) * .14;
  float stones = rocks(p, 7.3, 11);
  if (lod == 0) stones += rocks(p + vec2(1.7, -.9), 2.9, 23);
  return big - 5.5 + mid + fine * (.55 + .45 * m) + clear * stones;
}
int lodAt(float t) { return t < 70. ? 0 : t < 220. ? 1 : t < 520. ? 2 : 3; }

float capsule(vec3 p, vec3 a, vec3 b, float r0, float r1) {
  vec3 pa = p - a, ba = b - a; float h = clamp(dot(pa, ba) / dot(ba, ba), 0., 1.);
  return length(pa - ba * h) - mix(r0, r1, h);
}
float roundBox(vec3 p, vec3 b, float r) { vec3 q = abs(p) - b + r; return length(max(q, 0.)) + min(max(q.x, max(q.y, q.z)), 0.) - r; }
float blend(float a, float b, float k) { float h = clamp(.5 + .5 * (b - a) / k, 0., 1.); return mix(b, a, h) - k * h * (1. - h); }
vec3 figureCentre() { return mix(PELVIS, CHEST, .3); }

// The figure as capsules and rounded boxes around the joints from rig.mjs. y: 0 body, 1 scarf.
vec2 figure(vec3 p) {
  vec3 across = normalize(SHOULDERL - SHOULDERR), up = normalize(NECK - PELVIS), ahead = normalize(cross(across, up)); across = cross(up, ahead);
  mat3 toLocal = transpose(mat3(across, up, ahead));
  vec3 torso = toLocal * (p - mix(SPINE, CHEST, .6));
  float d = roundBox(torso, vec3(.15, .25, .1), .085);
  d = blend(d, roundBox(toLocal * (p - PELVIS), vec3(.14, .1, .095), .08), .05);
  d = min(d, roundBox(toLocal * (p - CHEST) + vec3(0., .02, .17), vec3(.13, .19, .075), .04));
  d = min(d, capsule(p, NECK - up * .04, HEAD, .068, .056));
  d = min(d, length((p - HEAD - vec3(0., .05, 0.)) * vec3(1.04, .88, 1.)) - .094);
  d = blend(d, capsule(p, HIPL, KNEEL, .083, .058), .03); d = blend(d, capsule(p, HIPR, KNEER, .083, .058), .03);
  d = min(d, capsule(p, KNEEL, ANKLEL, .056, .036)); d = min(d, capsule(p, KNEER, ANKLER, .056, .036));
  d = min(d, capsule(p, HEELL, TOEL, .03, .03)); d = min(d, capsule(p, HEELR, TOER, .03, .03));
  d = min(d, capsule(p, TOEL, TIPL, .03, .024)); d = min(d, capsule(p, TOER, TIPR, .03, .024));
  d = min(d, capsule(p, ANKLEL, mix(HEELL, TOEL, .4), .034, .03)); d = min(d, capsule(p, ANKLER, mix(HEELR, TOER, .4), .034, .03));
  d = blend(d, capsule(p, SHOULDERL, ELBOWL, .055, .042), .03); d = blend(d, capsule(p, SHOULDERR, ELBOWR, .055, .042), .03);
  d = min(d, capsule(p, ELBOWL, WRISTL, .04, .03)); d = min(d, capsule(p, ELBOWR, WRISTR, .04, .03));
  float cloth = 1e3;
  for (int i = 0; i < ${SCARF_POINTS - 1}; i++) cloth = min(cloth, capsule(p, uScarf[i], uScarf[i + 1], .03 - .0022 * float(i), .028 - .0022 * float(i)));
  return cloth < d ? vec2(cloth, 1.) : vec2(d, 0.);
}
vec3 figureNormal(vec3 p) {
  const vec2 e = vec2(.004, 0.);
  return normalize(vec3(figure(p + e.xyy).x - figure(p - e.xyy).x, figure(p + e.yxy).x - figure(p - e.yxy).x, figure(p + e.yyx).x - figure(p - e.yyx).x));
}
vec2 sphere(vec3 ro, vec3 rd, vec3 c, float r) {
  vec3 o = ro - c; float b = dot(o, rd), h = b * b - dot(o, o) + r * r;
  if (h < 0.) return vec2(1., -1.); h = sqrt(h); return vec2(-b - h, -b + h);
}
// The figure's own shadow on the ground, from a point near it.
float figureShadow(vec3 p) {
  vec2 s = sphere(p, SUN, figureCentre(), 2.); if (s.y < 0.) return 1.;
  float t = max(s.x, .01), lit = 1.;
  for (int i = 0; i < 26 && t < s.y; i++) { float d = figure(p + SUN * t).x; lit = min(lit, 7. * d / t + .14); if (d < .002) return .14; t += max(d, .03); }
  return clamp(lit, .14, 1.);
}
float terrainShadow(vec3 p) {
  // Measured from the coarse surface under p, so fine detail cannot shadow itself.
  float lit = 1., t = .3, bias = p.y - height(p.xz, 2);
  for (int i = 0; i < 26; i++) { vec3 q = p + SUN * t; float d = q.y - height(q.xz, 2) - bias * (1. - smoothstep(4., 40., t)); lit = min(lit, 12. * d / t); if (lit < 0.) break; t += clamp(d * .7, .35, 26.); if (t > 420.) break; }
  return smoothstep(0., 1., clamp(lit, 0., 1.));
}
float marchTerrain(vec3 ro, vec3 rd, float far) {
  float t = 0.; const float TOP = 240.;
  if (ro.y > TOP) { if (rd.y >= 0.) return -1.; t = (TOP - ro.y) / rd.y; }
  float last = t;
  for (int i = 0; i < 300; i++) {
    vec3 p = ro + rd * t; float d = p.y - height(p.xz, lodAt(t));
    if (d < .0008 * t + .002) { float a = last, b = t; for (int k = 0; k < 6; k++) { float m = .5 * (a + b); vec3 q = ro + rd * m; if (q.y - height(q.xz, lodAt(m)) < 0.) b = m; else a = m; } return .5 * (a + b); }
    if (p.y > TOP && rd.y > 0.) return -1.;
    last = t; t += max(.015 + .0018 * t, d * (t < 40. ? .4 : .55)); if (t > far) return -1.;
  }
  return t; // A grazing ray that spent its steps is on the surface in all but name.
}
vec3 terrainNormal(vec2 p, float t) {
  int lod = lodAt(t); vec2 e = vec2(max(.012, .0016 * t), 0.);
  return normalize(vec3(height(p - e.xy, lod) - height(p + e.xy, lod), 2. * e.x, height(p - e.yx, lod) - height(p + e.yx, lod)));
}
vec3 sky(vec3 rd) {
  float toSun = max(dot(rd, SUN), 0.), y = max(rd.y, 0.);
  vec3 c = mix(vec3(.5, .32, .34), vec3(.2, .16, .4), smoothstep(0., .17, y));
  c = mix(c, vec3(.05, .05, .15), smoothstep(.1, .55, y));
  c += vec3(1.1, .5, .17) * pow(toSun, 7.) * .62 + vec3(1.2, .72, .34) * pow(toSun, 70.) * .46;
  return c;
}
vec3 fog(vec3 c, vec3 ro, vec3 rd, float t) {
  const float DENSITY = .0034, FALL = .011; float k = rd.y * FALL, along = abs(k) < 1e-5 ? t : (1. - exp(-t * k)) / k;
  float f = 1. - exp(-DENSITY * exp(-ro.y * FALL) * along);
  return mix(c, sky(normalize(vec3(rd.x, max(rd.y, .012), rd.z))), f);
}
vec3 ground(vec3 p, vec3 rd, float t) {
  vec3 n = terrainNormal(p.xz, t);
  if (t < 60.) { vec2 e = vec2(.01, 0.), q = p.xz * 7.; float k = .05 * smoothstep(60., 10., t); n = normalize(n + k * vec3(noise(q - e.xy * 7.) - noise(q + e.xy * 7.), 0., noise(q - e.yx * 7.) - noise(q + e.yx * 7.)) * 6.); }
  float flat_ = smoothstep(.66, .92, n.y), band = noise(vec2(p.y * 1.3, (p.x + p.z) * .03)), speck = noise(p.xz * 2.3);
  vec3 rock = mix(vec3(.1, .07, .08), vec3(.27, .17, .14), band * band), dust = mix(vec3(.2, .13, .12), vec3(.33, .22, .17), speck);
  vec3 base = mix(rock, dust, flat_);
  float sun = max(dot(n, SUN), 0.) * terrainShadow(p + n * .04), near = length(p - figureCentre());
  float contact = 1.;
  if (near < 3.4) { sun *= figureShadow(p + n * .02); contact = mix(.5, 1., smoothstep(.0, .3, figure(p + n * .06).x)); }
  vec3 light = vec3(3.1, 1.85, 1.05) * sun + mix(vec3(.1, .07, .12), vec3(.2, .17, .36), .5 + .5 * n.y) * contact;
  return base * light;
}
// Slab tests against four pairs of octahedron faces, in a stretched and turned local frame.
vec4 beacon(vec3 ro, vec3 rd) {
  float c = cos(uBeaconTurn), s = sin(uBeaconTurn); mat3 turn = mat3(c, 0., -s, 0., 1., 0., s, 0., c);
  vec3 o = (turn * (ro - BEACON)) / vec3(1., 1.75, 1.), d = (turn * rd) / vec3(1., 1.75, 1.); float near = -1e9, far = 1e9; vec3 normal = vec3(0.);
  const vec3 AXES[4] = vec3[4](vec3(1., 1., 1.), vec3(1., 1., -1.), vec3(1., -1., 1.), vec3(-1., 1., 1.));
  for (int i = 0; i < 4; i++) {
    float a = dot(o, AXES[i]), b = dot(d, AXES[i]), t0 = (-BEACON_R - a) / b, t1 = (BEACON_R - a) / b; vec3 n = AXES[i] * -sign(b);
    if (t0 > t1) { float x = t0; t0 = t1; t1 = x; }
    if (t0 > near) { near = t0; normal = n; } far = min(far, t1);
  }
  if (near > far || far < 0.) return vec4(0., 0., 0., -1.);
  return vec4(normalize(normal * turn), near);
}
vec3 cubeShade(vec3 n, vec3 rd) {
  float sun = max(dot(n, SUN), 0.), rim = pow(1. - max(dot(n, -rd), 0.), 3.);
  return vec3(.012, .012, .022) + vec3(.09, .055, .04) * sun + vec3(.016, .016, .04) * (.5 + .5 * n.y) + vec3(.05, .03, .045) * rim;
}
void main() {
  if (uCalibrate > .5) { color = vec4(texture(uArt, artUv(uv)).rgb, 1.); return; }
  vec2 s = (uv * 2. - 1.) * vec2(uAspect, 1.); vec3 rd = normalize(uBasis * vec3(s, uFocal)), ro = uEye;
  vec3 col = sky(rd);

  vec4 b = beacon(ro, rd);
  float tGround = marchTerrain(ro, rd, 1400.), depth = tGround < 0. ? 1e9 : tGround;
  vec3 toBeacon = BEACON - ro; float along = dot(toBeacon, rd); vec3 miss = rd * along - toBeacon;
  vec3 side = normalize(cross(vec3(0., 1., 0.), toBeacon)); vec2 off = vec2(dot(miss, side), miss.y / 1.75) / BEACON_R;
  float visible = tGround < 0. || tGround > length(toBeacon) ? 1. : 0.;

  float tCube = 1e9; vec3 cubeN = vec3(0.);
  for (int i = 0; i < ${CUBES}; i++) {
    vec3 o = (ro - uCube[i].xyz) * uCubeR[i], d = rd * uCubeR[i], inv = 1. / d, k = abs(inv) * uCube[i].w, m = -inv * o, t0 = m - k, t1 = m + k;
    float near = max(max(t0.x, t0.y), t0.z), far = min(min(t1.x, t1.y), t1.z);
    if (near < far && near > 0. && near < tCube) { tCube = near; vec3 face = step(t0.yzx, t0.xyz) * step(t0.zxy, t0.xyz); cubeN = uCubeR[i] * (-sign(d) * face); }
  }
  if (b.w > 0. && b.w < depth && b.w < tCube) {
    float face = .5 + .5 * dot(b.xyz, -rd); col = mix(vec3(2.6, 1.9, 1.4), vec3(7., 6.1, 5.), face * face * face);
  }
  if (tGround > 0. && tGround < tCube) { vec3 p = ro + rd * tGround; col = fog(ground(p, rd, tGround), ro, rd, tGround); depth = tGround; }
  else if (tCube < 1e8) { col = fog(cubeShade(cubeN, rd), ro, rd, tCube); depth = tCube; }
  // A diamond glow around the beacon: L1 distance keeps the shape of the mark.
  float metric = abs(off.x) + abs(off.y), glow = .3 * exp(-max(metric - 1., 0.) * 1.1) + .09 * exp(-max(metric - 1., 0.) * .22);
  col += vec3(1.25, .84, .54) * glow * visible * (depth > length(toBeacon) ? 1. : .35) * (b.w > 0. ? 0. : 1.);

  if (uWordOn > .5) {
    vec2 at = uv + vec2(sin(uBoil * 91.) * .00018, cos(uBoil * 73.) * .0003), split = vec2(uSplit * 26. * uPixel.x, 0.);
    vec3 cover = vec3(texture(uArt, artUv(at + split)).a, texture(uArt, artUv(at)).a, texture(uArt, artUv(at - split)).a);
    col = mix(col, vec3(1.08, 1., .92), cover);
  }

  vec2 hit = sphere(ro, rd, figureCentre(), 1.75);
  if (hit.y > 0.) {
    float t = max(hit.x, .01); vec2 h = vec2(1.);
    for (int i = 0; i < 64 && t < hit.y; i++) { h = figure(ro + rd * t); if (h.x < .0006 + .00022 * t) break; t += h.x * .9; }
    if (h.x < .0016 + .00022 * t && t < depth + .02) {
      vec3 p = ro + rd * t, n = figureNormal(p);
      float sun = max(dot(n, SUN), 0.), rim = pow(1. - max(dot(n, -rd), 0.), 3.) * (.35 + .65 * max(dot(rd, SUN), 0.));
      vec3 base = h.y > .5 ? vec3(.62, .085, .04) : vec3(.05, .048, .07);
      vec3 lit = base * (vec3(2.4, 1.55, 1.) * sun + vec3(.32, .28, .5) * (.55 + .45 * n.y) + vec3(.2, .12, .1) * max(-n.y, 0.)) + (h.y > .5 ? vec3(.5, .13, .06) : vec3(.26, .15, .11)) * rim;
      col = fog(lit, ro, rd, t);
    }
  }
  color = vec4(col, 1.);
}`;

export const BRIGHT = HEAD + `uniform sampler2D uImage; void main() { vec3 c = texture(uImage, uv).rgb; color = vec4(max(c - .95, 0.) / (1. + .25 * dot(c, vec3(.3))), 1.); }`;
export const BLUR = HEAD + `uniform sampler2D uImage; uniform vec2 uStep; void main() {
  vec3 c = texture(uImage, uv).rgb * .227; const vec2 W = vec2(.3162, .0703), D = vec2(1.385, 3.231);
  for (int i = 0; i < 2; i++) c += (texture(uImage, uv + uStep * D[i]).rgb + texture(uImage, uv - uStep * D[i]).rgb) * W[i];
  color = vec4(c, 1.); }`;
export const POST = HEAD + `
uniform sampler2D uImage, uNear, uWide; uniform float uHit, uSeed, uFrame, uExposure, uCalibrate;
float hash(vec2 p) { uvec2 q = uvec2(ivec2(p)) * uvec2(0x3504f333u, 0xf1bbcdcbu); uint h = (q.x ^ q.y) * 741103597u; h ^= h >> 15; h *= 0x2c1b3c6du; return float(h >> 8) / 16777215.; }
vec3 tone(vec3 c) { c = (c * (2.51 * c + .03)) / (c * (2.43 * c + .59) + .14); return pow(clamp(c, 0., 1.), vec3(1. / 2.2)); }
void main() {
  if (uCalibrate > .5) { color = vec4(texture(uImage, uv).rgb, 1.); return; }
  vec2 q = uv;
  if (uHit > .02) { // Chosen columns repeat one row of pixels, up and down from it.
    float column = floor(uv.x * 118.), pick = hash(vec2(column, uSeed * 7.)), row = .48 + .22 * (hash(vec2(uSeed * 11., 3.)) - .5);
    float reach = uHit * (.04 + .24 * hash(vec2(column + 700., uSeed * 13.))) * step(.7, pick), d = uv.y - row;
    if (abs(d) < reach) q.y = row + d * .012;
  }
  vec2 shift = (uv - .5) * uHit * .0105 + vec2(uHit * .0016, 0.);
  vec3 c = vec3(texture(uImage, q + shift).r, texture(uImage, q).g, texture(uImage, q - shift).b);
  c += texture(uNear, uv).rgb * .55 + texture(uWide, uv).rgb * .8;
  vec2 v = uv - .5; c *= 1. - dot(v, v) * .62;
  c = tone(c * .9 * uExposure);
  c = mix(c, c * c * (3. - 2. * c), .38) * vec3(1.01, .99, 1.02);
  color = vec4(c + (hash(gl_FragCoord.xy + vec2(uFrame * 37., uFrame * 91.)) - .5) * .012, 1.);
}`;
