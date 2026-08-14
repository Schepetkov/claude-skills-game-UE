# Lighting cvars — UE 5.8

Names below were taken from 5.8 doc pages and cross-checked against a 5.8.1 source tree. **Defaults change between hotfixes — confirm against your own engine before quoting a default:**

```bash
grep -rn -A6 'TEXT("r\.Lumen\.ScreenProbeGather\.DownsampleFactor")' \
  Engine/Source/Runtime/Renderer/Private/Lumen/
```

The `FAutoConsoleVariableRef` declaration shows the backing variable's initializer (the true default) and the help text.

---

## Scalability entry points

| Cvar | Values | Notes |
|---|---|---|
| `sg.GlobalIlluminationQuality` | 0–4 | 0 Low (Lumen off) · 1 Medium = **Lumen Lite** · 2 High (60 fps console) · 3 Epic (30 fps console) · 4 Cinematic |
| `sg.ReflectionQuality` | 0–4 | pair with the above; 1 = SSR on smooth surfaces |
| `r.DynamicGlobalIlluminationMethod` | 0 none · 1 Lumen · 2 SSGI (**deprecated in 5.8**) | |
| `r.ReflectionMethod` | 0 none · 1 Lumen · 2 SSR | |
| `r.Lumen.FinalGatherMethod` | 0 = Irradiance Field (Lumen Lite) · 1 = Screen Probe Gather | what Medium flips |

Set per platform in `Platforms/<P>/Config/<P>DeviceProfiles.ini` under `[<Profile> DeviceProfile]` with `+CVars=`. Never bake these into `DefaultEngine.ini` — that defeats scalability.

---

## Lumen — cost levers

Ordered by (win ÷ risk). Apply top-down.

| Cvar | Trade |
|---|---|
| `r.Lumen.Reflections.MaxRoughnessToTraceForFoliage` | set `0.0` — foliage almost never needs traced reflections. Near-free win |
| `r.Lumen.Reflections.DownsampleFactor` | `1` full res, `2` quarter res. Big win, softer reflections |
| `r.Lumen.Reflections.DownsampleCheckerboard` | middle ground between the two |
| `r.Lumen.Reflections.MaxRoughnessToTraceClamp` | ~0.4 default. Below → traced rays; above → free rough specular from GI. Lowering saves rays, flattens glossy surfaces |
| `r.Lumen.Reflections.Allow` | `0` → SSR only. ~1 ms on low-end. Loses off-screen reflection entirely |
| `r.Lumen.ScreenProbeGather.DownsampleFactor` | probe spacing. Higher = cheaper, softer shadowing in GI |
| `r.Lumen.ScreenProbeGather.IntegrateDownsampleFactor` | `2` = half-res integration. Cheap, adds noise + softens normals. A 5.8 Lumen Lite ingredient |
| `r.Lumen.ScreenProbeGather.TracingOctahedronResolution` | rays per probe |
| `r.Lumen.ScreenProbeGather.ScreenTraces.HZBTraversal.SkipUnlitHits` | 5.8 addition, part of Lumen Lite |
| `r.Lumen.ScreenProbeGather.RadianceCache.ProbeResolution` | world-space radiance cache probe fidelity |
| `r.Lumen.ScreenProbeGather.RadianceCache.NumProbesToTraceBudget` | probes updated per frame — caps the cost spike when the camera moves fast |
| `r.Lumen.ScreenProbeGather.RadianceCache.GridResolution` | grid spacing; coarser reduces pops, costs quality |
| `r.LumenScene.DirectLighting.UpdateFactor` | surface cache direct-light refresh. Higher = cheaper, laggier |
| `r.LumenScene.Radiosity.UpdateFactor` | indirect bounce refresh rate |
| `r.LumenScene.DirectLighting.MaxLightsPerTile` | caps per-tile light cost in the surface cache |
| `r.Lumen.HardwareRayTracing.MaxIterations` | early ray termination; too low → over-occlusion artifacts |
| `r.Lumen.TraceMeshSDFs` | `0` → SWRT uses merged Global Distance Field only |
| `r.Lumen.HeightFog` / `r.Lumen.HeightFogOnGI` | **new default-on in 5.8**; explains fog appearance changes after upgrade |
| `r.Lumen.AsyncCompute` | `0` **only while profiling**. Leave on in shipping |

---

## Ray tracing scene

| Cvar | Note |
|---|---|
| `r.RayTracing` | master gate for HWRT and MegaLights |
| `r.RayTracing.Culling` | `3` recommended in Epic's Lumen performance guide |
| `r.RayTracing.Culling.Radius` | e.g. `15000`. Tighten aggressively — instance count is the HWRT cost driver |
| `r.RayTracing.RayTracingProxies.ProjectEnabled` | RT proxies for Nanite meshes |
| `r.RayTracing.Nanite.Mode` | `1` = experimental native Nanite ray tracing instead of fallback meshes |

