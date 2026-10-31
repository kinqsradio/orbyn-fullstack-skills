# Optional local graphics and simulation profile

This code extends the existing composition/review owners; it is not a new skill,
external authoring application or hosted renderer. Ordinary DOM/SVG work does not
install this profile. Source JSON is inert data. Trusted component/factory code
supplies renderer implementations; JSON never supplies imports, scripts or GLSL.

## Prepare dependencies outside managed source

The agent resolves actual paths and performs an authorized setup. Copy this
folder's `package.json` and `package-lock.json` into a **new ignored task output**,
then use `npm ci --ignore-scripts --no-audit --no-fund --prefix` for that exact
directory, with a task-owned cache. Keep `node_modules`, caches, generated bundles
and runtime evidence outside `skills/`; the library manifest inspects every file,
not just Git-tracked files. Never install into a consuming application's shared
global settings or copy shared instructions into its repository.

The exact released tuple in the lock is:

| Package | Version | License | Purpose |
|---|---|---|---|
| three | 0.186.1 | MIT | Scene, raster/WebGPU renderers, local glTF and controls |
| postprocessing | 6.39.5 | Zlib | Ordered WebGL raster effect graph |
| three-gpu-pathtracer | 0.0.27 | MIT | Separate WebGL and WebGPU progressive backends |
| three-mesh-bvh | 0.9.17 | MIT | Pathtracer acceleration structures |
| xatlas-web | 0.1.0 | MIT | Declared pathtracer peer; UV unwrap is not enabled by this adapter |
| jolt-physics | 1.1.1 | MIT | Single-thread embedded-WASM physics binding |
| esbuild (build only) | 0.25.5 | MIT | Local ESM dependency closure; not a runtime authoring app |

