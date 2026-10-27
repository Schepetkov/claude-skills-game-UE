---
name: ue-lighting
description: Unreal Engine 5.8 lighting and rendering — Lumen (incl. new Lumen Lite), MegaLights, Virtual Shadow Maps, Substrate, distance fields, reflections, and scalability/device profiles. Use when setting up or debugging scene lighting, choosing GI/shadow/reflection methods, hitting a GPU frame budget, fixing noise/ghosting/leaking/flicker, or authoring quality tiers per platform.
license: MIT
metadata:
  engine: "Unreal Engine 5.8"
---

# UE 5.8 Lighting & Rendering

## Ground truth rule (read first)

**Grep the engine source before quoting any cvar.** Epic's docs lag the source. Verified drift as of 5.8.1: the MegaLights doc page says `r.MegaLights.Allow`; the source declares `r.MegaLights.Allowed`, plus `r.MegaLights.EnableForProject` and `r.MegaLights.Supported` which the doc omits entirely.

Locate the engine source (see [Finding the engine source](#finding-the-engine-source) at the bottom), then:

```bash
# authoritative cvar list for a subsystem — name, default, help text
grep -rn 'TEXT("r\.Lumen\.' Engine/Source/Runtime/Renderer/Private/Lumen/
grep -rn 'TEXT("r\.MegaLights' Engine/Source/Runtime/Renderer/Private/MegaLights/
grep -rn 'TEXT("r\.Shadow\.Virtual' Engine/Source/Runtime/Renderer/Private/
```

The `FAutoConsoleVariableRef` declaration shows the backing variable's initializer — that is the true default, not whatever a doc page claims.

## Step 0: read the project's current renderer config

Before advising anything, check `Config/DefaultEngine.ini` for these — they change every recommendation that follows:

| Setting | Why it matters |
|---|---|
| `r.DynamicGlobalIlluminationMethod` | `0` none · `1` Lumen · `2` SSGI (**deprecated in 5.8**) |
| `r.ReflectionMethod` | `0` none · `1` Lumen · `2` SSR |
| `r.Lumen.TraceMeshSDFs` | `0` = software tracing uses the merged Global Distance Field only |
| `r.RayTracing` | gates HWRT and MegaLights |
| `r.Substrate` | if on, material advice must be Substrate-aware — do not mix in legacy shading-model assumptions |
| `r.DefaultFeature.*` | project-wide defaults that silently override what you see in a fresh level |

## Decision tree: pick the GI/reflection tier first

Quality tiers in 5.8 are driven by `sg.GlobalIlluminationQuality` and `sg.ReflectionQuality`:

| Level | Value | What it is | Target |
|---|---|---|---|
| Cinematic | 4 | Movie Render Queue | offline |
| Epic | 3 | Screen Probe Gather, full Lumen | 30 fps console |
| High | 2 | Screen Probe Gather, trimmed | 60 fps console |
| **Medium — "Lumen Lite"** | 1 | Irradiance Field final gather (`r.Lumen.FinalGatherMethod=0`) + SSR on smooth surfaces | **60 fps on PS5 / handhelds / Switch 2 / low-end PC** |
| Low | 0 | Lumen off | fallback |

**Lumen Lite is the headline 5.8 feature here**: ~2× faster than Lumen high quality while keeping dynamic GI and the art direction. It is the new default path for current-gen handhelds. If the project has any low-end target, author against Medium and verify it looks right — don't treat it as a degraded afterthought.

**SSGI is deprecated in 5.8** in favour of Lumen Lite. If you find `r.SSGI.*` in configs, that's dead weight — remove it rather than tuning it.

Set per-platform, not globally:

```ini
; <Project>/Platforms/<Platform>/Config/<Platform>DeviceProfiles.ini
[<Profile> DeviceProfile]
+CVars=sg.GlobalIlluminationQuality=2
+CVars=sg.ReflectionQuality=2
```

Baking these into `DefaultEngine.ini` defeats scalability — always resist that.

## Software vs Hardware ray tracing for Lumen

| | Software RT | Hardware RT |
|---|---|---|
| Traces | merged Global Distance Field | real geometry via TLAS |
| Cost driver | distance-field resolution, GDF updates | instance count, TLAS rebuild each frame |
| Scales with overlap? | no — indifferent to instance overlap | yes — badly |
| Quality | approximate, leaks through thin geometry | accurate |
| Use when | broad hardware target, dense/overlapping scenes | current-gen only, and you also want MegaLights |

HWRT budget rule: keep post-cull instances **under ~100k** on console. Check with `Stat SceneRendering` → *Ray tracing active instances*.

Culling levers:

```
r.RayTracing.Culling=3
r.RayTracing.Culling.Radius=15000
```

Per-mesh: disable **Affects Distance Field Lighting** on meshes that shouldn't contribute to SWRT; disable **Visible In Ray Tracing** on skyboxes and giant shells — an overlapping skybox in the RT scene is one of the most common Lumen cost bugs.

## MegaLights — 5.8 status: production-ready

MegaLights replaces the per-light shadow/shading path with a stochastic sampler at **constant cost**: many lights no longer scale cost linearly, but quality degrades as lighting complexity per pixel rises. That's the trade to explain — it is not free quality, it is *predictable* cost.

Enable: **Project Settings → Rendering → Direct Lighting**. It will prompt to also enable Support Hardware Ray Tracing — accept; MegaLights should run with **Lumen HWRT** so both share the RT scene overhead.

Real cvar names in 5.8.1 (`Runtime/Renderer/Private/MegaLights/`):

| Cvar | Purpose |
|---|---|
| `r.MegaLights.Supported` | platform support gate |
| `r.MegaLights.EnableForProject` | project-level enable (what the settings checkbox writes) |
| `r.MegaLights.Allowed` | runtime allow/deny — use in scalability & device profiles |
| `r.MegaLights.DirectionalLights` | directional light support (**off by default**) |
| `r.MegaLights.DownsampleMode` | primary quality/perf lever |
| `r.MegaLights.NumSamplesPerPixel` | second quality/perf lever |
| `r.MegaLights.LightAttenuationFalloff` | tightens light influence range; `0` disables the culling heuristic |
| `r.MegaLights.GuideByHistory` | temporal sample guiding |
| `r.MegaLights.MinSampleWeight` | sample rejection threshold |
| `r.MegaLights.ScreenTraces.Quality` | new in 5.8 |
| `r.MegaLights.Debug 1`, `.Debug.VisualizeTraces`, `.Debug.VisualizeLight`, `.Debug.LightId` | per-pixel ray visualization |

Per-light: **Allow MegaLights** (opt a light out) and **MegaLights Shadow Method** — Ray Tracing (default) or Virtual Shadow Maps. VSM per light re-adds per-light CPU/GPU/memory cost, so use it only for the few lights where RT shadows visibly fail.

5.8 improvements: much lower noise, and *early cull lights by light power* cuts sampling ~20% in Epic's test scenes.

**Hard limits** — check these before recommending MegaLights:
- Incompatible with the **Forward Renderer**.
- Not supported: mobile, Switch (gen 1), PS4/Xbox One.
- Unsupported surfaces: water, clouds, heterogeneous volumes, local volumetrics.
- The RT scene uses simplified Nanite proxies → possible shadow artifacts on high-detail meshes.
- Front Layer Translucency is expensive when it covers many screen pixels.

MegaLights **replaces** shadow maps, distance field shadows, ray traced shadows, deferred shading of lights, volumetric fog shadowing, and VSM projection. Do not tune those in parallel — you'll be tuning dead code paths.

## Virtual Shadow Maps

VSM cost is dominated by **invalidations**, not resolution. Anything that moves invalidates pages.

5.8 additions:

| Cvar | Note |
|---|---|
| `r.Shadow.Virtual.DeferredInvalidationBudget` | throttle invalidation work per frame; default is infinite (unbounded). Setting a budget trades shadow latency for stable frame time — good on a spiky scene |
| `r.Shadow.Virtual.PrefilteredDistant.ProjectEnable` | **experimental** prefiltered distant shadows |
| `r.Shadow.Virtual.Nanite.AllowTessellationDirectional` / `...AllowTessellationLocal` | disable Nanite tessellation in shadow passes — usually invisible, often a real win |

Debug with the **Virtual Shadow Map** viewmode. Look at *page allocation* and *invalidation* views first — 90% of VSM problems are a WPO material or a "static" actor being moved every frame.

Two classic culprits:
- A material with World Position Offset on a large mesh → invalidates its pages every frame. Set a **WPO Disable Distance**.
- An actor marked Static but transformed at runtime. Find them: `r.GlobalDistanceField.Debug.LogModifiedPrimitives`.

## Lumen tuning order (cheapest wins first)

1. **Fix the scene, not the cvars.** Overlapping meshes in the RT/DF scene, skyboxes visible in ray tracing, and runtime-moved static actors dominate everything below.
2. `r.Lumen.Reflections.MaxRoughnessToTraceForFoliage 0.0` — foliage rarely needs dedicated reflection rays.
3. `r.Lumen.Reflections.DownsampleFactor 2` or `r.Lumen.Reflections.DownsampleCheckerboard` — quarter/half-res reflections.
4. `r.Lumen.Reflections.MaxRoughnessToTraceClamp` (default ~0.4) — below the threshold traces rays, above gets free rough specular from GI.
5. `r.Lumen.ScreenProbeGather.DownsampleFactor` / `...IntegrateDownsampleFactor 2` / `...TracingOctahedronResolution` — the core final-gather cost knobs. Higher downsample = softer, noisier.
6. `r.LumenScene.DirectLighting.UpdateFactor`, `r.LumenScene.Radiosity.UpdateFactor`, `r.LumenScene.DirectLighting.MaxLightsPerTile` — surface cache refresh rate. Slower update = cheaper but laggier lighting response.
7. `r.Lumen.Reflections.Allow 0` — drop to SSR entirely, ~1 ms on low-end.

5.8 note: height fog is now applied to Lumen by default (`r.Lumen.HeightFog 1`, plus `r.Lumen.HeightFogOnGI`). If fog looks different after upgrading, that's why.

## Profiling lighting

```
r.Lumen.AsyncCompute 0        # REQUIRED for accurate per-pass timing — otherwise Lumen hides in async
stat GPU                      # three Lumen passes broken out
ProfileGPU                    # Ctrl+, in editor; opens the GPU Visualizer
r.ProfileGPU.TableFormatting  # 5.8: compact ProfileGPU output
stat SceneRendering           # ray tracing active instances, draw counts
stat unit                     # 5.8: now also shows GPU VRAM usage + budget
```

Always disable async compute before drawing conclusions about Lumen cost. Measuring with it on is the most common way people "prove" Lumen is cheap when it isn't.

Editor viewmodes worth naming: **Lumen → Performance Overview** (which pixels need reflection rays), **Lumen Scene**, **Surface Cache**, **Virtual Shadow Map → Page Allocation**.

## Symptom → cause table

| Symptom | Look at |
|---|---|
| Light leaking through thin walls | SWRT + thin geometry. Thicken, or move to HWRT. Check coverage in **Lumen Surface Cache** viewmode |
| Noisy/grainy indirect | Screen probe downsample too aggressive; `IntegrateDownsampleFactor`, `TracingOctahedronResolution` |
| GI lags behind a moving light | `r.LumenScene.DirectLighting.UpdateFactor` too high |
| Shadow flicker / shimmer under motion | VSM page invalidation storm — WPO material or moving "static" actor |
| Reflections vanish at grazing angles | `MaxRoughnessToTraceClamp` too low; or SSR fallback with no off-screen data |
| Sudden GPU spike near one prop | that mesh is in the RT scene and huge — check **Visible In Ray Tracing** |
| Frame time spikes only on camera cuts | 5.8 fixed a TSR memory spike at cuts/teleports; verify the engine version and check TSR history reset |
| Distance fields missing on an iGPU | 5.8 removed the old driver restriction — DFs now work on integrated GPUs. Note DF shader permutations are stripped when disabled in project settings, so toggling requires a shader rebuild |

## Substrate

If `r.Substrate=True`:

- Material authoring changes: slabs, coverage, and `r.Substrate.ProjectGBufferFormat` drive GBuffer layout and cost.
- 5.8 reduced Substrate shader permutations — compile times should beat 5.6/5.7. If they don't, check for a stale DDC before blaming Substrate.
- Do not mix legacy shading-model advice with Substrate materials. Grep `Engine/Source/Runtime/Renderer/Private/Substrate/` when unsure how a feature interacts.

## Finding the engine source

| Engine type | Where the source lives |
|---|---|
| **Source build** | The `EngineAssociation` GUID in the `.uproject` maps to a path under `HKCU:\SOFTWARE\Epic Games\Unreal Engine\Builds` (Windows) or `~/.config/Epic/UnrealEngine/Install.ini` (Linux). Full `Engine/Source/` tree — everything here is greppable. |
| **Launcher install** | `EngineAssociation` is a version string (`"5.8"`). Path under `HKLM:\SOFTWARE\EpicGames\Unreal Engine\<version>` → `InstalledDirectory`. Ships public headers but **not** the `Private/` sources where nearly all rendering cvars are declared. |

With only a Launcher install, confirm cvar names at runtime instead: the console autocompletes them, and `DumpConsoleCommands` writes the full list to `Saved/`. Say explicitly which method you used when quoting a name.

## Related

- [references/cvars.md](references/cvars.md) — grouped cvar tables with what each actually trades away

## Field notes from other projects

`field-notes/` next to this file (when present) holds lessons from other agents' retros, one per file. Before
debugging a symptom, `grep -ril "<symptom words>" field-notes/`. `status: observed` means seen in practice but not
yet checked against source — verify before relying on it; once checked, promote it into the tables above.