Budget: **< ~100k post-cull instances** on console. Measure via `Stat SceneRendering` → *Ray tracing active instances*.

Per-primitive flags that matter more than any cvar: **Visible In Ray Tracing** (turn off on skyboxes/shells), **Affects Distance Field Lighting** (turn off on clutter).

---

## MegaLights (names verified in 5.8.1 source)

| Cvar | Note |
|---|---|
| `r.MegaLights.Supported` | platform gate |
| `r.MegaLights.EnableForProject` | what the Project Settings checkbox writes |
| `r.MegaLights.Allowed` | runtime allow/deny — the one to put in device profiles. **Not** `r.MegaLights.Allow`, despite the docs |
| `r.MegaLights.DirectionalLights` | **off by default** |
| `r.MegaLights.DownsampleMode` | primary perf lever |
| `r.MegaLights.NumSamplesPerPixel` | secondary perf lever |
| `r.MegaLights.MinSampleWeight` | sample rejection |
| `r.MegaLights.LightAttenuationFalloff` | `0` disables the light-culling heuristic |
| `r.MegaLights.GuideByHistory` | temporal guiding — reduces noise, can add ghosting |
| `r.MegaLights.LightingDataFormat` | precision/memory |
| `r.MegaLights.WaveOps`, `r.MegaLights.FastClear`, `r.MegaLights.HairStrands.FastClear` | platform-level micro-opts |
| `r.MegaLights.ScreenTraces.Quality` | new in 5.8 |
| `r.MegaLights.Debug`, `.Debug.CursorX/Y`, `.Debug.LightId`, `.Debug.VisualizeLight`, `.Debug.VisualizeTraces`, `.Debug.VolumeSliceIndex` | per-pixel debugging |
| `r.MegaLights.Reset` | reset temporal history |
| `r.MegaLights.SimpleLightMode` | particle light handling |

Per-light properties: **Allow MegaLights**, **MegaLights Shadow Method** (Ray Tracing | Virtual Shadow Maps).

---

## Virtual Shadow Maps

| Cvar | Note |
|---|---|
| `r.Shadow.Virtual.DeferredInvalidationBudget` | 5.8; default infinite. Cap it to flatten frame-time spikes at the cost of shadow update latency |
| `r.Shadow.Virtual.PrefilteredDistant.ProjectEnable` | 5.8 **experimental** prefiltered distant shadows |
| `r.Shadow.Virtual.Nanite.AllowTessellationDirectional` | disable Nanite tessellation in directional shadow pass |
| `r.Shadow.Virtual.Nanite.AllowTessellationLocal` | same for local lights |
| `r.Shadow.Virtual.ResolutionLodBiasDirectional` / `...Local` | global quality/perf bias |
| `r.Shadow.Virtual.Cache` | caching — turning it off is a diagnostic, never a fix |

Diagnose with the **Virtual Shadow Map** viewmode; page allocation and invalidation views identify the offending primitive by name.

Related non-VSM: `r.GlobalDistanceField.Debug.LogModifiedPrimitives` finds static actors being moved at runtime — the root cause of most invalidation storms.

---

## Post-process / upscaling (5.8 changes)

| Cvar | Note |
|---|---|
| `r.DOF.PreferLowerBitDepth` | 5.8; lowers DoF buffer bit depth on bandwidth-bound platforms. Only effective with low recombine/accumulator quality |
| `r.Translucency.EarlyVelocityPass` | `2` = early velocity pass moved after volumetric cloud reconstruction (5.8) |
| `r.Water.SingleLayer.VelocityOutputPass` | `0` none · `1` prepass (**new default**) · `2` legacy base pass |
| `r.Mobile.Upscale.Quality` | 5.8, mobile upscaling control |

5.8 mobile: **multi-pass deferred is now the default**; forward rendering is opt-in. Mobile also gained SSAO, SSR, deferred decals, and contact shadows.

---

## Material / shader memory (5.8)

| Cvar | Note |
|---|---|
| `r.Material.StripUnusedDefaultTextures` | strips unused default textures at runtime — straight memory win |
| `r.Material.UseShaderCompilationParameters` | shader layout determined from translation output |

5.8 reduced shader permutations across volumetric fog, VSM, Substrate, MegaLights and Lumen. Diagnostics: `recompileshaders listtypes` now reports `PermutationCount`; the Material Editor shows a **Total Shaders** viewport overlay; `UMaterialEditingLibrary::ListShaders` exposes it to editor script.
