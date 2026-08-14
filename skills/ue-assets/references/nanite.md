# Nanite — UE 5.8 reference

Verify names/defaults against your engine before quoting:

```bash
grep -rn 'TEXT("r\.Nanite' Engine/Source/Runtime/Renderer/Private/Nanite/
grep -rn 'TEXT("r\.Nanite' Engine/Source/Runtime/Engine/Private/
```

## Requirements

- DirectX 12 + **Shader Model 6**, current desktop/console GPU, current drivers
- **SSD strongly recommended** — Nanite streams mesh pages on demand; on spinning disk the pop-in is a hardware problem, not a settings problem
- Deferred renderer only

## Support matrix

| Geometry | Nanite |
|---|---|
| Static mesh | ✅ |
| Skeletal mesh | ✅ (animation LODs, not geometry LODs; VSM support; voxel LODs) |
| Geometry collection | ✅ |
| ISM / HISM / spline mesh | ✅ |
| Foliage painter, landscape grass | ✅ |
| Landscape splines, blueprint splines | ✅ |

| Feature | Status |
|---|---|
| Opaque / Masked materials | ✅ |
| Translucent / additive | ❌ → default material + log warning |
| World Position Offset | ✅ but needs cluster-culling management (see WPO section) |
| Dynamic translate / rotate / non-uniform scale | ✅ |
| Morph targets | ❌ |
| Static displacement (offline adaptive tessellation) | ✅ |
| Dynamic tessellation + programmable displacement | ✅ |
| Decal projection (standard decals) | ✅ |
| Forward rendering, VR stereo, MSAA, lighting channels | ❌ |
| Native ray tracing | fallback meshes by default; `r.RayTracing.Nanite.Mode 1` = experimental native |
| Custom expressions / derivative-dependent material nodes | ⚠️ artifacts possible |

**Instance ceiling: 16,000,000 per scene**, streamed-in instances included. Hard clamp.

## Per-asset settings (Static Mesh Editor → Nanite Settings)

| Setting | What it really controls |
|---|---|
| **Enable Nanite Support** | the toggle. Also settable at import ("Build Nanite") |
| **Fallback Relative Error** | how coarse the fallback mesh is. Drives ray-tracing quality, complex collision accuracy, and non-Nanite-path appearance. Raise it to save memory, lower it when RT shadows/traces look wrong |
| **Position Precision** | vertex position quantization. Auto is right for most assets; forcing high precision on small props wastes memory |
| **Preserve Area** | prevents thin features (wires, railings, foliage cards) from disappearing during simplification |
| **Trim Relative Error** | removes tiny clusters below an error threshold |

Import-time: turn **Generate Lightmap UVs off** unless the project bakes lighting.

## 5.8 foliage additions

| Feature | Note |
|---|---|
| **Nanite Foliage** | instancing + skinned meshes + voxelization + animation + bone-based wind. ~0.1 ms GPU for 100k updating bones (Epic's measurement) |
| **Nanite Assemblies** | micro-instancing of repeated sub-parts — branches, fronds, small hard-surface details. Supplemental for both static and skeletal meshes. This is the mechanism that makes detailed trees affordable |
| **Nanite Pixel Programmable Distance** | foliage property; distance past which pixel-programmable (masked / WPO) material work is skipped. One of the highest-value foliage settings in 5.8 |
| Animation screen-size cutoff | animation auto-stops on trees below a screen-size threshold; wind still affects distant trees for immersion. Applies to grass and shrubs on skeletal meshes too |
| Skinned mesh **WPO Disable Distance** | set it. Unbounded WPO is the top cause of Virtual Shadow Map invalidation storms |
| Handheld raster/culling | significantly improved in 5.8 |
| Readback buffer reuse | 5.8 avoids per-frame reallocation |

## WPO and shadows — the interaction that bites

World Position Offset moves vertices every frame → the primitive's Virtual Shadow Map pages invalidate every frame → VSM cost explodes on wind-animated foliage.

Mitigations, in order:
1. **WPO Disable Distance** per component/asset — kills WPO past N units.
2. **Nanite Pixel Programmable Distance** — skips the pixel-programmable path entirely at distance.
3. `r.Shadow.Virtual.Nanite.AllowTessellationDirectional` / `...AllowTessellationLocal` = 0 — drop Nanite tessellation in shadow passes; usually invisible.
4. `r.Shadow.Virtual.DeferredInvalidationBudget` (5.8) — cap invalidation work per frame; trades shadow update latency for a stable frame time.

Diagnose with the **Virtual Shadow Map → invalidation** viewmode; it names the offending primitive.

## Visualization & profiling

Editor viewmodes: **Nanite Visualization** submenu — Overview, Triangles, Clusters, Instances, Primitives, Material Complexity, Overdraw, Material Count, Evaluate WPO, Pixel Programmable.

Read them like this:

| View | What a bad result looks like |
|---|---|
| Clusters | dense cluster churn on distant geometry → culling isn't working, check bounds |
| Overdraw | hot masked foliage → cut Pixel Programmable Distance |
| Evaluate WPO | large WPO regions at distance → missing WPO Disable Distance |
| Material Count | many materials per pixel → merge material slots |

Runtime:

```
stat nanite
stat GPU                 # Nanite raster/cull passes broken out
ProfileGPU               # or Ctrl+, in editor
r.Nanite.Visualize <mode>
```

Caution from Epic's docs: some visualization modes still don't render Nanite geometry, and normals/UVs previews on very dense meshes in the Static Mesh Editor are unreliable — don't debug shading from those.

## When NOT to use Nanite

- Low-poly / stylized assets under a few thousand triangles — the fixed overhead exceeds the savings.
- Anything that must be translucent.
- Anything driven by morph targets.
- Meshes that exist only as physics proxies or triggers.
- Small UI/prop meshes rendered at trivial screen size.

The honest test: build the scene both ways and compare `stat GPU` + `stat nanite`. On stylized low-poly content, non-Nanite with hand-authored LODs frequently wins.

## Ray tracing interaction

Default: RT uses the **fallback mesh**, not Nanite clusters. Consequences:
- Coarse fallbacks → shadow/reflection mismatch against the visible surface.
- If `r.RayTracing.RayTracingProxies.ProjectEnabled` is on, RT proxies are in play; check proxy quality when RT results look wrong.
- `r.RayTracing.Nanite.Mode 1` enables experimental native Nanite RT. Higher fidelity, higher cost, experimental — flag that clearly if recommending it.

Instance budget for HWRT: keep post-cull instances under ~100k on console (`Stat SceneRendering` → *Ray tracing active instances*), tightened with `r.RayTracing.Culling=3` and `r.RayTracing.Culling.Radius`.