The postprocessing peer range includes this Three release; current upstream main
is not substituted for it. Lock integrity identifies registry tarballs. Jolt's
registry `gitHead` is `cccf9d568e8cbae1569ba8e1a24de731591ba0a8` in
[JoltPhysics.js](https://github.com/jrouwe/JoltPhysics.js/tree/cccf9d568e8cbae1569ba8e1a24de731591ba0a8).
Its binding has its own MIT notice; the separately reviewed JoltPhysics C++ main
does not establish the binding's build identity. All full dependency notices are
copied from the installed exact packages into each generated profile.

Build a new browser closure with the trusted helper:

```sh
node /ABS/library/skills/orbyn-ui-design/examples/spatial-review/motion/graphics/build-profile.mjs \
  --profile /ABS/ignored/prepared-dependencies --out /ABS/ignored/new-browser-profile
```

The helper checks the source/installed lock and exact versions, then writes three
local ESM bundles, applicable legal-comment files, `NOTICES.md` and `profile.json`.
The receipt records builder/lock/module hashes and byte sizes. It refuses an
existing output and a profile larger than 32 MiB. The observed six-file bundle
closure is about 6.6 MiB; dependencies occupy about 84 MiB separately. No library
source, generated bundle or authoring asset is silently downloaded at playback.
No Draco/Meshopt/KTX2 decoder, texture, remote font, denoiser weight or model is
included. Such features require a separately declared, licensed local closure.

## Executable adapters

- [three.mjs](../three.mjs): `validateScene`, pure `sampleScene`,
  `localAssetResolver`, `createThreeScene`, `threeComponent`,
  `createAsyncResource` and an explicit `GraphicsUnavailable` error.
  A scene has version/source revision, camera/lights, stable parts, optional
  parent IDs and source-hashed local assets. Built-in geometry supports box,
  sphere, cylinder and plane; a trusted geometry-factory map supports new code
  without a universal JSON switch. Local glTF is parsed with an asset closure;
  camera/pose/picking share actual scene transforms. Part picking returns source
  revision, stable ID and visible hit point. Orbit takeover pauses the caller.
  Missing context, failed asset digest and loss are explicit. Owners dispose
  meshes, materials, textures, controls, listeners, renderer and object URLs.
- [simulation.mjs](../simulation.mjs): `createJoltWorld` and
  `createSimulation` implement fixed ticks and ordered events; `add`, `remove`,
  external property changes, gravity and impulses are explicit events.
  Checkpoints contain engine bytes, body definitions/membership, Jolt body IDs,
  gravity, event cursor, tick rate and source identity. Restore rebuilds the
  matching world before applying engine state; stale source/profile refuses.
  The source/event spec is captured on construction. Native C++ and arbitrary
  cross-build checkpoints are not qualified by a WASM result. Checkpoints are
  owned binary artifacts, not arbitrary editable scene JSON or a secure parser
  for untrusted native-state bytes.
- `sampleParticles` is an original, deterministic seeded time sampler. It does
  not override global randomness or approximate a seek with one clamped delta.
  `createParticleCloud` supplies lightweight points or actual small meshes for
  a pathtracer that does not render point sprites. Both consume the same sampled
  positions. This does not import a GUI particle editor or all Quarks behaviors.
- [effects.mjs](../effects.mjs): `validateEffects` and `createEffectGraph`
  support ordered bloom, vignette, brightness/contrast, depth of field and final
  tone mapping. Color/alpha/HDR settings have one owner; explicit delta avoids
  a wall-clock timer during sampled export. Composer targets/effects are disposed
  and the renderer's prior tone-mapping state is restored.
- `createProgressiveRenderer` serializes authored frames, rebuilds scene/BVH
  state, resets accumulation and waits for measured sample completion. Geometry,
  material, transform or camera changes cannot reuse the preceding frame's
  samples. The bounded default uses `setScene`, because an exposed
  `setSceneAsync` method does not prove a local BVH worker was installed.
  A trusted worker-qualified profile may supply `buildScene` explicitly.
  GPU device/context loss, deadlines, no-progress, superseding frames and owner
  cancellation leave failure receipts. **Await `dispose()`** before releasing its
  renderer, scene or page; it settles pending work before freeing tracer resources.

WebGL and WebGPU are separate backends. The WebGL composer is not automatically a
WebGPU pathtracer postprocess pipeline. Samples, GPU/driver/runtime, seed, frame
identity, cost and unsupported cells belong in delivery evidence. Stable noise
does not promise byte-identical images across arbitrary devices.

## Original demonstration and checks

Serve the existing motion directory and an explicitly built profile from a local
server, then open [graphics-demo.html](../graphics-demo.html) with a same-origin
`?profile=/path/to/profile/`. This six-second example has an original local GLB,
two bodies with changes to membership/properties, seeded particles, camera
takeover/picking and four selectable backends. It loads the fixed profile module
names only after checking their receipt hashes. It does not fetch a remote CDN.

Source: [scene](../graphics-scene.json), [simulation/event log](../graphics-simulation.json),
[demo code](../graphics-demo.mjs) and [original marker](../graphics-demo-assets/marker.glb).
The marker is code-authored geometry, not a downloaded sample model. Its current
SHA-256 is `2eb2262d608fcb771f3bedaaa25eb6fa37dea4786342b03c3b6103ffdb72841b`.

Run the focused tests with an explicit prepared profile:

```sh
ORBYN_GRAPHICS_PROFILE=/ABS/ignored/prepared-dependencies \
  node --test /ABS/library/skills/orbyn-ui-design/examples/spatial-review/motion/graphics.test.mjs
```

Without the variable, tests of actual Three/glTF/Jolt report skipped. Unit
renderer/tracer controls test lifecycle and failures; they are not GPU renders.
Actual Jolt WASM tests exercise checkpoint replay, parameter edits, gravity,
body removal/re-addition and cancellation. Actual Three tests check hierarchy,
glTF parsing and ray picking with a unit renderer. Browser raster/effects and
progressive backend qualification must inspect actual images and reported sample
counts separately. Neither package installation nor the test names qualify a GPU.

The standalone settings download is an export request, not proof of a repository
write. A prepared `graphics-review-v1` package uses the **existing** source-bound
review document and `/api/review` token/revision writer. Its graphics-v1 context
retains stable part/model identity, actual camera position/target, scene time and
physics tick, renderer mode, material/light parameters and viewport. Zero-comment
settings saves, anchored feedback, readback and paused reopening use that same
store, not a separate graphics database. Source changes and revision conflicts
refuse the write while retaining current local feedback. Examples demonstrate
techniques rather than restrict domains or styles.
